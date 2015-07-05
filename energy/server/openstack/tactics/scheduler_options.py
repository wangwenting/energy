class Migration(object):
    AIRFLOW = "AIRFLOW"
    OUTLETTEMP = "OUTLETTEMP"
    SIMPLEBALANCE = "SIMPLEBALANCE"
    POWERBALANCE = "POWERBALANCE"
    SENIOROUTLETTEMP = "SENIOROUTLETTEMP"

    def __init__(self):
        pass

    def set_migration(self, migration):
        self.migration_ = migration

    @property
    def migration(self):
        return self.migration_

    def is_migration(self, migration):
        return self.migration_ == migration

    def __str__(self):
        return "%s" % self.migration_


class Dispatch(object):
    THERMAL = "THERMAL"
    CUPS = "CUPS"
    NOVA = "NOVA"

    def __init__(self):
        pass

    def set_dispatch(self, dispatch):
        self.dispatch_ = dispatch

    @property
    def dispatch(self):
        return self.dispatch_

    def is_dispatch(self, dispatch):
        return self.dispatch_ == dispatch

    def __str__(self):
        return "%s" % self.dispatch_
