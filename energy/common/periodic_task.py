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

import datetime
import time

from oslo.config import cfg
from energy.common import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def periodic_task(*args, **kwargs):
    """Decorator to indicate that a method is a periodic task.
         Without arguments '@periodic_task', this will be run on every cycle
         of the periodic scheduler.
         enabled arguments is control periodic task whether effect
    """
    def decorator(f):

        f._periodic_task = True
        # Control frequency
        f._periodic_enabled = kwargs.pop('enabled', True)
        return f

    if kwargs:
        return decorator
    else:
        return decorator(args[0])


class _PeriodicTasksMeta(type):
    def __init__(cls, names, bases, dict_):
        """Metaclass that allows us to collect decorated periodic tasks."""
        super(_PeriodicTasksMeta, cls).__init__(names, bases, dict_)

        try:
            cls._periodic_tasks = cls._periodic_tasks[:]
        except AttributeError:
            cls._periodic_tasks = []

        for value in cls.__dict__.values():
            if getattr(value, '_periodic_task', False):
                task = value
                name = task.__name__
                if not task._periodic_enabled:
                    LOG.info('Skipping periodic task %(task)s because '
                             'it is disabled',
                             {'task': name})
                    continue

                cls._periodic_tasks.append((name, task))


class PeriodicTasks(object):
    __metaclass__ = _PeriodicTasksMeta

    def run_periodic_tasks(self):
        """Tasks to be run at a periodic interval."""
        for task_name, task in self._periodic_tasks:
            full_task_name = '.'.join([self.__class__.__name__, task_name])

            try:
                task(self)
            except Exception as e:
                LOG.exception("Error during %(full_task_name)s: %(e)s",
                              locals())
