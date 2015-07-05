import time
from energy.common.connection import Connection
from energy.interface.agent import AgentService
import json

from energy.agent.agentconnection import AgentConnection


def test_openstack_config():
    con = AgentConnection('localhost',10009,"agent_conc")
    con.connect()
    data = {"dispatch": "THERMAL",
            "migraton": "OUTLETTEMP",
            "outlet_temp": 40}
    print(con.set_openstack_config(json.dumps(data)))

#test_openstack_config()

def test_thermal_low():
    con = AgentConnection('localhost',10009,"agent_conc")
    con.connect()
    data = con.thermal_low_temp_host_select("11")
    return data

print(test_thermal_low()) 
