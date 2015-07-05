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

    services = Table('services', meta,
                     Column('created_at', DateTime),
                     Column('updated_at', DateTime),
                     Column('id', Integer,
                            primary_key=True, nullable=False),
                     Column('hostname', String(length=255),
                            ForeignKey('hosts.hostname'), nullable=False),
                     Column('service_name', String(length=255)),
                     Column('report_count', Integer, nullable=False))

    telemetry = Table('telemetry', meta,
                      Column('created_at', DateTime),
                      Column('updated_at', DateTime),
                      Column('id', Integer,
                             primary_key=True, nullable=False),
                      Column('hostname', String(length=255),
                             ForeignKey('hosts.hostname'), nullable=False),
                      Column('cpu_cups', Integer),
                      Column('io_cups', Integer),
                      Column('mem_cups', Integer),
                      Column('index_cups', Integer),
                      Column('inlet_temp', Integer),
                      Column('outlet_temp', Integer),
                      Column('thermal_margins', String(length=1024)),
                      Column('fans', String(length=1024)),
                      Column('airflow', Integer),
                      Column('system_power', Integer),
                      Column('cpu_power', Integer))
    try:
        hosts.create()
    except Exception:
        print('Exception while creating table hosts')
        meta.drop_all(tables=[hosts])
        raise

    try:
        services.create()
    except Exception:
        print('Exception while creating table services')
        meta.drop_all(tables=[services])
        raise

    try:
        telemetry.create()
    except Exception:
        print('Exception while creating table telemetry')
        meta.drop_all(tables=[telemetry])
        raise


def downgrade(migrate_engine):
    print("downgrade start")
    meta = MetaData()
    meta.bind = migrate_engine

    services = Table('services',
                     meta,
                     autoload=True)
    services.drop()

    telemetry = Table('telemetry',
                      meta,
                      autoload=True)
    telemetry.drop()

    hosts = Table('hosts',
                  meta,
                  autoload=True)
    hosts.drop()
