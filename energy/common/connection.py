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

import time
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

from energy import exception


class Connection(object):
    def __init__(self, ip, port, name):
        self.ip = ip
        self.port = port
        self.name = name
        self.transport = TSocket.TSocket(ip, port)
        self.transport = TTransport.TBufferedTransport(self.transport)
        self.protocol = TBinaryProtocol.TBinaryProtocol(self.transport)

    def connect(self):
        msg = "Connect must implement connect"
        raise exception.ConnectThriftNotImp(msg)

    def close(self):
        if self.transport:
            self.transport.close()

    def reconnect(self):
        try:
            print("Connect name:%s,ip:%s,port:%s"
                  % (self.name, self.ip, self.port))
            self.connect_time = time.time()
            self.transport.open()
        except Exception, e:
            print("Connect name:%s Failed Again" % e)
