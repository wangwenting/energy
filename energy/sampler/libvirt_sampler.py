# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# Copyright (c) 2010 Citrix Systems, Inc.
# Copyright (c) 2011 Piston Cloud Computing, Inc
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
A connection to a hypervisor through libvirt.

Supports KVM, LXC, QEMU, UML, and XEN.

**Related Flags**

:libvirt_type:  Libvirt domain type.  Can be kvm, qemu, uml, xen
                (default: kvm).
:libvirt_uri:  Override for the default libvirt URI (depends on libvirt_type).
"""

import errno
import hashlib
import functools
import glob
import multiprocessing
import os
import shutil
import sys
import time
import json
import uuid
import libvirt
from eventlet import greenthread
from eventlet import tpool

from xml.dom import minidom
from xml.etree import ElementTree
from energy.common import log as logging
from oslo.config import cfg
from energy.common import utils
from base import Sampler

LOG = logging.getLogger(__name__)

libvirt_opts = [
    cfg.StrOpt('instances_path',
               default='$state_path/instances',
               help='where instances are stored on disk'),
    cfg.StrOpt('libvirt_type',
               default='kvm',
               help='Libvirt domain type (valid options are: '
                    'kvm, lxc, qemu, uml, xen)'),
    cfg.StrOpt('libvirt_uri',
               default='',
               help='Override the default libvirt URI '
                    '(which is dependent on libvirt_type)'),
    cfg.StrOpt('cpuinfo_xml_template',
               default='$pybasedir/energy/bmc/sampler/cpuinfo.xml.template',
               help='CpuInfo XML Template (Used only live migration now)'),
    cfg.BoolOpt('libvirt_nonblocking',
                default=False,
                help='Use a separated OS thread pool to realize non-blocking'
                     ' libvirt calls'),
    ]

CONF = cfg.CONF
CONF.register_opts(libvirt_opts)


def patch_tpool_proxy():
    """eventlet.tpool.Proxy doesn't work with old-style in __str__()
    or __repr__() calls. See bug #962840 for details.
    We perform a monkey patch to replace those two instance methods.
    """
    def str_method(self):
        return str(self._obj)

    def repr_method(self):
        return repr(self._obj)

    tpool.Proxy.__str__ = str_method
    tpool.Proxy.__repr__ = repr_method


patch_tpool_proxy()


def get_connection(read_only):
    # These are loaded late so that there's no need to install these
    # libraries when not using libvirt.
    # Cheetah is separate because the unit tests want to load Cheetah,
    # but not libvirt.
    LOG.info(' get_connection global in libvirt_sampler.py')
    _late_load_cheetah()
    return LibvirtSampler(read_only)


def _late_load_cheetah():
    global Template
    if Template is None:
        t = __import__('Cheetah.Template', globals(), locals(),
                       ['Template'], -1)
        Template = t.Template


def _get_eph_disk(ephemeral):
    return 'disk.eph' + str(ephemeral['num'])


class LibvirtSampler(Sampler):

    def __init__(self, execute=utils.execute,
                 read_only=False, *args, **kwargs):
        super(LibvirtSampler, self).__init__(execute, *args, **kwargs)
        LOG.debug(' __init__() in libvirt_sampler.py')
        self._host_state = None
        self._initiator = None
        self._wrapped_conn = None
        self.read_only = read_only
        self._host_state = None
        self._number_of_vms = 0

    @property
    def host_state(self):
        if not self._host_state:
            self._host_state = HostState(self.read_only)
        return self._host_state

    def init_host(self, host):
        # NOTE(nsokolov): moved instance restarting to ComputeManager
        pass

    @property
    def libvirt_xml(self):
        if not hasattr(self, '_libvirt_xml_cache_info'):
            self._libvirt_xml_cache_info = {}

        return utils.read_cached_file(CONF.libvirt_xml_template,
                                      self._libvirt_xml_cache_info)

    @property
    def cpuinfo_xml(self):
        if not hasattr(self, '_cpuinfo_xml_cache_info'):
            self._cpuinfo_xml_cache_info = {}

        return utils.read_cached_file(CONF.cpuinfo_xml_template,
                                      self._cpuinfo_xml_cache_info)

    def _get_connection(self):
        if not self._wrapped_conn or not self._test_connection():
            LOG.debug(('Connecting to libvirt: %s'), self.uri)
            if not CONF.libvirt_nonblocking:
                self._wrapped_conn = self._connect(self.uri,
                                                   self.read_only)
            else:
                self._wrapped_conn = tpool.proxy_call(
                    (libvirt.virDomain, libvirt.virConnect),
                    self._connect, self.uri, self.read_only)

        return self._wrapped_conn

    _conn = property(_get_connection)

    def _test_connection(self):
        try:
            self._wrapped_conn.getCapabilities()
            return True
        except libvirt.libvirtError as e:
            if (e.get_error_code() == libvirt.VIR_ERR_SYSTEM_ERROR and
                e.get_error_domain() in (libvirt.VIR_FROM_REMOTE,
                                         libvirt.VIR_FROM_RPC)):
                LOG.debug(_('Connection to libvirt broke'))
                return False
            raise

    @property
    def uri(self):
        if CONF.libvirt_type == 'uml':
            uri = CONF.libvirt_uri or 'uml:///system'
        elif CONF.libvirt_type == 'xen':
            uri = CONF.libvirt_uri or 'xen:///'
        elif CONF.libvirt_type == 'lxc':
            uri = CONF.libvirt_uri or 'lxc:///'
        else:
            uri = CONF.libvirt_uri or 'qemu:///system'
        return uri

    @staticmethod
    def _connect(uri, read_only):
        auth = [[libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_NOECHOPROMPT],
                'root',
                None]

        if read_only:
            return libvirt.openReadOnly(uri)
        else:
            return libvirt.openAuth(uri, auth, 0)

    @staticmethod
    def get_host_ip_addr():
        return CONF.my_ip

    @staticmethod
    def get_vcpu_total():
        """Get vcpu number of physical computer.

        :returns: the number of cpu core.

        """

        # On certain platforms, this will raise a NotImplementedError.
        try:
            return multiprocessing.cpu_count()
        except NotImplementedError:
            LOG.warn(_("Cannot get the number of cpu, because this "
                       "function is not implemented for this platform. "
                       "This error can be safely ignored for now."))
            return 0

    def get_vcpu_used(self):
        """ Get vcpu usage number of physical computer.

        :returns: The total number of vcpu that currently used.

        """

        total = 0
        for dom_id in self._conn.listDomainsID():
            dom = self._conn.lookupByID(dom_id)
            vcpus = dom.vcpus()
            if vcpus is None:
                # dom.vcpus is not implemented for lxc, but returning 0 for
                # a used count is hardly useful for something measuring usage
                total += 1
            else:
                total += len(vcpus[1])
            # NOTE(gtt116): give change to do other task.
            greenthread.sleep(0)
        return total

    def get_hypervisor_type(self):
        """Get hypervisor type.

        :returns: hypervisor type (ex. qemu)

        """

        return self._conn.getType()

    def get_hypervisor_version(self):
        """Get hypervisor version.

        :returns: hypervisor version (ex. 12003)

        """

        # NOTE(justinsb): getVersion moved between libvirt versions
        # Trying to do be compatible with older versions is a lost cause
        # But ... we can at least give the user a nice message
        method = getattr(self._conn, 'getVersion', None)
        if method is None:
            raise "libvirt version is too old (does not support getVersion)"
            # NOTE(justinsb): If we wanted to get the version, we could:
            # method = getattr(libvirt, 'getVersion', None)
            # NOTE(justinsb): This would then rely on a proper version check

        return method()

    def list_instances(self):
        ret = [self._conn.lookupByID(x).name()
               for x in self._conn.listDomainsID()
               if x != 0]
        self._number_of_vms = len(ret)
        return ret

    def get_instance_load(self, host):
        LOG.info('WTWANG update_instance_load in libvirt_sampler.py')
        instance_infos = []
        vcpu = self.get_vcpu_total()
        for dom_id in self._conn.listDomainsID():

            instance_info = {}
            dom = self._conn.lookupByID(dom_id)
            instance_info["ID"] = dom.UUIDString()
            instance_info["active"] = dom.isActive()
            instance_info["host"] = host

            info_start = dom.info()
            print(info_start)
            start_time = time.time()

            time.sleep(1)

            info_end = dom.info()
            print(info_end)
            end_time = time.time()

            time_temp = (end_time - start_time)*1000*1000*1000

            cpu_usage = (info_end[4] - info_start[4])/time_temp
            print(cpu_usage)
            instance_info["loading"] = cpu_usage * (100.0/vcpu)
            instance_infos.append(instance_info)
        return json.dumps(instance_infos)

    def _lookup_by_name(self, instance_name):
        """Retrieve libvirt domain object given an instance name.

        All libvirt error handling should be handled in this method and
        relevant nova exceptions should be raised in response.

        """
        try:
            return self._conn.lookupByName(instance_name)
        except libvirt.libvirtError as ex:
            error_code = ex.get_error_code()
            if error_code == libvirt.VIR_ERR_NO_DOMAIN:
                raise "InstanceNotFound instance_id=" + instance_name

            msg = ("Error from libvirt while looking up %(instance_name)s: "
                   "[Error Code %(error_code)s] %(ex)s") % locals()
            raise "Error:" + msg

    def get_disk_backing_file(self, path):
        """Get the backing file of a disk image

        :param path: Path to the disk image
        :returns: a path to the image's backing store
        """
        out, err = utils.execute('qemu-img', 'info', path)
        backing_file = None

        for line in out.split('\n'):
            if line.startswith('backing file: '):
                if 'actual path: ' in line:
                    backing_file = line.split('actual path: ')[1][:-1]
                else:
                    backing_file = line.split('backing file: ')[1]
                break
        if backing_file:
            backing_file = os.path.basename(backing_file)

        return backing_file

    def get_instance_disk_info(self, instance_name):
        """Preparation block migration.

        :params ctxt: security context
        :params instance_ref:
            nova.db.sqlalchemy.models.Instance object
            instance object that is migrated.
        :return:
            json strings with below format::

                "[{'path':'disk', 'type':'raw',
                  'virt_disk_size':'10737418240',
                  'backing_file':'backing_file',
                  'disk_size':'83886080'},...]"

        """
        disk_info = []

        virt_dom = self._lookup_by_name(instance_name)
        xml = virt_dom.XMLDesc(0)
        doc = ElementTree.fromstring(xml)
        disk_nodes = doc.findall('.//devices/disk')
        path_nodes = doc.findall('.//devices/disk/source')
        driver_nodes = doc.findall('.//devices/disk/driver')

        for cnt, path_node in enumerate(path_nodes):
            disk_type = disk_nodes[cnt].get('type')
            path = path_node.get('file')

            if disk_type != 'file':
                LOG.debug(('skipping %(path)s since it looks like volume') %
                          locals())
                continue

            # get the real disk size or
            # raise a localized error if image is unavailable
            dk_size = int(os.path.getsize(path))

            disk_type = driver_nodes[cnt].get('type')
            if disk_type == "qcow2":
                out, err = utils.execute('qemu-img', 'info', path)

                # virtual size:
                size = [i.split('(')[1].split()[0] for i in out.split('\n')
                        if i.strip().find('virtual size') >= 0]
                virt_size = int(size[0])

                # backing file:(actual path:)
                backing_file = self.get_disk_backing_file(path)
            else:
                backing_file = ""
                virt_size = 0

            disk_info.append({'type': disk_type,
                              'path': path,
                              'virt_disk_size': virt_size,
                              'backing_file': backing_file,
                              'disk_size': dk_size})
        return utils.dumps(disk_info)

if __name__ == "__main__":
    test = LibvirtSampler()
    print(str(test.list_instances()))
    print(str(test.get_vcpu_used()))
    print(str(test.get_vcpu_total()))
    print(test.get_instance_load("master"))
