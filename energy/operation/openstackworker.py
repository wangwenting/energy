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

from energy.common import log
from energy.agent.agentconnection import AgentConnection
from novaworker import NovaWorker
from worker import conn_decorate

LOG = log.getLogger(__name__)


class OpenstackWorker(object):

    def __init__(self, ip=None, port=None):
        self.agent_ip = ip
        self.agent_port = port
        self.con = AgentConnection(self.agent_ip,
                                   self.agent_port, "Openstack_worker")
        self.worker = NovaWorker()

        try:
            self.con.connect()
        except Exception, e:
            LOG.exception("Connect to AgentConnection failed!:'%s'", e)
            LOG.debug("tring to reconnect to AgentConnection")
            self.con.reconnect()

    @conn_decorate
    def get_openstack_config(self, request=None):
        return self.con.get_openstack_config(request)

    @conn_decorate
    def get_openstack_host_usage(self, request=None):
        return self.con.get_openstack_host_usage(request)

    @conn_decorate
    def set_openstack_config(self, request=None):
        return self.con.set_openstack_config(request)

    @conn_decorate
    def thermal_low_temp_host_select(self):
        return self.con.thermal_low_temp_host_select()

    @conn_decorate
    def cups_low_workload_host_select(self):
        return self.con.cups_low_workload_host_select()

    def live_migration(self, server, host):
        return self.worker.live_migration(server, host, False, False)

    def get_vms_info(self):
        return self.worker.get_vms_info()
