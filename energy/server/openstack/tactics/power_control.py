import time
import eventlet
from oslo.config import cfg

from energy.db import api as db_api
from energy import exception
from energy.common import log
from energy.operation.bmcworker import BmcWorker


LOG = log.getLogger(__name__)
eventlet.monkey_patch()


class Solution(object):

    def __init__(self, vcpus, vcpus_used, max_cpus):
        self.vcpus = vcpus
        self.vcpus_used = vcpus_used
        self.free_vcpu = vcpus - vcpus_used
        self.max_cpus = max_cpus
        self.abs_score = 0
        self.hosts = []

    def add_host(self, host):
        self.hosts.append(host)
        self.cal_score()
        return True

    def delete_host(self, host):
        self.hosts.append(host)
        vcpus = sum([i.vcpu_num for i in self.hosts])
        if not self.is_loadding():
            self.abs_score = 100 + (self.free_vcpu/float(self.vcpus)*100)
        else:
            self.abs_score = 0

    def is_loadding(self):
        loading = self.vcpus_used/float(self.vcpus)
        LOG.debug("loading is %s" % loading)
        LOG.debug("max_cpus is %s" % self.max_cpus)
        if loading < self.max_cpus:
            return False
        return True

    def cal_score(self):
        vcpus = sum([i.vcpu_num for i in self.hosts])
        free_vcpu = self.vcpus - self.vcpus_used
        percent = (free_vcpu + vcpus)/float(self.vcpus)
        if percent >= (1 - self.max_cpus):
                self.abs_score = 200 - (percent + self.max_cpus - 1)*100
        else:
            self.abs_score = 50 + (percent - self.max_cpus + 1)*100
        return self.abs_score


class PowerControl(object):

    def __init__(self):
        self.bmc_worker = BmcWorker()
        self.power_on = PowerOnTactics()
        self.power_off = PowerOffTactics()

    def _sync_host_status(self, host):
        status = self.bmc_worker.get_host_status(host.bmc_ip)
        print(host.hostname, host.bmc_ip, status)
        info = {}
        info['update_at'] = time.time()
        info['status'] = status
        LOG.info("update server status Host:%s  status:%s" % (host.hostname, status))
        db_api.host_update(host.hostname, info)

    def update_host_status(self):
        try:
            print("Update Host status")
            hosts = db_api.host_get_all()
        except exception.QueryResultEmptyException, e:
            LOG.info("update host status get host exception:%s" % e.message)
            return

        pool = []
        for host in hosts:
            if host.status == "DONT_CTRL" or host.status == "WARNING":
                continue
            pool.append(eventlet.spawn(self._sync_host_status,
                                       host))

    def power_tactics(self):
        LOG.info("Start Power On Tactics")
        sleep_time = 240

        to_be_power_on_nodes = self.power_on.power_on_tactics()
        for node in to_be_power_on_nodes:
            LOG.info("Start power On Ip: %s" % node.bmc_ip)
            self.bmc_worker.power_on_host(node.bmc_ip)
            LOG.info("power on processing sleep %s" % sleep_time)
        if to_be_power_on_nodes:
            return "ON", to_be_power_on_nodes

        LOG.info("Start Power Off Tactics")
        to_be_power_off_nodes = self.power_off.power_off_tactics()
        for node in to_be_power_off_nodes:
            LOG.info("Start Power Off Ip: %s" % node.bmc_ip)
            self.bmc_worker.power_off_host(node.bmc_ip)
        LOG.info("End Power Tactics")
        return "OFF", to_be_power_off_nodes


