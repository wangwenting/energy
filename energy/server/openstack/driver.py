from oslo.config import cfg
from energy.common import log

from energy.server.openstack.tactics import power_control
from energy.server.openstack.tactics import outlettemp_mgr
from energy.server.openstack.tactics import senior_outlettemp_mgr
from energy.server.openstack.tactics import airflow_mgr
from energy.server.openstack.tactics import simplebalance_mgr
from energy.server.openstack.tactics import scheduler_options


CONF = cfg.CONF
LOG = log.getLogger(__name__)


class Driver(object):
    def __init__(self):
        self._migration = scheduler_options.Migration()
        self._dispatch = scheduler_options.Dispatch()
        self._power_tactics = power_control.PowerControl()
        self._outlet_temp = outlettemp_mgr.OutletTemp()
        self._senior_outlet_temp = senior_outlettemp_mgr.SeniorOutletTemp()
        self._airflow = airflow_mgr.Airflow()
        self._simple_balance = simplebalance_mgr.SimpleBalance()

    def update_host_status(self):
        self._power_tactics.update_host_status()

    def set_migration(self, migration):
        self._migration.set_migration(migration)

    def set_dispatch(self, dispatch):
        self._dispatch.set_dispatch(dispatch)

    def is_dispatch(self, dispatch):
        return self._dispatch.is_dispatch(dispatch)

    def is_migration(self, migration):
        return self._migration.is_migration(migration)

    def get_dispatch(self):
        return self._dispatch.dispatch

    def get_migration(self):
        return self._migration.migration

    def migration_tactics(self):
        LOG.info("Current Migration is %s" % self.get_migration())
        print("Current Migration is %s" % self.get_migration())
        if self.get_migration() == scheduler_options.Migration.OUTLETTEMP:
            self._outlet_temp.run()
        if self.get_migration() == scheduler_options.Migration.AIRFLOW:
            self._airflow.run()
        if self.get_migration() == scheduler_options.Migration.SIMPLEBALANCE:
            self._simple_balance.run()
        if self.get_migration() == scheduler_options.Migration.SENIOROUTLETTEMP:
            self._senior_outlet_temp.run()

    def power_tactics(self):
        return self._power_tactics.power_tactics()
