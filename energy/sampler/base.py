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

import os
import socket
import time
import re
import string

from oslo.config import cfg

from energy.common import log as logging
from energy.common import utils

energy_sampler_opts = [
    cfg.StrOpt('sampler_config',
               default='/etc/energy/energy.conf',
               help='The configure file contains paramters of sampling data.',
               ),
]

LOG = logging.getLogger(__name__)

bmc_sampler_opts = [
    cfg.IntOpt('reserved_percentage_sampler',
               default=0,
               help='The percentage of backend capacity is reserved'),
]

CONF = cfg.CONF
CONF.register_opts(energy_sampler_opts, group='sampler')


class Sampler(object):
    """Executes commands relating to Bmcs."""
    def __init__(self, execute=utils.execute, *args, **kwargs):
        self.set_execute(execute)

    def set_execute(self, execute):
        self._execute = execute

    def _try_execute(self, *command, **kwargs):
        tries = 0
        while True:
            try:
                self._execute(*command, **kwargs)
                return True
            except:
                tries = tries + 1
                if tries >= self.configuration.num_shell_tries:
                    raise
                LOG.exception(_("Recovering from a failed execute.  "
                                "Try number %s"), tries)
                time.sleep(tries ** 2)
