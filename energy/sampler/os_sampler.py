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
import json

from oslo.config import cfg

from energy.common import log as logging
from energy.common import utils
from base import Sampler

LOG = logging.getLogger(__name__)

bmc_os_sampler_opts = [
    cfg.IntOpt('reserved_percentage_sampler',
               default=0,
               help='The percentage of backend capacity is reserved'),
    cfg.StrOpt('disk_path',
               default='/',
               help='The file path to get disk size.'),

]

CONF = cfg.CONF
CONF.register_opts(bmc_os_sampler_opts)


class OSSampler(Sampler):
    """Executes commands relating to Bmcs."""
    def __init__(self, execute=utils.execute, *args, **kwargs):
        super(OSSampler, self).__init__(execute, *args, **kwargs)
        self._stats = {}

    def cpu_processors_number(self):
        LOG.debug('cpu_processors_number in os_sampler.py')

        with open("/proc/cpuinfo", "r") as fp:
            cpuinfo = fp.read()
        number = re.findall("processor\W+\:\W+\d+", cpuinfo)
        return len(number)

    def cpu_info(self):
        LOG.debug('cpu_processors_number in os_sampler.py')

        info_dict = {}
        lines = os.popen("lscpu").readlines()
        for line in lines:
            if line.strip():
                line = line.rstrip('\n')
                print "line:" + line
                if line.startswith('CPU(s)'):
                    info_dict['cpus'] = int(line.split(':')[1])
                elif line.startswith('Socket(s)'):
                    info_dict['sockets'] = int(line.split(':')[1])
                elif line.startswith('Thread(s) per core:'):
                    info_dict['threads_per_core'] = int(line.split(':')[1])
                elif line.startswith('Core(s) per socket:'):
                    info_dict['cores_per_socket'] = int(line.split(':')[1])

        return json.dumps(info_dict)

    def cpu_util(self, sleep_time):
        """
        > head /proc/stat
        cpu  2852852    1868   90524    223777230   55502   0   260 0 0 0
              (user)    (nice)  (sys)      (idle)   (iowait)(irq)(softirq)

        ultilization = (1 - idle / all) * 100  %
        """
        LOG.debug('cpu_utilization in os_sampler.py')
        begin = self.cpu_stat()
        time.sleep(sleep_time)
        to = self.cpu_stat()
        return round(100 - ((to[3] - begin[3]) * 100.0 /
                     (sum(to) - sum(begin))), 2)

    def mem_util(self):
        ret = os.popen("free | grep Mem | awk '{print $3 * 100 / $2}'").read()
        return float(ret)

    def disk_io_utilization(self):
        # cmd = "iostat -x -k -d |grep sda|awk '{print ($4 + $5) * $11 / 10}'"
        # ret = os.popen(cmd).read()
        # return float(ret)
        return 0.0

    def cpu_stat_details(self):
        LOG.debug('cpu_stat_details in os_sampler.py')
        info = open("/proc/stat", "r").read()
        return [[int(j) for j in i.replace("  ", " ").split(" ")[1:8]]
                for i in open("/proc/stat", "r").read().split("\n")
                if i.startswith("cpu")]

    def cpu_stat(self):
        ret = open("/proc/stat", "r").readline().strip().split(" ")[2:9]
        return [int(i) for i in ret]

    def mem_mb_total(self):
        ret = os.popen("free | grep Mem | awk '{print $2}'").read()
        return int(ret)/1024

    def disk_gb_total(self):
        stat = os.statvfs(CONF.disk_path)
        size = stat.f_blocks * stat.f_frsize
        return int(size/1073741824)

if __name__ == "__main__":
    test = OSSampler()
    print("cpu_processors_number: %s" % test.cpu_processors_number())
    print("cpu_utilization: %s" % test.cpu_util(1))
    print("mem_utilization: %s" % test.mem_util())
    print("disk_io_utilization: %s" % test.disk_io_utilization())
    print("cpu_stat_details:%s " % test.cpu_stat_details())
    print("cpu_stat:%s" % test.cpu_stat())
    print("cpu_info:%s" % (test.cpu_info()))
    print("mem_total:%s" % (test.mem_mb_total()))
    print("disk_total:%s" % (test.disk_gb_total()))
