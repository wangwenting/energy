namespace java energy.interface.agent
namespace py energy.interface.agent
namespace cpp energy.interface.agent

struct Result {
    1: i32 code,
    2: string value,
    3: string describe
}


service AgentService {

    Result host(1:string request),
    Result power(1:string request),
    Result temp(1:string request),
    Result airflow(1:string request),
    Result cups(1:string request),
    Result fanspeed(1:string request),
    Result thermalmargin(1:string request),

    Result get_openstack_config(1:string request),
    Result set_openstack_config(1:string request),
    Result get_openstack_host_usage(1:string request),
    Result thermal_low_temp_host_select(1:string request),
    Result cups_low_workload_host_select(1:string request),

    Result get_hadoop_config(1:string request),
    Result set_hadoop_config(1:string request),
    
}
