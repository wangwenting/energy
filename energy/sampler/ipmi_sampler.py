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
import json

from oslo.config import cfg

from energy.common import log as logging
from energy.common import utils
from base import Sampler


LOG = logging.getLogger(__name__)

bmc_ipmi_sampler_opts = [
    cfg.IntOpt('reserved_percentage_sampler_ipmi',
               default=0,
               help='The percentage of backend capacity is reserved'),
    cfg.StrOpt('sensor_json_config_location',
               default='/etc/energy/sensors.json',
               help='Absolute path to scheduler configuration JSON file.'),
]

CONF = cfg.CONF
CONF.register_opts(bmc_ipmi_sampler_opts)


LOG = logging.getLogger(__name__)

BMC_PREFIX = "ipmitool raw "
ME_PREFIX = "ipmitool -b 6 -t 0x2c raw "
BMC_LAN_CHANNEL = "0x01"

GET_BMC_IP = BMC_PREFIX + "0x0c 0x02 " + \
             BMC_LAN_CHANNEL + " 0x03 0x00 0x00"
GET_BMC_MAC = BMC_PREFIX + "0x0c 0x02 " + \
              BMC_LAN_CHANNEL + " 0x05 0x00 0x00"
GET_BMC_HOSTNAME = BMC_PREFIX + "0x0c 0x02 " + \
                   BMC_LAN_CHANNEL + " 0xc7 0x00 0x00"
GET_SYS_POWER = ME_PREFIX + "0x2e 0xc8 0x57 0x01 0x00 0x01 0x00 0x00"
GET_CPU_POWER = ME_PREFIX + "0x2e 0xc8 0x57 0x01 0x00 0x01 0x01 0x00"
GET_CPU_UTIL = ME_PREFIX + "0x04 0x2d 0xbe"
GET_MEM_UTIL = ME_PREFIX + "0x04 0x2d 0xc0"
GET_IO_UTIL = ME_PREFIX + "0x04 0x2d 0xbf"
GET_CUPS_INDEX = ME_PREFIX + "0x2e 0x65 0x57 0x01 0x00 0x01"
GET_SENSOR_READING = "ipmitool sensor reading "


class IpmiOptions(object):
    """IpmiOptions monitors a local .json file for changes and loads
       it if needed. This file is converted to a data structure, it's contains
       many category sensor elements
    """

    def __init__(self):
        super(IpmiOptions, self).__init__()
        self.data = {}
        self.last_modified = None
        self.last_checked = None

    def _get_file_handle(self, filename):
        """Get file handle. Broken out for testing."""
        return open(filename)

    def _get_file_timestamp(self, filename):
        """Get the last modified datetime. Broken out for testing."""
        try:
            return os.path.getmtime(filename)
        except os.error as e:
            LOG.debug("Could not stat ipmi options file %(filename)s: \
                      '%(e)s'", {'filename': filename, 'e': e})

    def _load_file(self, handle):
        """Decode the JSON file. Broken out for testing."""
        try:
            return json.load(handle)
        except ValueError as e:
            LOG.exception(("Could not decode scheduler options: '%s'"), e)
            return {}

    def _get_time_now(self):
        """Get current UTC. Broken out for testing."""
        return timeutils.utcnow()

    def get_configuration(self, filename=None):
        """Check the json file for changes and load it if needed."""
        if not filename:
            filename = CONF.sensor_json_config_location
        if not filename:
            return self.data
        if self.last_checked:
            now = self._get_time_now()
            if now - self.last_checked < datetime.timedelta(minutes=5):
                return self.data
        last_modified = self._get_file_timestamp(filename)
        if (not last_modified or not self.last_modified or
                last_modified > self.last_modified):
            self.data = self._load_file(self._get_file_handle(filename))
            self.last_modified = last_modified
        if not self.data:
            self.data = {}

        return self.data


class IpmiSampler(Sampler):
    """Executes commands relating to Bmcs."""
    def __init__(self, execute=utils.execute, *args, **kwargs):
        super(IpmiSampler, self).__init__(execute, *args, **kwargs)
        self._stats = {}
        self._options = IpmiOptions()

    def _raw_data(self):
        LOG.debug('_raw_data() in ipmi_sampler.py')
        data = self._time_out_cmd(GET_SYS_POWER, 10)
        data = data.strip().split(' ')

        _r = lambda x: x.reverse() or string.atoi("0x" + "".join(x), 16)
        return _r(data[3:5]), _r(data[5:7]), _r(data[7:9])

    def power_consumption(self):
        return self._raw_data()[0]

    def _time_out_cmd(self, cmd, length_of_result, wait_time=5):
        """Time our function for execute cmd.

        function is used for get bmc's information.
        It needs wait time and check the length of
        command.
        """
