import sys
import time

import eventlet
eventlet.monkey_patch()
from loopingcall import FixedIntervalLoopingCall




def fun1():
    print(11111111)


def fun2():
    print(222222)

if __name__ == "__main__":
    parse1 = FixedIntervalLoopingCall(fun1)
    parse2 = FixedIntervalLoopingCall(fun2)
    parse1.start(interval=1,
                 initial_delay=0)
    parse2.start(interval=2, initial_delay=0)
    for i in range(0,100):
        print(i)
        time.sleep(2)
