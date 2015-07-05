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

from energy import manager
from energy.server.hostserver import HostServiceIns
from energy.common import threadgroup

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class ThriftManager(manager.Manager):

    def __init__(self, host=None):
        super(ThriftManager, self).__init__(host=None)
        self._services = threadgroup.ThreadGroup()

    def add_host_service(self):
        self._services.add_thread(HostServiceIns.run_service)

    def wait(self):
        self._service.wait()
