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

from oslo.config import cfg
import json
import signal
import time

from energy.common import log

from energy.interface.agent import AgentService
from energy.interface.agent.ttypes import *

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

from energy.agent.hostconnection import HostConnection
from energy.agent.openstackconnection import OpenstackConnection
from energy.agent.hadoopconnection import HadoopConnection

LOG = log.getLogger(__name__)


energy_agent_opts = [
    cfg.StrOpt('server_ip',
               required=True,
               help='the energy-server ip',),
    cfg.IntOpt('server_port',
               default='10010',
               help='the energy-server port',),
    cfg.StrOpt('hadoop_ip',
               default='',
               help='the server which load the hadoop strategy ip',),
    cfg.IntOpt('hadoop_port',
               default='10011',
               help='the server whick load the hadoop strategy port',),
    cfg.StrOpt('openstack_ip',
               default='',
               help='the server which load the hadoop strategy ip',),
    cfg.IntOpt('openstack_port',
               default='10012',
               help='the server whick load the hadoop strategy port',),
    cfg.IntOpt('agent_port',
               default='10009',
               help='the agent service port',)
]

CONF = cfg.CONF
CONF.register_opts(energy_agent_opts)


class AgentServiceHandler(object):

    def __init__(self, values, *args, **kwargs):
        self.server_enable = {"openstack": False, "hadoop": False}
        print(kwargs)
        self.server_ip = values.get("server_ip", None)
        self.server_port = values.get("server_port", None)
        self.hostserver = HostConnection(self.server_ip,
                                         self.server_port,
                                         "HostConnection")
        self.hostserver.connect()

        self.openstack_ip = values.get("openstack_ip", None)
        if self.openstack_ip:
            self.openstack_port = values.get("openstack_port", None)
            self.openstackserver = OpenstackConnection(self.openstack_ip,
                                                       self.openstack_port,
                                                       "openstackConnection")
            self.openstackserver.connect()
            self.server_enable["openstack"] = True

        self.hadoop_ip = values.get("hadoop_ip", None)
        if self.hadoop_ip:
            self.hadoop_port = values.get("hadoop_port", None)
            self.hadoopserver = HadoopConnection(self.hadoop_ip,
                                                 self.hadoop_port,
                                                 "hadoopConnection")
            self.hadoopserver.connect()
            self.server_enable["hadoop"] = True

    def conn_decorate_host(func):
        def wraper(self, request):
            try:
                return func(self, request)
            except:
                temp = 3
                while temp:
                    try:
                        self.hostserver = HostConnection(self.server_ip,
                                                         self.server_port,
                                                         "HostConnection")
                        self.hostserver.connect()
                        return func(self, request)
                    except Exception, e:
                        LOG.warning("HostConnection \
                               Error = %s time = %s" % (e.message, temp))
                    time.sleep(3)
                    temp = temp - 1
                    if temp == 0:
                        return Result(code=0001, value="",
                                      describe="agent connect \
                                                host server failed")
        return wraper

    def conn_decorate_openstack(func):
        def wraper(self, request):
            try:
                return func(self, request)
            except:
                temp = 3
                while temp:
                    try:
                        self.openstackserver = OpenstackConnection(self.openstack_ip,
                                                                   self.openstack_port,
                                                                   "openstackConnection")
                        self.openstackserver.connect()
                        return func(self, request)
                    except Exception, e:
                        LOG.warning("openstackConnection Error = %s\
                                    time = %s" % (e.message, temp))
                    time.sleep(3)
                    temp = temp - 1
                    if temp == 0:
                        return Result(code=0002, value="",
                                      describe="agent connect \
                                      openstack server failed")
        return wraper

    @conn_decorate_host
    def host(self, request):
        host = self.hostserver.host(request)
        re = Result(code=0, value=host, describe="succeed")
        return re

    @conn_decorate_host
    def power(self, request):
        power = self.hostserver.power(request)
        re = Result(code=0, value=power, describe="succeed")
        return re

    @conn_decorate_host
    def temp(self, request):
        temp = self.hostserver.temp(request)
        re = Result(code=0, value=temp, describe="succeed")
        return re

    @conn_decorate_host
    def airflow(self, request):
        airflow = self.hostserver.airflow(request)
        re = Result(code=0, value=airflow, describe="succeed")
        return re

    @conn_decorate_host
    def cups(self, request):
        cups = self.hostserver.cups(request)
        re = Result(code=0, value=cups, describe="succeed")
        return re

    @conn_decorate_host
    def fanspeed(self, request):
        fanspeed = self.hostserver.fanspeed(request)
        re = Result(code=0, value=fanspeed, describe="succeed")
        return re

    @conn_decorate_host
    def thermalmargin(self, request):
        thermalmargin = self.hostserver.thermalmargin(request)
        re = Result(code=0, value=thermalmargin, describe="succeed")
        return re

    @conn_decorate_openstack
    def get_openstack_config(self, request):
        if self.server_enable["openstack"]:
            openstack_config = self.openstackserver.\
                               get_openstack_config(request)
            re = Result(code=0, value=openstack_config, describe="succeed")
        else:
            re = Result(code=-1, value="",
                        describe="openstack server not config")
        return re

    @conn_decorate_openstack
    def set_openstack_config(self, request):
        if self.server_enable["openstack"]:
            result = self.openstackserver.\
                     set_openstack_config(request)
            re = Result(code=0, value=result, describe="succeed")
        else:
            re = Result(code=-1, value="",
                        describe="openstack server not config")
        return re

    @conn_decorate_openstack
    def get_openstack_host_usage(self, request):
        if self.server_enable["openstack"]:
            result = self.openstackserver.\
                     get_openstack_host_usage(request)
            re = Result(code=0, value=result, describe="succeed")
        else:
            re = Result(code=-1, value="",
                        describe="openstack server not config")
        return re

    @conn_decorate_openstack
    def thermal_low_temp_host_select(self, request):
        if self.server_enable["openstack"]:
            result = self.openstackserver.\
                     thermal_low_temp_host_select(request)
            re = Result(code=0, value=result, describe="succeed")
        else:
            re = Result(code=-1, value="",
                        describe="openstack server not config")
        return re

    @conn_decorate_openstack
    def cups_low_workload_host_select(self, request):
        if self.server_enable["openstack"]:
            result = self.openstackserver.\
                     cups_low_workload_host_select(request)
            re = Result(code=0, value=result, describe="succeed")
        else:
            re = Result(code=-1, value="",
                        describe="openstack server not config")
        return re

    def get_hadoop_config(self, request):
        try:
            if self.server_enable["hadoop"]:
                hadoop_config = self.hadoopserver.get_hadoop_config(request)
                re = Result(code=0, value=hadoop_config, describe="succeed")
            else:
                re = Result(code=-1, value="",
                            describe="hadoop server not config")

        except Exception, e:
            re = Result(code=-1, value="", describe=e.message)
        return re

    def set_hadoop_config(self, request):
        pass


class AgentServiceIns(object):
    def __init__(self):
        self.server_ip = CONF.server_ip
        self.server_port = CONF.server_port
        self.openstack_ip = CONF.openstack_ip
        self.openstack_port = CONF.openstack_port
        self.hadoop_ip = CONF.hadoop_ip
        self.hadoop_port = CONF.hadoop_port
        self.agent_port = CONF.agent_port
        self.values = {"server_ip": self.server_ip,
                       "server_port": self.server_port,
                       "openstack_ip": self.openstack_ip,
                       "openstack_port": self.openstack_port,
                       "hadoop_ip": self.hadoop_ip,
                       "hadoop_port": self.hadoop_port}

    def run(self):
        handler = AgentServiceHandler(self.values)
        processor = AgentService.Processor(handler)
        transport = TSocket.TServerSocket(port=self.agent_port)
        tfactory = TTransport.TBufferedTransportFactory()
        pfactory = TBinaryProtocol.TBinaryProtocolFactory()
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        server = TServer.TThreadPoolServer(processor, transport,
                                           tfactory, pfactory)

        LOG.info("The Agent  Service is Start")
        server.serve()
