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

eventlet.monkey_patch()
LOG = log.getLogger(__name__)


class SimpleBalancePolicy():
    def __init__(self):
        self.worker = NovaWorker()

    def get_work_load(self):
        try:
            result = db_api.op_config_get()
        except exception.QueryResultEmptyException, e:
            LOG.info("SimpleBalance Error:%s" % e.message)
        try:
            mig_threshold = json.loads(result.mig_threshold)
            self.workload = int(mig_threshold["workload"])
        except Exception, e:
            LOG.info("SimpleBalancePolicy Parse Error:%s" % e.message)

    def evaluate_hosts(self, hosts):
        self.get_work_load()
        LOG.info("SimpleBalancePolicy migration workload is %s" % self.workload)

        def _evaluate(host):
            LOG.info("WTWANG EVALUATE %s" % host['instance_workload'])

            instance_workloads = json.loads(host['instance_workload'])
            host['workload'] = sum([(i["loading"]) for i in instance_workloads])
            LOG.info("WTWTANG host:%s workload:%s " % (host["host"], host["workload"]))

            host['need_release_resource'] = True if host['workload'] > self.workload else False
            free_vcpus = host["vcpu_num"] - host["vcpu_used"]
            host['can_add_resource'] = free_vcpus if (free_vcpus > 0) else 0
            return host

        for host_name in hosts:
            hosts[host_name] = _evaluate(hosts[host_name])

        return hosts

    def avg_loading(self, hosts):
        sum_loading = sum([float(value["workload"]) for i, value in hosts.items()])
        LOG.info("WTWANG avg_loading is %s" % sum_loading)
        return sum_loading/float(len(hosts))

    def get_porper_instance(self, pro_value, vms, instance_workload):
        instance_workloads = json.loads(instance_workload)
        LOG.info("instance_workload is %s" % instance_workload)
        min_value = 100
        instance_id = None
        vm_load = 0
        index = 0
        for value in instance_workloads:
            j = pro_value - value["loading"]
            if j > 0 and j < min_value:
                min_value = j
                instance_id = value["ID"]
                vm_load = value["loading"]

        for vm in vms:
            if vm["uuid"] == instance_id:
                vm["loading"] = vm_load
                return vm
        return None

    def vms_to_be_move(self, avg_loading, hosts):
        vms_to_be_move = []
        for host_name, host in hosts.items():
            if host['need_release_resource'] and len(host['vms']) > 0:
                value = host['workload'] - avg_loading
                LOG.info("WTWANG Release resource Host:%s, value:%s" % (host["host"], value))
                vm = self.get_porper_instance(value, host['vms'], host['instance_workload'])
                if vm:
                    vms_to_be_move.append(vm)
        LOG.debug("WTWANG VMS_TO_BE_MOVE %s" % vms_to_be_move)
        return vms_to_be_move

    def low_workload_hosts(self, hosts):
        low_workload_hosts = []
        workload_hosts = []
        for host_name, host in hosts.items():
            if not host['need_release_resource'] and host['can_add_resource']:
                workload_hosts.append(host)
        workload_hosts.sort(lambda x, y: cmp(x["workload"], y["workload"]))
        LOG.info("workload_hosts info :%s" % workload_hosts)
        for item in workload_hosts:
            low_workload_hosts.append(item)
            break
        LOG.info("LOW workload HOSTS is %s" % low_workload_hosts)
        return low_workload_hosts

    def generate_state(self, source_group, target_group):
        LOG.debug("WTWANG SimpleBalancePolicy Policy generate_state Start")
        vm_map = self.worker.get_vm_total_info()
        LOG.debug("WTWANG  LEN of vm_map %s info: %s" % (vm_map.__len__(), vm_map))

        for h in vm_map.keys():
            if h not in target_group:
                del vm_map[h]

        input_state = {}
        output_state = {}

        vm_map = self.evaluate_hosts(vm_map)

        avg_loading = self.avg_loading(vm_map)

        LOG.debug("WTWANG evaluate_hosts  %s, avg_loading:%s " % (vm_map, avg_loading))
        for h in vm_map.values():
            for vm in h['vms']:
                ele = operation.Element(vm["uuid"], vm["host"], [1, 1])
                input_state[ele] = ele.src
                output_state[ele] = ele.src

        vms_to_be_move = self.vms_to_be_move(avg_loading, vm_map)

        target_group = [t for t in self.low_workload_hosts(vm_map) if t['host'] in target_group]

        # move vm on candicate host to other host
        for vm in vms_to_be_move:
            ele = operation.Element(vm["uuid"], input_state[vm["uuid"]], [1, 1])
            for target in target_group:
                target_value = target['workload'] + vm["loading"]
                LOG.info("WTWANG Target Value is %s" % target_value)
                if target['can_add_resource'] and target_value < avg_loading:
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


class SimpleBalance(object):

    def run(self):
        LOG.debug("WTWANG SimpleBalance run start")
        simple_balance = SimpleBalancePolicy()
        hosts = db_api.host_get_all()

        g = set([host.hostname for host in hosts if host.status == "ACTIVE"])
        tg = set([host.hostname for host in hosts if host.status in ("ACTIVE", "DONT_CTRL")])

        LOG.info("WTWANG Source Host %s" % g)
        LOG.info("WTWANG Dest Host %s" % tg)
        i, o, c, r = simple_balance.generate_state(g, tg)

        pg = operation.PlanGenerator()
        plan = pg.generate(i, o, c, r)

        LOG.debug("WTWANG Pan %s" % plan)
        engine = operation.ExcutorEngine()
        engine.excute_plan(plan)
        while not engine.done:
            eventlet.sleep(1)