#        print "cmd = " + cmd
        start_time = time.time()
        ret = os.popen(cmd).read()
        while (time.time() - start_time < wait_time and
                len(ret) < length_of_result):
            ret = os.popen(cmd).read()
            time.sleep(1)

        return ret

    def local_bmc_ip(self):
        """Get local physical machine's bmc IP.

        Each physical machine has its own bmc which
        is a small Linux system. This function is used
        to get the local BMC's IP address.
        """
        ret = self._time_out_cmd(GET_BMC_IP, 15)
        ip = ".".join([str(string.atoi(i, 16))
                      for i in ret.strip().split(" ")][1:])
        return ip

    def local_bmc_mac(self):
        data = self._time_out_cmd(GET_BMC_MAC, 21)
        data = data.lstrip()
        data = data.split(" ")[1:]
        mac = "".join(data).upper().strip()
        return mac

    def local_bmc_hostname(self):
        data = self._time_out_cmd(GET_BMC_HOSTNAME, 53)
        data = data.replace("\n", "") + ' '
        data = data.replace("  ", " ")
        data = data.lstrip()

        temp = ''
        hostname = ''

        for i in data:
            if i == ' ':
                hostname = hostname + chr(string.atoi(temp, 16))
                temp = ''
            else:
                temp = temp + i
        return hostname

    def fans_info(self):
        data = self._options.get_configuration()
        info = {}
        if "fans" in data:
            for f in data["fans"]:
                info[f] = self._sensor_reading('"' + f + '"')
        return json.dumps(info)

    def thermal_info(self):
        data = self._options.get_configuration()
        info = {}
        if "thermal" in data:
            for f in data["thermal"]:
                info[f] = self._sensor_reading('"' + f + '"')
        return json.dumps(info)

    def _sensor_reading(self, arg):
        data = self._time_out_cmd(GET_SENSOR_READING + str(arg), 22)
        if len(data) != 0:
            data = data.split('|')
            data = data[-1].strip()
            return data
        else:
            return None

    def system_power(self):
        data = self._time_out_cmd(GET_SYS_POWER, 15)
        if len(data) != 0:
                bytes = data.split()
                power = int(bytes[4] + bytes[3], 16)
        return power

    def cpu_power(self):
        data = self._time_out_cmd(GET_CPU_POWER, 15)
        if len(data) != 0:
                bytes = data.split()
                power = int(bytes[4] + bytes[3], 16)

        return power

    def cups(self):
        io_cups = None
        mem_cups = None
        cpu_cups = None
        cup = None

        data_cpu = self._time_out_cmd(GET_CPU_UTIL, 5)
        if len(data_cpu) != 0:
            bytes = data_cpu.split()
            cpu_cups = int(bytes[0], 16)

        data_mem = self._time_out_cmd(GET_MEM_UTIL, 5)
        if len(data_mem) != 0:
            bytes = data_mem.split()
            mem_cups = int(bytes[0], 16)
        data_io = self._time_out_cmd(GET_IO_UTIL, 5)

        if len(data_io) != 0:
            bytes = data_io.split()
            io_cups = int(bytes[0], 16)
        data_index = self._time_out_cmd(GET_CUPS_INDEX, 5)

        if len(data_index) != 0:
            bytes = data_index.split()
            index_cups = int(bytes[4] + bytes[3], 16)
        cups = {}
        cups["io"] = io_cups
        cups["mem"] = mem_cups
        cups["core"] = cpu_cups
        cups["index"] = index_cups

        return cups

#   check the inlet inlet sensor to get the data
    def inlet_temperature(self):
        data = self._options.get_configuration()
        info = None
        if "inlet_temp" in data:
            info = self._sensor_reading('"' + data["inlet_temp"] + '"')
            if len(info) != 0:
                info = info.split('|')
                info = info[-1].strip()
        return info

#   check the outlet temp from the sensor, should be moved to energy agent
    def outlet_temperature(self):
        data = self._options.get_configuration()
        info = None
        if "outlet_temp" in data:
            info = self._sensor_reading('"' + data["outlet_temp"] + '"')
            if len(info) != 0:
                info = info.split('|')
                info = info[-1].strip()
        return info

#   get airflow from the sensor, should be placed in energy-agent
    def airflow(self):
        data = self._options.get_configuration()
        info = None
        if "airflow" in data:
            info = self._sensor_reading('"' + data["airflow"] + '"')
            if len(info) != 0:
                info = info.split('|')
                info = info[-1].strip()
        return info

# hc add for telemetry api 20140603, end
if __name__ == "__main__":

    test = IpmiSampler()
    print"system_power: " + str(test.system_power())
    print "cups: " + str(test.cups())
    print "cpu_power: " + str(test.cpu_power())
    print "fan_info: " + str(test.fans_info())
    print "inlet_temp: " + str(test.inlet_temperature())
    print "outlet_temp: " + str(test.outlet_temperature())
    print "airflow: " + str(test.airflow())
