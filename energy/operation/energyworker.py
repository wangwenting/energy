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

import pprint
import time
from oslo.config import cfg

from energy.common import log
from energy.agent.agentconnection import AgentConnection
from worker import conn_decorate

LOG = log.getLogger(__name__)


class EnergyWorker():

    def __init__(self, ip=None, port=None):
        self.agent_ip = ip
        self.agent_port = port
        print(self.agent_ip, self.agent_port)
        self.con = AgentConnection(self.agent_ip,
                                   self.agent_port,
                                   "energy_worker")
        try:
            self.con.connect()
        except Exception, e:
            self.con.reconnect()

    @conn_decorate
    def get_host(self, request=None):
        return self.con.host(request)

    @conn_decorate
    def get_temp(self, request=None):
        return self.con.temp(request)

    @conn_decorate
    def get_airflow(self, request=None):
        return self.con.airflow(request)

    @conn_decorate
    def get_power(self, request=None):
        return self.con.power(request)

    @conn_decorate
    def get_cups(self, request=None):
        return self.con.cups(request)

    @conn_decorate
    def get_fanspeed(self, request=None):
        return self.con.fanspeed(request)

    @conn_decorate
    def get_thermal(self, request=None):
        return self.con.thermalmargin(request)

if __name__ == "__main__":
    ins = EnergyWorker('localhost', 10009)
    print ins
    pprint.pprint(ins.get_host("111"))