class PowerOffTactics(object):

    @staticmethod
    def generate(nodes, vcpus, vcpus_used, max_cpus):

        solutionList = []
        for s in nodes:
            vcpus_ = vcpus - s.vcpu_num

            solution = Solution(vcpus_, vcpus_used, max_cpus)
            solution.delete_host(s)
            LOG.info(solution)
            if not solution.is_loadding():
                    solutionList.append(solution)
        solutionList.sort(lambda x, y: cmp(x.abs_score, y.abs_score))
        if solutionList:
            return solutionList[0]
        return Solution(vcpus_, vcpus_used, max_cpus)

    def power_off_tactics(self):
        hosts = db_api.host_get_all()
        services = db_api.service_get_all()
        op_usage = db_api.op_hostusage_get_all()
        op_config = db_api.op_config_get()

        under_ctrl_active_hosts = []
        active_hosts = []
        for i in hosts:
            if i.status in ("ACTIVE", "LEGACY_ON", "DONT_CTRL"):
                active_hosts.append(i.hostname)
                if i.status != "DONT_CTRL":
                    under_ctrl_active_hosts.append(i.hostname)

        under_ctrl_active_op_usage = [i for i in op_usage if i.hostname in under_ctrl_active_hosts]
        active_op_usage = [i for i in op_usage if i.hostname in active_hosts]

        nodes = [i for i in under_ctrl_active_op_usage if not i.running_vms]

        LOG.debug("power off active_nodes %s" % active_hosts)
        LOG.debug("power off under_ctrl_active_nodes %s" % under_ctrl_active_hosts)

        to_be_power_off_nodes = []
        if nodes:
            vcpus = sum([(i.vcpu_num) for i in active_op_usage])
            vcpus_used = sum([(i.vcpu_used) for i in active_op_usage])
            vcpu_max = (op_config.asm_threshold/100.0) if op_config else 0.8
            LOG.debug("PowerOffTactics Param vcpus = %s, vcpus_used = %s, vcpus_max = %s"
                      % (vcpus, vcpus_used, vcpu_max))
            solution = PowerOffTactics.generate(nodes, vcpus, vcpus_used, vcpu_max)
            LOG.debug("PowerOffTactics solution is %s" % solution)
            to_be_power_off = solution.hosts
            print("PowerOffTactics to be power off is %s" % to_be_power_off)
            to_be_power_off_hostnames = [i.hostname for i in to_be_power_off]
            to_be_power_off_nodes = [i for i in hosts if i.hostname in to_be_power_off_hostnames]
        return to_be_power_off_nodes


class PowerOnTactics(object):

    @staticmethod
    def generate(nodes, vcpus, vcpus_used, max_cpus):
        solution = Solution(vcpus, vcpus_used, max_cpus)
        if not solution.is_loadding():
            LOG.info("Current status well return blank solution")
            return solution

        solutionList = []
        for s in nodes:
            solution = Solution(vcpus, vcpus_used, max_cpus)
            solution.add_host(s)
            LOG.debug("Add host name : %s" % s.hostname)

            LOG.info(solution)
            solutionList.append(solution)
        solutionList.sort(lambda x, y: cmp(x.abs_score, y.abs_score))
        if solutionList:
            return solutionList[0]
        return Solution(vcpus, vcpus_used, max_cpus)

    def power_on_tactics(self):
        hosts = db_api.host_get_all()
        services = db_api.service_get_all()
        op_usage = db_api.op_hostusage_get_all()
        op_config = db_api.op_config_get()

        active_nodes = [i.hostname for i in hosts if i.status in ("ACTIVE", "LEGACY_ON", "DONT_CTRL")]
        active_op_usage = [i for i in op_usage if i.hostname in active_nodes]
        standby_nodes = [i.hostname for i in hosts if i.status in ("STANDBY", "ERROR")]
        standby_op_usage = [i for i in op_usage if i.hostname in standby_nodes]
        vcpus = sum([(i.vcpu_num) for i in active_op_usage])
        vcpus_used = sum([(i.vcpu_used) for i in active_op_usage])
        vcpu_max = (op_config.asm_threshold/100.0) if op_config else 0.8

        LOG.debug("power on active_nodes %s" % active_nodes)
        LOG.debug("power on standby_nodes %s" % standby_nodes)

        to_be_power_on = []
        LOG.debug("PowerOnTactics Param vcpus = %s, vcpus_used = %s, vcpus_max=%s"
                  % (vcpus, vcpus_used, vcpu_max))
        solution = PowerOnTactics.generate(standby_op_usage, vcpus, vcpus_used, vcpu_max)

        LOG.debug("PowerOnTactics solution is %s" % solution)
        to_be_power_on = solution.hosts
        print("PowerOnTactics solution is %s" % to_be_power_on)
        to_be_power_on_hostnames = [i.hostname for i in to_be_power_on]
        to_be_power_on_nodes = [i for i in hosts if i.hostname in to_be_power_on_hostnames]
        return to_be_power_on_nodes
