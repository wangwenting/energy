# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from oslo.config import cfg
from oslo.db import concurrency
from energy.common import log
from energy.common import utils

# _BACKEND_MAPPING = {'sqlalchemy': 'test.db.sqlalchemy.api'}
db_opts = [
    cfg.StrOpt('db_backend',
               default='sqlalchemy',
               help='The backend to use for db')]

CONF = cfg.CONF
CONF.register_opts(db_opts)

# IMPL = concurrency.TpoolDbapiWrapper(CONF, backend_mapping=_BACKEND_MAPPING)
IMPL = utils.LazyPluggable('db_backend',
                           sqlalchemy='energy.db.sqlalchemy.api')

LOG = log.getLogger(__name__)

''' hosts'''


def host_create(values):
    return IMPL.host_create(values)


def host_update(hostname, values):
    return IMPL.host_update(hostname, values)


def host_get_all():
    return IMPL.host_get_all()


def host_get_by_hostname(hostname):
    return IMPL.host_get_by_hostname(hostname)


'''service'''


def service_create(values):
    return IMPL.service_create(values)


def service_destroy(hostname, service_name):
    return IMPL.service_destroy(hostname, service_name)


def service_update(hostname, service_name, values):
    return IMPL.service_update(hostname, service_name,  values)


def service_get_all():
    return IMPL.service_get_all()


def service_get_by_hostname(hostname):
    return IMPL.service_get_by_hostname(hostname)


def service_get_by_service_name(service_name):
    return IMPL.service_get_by_service_name(service_name)


def service_get_by_multiple(hostname, service_name):
    return IMPL.service_get_by_multiple(hostname, service_name)


'''telemetry'''


def telemetry_create(values):
    return IMPL.telemetry_create(values)


def telemetry_update(hostname, values):
    return IMPL.telemetry_update(hostname, values)


def telemetry_get_all():
    return IMPL.telemetry_get_all()


def telemetry_get_by_hostname(hostname):
    return IMPL.telemetry_get_by_hostname(hostname)


'''openstack_host_usage'''


def op_hostusage_create(values):
    return IMPL.op_hostusage_create(values)


def op_hostusage_update(hostname, values):
    return IMPL.op_hostusage_update(hostname, values)


def op_hostusage_get_all():
    return IMPL.op_hostusage_get_all()


def op_hostusage_get_by_hostname(hostname):
    return IMPL.op_hostusage_get_by_hostname(hostname)


'''openstack_config'''


def op_config_create(values):
    return IMPL.op_config_create(values)


def op_config_update(values):
    return IMPL.op_config_update(values)


def op_config_get():
    return IMPL.op_config_get()
