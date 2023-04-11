import os
import time
from novaclient import client as nvclient
from keystoneauth1 import identity
from keystoneauth1 import session
from neutronclient.v2_0 import client
n_netw = int(input("Enter number of virtual networks to be creates: "))
print(n_netw)
username='admin'
password='nikkinvo'
project_name='admin'
project_domain_name='Default'
user_domain_name='Default'
auth_url='http://172.16.200.2/identity'
# neutron = client.Client(auth_url=auth_url,
#                                 username=username,
#                                 password=password,
#                                 project_name=project_name,
#                                 user_domain_name=user_domain_name,
#                                 project_domain_name=project_domain_name)
nova = nvclient.Client(version='2.1', auth_url= "http://172.16.200.2/identity", username = "admin", password = "nikkinvo", user_domain_name = "Default", project_name = "admin",project_domain_name = "Default")
auth = identity.Password(auth_url=auth_url,
                         username=username,
                         password=password,
                         project_name=project_name,
                         project_domain_name=project_domain_name,
                         user_domain_name=user_domain_name)

sess = session.Session(auth=auth)
neutron = client.Client(session=sess)
# external_net = neutron.list_subnets(name='shared-subnet')
# print(external_net)
# print(external_net['subnets'][0]['id'])
count = 0
for n in range(n_netw):
    network_name = input("Enter Name of network that you want to create:")
    print(network_name)
    netw = neutron.create_network({'network': {'name': network_name, 'shared': True}})['network']
    network_id = netw['id']
    print('Network %s created' % network_id)
    network_cidr = input("Enter cidr of network that you want to create:")
    print(network_cidr)
    subnet = neutron.create_subnet({'subnet': {'network_id': netw['id'], 'cidr': network_cidr, 'ip_version': 4, 'enable_dhcp': True}})['subnet']
    
    print('Created subnet %s' % subnet)
    im = nova.glance.find_image("nat_mininet")
    fl = nova.flavors.find(name= "m1.large")
    key_name = 'containervm'
    instance_id = 'my-vm-{}'.format(n+1)
    nic = {'net-id': netw['id']}
    new_vm = nova.servers.create(name=instance_id, image=im, flavor=fl,
                             key_name=key_name, nics=[nic])
    print(new_vm)
    vm_id = new_vm.id
    time.sleep(40)
    external_net = neutron.list_networks(name='public')['networks'][0]
    shared_net =  neutron.list_subnets(name='shared-subnet')['subnets'][0]
    print(external_net['id'])
    ports = neutron.list_ports(device_id=vm_id)['ports']
    if ports:
        port_id = ports[0]['id']
        print('Port ID: {}'.format(port_id))
    else:
        print('No ports found for instance {}'.format(instance_id))
    router_name = "rouint"
    if count == 0:
        router_body = {'router': {'name': router_name}}
        router = neutron.create_router(body=router_body)['router']
        router_id = router['id']
        neutron.add_interface_router(router_id, {'subnet_id': shared_net['id']})
        neutron.add_interface_router(router_id, {'subnet_id': subnet['id']})
        neutron.add_gateway_router(router_id, {'network_id': external_net['id']})
        time.sleep(20)
    else:

        router_list = neutron.list_routers(name=router_name)['routers']
        routerf = router_list[0]
        router_id = routerf['id']
        neutron.add_interface_router(router_id, {'subnet_id': subnet['id']})
        # external_net = neutron.list_networks(name='public')['networks'][0]
       
    floating_ip = neutron.create_floatingip({'floatingip': {'floating_network_id': external_net['id']}})
    neutron.update_floatingip(floating_ip['floatingip']['id'], {'floatingip': {'port_id': port_id}})
    count = count + 1
print("INNNN")
instance_name1 = "my-vm-1"
instance1 = nova.servers.find(name=instance_name1)
instance_id1 = instance1.id
instance_name2 = "my-vm-2"
instance2 = nova.servers.find(name=instance_name2)
instance_id2 = instance1.id
ports = neutron.list_ports(device_id=instance_id1)['ports']
ports2 = neutron.list_ports(device_id=instance_id2)['ports']
# Disable port security and remove security groups from each port
for port in ports:
    port_id = port["id"]
    port_body = {"port": {"port_security_enabled": False, "security_groups": []}}
    p1 = neutron.update_port(port_id, port_body)
    print(p1)
for port2 in ports2:
    port_id2 = port2["id"]
    port_body2 = {"port": {"port_security_enabled": False, "security_groups": []}}
    p2 = neutron.update_port(port_id2, port_body2)
    print(p2)