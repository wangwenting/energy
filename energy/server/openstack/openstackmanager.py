from oslo.config import cfg
import json
from energy.common import log
import time


from energy.server import manager
from energy.server.openstack.openstackserver import OpenstackServiceIns
from energy.server.openstack.driver import Driver
from energy.common import periodic_task
from energy.db import api as db_api
from energy import exception
from energy.operation.novaworker import NovaWorker
from energy.common import utils

LOG = log.getLogger(__name__)

nova_strategy_opts = [
    cfg.StrOpt('dispatch',
               default='THERMAL',
               help='The opentasck dispatch vm echedule'),
    cfg.StrOpt('migration',
               default='OUTLETTEMP',
               help='The openstack migration vm schedule'),
    cfg.StrOpt('asm_enabled',
               default=False,
               help='The Host Power on and off option'),
    cfg.StrOpt('mig_enabled',
               default=False,
               help='openstack migation option which control vm if not migration'),
    cfg.StrOpt('asm_threshold',
               default=80,
               help='power on and off margin'),
    cfg.StrOpt('outlet_temp',
               default=40,
               help='the migration of outlet_temp margin'),
    ]

CONF = cfg.CONF
CONF.register_opts(nova_strategy_opts, group='openstack')


class Lock(object):
    def __init__(self, lock_time=0):
        self.default_lock_time = lock_time
        self.locked_time = time.time()
        self.lock_status = False

    def is_locked(self):
        if not self.lock_status:
            return self.lock_status
        if self.lock_time:
            _t = time.time()
            if _t > (self.locked_time + self.lock_time):
                self.lock_status = False
            else:
                return int(self.lock_time - _t + self.locked_time)
        return self.lock_status

    def lock(self, lock_time=0):
        self.lock_time = lock_time if lock_time else self.default_lock_time
        self.locked_time = time.time()
        self.lock_status = True

    def unlock(self):
        self.lock_status = False


class StrategyLock(object):

    _lock = {}

    def __new__(cls, *args, **kwargs):
        if '_inst' not in vars(cls):
            cls._inst = super(StrategyLock, cls).__new__(cls, *args, **kwargs)
        return cls._inst

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            self._lock.setdefault(k, Lock(**v))

    def get(self, name):
        if name in self._lock:
            return self._lock[name]


