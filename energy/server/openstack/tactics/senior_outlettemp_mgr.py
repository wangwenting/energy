"""
Standby worker for strategy service.
"""

import time
import eventlet
from eventlet.timeout import Timeout
import threading
import copy
import json

from oslo.config import cfg

from energy.db import api as db_api
from energy import exception
from energy.common import log
from energy.server.openstack.tactics import operation
from energy.operation.novaworker import NovaWorker

# just for  test
import sys
from energy.common import config

eventlet.monkey_patch()
LOG = log.getLogger(__name__)


class SeniorOutletTempPolicy():
    def __init__(self):
        self.worker = NovaWorker()
        self.avg_outlet = 32
        pass

    def get_outlet_temp(self):
        self.outlet_temp = None
        try:
            result = db_api.op_config_get()
        except exception.QueryResultEmptyException, e:
            LOG.info("OutletTempPolicy Error:%s" % e.message)
        try:
            mig_threshold = json.loads(result.mig_threshold)
            self.outlet_temp = mig_threshold["outlet_temp"]
        except Exception, e:
            LOG.info("OutletTempPolicy Parse Error:%s" % e.message)

    def evaluate_hosts(self, hosts):
        self.get_outlet_temp()
        LOG.info("outlet_temp migration temperature is %s" % self.outlet_temp)

        def _evaluate(host):
            LOG.info("WTWANG OUTLET_TEMP %s" % host['outlet_temp'])
            print("WTWANG OUTLET_TEMP %s" % host['outlet_temp'])
            host['need_release_resource'] = True if host['outlet_temp'] > self.avg_outlet else False
            free_vcpus = host["vcpu_num"] - host["vcpu_used"]

            host['can_add_resource'] = free_vcpus if (free_vcpus > 0) else 0
            return host

        for host_name in hosts:
            LOG.info("Host info is %s" % hosts[host_name])
            hosts[host_name] = _evaluate(hosts[host_name])
        return hosts

    def vms_to_be_move(self, hosts):
        vms_to_be_move = []
        for host_name, host in hosts.items():
            if host['need_release_resource'] and len(host['vms']) > 0:
                vms_to_be_move.append(host['vms'][0])
        LOG.debug("WTWANG VMS_TO_BE_MOVE %s" % vms_to_be_move)
        return vms_to_be_move

    def low_outlet_temp_hosts(self, hosts):
        low_outlet_temp_hosts = []
        outlet_temp_hosts = []
        for host_name, host in hosts.items():
            if not host['need_release_resource'] and host['can_add_resource']:
                outlet_temp_hosts.append(host)
        outlet_temp_hosts.sort(lambda x, y: cmp(x["outlet_temp"], y["outlet_temp"]))
        LOG.info("outlet_temp_hosts info :%s" % outlet_temp_hosts)
        for item in outlet_temp_hosts:
            low_outlet_temp_hosts.append(item)
            break
        LOG.info("LOW OUTLET TEMP HOSTS is %s" % low_outlet_temp_hosts)
        return low_outlet_temp_hosts

    def generate_state(self, source_group, target_group):
        LOG.debug("WTWANG OutletTempPolicy Policy generate_state Start")
        try:
            vm_map = self.worker.get_vm_total_info()
        except exception.ConnectNovaException, e:
            self.worker.reconnect()
            vm_map = self.novacliet.get_vm_total_info()
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
        target_group = [t for t in self.low_outlet_temp_hosts(vm_map) if t['host'] in target_group]

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


class SeniorOutletTemp(object):

    def run(self):
        LOG.debug("WTWANG SeniorOutletTemprun start")
        airflow = SeniorOutletTemp()
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
