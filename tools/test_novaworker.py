from novaclient import client as nova_client
import pdb
nova_api_version = "1.1"
nova_user_name = "nova"
nova_password = "password"
nova_tenant_name = "service"
nova_auth_url = "http://10.10.20.51:35357/v2.0"

nc = nova_client.Client(nova_api_version,
                        nova_user_name, nova_password,
                        nova_tenant_name, nova_auth_url)
print nc
#pdb.set_trace()

a = nc.servers.list()
print(a)
for item in a:
    print(dir(item))
    print(item.__getattr__("OS-EXT-SRV-ATTR:host"),item.id, item.image, item.human_id, item.hostId)
b = nc.services.list()
for item in b:
    print(item.binary, item.status, item.host)

