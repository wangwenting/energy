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

import energy.wsgi as base_wsgi
from routes import Mapper
import routes.middleware
import webob.dec
import webob.exc
from webob import Response
from webob import Request
from oslo.config import cfg

from energy.api.hadoop import HadoopRouter
from energy.api.common import CommonRouter
from energy.api.openstack import OpenstackRouter
from energy.common import log
from wsgiref.simple_server import make_server
LOG = log.getLogger(__name__)

energy_worker_opts = [
    cfg.StrOpt('agent_ip',
               required=True,
               help='the energy-server ip'),
    cfg.IntOpt('agent_port',
               default='10009',
               help='the energy-server port')]

CONF = cfg.CONF
CONF.register_opts(energy_worker_opts)


class APIRouter(base_wsgi.Router):
    @classmethod
    def factory(cls, global_config, **local_config):
        print "In APIRouter.factory", global_config, local_config
        return cls()

    def __init__(self):

        hadoop_router = HadoopRouter()
        common_router = CommonRouter(CONF.agent_ip, CONF.agent_port)
        openstack_router = OpenstackRouter(CONF.agent_ip, CONF.agent_port)

        mapper = Mapper()
        mapper.connect(None, "/hadoop/{action}", controller=hadoop_router)
        mapper.connect(None, "/common/{action}", controller=common_router)
        mapper.connect(None, "/openstack/{action}",
                       controller=openstack_router)

        super(APIRouter, self).__init__(mapper)


if __name__ == "__main__":
    app = APIRouter()
    httpd = make_server('localhost', 8080, app)
    httpd.serve_forever()
