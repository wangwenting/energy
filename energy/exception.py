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

from oslo.config import cfg
import webob.exc

CONF = cfg.CONF


class ConvertedException(webob.exc.WSGIHTTPException):
    def __init__(self, code=0, title="", explanation=""):
        self.code = code
        self.title = title
        self.explanation = explanation
        super(ConvertedException, self).__init__()


class ProcessExecutionError(IOError):
    def __init__(self, stdout=None, stderr=None, exit_code=None, cmd=None,
                 description=None):
        self.exit_code = exit_code
        self.stderr = stderr
        self.stdout = stdout
        self.cmd = cmd
        self.description = description

        if description is None:
            description = 'Unexpected error while running command.'
        if exit_code is None:
            exit_code = '-'
        message = '%(description)s\nCommand: %(cmd)s\n' \
                  'Exit code: %(exit_code)s\nStdout: %(stdout)r\n' \
                  'Stderr: %(stderr)r' % locals()
        IOError.__init__(self, message)


class EnergyException(Exception):
    """Base Energy Exception

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.

    """
    message = "An unknown exception occurred."
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass
        if not message:
            try:
                message = self.message % kwargs
                self.message = message

            except Exception as e:
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                for name, value in kwargs.iteritems():
                    LOG.error("%s: %s" % (name, value))
                else:
                    # at least get the core message out if something happened
                    message = self.message
        self.message = message
        super(EnergyException, self).__init__(message)


class QueryResultEmptyException(EnergyException):
    message = "Query didn't find any result." + ": %(detail)s"


class HostsDuplicateException(EnergyException):
    message = "Insert to Table Hosts Duplicate" + ": %(detail)s"


class ConnectNovaException(EnergyException):
    message = "Connect to Nova Failed"


class ConnectThriftNotImp(EnergyException):
    message = "Thrift Connect not Implement"


class ConnectThriftException(EnergyException):
    message = "Thrift Server Not Connect"
