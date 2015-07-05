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

import webob.dec
import webob.exc
from webob import Response
from webob import Request
from oslo.config import cfg

from energy.common import log
import energy.wsgi as base_wsgi

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class HadoopRouter():
    def __init__(self):
        pass

    @webob.dec.wsgify(RequestClass=Request)
    def __call__(self, req):
        print "In HadoopRouter"
        LOG.debug("In hadoopRouter")
        resp = Response()
        resp.status = "200 OK"
        resp.content_type = "text/plain"
        resp.body = str(req.environ['wsgiorg.routing_args'][1])

        callback = req.GET.get("callback", "")
        if callback:
            body = "%s(%s)" % (callback, resp.body)
            resp.text = body

        return resp
