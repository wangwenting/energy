namespace java energy.interface.host
namespace py energy.interface.host
namespace cpp energy.interface.host


service HostInfoService {

    string host(1:string request),
    string power(1:string request),
    string temp(1:string request),
    string airflow(1:string request),
    string cups(1:string request),
    string fanspeed(1:string request),
    string thermalmargin(1:string request)
    
}
