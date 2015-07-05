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

import signal
import eventlet
from oslo.config import cfg

from energy.common import threadgroup
from energy.common import log as logging

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


def _sighup_supported():
    return hasattr(signal, 'SIGHUP')


def _set_signals_handler(handler):
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)
    if _sighup_supported():
        signal.signal(signal.SIGHUP, handler)


def _is_sighup_and_daemon(signo):
    if not (_sighup_supported() and signo == signal.SIGHUP):
        return False
    return _is_daemon()


def _signo_to_signame(signo):
    signals = {signal.SIGTERM: 'SIGTERM',
               signal.SIGINT: 'SIGINT'}
    if _sighup_supported():
        signals[signal.SIGHUP] = 'SIGHUP'
    return signals[signo]


class Service(object):
    """Service object for binaries running on hosts."""

    def __init__(self, threads=1000):
        print('common service start')
        self.tg = threadgroup.ThreadGroup(threads)

    def start(self):
        pass

    def stop(self):
        self.tg.stop()

    def wait(self):
        self.tg.wait()


class Launcher(object):
    """Launch one or more services and wait for them to complete."""

    def __init__(self):
        """Initialize the service launcher.

        :returns: None

        """
        self._services = threadgroup.ThreadGroup()

    @staticmethod
    def run_service(service):
        """Start and wait for a service to finish.

        :param service: service to run and wait for.
        :returns: None

        """
        service.start()
        service.wait()

    def launch_service(self, service):
        """Load and start the given service.

        :param service: The service you would like to start.
        :returns: None

        """
        self._services.add_thread(self.run_service, service)
        print("service is add to services")

    def stop(self):
        """Stop all services which are currently running.

        :returns: None

        """
        self._services.stop()

    def wait(self):
        """Waits until all services have been stopped, and then returns.

        :returns: None

        """
        print('services wait')
        self._services.wait()


class SignalExit(SystemExit):
    def __init__(self, signo, exccode=1):
        super(SignalExit, self).__init__(exccode)
        self.signo = signo


class ServiceLauncher(Launcher):
    def _handle_signal(self, signo, frame):
        # Allow the process to be killed again and die from natural causes
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        raise SignalExit(signo)

    def wait(self, ready_callback=None):
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        status = None
        try:
            super(ServiceLauncher, self).wait()
        except SignalExit as exc:
            signame = {signal.SIGTERM: 'SIGTERM',
                       signal.SIGINT: 'SIGINT'}[exc.signo]
            LOG.info('Caught %s, exiting', signame)
            status = exc.code
        except SystemExit as exc:
            status = exc.code
        finally:
            self.stop()
        return status


def launch(service, workers=1):
    launcher = ServiceLauncher()
    launcher.launch_service(service)
    return launcher
