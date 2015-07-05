from oslo.config import cfg
import json
import subprocess

from energy.common import log

from energy.interface.openstack import OpenstackService

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

from energy.db import api as db_api
from energy import exception

LOG = log.getLogger(__name__)


energy_openstack_opts = [
    cfg.StrOpt('openstack_ip',
               required=True,
               help='the energy-server for openstack ip'),
    cfg.IntOpt('openstack_port',
               default='10012',
               help='the energy-server for openstack port'),
    cfg.StrOpt("service_name",
               default='energy-sampler',
               help='get services status by service name')
]

CONF = cfg.CONF
CONF.register_opts(energy_openstack_opts)


class OpenstackServiceHandler(object):
    def __init__(self, manager):
        self.manager = manager

    def get_openstack_config(self, request):
        try:
            result = db_api.op_config_get()
        except exception.QueryResultEmptyException, e:
            LOG.info("Get OpConfig From Db Error:%s" % e.message)
            return json.dumps({"code": "1001", "describe": e.message})
        try:
            mig_threshold = json.loads(result.mig_threshold)
            config = {'dispatch': result.dispatch,
                      'migration': result.migration,
                      'mig_threshold': mig_threshold,
                      'asm_threshold': result.asm_threshold,
                      'mig_enabled': result.mig_enabled,
                      'asm_enabled': result.asm_enabled}
            return json.dumps(config)
        except Exception, e:
            LOG.info("parse openstack config failed:%s" % e.message)
            return json.dumps({"code": "1002", "describe": e.message})

    def _dispatch_update(self, dispatch, migration):
        LOG.info("_dispatch_update name :%s" % dispatch)
        ret = subprocess.call("bash /usr/local/bin/schrestart %s" % dispatch, shell=True)
        self.manager.set_dispatch(dispatch)
        self.manager.set_migration(migration)
        LOG.info("_dispatch_update end ")
        return ret

    def _manager_update(self, data):
        try:
            dispatch = data.get("dispatch", None)
            migration = data.get("migration", None)
            mig_enabled = data.get("mig_enabled", None)
            asm_enabled = data.get("asm_enabled", None)
            current_dis = self.manager.get_dispatch()
            current_mig = self.manager.get_migration()
            LOG.info("_manager_update dispatch:%s, migration:%s, current_dis:%s,\
                      current_mig:%s" % (dispatch, migration,
                                         current_dis, current_mig))
            if asm_enabled is not None:
                self.manager.set_asm_enabled(asm_enabled)
            if mig_enabled is not None:
                self.manager.set_mig_enabled(mig_enabled)
            if dispatch and self.manager.is_dispatch(dispatch):
                LOG.info("Dispatch is Same Current Dispatch")
                self.manager.set_migration(migration)
            elif dispatch and not self.manager.is_dispatch(dispatch):
                LOG.info("Dispatch not same Current Dispatch")
                self._dispatch_update(dispatch, migration)
        except Exception, e:
            LOG.info("Error: _manager_update message:%s" % e.message)

    def _get_mig_threshold(self, data):
        keys = ["airflow", "inlet_temp", "outlet_temp", "power_consumption",
                "workload", "power_increase"]
        ret = {}
        for k in keys:
            value = data.get(k, None)
            if value is not None:
                ret[k] = value
        if ret:
            return json.dumps(ret)
        return None

    def set_openstack_config(self, request):
        try:
            request = json.loads(request)
            keys = ["dispatch", "migration", "asm_threshold", "mig_enabled",
                    "asm_enabled"]
            data = {}
            for k in keys:
                value = request.get(k, None)
                if value is not None:
                    data[k] = value
            mig_threshold = self._get_mig_threshold(request)
            if mig_threshold:
                data["mig_threshold"] = mig_threshold

            LOG.info("Set Openstack Config Data:%s" % json.dumps(data))

            self._manager_update(request)

            try:
                op_config = db_api.op_config_get()
            except exception.QueryResultEmptyException, e:
                LOG.info("op config table is Empty")
                db_api.op_config_create(data)
                return json.dumps({"code": 1004,
                                   "describe": "op config table is Empty"})
            db_api.op_config_update(data)
            return json.dumps({"code": 0})
        except Exception, e:
            LOG.info("Error: set_openstack_config message:%s" % e.message)
            return json.dumps({"code": 1003, "describe": e.message})

    def get_openstack_host_usage(self, request):
        try:
            result = db_api.op_hostusage_get_all()
        except exception.QueryResultEmptyException, e:
            LOG.info("Get openstack host usage From Db Error:%s" % e.message)
            return json.dumps({"code": "1005", "describe": e.message})
        usages = []
        for i in result:
            instance_load = json.loads(i.instance_load)
            usages.append({"vcpu_num": i.vcpu_num,
                           "running_vms": i.running_vms,
                           "instance_load": instance_load,
                           "vcpu_used": i.vcpu_used,
                           "hostname": i.hostname})
        return json.dumps(usages)

    def thermal_low_temp_host_select(self, request):
        return self.manager.thermal_low_temp_host_select(request)

    def cups_low_workload_host_select(self, request):
        return self.manager.cups_low_workload_host_select(request)


class OpenstackServiceIns(object):
    @staticmethod
    def run_service(manager):
        handler = OpenstackServiceHandler(manager)
        processor = OpenstackService.Processor(handler)
        transport = TSocket.TServerSocket(port=CONF.openstack_port)
        tfactory = TTransport.TBufferedTransportFactory()
        pfactory = TBinaryProtocol.TBinaryProtocolFactory()
        server = TServer.TThreadPoolServer(processor, transport,
                                           tfactory, pfactory)
        LOG.info("The server for Openstack Service is Start")
        print("The server for Openstack Service is Start")
        server.serve()
