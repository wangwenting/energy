from oslo.config import cfg
from sqlalchemy.ext.declarative import declarative_base
from oslo.db.sqlalchemy import models
from energy.common import timeutils
from sqlalchemy import Column
from sqlalchemy import orm
from sqlalchemy import DateTime, Integer, String, Boolean, ForeignKey
from energy.common import log


CONF = cfg.CONF
BASE = declarative_base()

LOG = log.getLogger(__name__)


class EnergyBase(
               models.TimestampMixin,
               models.ModelBase):
    metadata = None

    created_at = Column(DateTime, default=lambda: timeutils.utcnow())
    updated_at = Column(DateTime, onupdate=lambda: timeutils.utcnow())

    def save(self, session=None):
        from energy.db.sqlalchemy import api

        if session is None:
            session = api.get_session()
        super(EnergyBase, self).save(session=session)


class Host(BASE, EnergyBase):
    """Host inforamtion"""

    __tablename__ = 'hosts'

    hostname = Column(String(255), primary_key=True)
    cpu_info = Column(String(1024))
    mem_in_mb = Column(Integer)
    disk_in_gb = Column(Integer)
    bmc_ip = Column(String(255))
    status = Column(String(255))
    mem_used_in_mb = Column(Integer)
    cpu_used = Column(Integer)

    def __str__(self):
        return "hostname:%s, cpu_info:%s, mem_in_mb:%s, disk_in_gb:%s, bmc_ip:%s\
                status:%s, mem_used_in_mb:%s, cpu_used:%s"\
                % (self.hostname, self.cpu_info, self.mem_in_mb,
                   self.disk_in_gb, self.bmc_ip, self.status,
                   self.mem_used_in_mb, self.cpu_used)


class Service(BASE, EnergyBase):
    """Represents a running service on a host."""

    __tablename__ = 'services'

    id = Column(Integer, primary_key=True)
    hostname = Column(String(255), ForeignKey('hosts.hostname'),
                      nullable=False)
    # host = orm.relationship(Hosts,
    #                       backref=orm.backref('hosts'),
    #                       foreign_keys=hostname,
    #                       primaryjoin='Service.hostname == Hosts.hostname,')

    service_name = Column(String(255))
    report_count = Column(Integer, nullable=False, default=0)

    def __str__(self):
        return "id:%s, hostname:%s, service_name:%s,report_count:%s"\
                % (self.id, self.hostname, self.service_name,
                   self.report_count)


class Telemetry(BASE, EnergyBase):
    """The telemetry data on from each host."""

    __tablename__ = 'telemetry'

    id = Column(Integer, primary_key=True)
    hostname = Column(String(255), ForeignKey('hosts.hostname'),
                      nullable=False)

    cpu_cups = Column(Integer)
    io_cups = Column(Integer)
    mem_cups = Column(Integer)
    index_cups = Column(Integer)
    inlet_temp = Column(Integer)
    outlet_temp = Column(Integer)
    thermal_margins = Column(String(255))
    fans = Column(String(255))
    airflow = Column(Integer)
    system_power = Column(Integer)
    cpu_power = Column(Integer)

    def __str__(self):
        return "id:%s, hostname:%s, cpu_cups:%s, io_cups:%s, mem_cups:%s,\
                index_cups:%s, inlet_temp:%s, outlet_temp:%s,\
                termal_margins:%s, fans:%s, airflow:%s, \
                system_power:%s, cpu_power:%s"\
                % (self.id, self.hostname, self.cpu_cups, self.io_cups,
                   self.mem_cups, self.index_cups, self.inlet_temp,
                   self.outlet_temp, self.thermal_margins, self.fans,
                   self.airflow, self.system_power, self.cpu_power)

    def __init__(self):
        '''Initialization of the values'''
        self.create_at = timeutils.utcnow()
        self.updated_at = timeutils.utcnow()
        self.cpu_cups = 0
        self.io_cups = 0
        self.mem_cups = 0
        self.index_cups = 0
        self.inlet_temp = 0
        self.outlet_temp = 0
        self.thermal_margins = 0
        self.fans = "{}"
        self.airflow = 0
        self.system_power = 0
        self.cpu_power = 0


class OpenstackHostUsage(BASE, EnergyBase):
    """OpenStack related usage information."""

    __tablename__ = 'openstack_host_usage'

    id = Column(Integer, primary_key=True)
    hostname = Column(String(255), ForeignKey('hosts.hostname'),
                      nullable=False)

    vcpu_num = Column(Integer)
    running_vms = Column(Integer)
    vcpu_used = Column(Integer)
    instance_load = Column(String(10240))

    def __str__(self):
        return "id:%s, hostname:%s, vcpu_num:%s, running_vms:%s, vcpu_used:%s\
                insance_load:%s "\
                % (self.id, self.hostname, self.vcpu_num, self.running_vms,
                   self.vcpu_used, self.instance_load)


class OpenstackConfig(BASE, EnergyBase):
    """Openstack realted configuration items"""
    __tablename__ = 'openstack_config'

    id = Column(Integer, primary_key=True)
    dispatch = Column(String(255))
    migration = Column(String(255))
    mig_threshold = Column(String(1024))
    asm_threshold = Column(Integer)
    mig_enabled = Column(Boolean)
    asm_enabled = Column(Boolean)
    # workload = Coulumn(Integer)

    def __str__(self):
        return "id:%s, dispatch:%s, migration:%s, mig_threshold:%s,\
                asm_threshold:%s, mig_enabled:%s, asm_enabled:%s"\
                % (self.id, self.dispatch, self.migration, self.mig_threshold,
                   self.asm_threshold, self.mig_enabled, self.asm_enabled)
