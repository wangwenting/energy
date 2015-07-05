import time
from energy.agent.hostconnection import HostConnection
from energy.agent.openstackconnection import OpenstackConnection


   
con = HostConnection('localhost',10010,"host_conc")
con.connect()
a = con.host("1111")
print(a)

#b = con.temp("11111")
#print(b)
#b = con.cups("111")
#print(b)
#b = con.thermalmargin("111")
#print(b)
#b = con.fanspeed("111")
#print(b)
#b = con.power("111")
#print(b)


con1 = OpenstackConnection('localhost',10012,"hadoop_conc")
con1.connect()
c = con1.get_openstack_config("1111")
print(c)

d = con1.thermal_low_temp_host_select("1111")
print(d)

e = con1.cups_low_workload_host_select("1111")
print(e)
#d = con1.set_openstack_config(json.dumps({"mig_enabled":True,
#                                          "asm_enabled": False}))
#print d
#c = con1.get_openstack_config("1111")
#print(c)
