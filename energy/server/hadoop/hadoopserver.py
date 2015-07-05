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

from energy.interface.hadoop import HadoopService

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

LOG = log.getLogger(__name__)


energy_hadoop_opts = [
    cfg.StrOpt('hadoop_ip',
               required=True,
               help='the energy-server for hadoop ip'),
    cfg.IntOpt('hadoop_port',
               default='10011',
               help='the energy-server for hadoop port')
]

CONF = cfg.CONF
CONF.register_opts(energy_hadoop_opts)


class HadoopServiceHandler(object):
    def get_hadoop_config(self, request):
        config = {"config": []}
        return json.dumps(config)


class HadoopServiceIns(object):
    @staticmethod
    def run_service():
        handler = HadoopServiceHandler()
        processor = HadoopService.Processor(handler)
        transport = TSocket.TServerSocket(port=CONF.hadoop__port)
        tfactory = TTransport.TBufferedTransportFactory()
        pfactory = TBinaryProtocol.TBinaryProtocolFactory()
        server = TServer.TThreadPoolServer(processor, transport,
                                           tfactory, pfactory)
        LOG.info("The server for Hadoop Service is Start")
        print("The server for Hadoop Service is Start")
        server.serve()
