namespace java energy.interface.openstack
namespace py energy.interface.openstack
namespace cpp energy.interface.openstack


service OpenstackService {

    string get_openstack_config(1:string request),
    string set_openstack_config(1:string request),
    string get_openstack_host_usage(1:string request),
    string thermal_low_temp_host_select(1:string request),
    string cups_low_workload_host_select(1:string request),
    
}