class OpenstackManager(manager.ThriftManager):

    def __init__(self, host=None):
        super(OpenstackManager, self).__init__(host=None)
        self.driver = Driver()
        self.worker = NovaWorker()
        try:
            config = db_api.op_config_get()
            self.driver.set_dispatch(config.dispatch)
            self.driver.set_migration(config.migration)
            self.set_asm_enabled(config.asm_enabled)
            self.set_mig_enabled(config.mig_enabled)
        except exception.QueryResultEmptyException, e:
            LOG.info("The Table openstack_config table is empty, \
                      OpenstackManager First Init")
            print("The Table openstack_config table is empty")
            dispatch = CONF.openstack.dispatch
            migration = CONF.openstack.migration
            asm_enabled = CONF.openstack.asm_enabled == str(True)
            mig_enabled = CONF.openstack.mig_enabled == str(True)
            asm_threshold = CONF.openstack.asm_threshold
            mig_threshold = json.dumps({"outlet_temp": int(CONF.openstack.outlet_temp)})
            data = {"dispatch": dispatch,
                    "migration": migration,
                    "asm_enabled": asm_enabled,
                    "mig_enabled": mig_enabled,
                    "asm_threshold": asm_threshold,
                    "mig_threshold": mig_threshold}

            self.driver.set_dispatch(dispatch)
            self.driver.set_migration(migration)
            self.set_asm_enabled(asm_enabled)
            self.set_mig_enabled(mig_enabled)
            try:
                db_api.op_config_create(data)
            except Exception, e:
                LOG.info("When First Init Openstack Error:%s " % e.message)
                print("When First Init Openstack Error:%s " % e.message)

    def add_service(self):
        self._services.add_thread(OpenstackServiceIns.run_service, self)

    @periodic_task.periodic_task
    def update_host_status(self):
        self.driver.update_host_status()

    @periodic_task.periodic_task
    def power_tactics(self):
        LOG.info("Start Power Tactics the asm_enabled is %s" % self.asm_enabled())
        if self.asm_enabled():
            LOG.info("Start POWER Tactics")
            power_on_lock = StrategyLock(power_on_lock={'lock_time': 240})\
                                        .get('power_on_lock')
            LOG.debug("WTWANG TEST POWER TACTICS")
            if power_on_lock.is_locked():
                LOG.info("Locked by power")
                LOG.info("WTWANG lock time %s" % power_on_lock.is_locked())
                return []
            status, ret = self.driver.power_tactics()
            if ret and status == "ON":
                LOG.info("Locked by power on")
                power_on_lock.lock()
            elif ret and status == "OFF":
                LOG.info("Locked by power off")
                power_on_lock.lock(30)
            return ret

    @periodic_task.periodic_task
    def migration_tactics(self):
        LOG.info("Start Migration Tactics the mgi_enabled is:%s" % self.mig_enabled())
        if self.mig_enabled():
            LOG.info("Start Migration Tactics")
            LOG.info("Current dispatch = %s migration = %s" % (self.driver.get_dispatch(),
                                                               self.driver.get_migration()))
            power_on_lock = StrategyLock(power_on_lock={'lock_time': 240}).get('power_on_lock')

            if power_on_lock.is_locked():
                LOG.info("Locked by power on")
                LOG.info("WTWANG lock time %s" % power_on_lock.is_locked())
                return

            instance_event_lock = StrategyLock(instance_event_lock={'lock_time': 30}).get(
                                               'instance_event_lock')
            if instance_event_lock.is_locked():
                LOG.info("Locked by create instance or migration")
                LOG.info("WTWANG lock time %s" % instance_event_lock.is_locked())
                return
            vms = self.worker.get_vms_info()["vm"]
            for vm in vms:
                print(vm)
                if vm['status'] != "ACTIVE":
                    instance_event = True
            else:
                instance_event = False
            if instance_event:
                instance_event_lock.lock()
            self.driver.migration_tactics()

    def thermal_low_temp_host_select(self, request):
        try:
            result = db_api.telemetry_get_all()
        except exception.QueryResultEmptyException, e:
            LOG.info("Get telemetry data from db error:%s" % e.message)
            return json.dumps({"code": 1006, "describe": "Thermal Low Temp \
                               Host Select Db Error No Data"})
        services = db_api.service_get_by_service_name(CONF.service_name)

        infos = []
        for service in services:
            if utils.service_is_up(service):
                for re in result:
                    if service.hostname == re.hostname:
                        infos.append({"host": re.hostname,
                                      "thermal": re.inlet_temp})
                        break
        LOG.info("infos %s" % infos)
        infos.sort(lambda x, y: cmp(x["thermal"], y["thermal"]))
        host_cap = {}
        ret = db_api.op_hostusage_get_all()
        for r in ret:
            if r.vcpu_used >= r.vcpu_num:
                host_cap[r.hostname] = False
            else:
                host_cap[r.hostname] = True

        ret_host = []
        for info in infos:
            if host_cap[info['host']]:
                ret_host.append(info['host'])
                break

        LOG.info("Ret value:%s" % ret_host)
        instance_event_lock = StrategyLock(instance_event_lock={'lock_time': 30}).get(
                                           'instance_event_lock')
        instance_event_lock.lock()
        return json.dumps(ret_host)

    def cups_low_workload_host_select(self, request):
        try:
            result = db_api.telemetry_get_all()
        except exception.QueryResultEmptyException, e:
            LOG.info("Get telemetry data from db error:%s" % e.message)
            return json.dumps({"code": 1006, "describe": "Thermal Low Temp \
                               Host Select Db Error No Data"})
        services = db_api.service_get_by_service_name(CONF.service_name)

        infos = []
        for service in services:
            if utils.service_is_up(service):
                for re in result:
                    if service.hostname == re.hostname:
                        infos.append({"host": re.hostname,
                                      "cups": re.index_cups})
                        break
        LOG.info("infos %s" % infos)
        infos.sort(lambda x, y: cmp(x["cups"], y["cups"]))

        host_cap = {}
        ret = db_api.op_hostusage_get_all()
        for r in ret:
            if r.vcpu_used >= r.vcpu_num:
                host_cap[r.hostname] = False
            else:
                host_cap[r.hostname] = True

        ret_host = []
        for info in infos:
            if host_cap[info['host']]:
                ret_host.append(info['host'])
                break

        LOG.info("Ret value:%s" % ret_host)

        instance_event_lock = StrategyLock(instance_event_lock={'lock_time': 30}).get(
                                           'instance_event_lock')
        instance_event_lock.lock()
        return json.dumps(ret_host)

    def get_dispatch(self):
        return self.driver.get_dispatch()

    def get_migration(self):
        return self.driver.get_migration()

    def set_dispatch(self, dispatch):
        self.driver.set_dispatch(dispatch)

    def set_migration(self, migration):
        self.driver.set_migration(migration)

    def set_asm_enabled(self, asm):
        self._asm_enabled = asm

    def set_mig_enabled(self, mig):
        self._mig_enabled = mig

    def is_dispatch(self, dispatch):
        return self.driver.is_dispatch(dispatch)

    def asm_enabled(self):
        return self._asm_enabled

    def mig_enabled(self):
        return self._mig_enabled
