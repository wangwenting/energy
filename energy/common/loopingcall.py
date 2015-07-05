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

import sys
import time

from eventlet import event
from eventlet import greenthread


def _ts():
    return time.time()


class LoopingCallDone(Exception):

    def __init__(self, retvalue=True):
        self.retvalue = retvalue


class LoopingCallBase(object):
    def __init__(self, f=None, *args, **kw):
        self.args = args
        self.kw = kw
        self.f = f
        self._running = False
        self.done = None

    def stop(self):
        self._running = False

    def wait(self):
        return self.done.wait()


class FixedIntervalLoopingCall(LoopingCallBase):

    def start(self, interval, initial_delay=None):
        self._running = True
        done = event.Event()

        def _inner():
            initial_delay = 1
            if initial_delay:
                greenthread.sleep(initial_delay)
            try:
                while self._running:
                    start = _ts()
                    print('function start')
                    self.f(*self.args, **self.kw)
                    print('function end')
                    end = _ts()
                    if not self._running:
                        break
                    delay = end - start - interval
                    if delay > 0:
                        print(('task %(func_name)s run outlasted '
                               'interval by %(delay).2f sec'),
                              {'func_name': repr(self.f), 'delay': delay})
                    greenthread.sleep(-delay if delay < 0 else 0)
            except LoopingCallDone as e:
                print("LoopingCallDone")
                self.stop()
                done.send(e.retvalue)
            except Exception:
                print('in fixed duration looping call')
                done.send_exception(*sys.exc_info())
                return
            else:
                done.send(True)

        self.done = done

        greenthread.spawn_n(_inner)
        return self.done
