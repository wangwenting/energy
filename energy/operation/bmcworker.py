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
import os
import eventlet
import time

from energy.common import log

LOG = log.getLogger(__name__)

bmc_opts = [
    cfg.StrOpt('bmc_user',
               default='root',
               help='for logon bmc manager user'),
    cfg.StrOpt('bmc_password',
               default='superuser',
               help='for logn bmc manager password')
    ]

CONF = cfg.CONF
CONF.register_opts(bmc_opts)


class BmcWorker():

    def __init__(self, *args, **kwargs):

        self._bmc_user = CONF.bmc_user
        self._bmc_password = CONF.bmc_password
        self._str = 'timeout 1 ipmitool -H %s\
                    -I lanplus -U %s -P %s raw %s'

        self._power_on_str = '0x00 0x02 0x01'
        self._power_off_str = '0x00 0x02 0x00'
        self._init_power_status_str = '0x06 0x04'
        self._power_status_str = '0x06 0x07'

    def _exe_cmd(self, cmd):
        """NOTE: Execute a command.

        It is notable that it just execute the command without
        os.popen(cmd).read()
        """
        return os.popen(cmd)

    def power_on_host(self, ip):
        cmd = self._str % (ip, self._bmc_user, self._bmc_password,
                           self._power_on_str)
        status = self._exe_cmd(cmd).read()
        time.sleep(3)
        status = self._exe_cmd(cmd).read()
        if len(status) != 0:
            return True
        else:
            return False

    def power_off_host(self, ip):
        cmd = self._str % (ip, self._bmc_user, self._bmc_password,
                           self._power_off_str)
        status = self._exe_cmd(cmd).read()
        if len(status) != 0:
            return True
        else:
            return False

    def _get_bmc_status(self, ip):
        cmd = self._str % (ip, self._bmc_user, self._bmc_password,
                           self._init_power_status_str)
        status = self._exe_cmd(cmd)
        eventlet.sleep(seconds=0)
        try:
            with eventlet.Timeout(1):
                status = status.read()
        except eventlet.Timeout:
            LOG.warn("WARNING: GET HOST STATUS TIME OUT")
        if len(status) != 0:
            return "ACTIVE"
        else:
            return "LOSE"

    def get_bmc_status(self, ip):
        times = 1
        status = self._get_bmc_status(ip)
        while(status == "LOSE" and times < 3):
            status = self._get_bmc_status(ip)
            times = times + 1
        return status

    def _get_host_status(self, ip):
        if self.get_bmc_status(ip) == 'LOSE':
            return "LOSE"

        cmd = self._str % (ip, self._bmc_user, self._bmc_password,
                           self._power_status_str)
        fp = self._exe_cmd(cmd)
        eventlet.sleep(seconds=0)
        try:
            with eventlet.Timeout(1):
                status = fp.read().strip()[0:2]
        except eventlet.Timeout:
            LOG.warn("WARNING: GET HOST STATUS TIME OUT")
        LOG.debug("WTWANG HOST STATUS %s " % status)
        if status == "00":
            return "ACTIVE"
        if status == "05":
            return "STANDBY"
        if status == "20":
            return "LEGACY_ON"
        return "ERROR"

    def get_host_status(self, ip):
        times = 1
        status = self._get_host_status(ip)
        while(status == "ERROR" and times < 3):
            status = self._get_host_status(ip)
            times = times + 1
        return status

if __name__ == "__main__":
    bmc_worker = BmcWorker()
    print(bmc_worker.get_host_status("10.239.52.27"))
