from oslo.config import cfg
from oslo.db import concurrency
from energy.common import utils


IMPL = utils.LazyPluggable('db_backend',
                           sqlalchemy='energy.db.sqlalchemy.migration')


INIT_VERSION = 000


def db_sync(version=None):
    """Migrate the database to `version` or the most recent version."""
    return IMPL.db_sync(version=version)


def db_version():
    """Display the current database version."""
    return IMPL.db_version()
