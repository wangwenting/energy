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

import sys
import time

from oslo.config import cfg
from novaclient import client

from energy.common import config
from energy.common import log
from energy.db import api as db_api

LOG = log.getLogger(__name__)

nova_client_opts = [
    cfg.StrOpt('nova_os_tenant_name',
               default='admin',
               help='Then tenant of nova service registered.'),
    cfg.StrOpt('nova_os_username',
               default='admin',
               help='The username of nova service registered in keystone.'),
    cfg.StrOpt('nova_os_password',
               default='password',
               help='The password of nova service registered in keystone..'),
    cfg.StrOpt('nova_os_auth_url',
               default='http://10.10.20.51:35357/v2.0/',
               help='The keystone service host and port.'),
    ]

CONF = cfg.CONF
CONF.register_opts(nova_client_opts, group='openstack')


def conn_decorator(fun):
    def wraper(self):
        try:
            return fun(self)
        except:
            temp = 3
            while temp:
                try:
                    os_nova_client_api_version = "1.1"
                    client.Client(os_nova_client_api_version,
                                  CONF.openstack.nova_os_username,
                                  CONF.openstack.nova_os_password,
                                  CONF.openstack.nova_os_tenant_name,
                                  CONF.openstack.nova_os_auth_url)
                    return fun(self)
                except Exception, e:
                    print (e)
                time.sleep(3)
                temp = temp - 1
                if temp == 0:
                    LOG.excetion("Connect to nova client failed!")
                    raise Exception("Connect to nova client failed!")
    return wraper


class NovaWorker(object):

    def __init__(self):
        self.client = self._get_novaclient()

    @conn_decorator
    def _get_novaclient(self):
        os_nova_client_api_version = "1.1"
        return client.Client(os_nova_client_api_version,
                             CONF.openstack.nova_os_username,
                             CONF.openstack.nova_os_password,
                             CONF.openstack.nova_os_tenant_name,
                             CONF.openstack.nova_os_auth_url)

    def _get_hostname_from_novaclient(self):
        '''get hostname whick are active form openstack '''

        hostname = [service for service in self.client.services.list()
                    if service.status == "enabled" and
                    service.binary == "nova-compute"]
        hostname = [{"host": service.host} for service in hostname]
        return hostname

    def _get_hosts_info(self):
        return db_api.host_get_all()

    def _get_telemetry_info(self):
        return db_api.telemetry_get_all()

    def _get_openstack_host_usage(self):
        return db_api.op_hostusage_get_all()

    def _get_vms(self):
        vms = [vm for vm in self.client.servers.list()]
        vms = [{"host": vm.__getattr__("OS-EXT-SRV-ATTR:host"),
                "uuid": vm.id,
                "status": vm.status,
                "name": vm.name} for vm in vms]
        return vms

    def live_migration(self, server, host):
        LOG.info("------------------live-migration starting----------------------")
        self.client.servers.live_migrate(server, host, False, False)

    def get_vms_info(self):
        vms_info = {}
        vms = self._get_vms()
        if not vms:
            vms_info["code"] = -1
            vms_info["description"] = "vms information is null"
        else:
            vms_info["code"] = 0
            vms_info["description"] = "success"
        vms_info["vm"] = vms
        return vms_info

    def get_vm_total_info(self):
        host_name = self._get_hostname_from_novaclient()
        host_info_from_db = self._get_hosts_info()
        host_usage_info_from_db = self._get_openstack_host_usage()
        telemetry_info_from_db = self._get_telemetry_info()
        vms_total_info = {}

        for name in host_name:
            host = {"vms": []}
            host.update(name)
            vms_total_info.setdefault(name['host'], host)

        for info_db in host_info_from_db:
            for hostname in host_name:
                if info_db.hostname == hostname['host']:
                    info = {"cpu_info": info_db.cpu_info,
                            "mem_in_mb": info_db.mem_in_mb,
                            "disk_in_gb": info_db.disk_in_gb,
                            "bmc_ip": info_db.bmc_ip,
                            "status": info_db.status,
                            "mem_used_in_mb": info_db.mem_used_in_mb,
                            "cpu_used": info_db.cpu_used}
                    vms_total_info[info_db.hostname].update(info)

        for info_db in telemetry_info_from_db:
            for hostname in host_name:
                if info_db.hostname == hostname['host']:
                    info = {"cpu_cups": info_db.cpu_cups,
                            "io_cups": info_db.io_cups,
                            "mem_cups": info_db.mem_cups,
                            "index_cups": info_db.index_cups,
                            "inlet_temp": info_db.inlet_temp,
                            "outlet_temp": info_db.outlet_temp,
                            "thermal_margins": info_db.thermal_margins,
                            "fans": info_db.fans,
                            "airflow": info_db.airflow,
                            "sys_power": info_db.system_power,
                            "cpu_power": info_db.cpu_power}
                    vms_total_info[info_db.hostname].update(info)

        for info_db in host_usage_info_from_db:
            for hostname in host_name:
                if info_db.hostname == hostname['host']:
                    info = {"vcpu_num": info_db.vcpu_num,
                            "running_vms": info_db.running_vms,
                            "vcpu_used": info_db.vcpu_used,
                            "instance_workload": info_db.instance_load}
                    vms_total_info[info_db.hostname].update(info)

        vm_info = [vm for vm in self._get_vms() if vm["status"] == "ACTIVE"]
        for vm in vm_info:
            vms_total_info[vm['host']]['vms'].append(vm)

        return vms_total_info
