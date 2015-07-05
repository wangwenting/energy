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

import logging
import logging.config
import logging.handlers
import os
import sys
import traceback
import inspect

from oslo.config import cfg


_DEFAULT_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


common_cli_opts = [
    cfg.BoolOpt('debug',
                default=False,
                help='DEBUG instead of default WARNING level'),
    cfg.BoolOpt('verbose',
                default=False,
                help='INFO instead of default WARNING level).'),
]

logging_cli_opts = [
    cfg.StrOpt('log_format',
               metavar='FORMAT',
               default='%(asctime)s.%(msecs)03d %(process)d %(levelname)s '
                       '%(name)s [-] %(message)s',
               help='A logging.Formatter log message format string which may '
                    'use any of the available logging.LogRecord attributes.'),
    cfg.StrOpt('log_date_format',
               default=_DEFAULT_LOG_DATE_FORMAT,
               metavar='DATE_FORMAT',
               help='Format string for %%(asctime)s in log records. '
                    'Default: %(default)s .'),
    cfg.StrOpt('log_file',
               metavar='PATH',
               help='(Optional) Name of log file to output to. '
                    'If no default is set, logging will go to stdout.'),
    cfg.StrOpt('log_dir',
               default='/var/log/energy/',
               help='(Optional) The base directory used for relative '
                    '--log-file paths.'),
]


CONF = cfg.CONF
CONF.register_cli_opts(common_cli_opts)
CONF.register_cli_opts(logging_cli_opts)


def _get_process_name():
    return os.path.basename(inspect.stack()[-1][1])


def _get_log_file_path(binary=None):
    logfile = CONF.log_file
    logdir = CONF.log_dir

    if logfile and logdir:
        return os.path.join(logdir, logfile)

    if logdir:
        binary = binary or _get_process_name()
        return '%s.log' % (os.path.join(logdir, binary),)

    return None


def _create_log_excepthook(product_name):
    def log_excepthook(exc_type, value, tb):
        extra = {'exc_info': (exc_type, value, tb)}
        getLogger(product_name).critical(
            "".join(traceback.format_exception_only(exc_type, value)),
            **extra)
    return log_excepthook


def setup(product_name, version='unknown'):
    _setup_log_from_conf(product_name, version)
    sys.excepthook = _create_log_excepthook(product_name)


def _setup_log_from_conf(project, version):

    log_root = getLogger(None).logger
    for handler in log_root.handlers:
        log_root.removeHandler(handler)

    logpath = _get_log_file_path()

    if logpath:
        filelog = logging.handlers.WatchedFileHandler(logpath)
        log_root.addHandler(filelog)

    elif not logpath:
        streamlog = logging.StreamHandler(sys.stdout)
        log_root.addHandler(streamlog)

    datefmt = CONF.log_date_format
    for handler in log_root.handlers:
        handler.setFormatter(logging.Formatter(fmt=CONF.log_format,
                                               datefmt=datefmt))

    if CONF.debug:
        log_root.setLevel(logging.DEBUG)
    elif CONF.verbose:
        log_root.setLevel(logging.INFO)
    else:
        log_root.setLevel(logging.WARNING)

_loggers = {}


def getLogger(name='unknown', version='unknown'):
    if name not in _loggers:
        _loggers[name] = logging.LoggerAdapter(logging.getLogger(name), None)
    return _loggers[name]
