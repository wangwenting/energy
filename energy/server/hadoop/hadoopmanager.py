from oslo.config import cfg
from energy.common import log


from energy.server import manager
from energy.server.hadoopserver import HadoopServiceIns
from energy.common import periodic_task


CONF = cfg.CONF
LOG = log.getLogger(__name__)


class HadoopManager(manager.ThriftManager):

    def __init__(self):
        super(HadoopManager, self).__init__(host=None)

    def add_service(self):
        self._services.add_thread(HadoopServiceIns.run_service)

    @periodic_task.periodic_task
    def test(self):
        print("just for a hadoop manager test")
