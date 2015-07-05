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
from energy.interface.hadoop import HadoopService


class HadoopConnection(Connection):

    def __init__(self, ip, port, name):
        super(HadoopConnection, self).__init__(ip, port, name)

    def connect(self):
        self.__service = HadoopService.Client(self.protocol)
        self.transport.open()
        if not self.__service:
            raise RuntimeError("Invalid Thrift init params")

    def get_hadoop_config(self, request):
        return self.__service.get_hadoop(request)
