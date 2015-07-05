from oslo.config import cfg
from oslo.db.sqlalchemy import session as db_session
import threading
from oslo.db import exception as db_exc

from energy import exception
from energy.db.sqlalchemy import models
from energy.common import log
from energy.common import timeutils

CONF = cfg.CONF

LOG = log.getLogger(__name__)

_ENGINE_FACADE = None
_LOCK = threading.Lock()


def _create_facade_lazily():
    global _LOCK, _ENGINE_FACADE
    if _ENGINE_FACADE is None:
        with _LOCK:
            if _ENGINE_FACADE is None:
                _ENGINE_FACADE = db_session.EngineFacade.from_config(CONF)
    return _ENGINE_FACADE


def get_engine(use_slave=False):
    facade = _create_facade_lazily()
    return facade.get_engine(use_slave=use_slave)


def get_session(use_slave=False, **kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(use_slave=use_slave, **kwargs)


def model_query(model, *args, **kwargs):

    session = kwargs.get('session') or get_session()
    query = session.query(model, *args)

    return query


'''for hosts Table Operation'''


def host_create(values):
    host_ref = models.Host()
    host_ref.update(values)
    try:
        host_ref.save()
    except db_exc.DBDuplicateEntry, e:
        value = values.get("hostname")
        msg = "Error: duplicate by hostname:%s" % values.get("hostname")
        raise exception.HostsDuplicateException(msg)
    return host_ref


def host_get(hostname, session=None):
    query = model_query(models.Host, session=session).\
                 filter_by(hostname=hostname).first()
    if not query:
        msg = "Error: Update by hostname:%s Not Found" % hostname
        raise exception.QueryResultEmptyException(msg)
    return query


def host_update(hostname, values):
    session = get_session()
    with session.begin():
        host_ref = host_get(hostname, session=session)
        values['updated_at'] = timeutils.utcnow()
        host_ref.update(values)
        host_ref.save(session=session)


def host_get_all():
    query = model_query(models.Host)
    return query.all()


def host_get_by_hostname(hostname):
    query = model_query(models.Host).\
                 filter_by(hostname=hostname).first()

    if not query:
        msg = "Error:Get Hosts  by hostname:%s Not Found" % hostname
        raise exception.QueryResultEmptyException(msg)
    return query


'''for services table Operation'''


def service_create(values):
    service_ref = models.Service()
    service_ref.update(values)
    service_ref.save()
    return service_ref


def service_destroy(hostname, service_name):
    session = get_session()
    with session.begin():
        service_ref = service_get(hostname, service_name, session=session)
        service_ref.delete(session=session)


def service_get(hostname, service_name, session=None):
    query = model_query(models.Service, session=session).\
                 filter_by(hostname=hostname).\
                 filter_by(service_name=service_name).first()
    if not query:
        msg = "Error:Get Services by hostname:%s service_name:%s\
               Not Found" % (hostname, service_name)
        raise exception.QueryResultEmptyException(msg)
    return query


def service_update(hostname, service_name, values):
    session = get_session()
    with session.begin():
        service_ref = service_get(hostname, service_name, session=session)
        values['updated_at'] = timeutils.utcnow()
        service_ref.update(values)
        service_ref.save(session=session)


def service_get_all():
    query = model_query(models.Service)
    return query.all()


def service_get_by_hostname(hostname):
    query = model_query(models.Service).filter_by(hostname=hostname).all()

    if not query:
        msg = "Error: No Service quered by hostname :%s " % hostname
        raise exception.QueryResultEmptyException(msg)
    return query


def service_get_by_service_name(service_name):
    query = model_query(models.Service).filter_by(service_name=service_name).all()

    if not query:
        msg = "Error: No Service quered by servicename:%s " % service_name
        raise exception.QueryResultEmptyException(msg)
    return query


def service_get_by_multiple(hostname, service_name):
    query = model_query(models.Service).filter_by(hostname=hostname)\
                        .filter_by(service_name=service_name).first()

    if not query:
        msg = "Error: No Service quered by hostname :%s, service_name:%s "\
               % (hostname, service_name)
        raise exception.QueryResultEmptyException(msg)
    return query


'''for telemetry table Operation'''


def telemetry_create(values):
    telemetry_ref = models.Telemetry()
    telemetry_ref.update(values)
    telemetry_ref.save()
    return telemetry_ref


def telemetry_get(hostname, session=None):
    query = model_query(models.Telemetry, session=session).\
                 filter_by(hostname=hostname).first()
    if not query:
        msg = "Error: update telemetry hostname :%s Not Found" % hostname
        raise exception.QueryResultEmptyException(msg)
    return query


def telemetry_update(hostname, values):
    session = get_session()
    with session.begin():
        telemetry_ref = telemetry_get(hostname, session=session)
        values['updated_at'] = timeutils.utcnow()
        telemetry_ref.update(values)
        telemetry_ref.save(session=session)


def telemetry_get_all():
    query = model_query(models.Telemetry)
    return query.all()


def telemetry_get_by_hostname(hostname):
    query = model_query(models.Telemetry).filter_by(hostname=hostname).first()

    if not query:
        msg = "Error: No Telemetry quered by hostname :%s " % hostname
        raise exception.QueryResultEmptyException(msg)
    return query


'''for openstack_host_usage table Operation'''


def op_hostusage_create(values):
    op_hostusage_ref = models.OpenstackHostUsage()
    op_hostusage_ref.update(values)
    op_hostusage_ref.save()
    return op_hostusage_ref


def op_hostusage_get(hostname, session=None):
    query = model_query(models.OpenstackHostUsage, session=session).\
                 filter_by(hostname=hostname).first()
    if not query:
        msg = "Error: update op_hostusage by hostname :%s Not Found" % hostname
        raise exception.QueryResultEmptyException(msg)
    return query


def op_hostusage_update(hostname, values):
    session = get_session()
    with session.begin():
        op_hostusage_ref = op_hostusage_get(hostname, session=session)
        values['updated_at'] = timeutils.utcnow()
        op_hostusage_ref.update(values)
        op_hostusage_ref.save(session=session)


def op_hostusage_get_all():
    query = model_query(models.OpenstackHostUsage)
    return query.all()


def op_hostusage_get_by_hostname(hostname):
    query = model_query(models.OpenstackHostUsage).\
                       filter_by(hostname=hostname).first()

    if not query:
        msg = "Error: No op_hostusage quered by hostname :%s " % hostname
        raise exception.QueryResultEmptyException(msg)
    return query


'''for openstack_config table Operation'''


def op_config_create(values):
    op_config_ref = models.OpenstackConfig()
    op_config_ref.update(values)
    op_config_ref.save()
    return op_config_ref


def op_config_get(session=None):
    query = model_query(models.OpenstackConfig, session=session).first()

    if not query:
        msg = "Error: No op_config please set openstack config"
        raise exception.QueryResultEmptyException(msg)
    return query


def op_config_update(values):
    session = get_session()
    with session.begin():
        op_config_ref = op_config_get(session=session)
        values['updated_at'] = timeutils.utcnow()
        op_config_ref.update(values)
        op_config_ref.save(session=session)
