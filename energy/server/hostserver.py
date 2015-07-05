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

from energy.common import log

from energy.interface.host import HostInfoService
from energy.interface.agent.ttypes import *

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

from energy.db import api as db_api

LOG = log.getLogger(__name__)


energy_host_opts = [
    cfg.StrOpt('server_ip',
               required=True,
               help='the energy-server ip'),
    cfg.IntOpt('server_port',
               default='10010',
               help='the energy-server port')
]

CONF = cfg.CONF
CONF.register_opts(energy_host_opts)


class HostServiceHandler(object):
    def host(self, request):
        try:
            hosts_info = db_api.host_get_all()
        except Exception, e:
            LOG.info("Get Host From Db Error:%s" % e.message)
            return None
        hosts = []
        for i in hosts_info:
            cpu = json.loads(i.cpu_info)
            hosts.append({"hostname": i.hostname,
                          "status": i.status,
                          "cpu_info": cpu,
                          "mem_in_mb": i.mem_in_mb,
                          "cpu_used": i.cpu_used,
                          "mem_used_in_mb": i.mem_used_in_mb,
                          "disk_in_gb": i.disk_in_gb})
        return json.dumps(hosts)

    def power(self, request):
        try:
            telemetry_info = db_api.telemetry_get_all()
        except Exception, e:
            LOG.info("Get Telemetry From Db Error:%s" % e.message)
            return None
        powers = []
        for i in telemetry_info:
            powers.append({"hostname": i.hostname,
                           "system_power": i.system_power,
                           "cpu_power": i.cpu_power})
        return json.dumps(powers)

    def temp(self, request):
        try:
            telemetry_info = db_api.telemetry_get_all()
        except Exception, e:
            LOG.info("Get Telemetry From Db Error:%s" % e.message)
            return None
        powers = []
        telemetry_info = db_api.telemetry_get_all()
        temps = []
        for i in telemetry_info:
            temps.append({"hostname": i.hostname,
                          "inlet_temp": i.inlet_temp,
                          "outlet_temp": i.outlet_temp})
        return json.dumps(temps)

    def airflow(self, request):
        try:
            telemetry_info = db_api.telemetry_get_all()
        except Exception, e:
            LOG.info("Get Telemetry From Db Error:%s" % e.message)
            return None
        airflows = []
        for i in telemetry_info:
            airflows.append({"hostname": i.hostname,
                             "airflow": i.airflow})
        return json.dumps(airflows)

    def cups(self, request):
        try:
            telemetry_info = db_api.telemetry_get_all()
        except Exception, e:
            LOG.info("Get Telemetry From Db Error:%s" % e.message)
            return None
        cups = []
        for i in telemetry_info:
            cups.append({"hostname": i.hostname,
                         "io_cups": i.io_cups,
                         "cpu_cups": i.cpu_cups,
                         "mem_cups": i.mem_cups,
                         "index_cups": i.index_cups})
        return json.dumps(cups)

    def fanspeed(self, request):
        try:
            telemetry_info = db_api.telemetry_get_all()
        except Exception, e:
            LOG.info("Get Telemetry From Db Error:%s" % e.message)
            return None
        fanspeeds = []
        for i in telemetry_info:
            fan = json.loads(i.fans)
            fanspeeds.append({"hostname": i.hostname,
                              "fans": fan})
        return json.dumps(fanspeeds)

    def thermalmargin(self, request):
        try:
            telemetry_info = db_api.telemetry_get_all()
        except Exception, e:
            LOG.info("Get Telemetry From Db Error:%s" % e.message)
            return None
        thermal_margins = []
        for i in telemetry_info:
            margin = json.loads(i.thermal_margins)
            thermal_margins.append({"hostname": i.hostname,
                                    "thermal_margins": margin})
        return json.dumps(thermal_margins)


class HostServiceIns(object):
    @staticmethod
    def run_service():
        handler = HostServiceHandler()
        processor = HostInfoService.Processor(handler)
        transport = TSocket.TServerSocket(port=CONF.server_port)
        tfactory = TTransport.TBufferedTransportFactory()
        pfactory = TBinaryProtocol.TBinaryProtocolFactory()
        server = TServer.TThreadPoolServer(processor, transport,
                                           tfactory, pfactory)
        LOG.info("The Host  Service is Start")
        print("The Host Service is Start")
        server.serve()
