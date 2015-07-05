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
from energy.common import log
from energy.common import periodic_task


CONF = cfg.CONF
LOG = log.getLogger(__name__)


class Manager(periodic_task.PeriodicTasks):

    def __init__(self, host=None):
        if not host:
            host = CONF.host
        self.host = host

    def periodic_tasks(self):
        """Tasks to be run at a periodic interval."""
        print('manage_periodic_tasks')
        return self.run_periodic_tasks()

    def add_host_service(self):
        """Init host info thrift service
        Child classes should override this method
        """
        pass

    def cleanup_host(self):
        """Hook to do cleanup work when the service shuts down.

        Child classes should override this method.
        """
        pass

    def add_service(self):
        pass

    def wait(self):
        pass
