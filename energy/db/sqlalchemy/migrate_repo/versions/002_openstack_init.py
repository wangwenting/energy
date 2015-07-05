from sqlalchemy import Boolean, Column, DateTime, ForeignKey
from sqlalchemy import Integer, MetaData, String, Table
from sqlalchemy import Table, Text, Float


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine;
    # bind migrate_engine to# your metadata
    print("upgrade start")
    meta = MetaData()
    meta.bind = migrate_engine

    hosts = Table('hosts', meta,
                  Column('created_at', DateTime),
                  Column('updated_at', DateTime),
                  Column('hostname', String(length=255),
                         primary_key=True, nullable=False),
                  Column('cpu_info', String(length=1024)),
                  Column('mem_in_mb', Integer),
                  Column('disk_in_gb', Integer),
                  Column('bmc_ip', String(length=255)),
                  Column('status', String(length=255)),
                  Column('mem_used_in_mb', Integer),
                  Column('cpu_used', Integer))

    openstack_host_usage = Table('openstack_host_usage', meta,
                                 Column('created_at', DateTime),
                                 Column('updated_at', DateTime),
                                 Column('id', Integer, primary_key=True,
                                        nullable=False),
                                 Column('hostname', String(length=255),
                                        ForeignKey('hosts.hostname'),
                                        nullable=False),
                                 Column('vcpu_num', Integer),
                                 Column('running_vms', Integer),
                                 Column('instance_load', String(length=10240)),
                                 Column('vcpu_used', Integer))

    openstack_config = Table('openstack_config', meta,
                             Column('created_at', DateTime),
                             Column('updated_at', DateTime),
                             Column('id', Integer, primary_key=True,
                                    nullable=False),
                             Column('dispatch', String(length=255)),
                             Column('migration', String(length=255)),
                             Column('mig_threshold', String(length=1024)),
                             Column('asm_threshold', Integer),
                             Column('mig_enabled', Boolean),
                             Column('asm_enabled', Boolean))

    try:
        openstack_host_usage.create()
    except Exception:
        print('Exception while creating table openstack_host_usage')
        meta.drop_all(tables=[openstack_host_usage])
        raise

    try:
        openstack_config.create()
    except Exception:
        print('Exception while creating table openstack_config')
        meta.drop_all(tables=[openstack_config])
        raise


def downgrade(migrate_engine):
    print("downgrade start")
    meta = MetaData()
    meta.bind = migrate_engine

    openstack_host_usage = Table('openstack_host_usage',
                                 meta,
                                 autoload=True)
    openstack_host_usage.drop()

    openstack_config = Table('openstack_config',
                             meta,
                             autoload=True)
    openstack_config.drop()
