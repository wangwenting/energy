"""
Thermal (Random) Scheduler implementation, data gathering is a periodictiy task by energy-bmc
rank the servers base on outlet temperature hottest to coolest
choose the coolest server
"""

import random
import json

from oslo.config import cfg

from nova.compute import rpcapi as compute_rpcapi
from nova import exception
from nova.scheduler import driver
from nova.openstack.common import log as logging
from nova.openstack.common.gettextutils import _

from energy.agent.agentconnection import AgentConnection


thermal_opts = [
    cfg.StrOpt('energy_ip',
               required=True,
               help='The user name of energy serivce registered in Keystone'),
    cfg.IntOpt('energy_port',
               default=10009,
               help='The password of energy service registered in Keystone'),
    ]

LOG = logging.getLogger(__name__)
CONF = cfg.CONF
CONF.register_opts(thermal_opts)
CONF.import_opt('compute_topic', 'nova.compute.rpcapi')


class ThermalScheduler(driver.Scheduler):
    """Implements Scheduler as a random node selector."""

    def __init__(self, *args, **kwargs):
        self.compute_rpcapi = compute_rpcapi.ComputeAPI()
        super(ThermalScheduler, self).__init__(*args, **kwargs)
        LOG.info("energy_ip:%s, energy_port:%s " % (CONF.energy_ip, CONF.energy_port))
        self.con = AgentConnection(CONF.energy_ip, CONF.energy_port, "AgentCon")
        try:
            self.con.connect()
        except Exception, e:
            LOG.exception("Connect to AgentConnection failed!:'%s'", % e)

    def _filter_hosts(self, request_spec, hosts, filter_properties, elevated=None):
        """Filter a list of hosts based on request_spec."""
        LOG.debug("WTWANG _filter_hosts start hosts:%s" % hosts)
        ignore_hosts = filter_properties.get('ignore_hosts', [])
        hosts = [host for host in hosts if host not in ignore_hosts]
        all_hosts = self.host_manager.get_all_host_states(elevated)
        filtered_hosts = self.host_manager.get_filtered_hosts(all_hosts,
                                                              filter_properties)
        filtered_hosts = [host.host for host in filtered_hosts]
        LOG.debug("WTWANG Filter hosts %s" % filtered_hosts)
        hosts = [host for host in hosts if host in filtered_hosts]
        return hosts

    def thermal_low_temp_host_select(self):
        try:
            ret = self.con.thermal_low_temp_host_select()
        except Exception, e:
            self.con.connect()
            return self.con.thermal_low_temp_host_select()
        return ret

    def _schedule(self, context, topic, request_spec, filter_properties):
        LOG.debug("WTWANG _schedule start topic :%s" % topic)
        """Picks a host that is up at random."""
        elevated = context.elevated()
        hosts = self.hosts_up(elevated, topic)
        if not hosts:
            msg = _("Is the appropriate service running?")
            raise exception.NoValidHost(reason=msg)

        hosts = self._filter_hosts(request_spec, hosts, filter_properties, elevated)
        if not hosts:
            msg = _("Could not find another compute")
            raise exception.NoValidHost(reason=msg)

        request_spec['compute_host_list'] = hosts
        LOG.info('WTWANG _scheduler request_spec %s' % request_spec)
        ret = self.thermal_low_temp_host_select()
        if ret.value:
            ret = json.loads(ret.value)
        else:
            return None
        LOG.info('WTWANG ret of thermal_host_select = %s' % ret)
        if len(ret) > 0:
            hosts = ret

        return hosts[int(random.random() * len(hosts))]

    def select_destinations(self, context, request_spec, filter_properties):
        """Selects a set of random hosts."""
        num_instances = request_spec['num_instances']
        LOG.info('wtwang num_insances:%s' % num_instances)
        selected_host = [self._schedule(context, CONF.compute_topic,
                                        request_spec, filter_properties)]
        dests = []
        for i in range(0, num_instances):
            dests.append(dict(host=selected_host[0], nodename=selected_host[0],
                              limits=None))

        return dests

    def schedule_run_instance(self, context, request_spec,
                              admin_password, injected_files,
                              requested_networks, is_first_time,
                              filter_properties, legacy_bdm_in_spec):
        """Create and run an instance or instances."""

        instance_uuids = request_spec.get('instance_uuids')

        for num, instance_uuid in enumerate(instance_uuids):
            request_spec['instance_properties']['launch_index'] = num
            try:
                host = self._schedule(context, CONF.compute_topic,
                                      request_spec, filter_properties)
                updated_instance = driver.instance_update_db(context,
                                                             instance_uuid)
                self.compute_rpcapi.run_instance(context,
                                                 instance=updated_instance, host=host,
                                                 requested_networks=requested_networks,
                                                 injected_files=injected_files,
                                                 admin_password=admin_password,
                                                 is_first_time=is_first_time,
                                                 request_spec=request_spec,
                                                 filter_properties=filter_properties,
                                                 legacy_bdm_in_spec=legacy_bdm_in_spec)
            except Exception as ex:
                # NOTE(vish): we don't reraise the exception here to make sure
                #             that all instances in the request get set to
                #             error properly
                driver.handle_schedule_error(context, ex, instance_uuid,
                                             request_spec)

    def schedule_prep_resize(self, context, image, request_spec,
                             filter_properties, instance, instance_type,
                             reservations):
        """Select a target for resize."""

        host = self._schedule(context, CONF.compute_topic, request_spec,
                              filter_properties)
        self.compute_rpcapi.prep_resize(context, image, instance,
                                        instance_type, host, reservations)
