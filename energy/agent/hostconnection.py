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


from energy.common.connection import Connection
from energy.interface.host import HostInfoService


class HostConnection(Connection):

    def __init__(self, ip, port, name):
        super(HostConnection, self).__init__(ip, port, name)

    def connect(self):
        self.__service = HostInfoService.Client(self.protocol)
        self.transport.open()
        if not self.__service:
            raise RuntimeError("Invalid Thrift init params")

    def host(self, request):
        return self.__service.host(request)

    def power(self, request):
        return self.__service.power(request)

    def temp(self, request):
        return self.__service.temp(request)

    def airflow(self, request):
        return self.__service.airflow(request)

    def cups(self, request):
        return self.__service.cups(request)

    def fanspeed(self, request):
        return self.__service.fanspeed(request)

    def thermalmargin(self, request):
        return self.__service.thermalmargin(request)
