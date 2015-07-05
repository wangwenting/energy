import socket
import os
import sys
import random
from oslo.config import cfg
from energy.common import log
from energy.common import utils
from energy.common import service as ser
from energy.db import api as db_api
from energy import exception

LOG = log.getLogger(__name__)

service_opts = [
    cfg.IntOpt('report_interval',
               default=10,
               help='Seconds between nodes reporting state to datastore'),
    cfg.IntOpt('periodic_interval',
               default=5,
               help='seconds between running periodic tasks'),
    cfg.IntOpt('periodic_fuzzy_delay',
               default=60,
               help='Range of seconds to randomly delay when starting the'
                    ' periodic task scheduler to reduce stampeding.'
                    ' (Disable by setting to 0)'),
    cfg.StrOpt('sampler_manager',
               default='energy.sampler.manager.OpenStackSamplerManager',
               help='full class name for the Manager for sampler'),
    cfg.StrOpt('server_manager',
               default='energy.server.openstack.openstackmanager.OpenstackManager',
               help='full class name for the Manager for server'),
    cfg.StrOpt('host',
               default=socket.gethostname(),
               help='Name of this node.  This can be an opaque identifier.  '
                    'It is not necessarily a hostname, FQDN, or IP address.'),

    ]

CONF = cfg.CONF
CONF.register_opts(service_opts)


class Service(ser.Service):
    def __init__(self, host, manager, binary, report_interval=None,
                 periodic_enable=None, periodic_fuzzy_delay=None,
                 periodic_interval_max=None, periodic_interval=True,
                 *args, **kwargs):
        print("start create  service")
        super(Service, self).__init__()
        self.host = host
        self.manager_class_name = manager
        self.binary = binary
        print("host:%s, binary:%s" % (self.host, self.binary))

        manager_class = utils.import_class(self.manager_class_name)
        self.manager = manager_class(host=self.host, *args, **kwargs)
        self.report_interval = report_interval
        self.periodic_interval = periodic_interval
        self.periodic_fuzzy_delay = periodic_fuzzy_delay
        self.saved_args, self.saved_kwargs = args, kwargs
        print("service create sucess")

    def _create_service_ref(self):
        values = {
            'hostname': self.host,
            'service_name': self.binary,
            'report_count': 0
        }
        service = db_api.service_create(values)
        return service

    def report_state(self):
        state = {}
        try:
            print("report service state")
            service_ref = db_api.service_get_by_multiple(self.host, self.binary)
        except exception.QueryResultEmptyException, e:
            print("create services table data first time")
            self._create_service_ref()
            service_ref = db_api.service_get_by_multiple(self.host, self.binary)
        try:
            state['report_count'] = service_ref.report_count + 1
            db_api.service_update(self.host, self.binary, state)
        except Exception, e:
            print("update service tables error: hostname:%s, service:%s\
                   message:%s" % (self.host, self.binary, e.message))

    def start(self):
        self.manager.add_host_service()
        self.manager.add_service()

        if self.periodic_fuzzy_delay:
            initial_delay = random.randint(0, self.periodic_fuzzy_delay)
        else:
            initial_delay = None

        try:
            service_ref = db_api.service_get_by_multiple(self.host, self.binary)
        except exception.QueryResultEmptyException, e:
            print("create services table data first time")
            self._create_service_ref()

        self.tg.add_timer(self.report_interval, self.report_state, 5)

        self.tg.add_timer(self.periodic_interval, self.periodic_tasks,
                          initial_delay)

    def __getattr__(self, key):
        manager = self.__dict__.get('manager', None)
        return getattr(manager, key)

    @classmethod
    def create(cls, host=None, manager=None,
               report_interval=None,
               periodic_fuzzy_delay=None,
               periodic_interval=None):
        """Instantiates class and passes back application object.

        :param host: defaults to CONF.host
        :param manager: defaults to CONF.<topic>_manager
        :param report_interval: defaults to CONF.report_interval
        :param periodic_enable: defaults to CONF.periodic_enable
        :param periodic_fuzzy_delay: defaults to CONF.periodic_fuzzy_delay
        :param periodic_interval_max: if set, the max time to wait between runs

        """
        if not host:
            host = CONF.host
        binary = os.path.basename(sys.argv[0])
        print(binary.rpartition('energy-')[2])
        if not manager:
            manager_cls = ('%s_manager' %
                           binary.rpartition('energy-')[2])
            print(manager_cls)
            manager = CONF.get(manager_cls, None)
        if report_interval is None:
            report_interval = CONF.report_interval
        if periodic_fuzzy_delay is None:
            periodic_fuzzy_delay = CONF.periodic_fuzzy_delay
        if periodic_interval is None:
            periodic_interval = CONF.periodic_interval

        service_obj = cls(host, manager, binary,
                          report_interval=report_interval,
                          periodic_fuzzy_delay=periodic_fuzzy_delay,
                          periodic_interval=periodic_interval)

        return service_obj

    def kill(self):
        """Destroy the service object in the datastore."""
        self.stop()
        db_api.service_destroy(self.host, self.binary)

    def stop(self):
        try:
            self.manager.cleanup()
        except Exception:
            LOG.exception('Service error occurred during cleanup_host')
            pass

        super(Service, self).stop()

    def periodic_tasks(self, raise_on_error=False):
        """Tasks to be run at a periodic interval."""
        print("service periodic_tasks start")
        return self.manager.periodic_tasks()

_launcher = None


def serve(server, workers=None):
    global _launcher
    if _launcher:
        raise RuntimeError(_('serve() can only be called once'))
    print('start serve')

    _launcher = ser.launch(server, workers=workers)
    print('end serve')


def wait():
    _launcher.wait()
