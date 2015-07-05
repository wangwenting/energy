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

import json
import time
import ast
import threading
import traceback
import webob.exc
import webob.dec

from webob import Response
from webob import Request
from wsgiref.simple_server import make_server
from oslo.config import cfg

from energy.common import log
from energy.operation.energyworker import EnergyWorker
import energy.wsgi as base_wsgi


CONF = cfg.CONF
LOG = log.getLogger(__name__)


class CommonInfoHandler(threading.Thread):
    info_cache = {}
    info_pool = {}

    def __init__(self, ip, port):
        self.worker = EnergyWorker(ip, port)
        super(CommonInfoHandler, self).__init__()

    def __getattr__(self, key):
        if key in self.info_pool:
            return self.info_pool[key]
        return None

    def _sync_data(self):
        self.info_cache['host_info'] = self.worker.get_host()
        self.info_cache['temp_info'] = self.worker.get_temp()
        self.info_cache['airflow_info'] = self.worker.get_airflow()
        self.info_cache['power_info'] = self.worker.get_power()
        self.info_cache['cups_info'] = self.worker.get_cups()
        self.info_cache['fanspeed_info'] = self.worker.get_fanspeed()
        self.info_cache['thermal_info'] = self.worker.get_thermal()

        self.info_pool['host'] = self.info_cache['host_info']
        self.info_pool['temp'] = self.info_cache['temp_info']
        self.info_pool['airflow'] = self.info_cache['airflow_info']
        self.info_pool['power'] = self.info_cache['power_info']
        self.info_pool['cups'] = self.info_cache['cups_info']
        self.info_pool['fanspeed'] = self.info_cache['fanspeed_info']
        self.info_pool['thermal'] = self.info_cache['thermal_info']

    def run(self):
        while 1:
            try:
                self._sync_data()
            except Exception, e:
                LOG.exception("Could not sync host info: '%s'", e)
                traceback.print_exc()
                time.sleep(5)
            time.sleep(1)


class CommonRouter():
    def __init__(self, ip, port):
        self.commonHandler = CommonInfoHandler(ip, port)
        self.commonHandler.daemon = True
        self.commonHandler.start()
        LOG.debug("CommonHandlerInfo thread starting...")

    @webob.dec.wsgify(RequestClass=Request)
    def __call__(self, req):
        print "In Common Router"
        LOG.debug("In Common Router")
        args = req.environ['wsgiorg.routing_args'][1]
        action = args['action']
        resp = Response()
        resp.status = "200 OK"
        resp.content_type = "application/javascript"
        if action in ['host', 'power', 'temp', 'airflow',
                      'cups', 'fanspeed', 'thermal']:
            result = getattr(self.commonHandler, action)
            jsondict = {}
            jsondict["code"] = result.code
            jsondict["description"] = result.describe
            jsondict[action] = json.loads(result.value)
            resp.body = json.dumps(jsondict)
        else:
            resp.body = '{}'

        callback = req.GET.get("callback", "")
        if callback:
            body = "%s(%s)" % (callback, resp.body)
            resp.text = body

        return resp


if __name__ == "__main__":
    ins = CommonRouter("localhsot", 8080)
    print ins.commonHandler.worker.host("22222222")
    app = Router()
    httpd = make_server('localhost', 8282, app)
    httpd.serve_forever()
