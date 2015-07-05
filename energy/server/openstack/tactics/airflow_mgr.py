"""
Standby worker for strategy service.
"""

import time
import eventlet
import copy
import json

from oslo.config import cfg

from energy.db import api as db_api
from energy import exception
from energy.common import log
from energy.server.openstack.tactics import operation
from energy.operation.novaworker import NovaWorker

eventlet.monkey_patch()
LOG = log.getLogger(__name__)


class AirflowPolicy():

    def __init__(self):
        self.worker = NovaWorker()

    def _sync_host_status(self, host):
        info = {}
        info['update_at'] = time.time()
        info['status'] = "WARNING"
        LOG.info("Airflow update server status Host:%s  status:%s" % (host.hostname, info['status']))
        db_api.host_update(host.hostname, info)

    def update_host_status(self, hostname):
        try:
            LOG.info("Airflow migration Update Host status Host:%s" % hostname)
            hosts = db_api.host_get_all()
        except exception.QueryResultEmptyException, e:
            LOG.info("update host status get host exception:%s" % e.message)
            return

        for host in hosts:
            if host.status == "DONT_CTRL" or host.status == "WARNING":
                continue
            LOG.info("host:%s hostname:%s" % (host.hostname, hostname))
            LOG.info("host:%s hostname:%s" % (type(host.hostname), type(hostname)))
            LOG.info("len:%s, len:%s" % (len(hostname), len(host.hostname)))
            if host.hostname == hostname:
                LOG.info("update hostname:%s, status:%s" % (hostname, "WARNING"))
                eventlet.spawn(self._sync_host_status, host)
                # self._sync_host_status(host)

    def get_margin_info(self):
        self.inlet_temp = None
        self.airflow = None
        self.power_consumption = None
        try:
            config = db_api.op_config_get()
        except exception.QueryResultEmptyException, e:
            LOG.info("AirflowPolicy Error:%s" % e.message)
        try:
            mig_threshold = json.loads(config.mig_threshold)
            self.inlet_temp = mig_threshold["inlet_temp"]
            self.airflow = mig_threshold["airflow"]
            self.power_consumption = mig_threshold["power_consumption"]
        except Exception, e:
            LOG.info("AirflowPolicy Parse Error:%s" % e.message)

    def evaluate_hosts(self, hosts):
        self.get_margin_info()
        LOG.info("airflow migration inlet_temp:%s , airflow:%s, power_consumption:%s"
                 % (self.inlet_temp, self.airflow, self.power_consumption))

        def _evaluate(host, name):
            LOG.info("WTWANG EVALUATE inlet_temp:%s, airflow:%s, sys_power:%s, hostname:%s"
                     % (host['inlet_temp'], host["airflow"], host["sys_power"], name))

            host['need_release_resource'] = False
            host['is_all_migration'] = False
            if host["airflow"] and host["airflow"] > self.airflow:
                if host["inlet_temp"] and host["sys_power"]:
                    if host["inlet_temp"] > self.inlet_temp and host["sys_power"] > self.power_consumption:
                        host['need_release_resource'] = True
                    elif host["inlet_temp"] < self.inlet_temp and host["sys_power"] < self.power_consumption:
                        LOG.info("All Vm Need to Migration")
                        host['need_release_resource'] = True
                        host['is_all_migration'] = True
                        self.update_host_status(host_name)
            free_vcpus = host["vcpu_num"] - host["vcpu_used"]
            host['can_add_resource'] = free_vcpus if (free_vcpus > 0) else 0
            return host
        for host_name in hosts:
            # LOG.debug("Host info is %s" % hosts[host_name])
            hosts[host_name] = _evaluate(hosts[host_name], host_name)

        return hosts

    def vms_to_be_move(self, hosts):
        vms_to_be_move = []
        for host_name, host in hosts.items():
            if host['need_release_resource'] and len(host['vms']) > 0 and not host["is_all_migration"]:
                vms_to_be_move.append(host['vms'][0])
            if host['need_release_resource'] and len(host['vms']) > 0 and host["is_all_migration"]:
                for i in range(len(host['vms'])):
                    vms_to_be_move.append(host['vms'][i])
        LOG.info("WTWANG VMS_TO_BE_MOVE %s" % vms_to_be_move)
        return vms_to_be_move

    def low_airflow_hosts(self, hosts):
        low_airflow_hosts = []
        airflow_hosts = []
        for host_name, host in hosts.items():
            if not host['need_release_resource'] and host['can_add_resource']:
                airflow_hosts.append(host)
        airflow_hosts.sort(lambda x, y: cmp(x["airflow"], y["airflow"]))
        LOG.info("airflow_hosts info :%s" % airflow_hosts)
        for item in airflow_hosts:
            low_airflow_hosts.append(item)
            break
        LOG.info("LOW airflow HOSTS is %s" % low_airflow_hosts)
        return low_airflow_hosts

    def generate_state(self, source_group, target_group):
        LOG.debug("--------------WTWANG AirflowPolicy Policy generate_state Start--------------")
        vm_map = self.worker.get_vm_total_info()
        LOG.debug("WTWANG  LEN of vm_map %s info: %s" % (vm_map.__len__(), vm_map))

        for h in vm_map.keys():
            if h not in target_group:
                del vm_map[h]

        input_state = {}
        output_state = {}

        vm_map = self.evaluate_hosts(vm_map)
        LOG.debug("WTWANG evaluate_hosts  %s " % vm_map)

        for h in vm_map.values():
            for vm in h['vms']:
                ele = operation.Element(vm["uuid"], vm["host"], [1, 1])
                input_state[ele] = ele.src
                output_state[ele] = ele.src

        vms_to_be_move = self.vms_to_be_move(vm_map)
        target_group = [t for t in self.low_airflow_hosts(vm_map) if t['host'] in target_group]

        # move vm on candicate host to other host
        for vm in vms_to_be_move:
            ele = operation.Element(vm["uuid"], input_state[vm["uuid"]], [1, 1])
            for target in target_group:
                if target['can_add_resource']:
                    output_state[ele] = target['host']
                    target['can_add_resource'] = target['can_add_resource'] - 1
                    break

        capacity = {}
        for h in vm_map:
            capacity[h] = [100, 100]
        remain_capacity = copy.deepcopy(capacity)
        for vm, host in input_state.iteritems():
            remain_capacity[host] = [remain_capacity[host][k] - vm.size[k] for k in xrange(2)]

        LOG.debug("WTWANG INPUT_STATE %s " % input_state)
        LOG.debug("WTWANG OUTPUT_STATE %s " % output_state)
        return input_state, output_state, capacity, remain_capacity


class Airflow(object):

    def run(self):
        LOG.debug("----------------WTWANG Airflow run start---------------------")
        airflow = AirflowPolicy()
        hosts = db_api.host_get_all()

        g = set([host.hostname for host in hosts if host.status == "ACTIVE"])
        tg = set([host.hostname for host in hosts if host.status in ("ACTIVE", "DONT_CTRL")])

        LOG.info("WTWANG Source Host %s" % g)
        LOG.info("WTWANG Dest Host %s" % tg)
        i, o, c, r = airflow.generate_state(g, tg)

        pg = operation.PlanGenerator()
        plan = pg.generate(i, o, c, r)

        LOG.debug("WTWANG Pan %s" % plan)
        engine = operation.ExcutorEngine()
        engine.excute_plan(plan)
        while not engine.done:
            eventlet.sleep(1)
