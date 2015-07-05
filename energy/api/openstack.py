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
import threading
import webob.dec
import webob.exc
import traceback
from webob import Response
from webob import Request
from oslo.config import cfg

from energy.common import log
from energy.operation.openstackworker import OpenstackWorker
import energy.wsgi as base_wsgi

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class OpenstackHandler(threading.Thread):
    info_cache = {}
    info_pool = {}

    def __init__(self, ip, port):
        self.worker = OpenstackWorker(ip, port)
        super(OpenstackHandler, self).__init__()

    def __getattr__(self, action):
        if key in self.info_pool:
            return self.action
        return None

    def get_openstack_config(self):
        return self.worker.get_openstack_config()

    def get_openstack_host_usage(self):
        return self.worker.get_openstack_host_usage()

    def set_openstack_config(self, data):
        return self.worker.set_openstack_config(data)

    def get_vms_info(self):
        return self.worker.get_vms_info()

    def thermal_low_temp_host_select(self):
        return self.worker.thermal_low_temp_host_select()

    def cups_low_workload_host_select(self):
        return self.worker.cups_low_workload_host_select()


class OpenstackRouter():
    def __init__(self, ip, port):
        self.openstackhandler = OpenstackHandler(ip, port)
        self.openstackhandler.daemon = True
        self.openstackhandler.start()
        LOG.debug("openstackHandinfo thread startding...")

    @webob.dec.wsgify(RequestClass=Request)
    def __call__(self, req):
        print "In OpenstackRouter"
        LOG.debug("In OpenstackRouter")
        resp = Response()
        resp.status = "200 OK"
        resp.content_type = "application/javascript"
        resp.headers['Access-Control-Allow-Origin'] = '*'
        args = req.environ['wsgiorg.routing_args'][1]
        action = args['action']
        if req.method == "GET" and action == "config":
            info = self.openstackhandler.get_openstack_config()
            jsondict = {"code": info.code,
                        "description": info.describe,
                        action: json.loads(info.value)}
            resp.body = json.dumps(jsondict)
        elif req.method == "GET" and action == "host_usage":
            info = self.openstackhandler.get_openstack_host_usage()
            jsondict = {"code": info.code,
                        "description": info.describe,
                        action: json.loads(info.value)}
            resp.body = json.dumps(jsondict)
        elif req.method == "GET" and action == "vm":
            info = self.openstackhandler.get_vms_info()
            resp.body = json.dumps(info)
        elif req.method == "POST" and action == "config":
            if '&' in req.body:
                data = self.parse_url(req.body)
            elif '{' in req.body:
                data = req.body

            if "callback" in data:
                del data["callback"]
            self.openstackhandler.set_openstack_config(json.dumps(data))
        else:
            resp.body = '{}'

        callback = req.GET.get("callback", "")
        if callback:
            body = "%s(%s)" % (callback, resp.body)
            resp.text = body

        return resp

    def parse_url(self, body):
        data = {}
        try:
            params = body.split('&')
            for param in params:
                par = param.split('=')
                if par[1].isdigit():
                    par[1] = int(par[1])
                data[par[0]] = par[1]
        except Exception, e:
            LOG.info("Post request parse body error:%s" % e.message)
        return data
