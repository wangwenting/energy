#           Copyright (c)  2015, Intel Corporation.
#
#   This Software is furnished under license and may only be used or
# copied in accordance with the terms of that license. No license,
# express or implied, by estoppel or otherwise, to any intellectual
# property rights is granted by this document. The Software is
# subject to change without notice, and should not be construed as
# a commitment by Intel Corporation to market, license, sell or
# support any product or technology. Unless otherwise provided for
# in the * license under which this Software is provided, the
# Software is provided AS IS, with no warranties of any kind,
# express or implied. Except as expressly permitted by the Software
# license, neither Intel Corporation nor its suppliers assumes any
# responsibility or liability for any errors or inaccuracies that
# may appear herein. Except as expressly permitted by the Software
# license, no part of the Software may be reproduced, stored in a
# retrieval system, transmitted in any form, or distributed by any
# means without the express written consent of Intel Corporation.


import socket
import json

from energy import manager
from energy import exception
from energy.db import api as db_api
from energy.common import periodic_task
from energy.common import log
from ipmi_sampler import IpmiSampler
from libvirt_sampler import LibvirtSampler
from os_sampler import OSSampler

LOG = log.getLogger(__name__)


class SamplerManager(manager.Manager):

    def __init__(self, *args, **kwargs):
        print 'Sampler Manager construct'
        self.hostname = socket.gethostname()
        self.init_value = {'hostname': self.hostname}

        self.ipmi_sampler = IpmiSampler()
        self.libvirt_sampler = LibvirtSampler()
        self.os_sampler = OSSampler()

        host_info = {}
        host_info['hostname'] = self.hostname
#        currently cpu info is get from libvirt
        host_info['cpu_info'] = self.os_sampler.cpu_info()
        host_info['mem_in_mb'] = self.os_sampler.mem_mb_total()
        host_info['disk_in_gb'] = self.os_sampler.disk_gb_total()
        host_info['bmc_ip'] = self.ipmi_sampler.local_bmc_ip()
        print str(host_info)
        try:
            query = db_api.host_get_by_hostname(self.hostname)
            db_api.host_update(self.hostname, host_info)
        except exception.QueryResultEmptyException:
            db_api.host_create(host_info)

        try:
            query = db_api.telemetry_get_by_hostname(self.hostname)
            print query
            db_api.telemetry_update(self.hostname, self.init_value)
        except exception.QueryResultEmptyException:
            db_api.telemetry_create(self.init_value)

    def init_host(self):
        print 'Sampler Manager init_host'

    @periodic_task.periodic_task
    def call_ipmi_samplers(self):
        try:
            print 'start to call_samplers...'
            cups = self.ipmi_sampler.cups()
            tel_value = {}
            tel_value['system_power'] = self.ipmi_sampler.system_power()
            tel_value['cpu_power'] = self.ipmi_sampler.cpu_power()
            tel_value['airflow'] = self.ipmi_sampler.system_power()
            tel_value['inlet_temp'] = self.ipmi_sampler.inlet_temperature()
            tel_value['outlet_temp'] = self.ipmi_sampler.outlet_temperature()
            tel_value['fans'] = self.ipmi_sampler.fans_info()
            tel_value['thermal_margins'] = self.ipmi_sampler.thermal_info()
            tel_value['cpu_cups'] = cups['core']
            tel_value['io_cups'] = cups['io']
            tel_value['mem_cups'] = cups['mem']
            tel_value['index_cups'] = cups['index']
            db_api.telemetry_update(self.hostname, tel_value)

        except Exception, e:
            print("Error happens during ipmi sampler call:" + str(e))

    @periodic_task.periodic_task
    def call_os_samplers(self):
        try:
            host_info = {}
            host_info['hostname'] = self.hostname
            host_info['mem_used_in_mb'] = int(self.os_sampler.mem_util())
            host_info['cpu_used'] = int(self.os_sampler.cpu_util(2))
            db_api.host_update(self.hostname, host_info)
        except Exception, e:
            print("Error happens during os sampler call:" + str(e))


class OpenStackSamplerManager(SamplerManager):
    def __init__(self, *args, **kwargs):
        super(OpenStackSamplerManager, self).__init__()
        print 'OpenStack Sampler Manager construct'
        try:
            query = db_api.op_hostusage_get_by_hostname(self.hostname)
            db_api.op_hostusage_update(self.hostname, self.init_value)
        except exception.QueryResultEmptyException:
            db_api.op_hostusage_create(self.init_value)

    @periodic_task.periodic_task
    def call_os_samplers(self):
        print 'start to call_samplers'
        ophost_value = {}
        ophost_value['running_vms'] = len(self.libvirt_sampler.
                                          list_instances())
        ophost_value['vcpu_used'] = self.libvirt_sampler.get_vcpu_used()
        ophost_value['vcpu_num'] = self.libvirt_sampler.get_vcpu_total()
        ophost_value['instance_load'] = self.libvirt_sampler.get_instance_load(self.hostname)

        print("instances: %s" % self.libvirt_sampler.list_instances())
        print("vcpu used: %s" % ophost_value['vcpu_used'])
        print("vcpu num: %s" % ophost_value['vcpu_num'])
        print("instance_load: %s" % ophost_value['instance_load'])
        db_api.op_hostusage_update(self.hostname, ophost_value)


class HadoopSamplerManager(SamplerManager):
    def __init__(self, *args, **kwargs):
        super(HadoopSamplerManager, self).__init__()
        print 'Hadoop Sampler Manager construct'


class CloudStackSamplerManager(SamplerManager):
    def __init__(self, *args, **kwargs):
        super(CloudStackSamplerManager, self).__init__()
        print 'CloudStack Sampler Manager construct'
