import sys
from oslo.config import cfg


from energy.common import config
from energy.db import api as db_api


CONF = cfg.CONF


if __name__=="__main__":
    

    config.parse_args(sys.argv[1:])
    #values={'hostname':"11111",
    #        'status':"active"}
    #db_api.hosts_create(values)

    a = db_api.host_get_all()
    for i in a:
        print(i)

    b = db_api.host_get_by_hostname("11111")
    for i in b:
        print(i)

    values1={'hostname':"11111",
            'status':"LOSE"}
    db_api.host_update(values1["hostname"], values1)



    #values2={'hostname':"11111",'service_name':"energy_test",
    #          'report_count':1}
    #db_api.service_create(values2)

    
    a = db_api.service_get_all()
    for i in a:
        print(i)

    b = db_api.service_get_by_hostname("11111")
    for i in b:
        print(i)

    
    values2={'hostname':"11111",'service_name':"energy_test",
              'report_count':2}

    db_api.service_update(values2["hostname"], values2["service_name"],values2)

    #values3={'hostname':"11111",'cpu_cups':100,\
    #         'io_cups':55,'thermal_margin':"dadfafd"}

    #db_api.telemetry_create(values3)
    a = db_api.telemetry_get_all()
    for i in a:
        print(i)

    b = db_api.telemetry_get_by_hostname("11111")
    print(b)

    
    values4={'hostname':"11111",'cpu_cups':330,\
             'io_cups':55,'thermal_margins':"dadfafd"}
    db_api.telemetry_update(values4["hostname"], values4)



    values5 = {'dispatch':"aaaaaaaaa",'migration':"bbbbbb",
               'mig_enabled':True,'asm_enabled':True}
    #db_api.op_config_create(values5)

    a = db_api.op_config_get()
    print(a)

    values6 = {'dispatch':"aaaaaaaaa",'migration':"bbbbbb",
               'mig_enabled':False,'asm_enabled':True}

    db_api.op_config_update(values6)


    values7 = {'hostname':"11111", 'vcpu_num':10, 'vcpu_used':6}
    #db_api.op_hostusage_create(values7)
    
    a = db_api.op_hostusage_get_all()
    for i in a:
        print(i)
    b = db_api.op_hostusage_get_by_hostname("11111")
    print(b)

    values8 = {'hostname':"11111", 'vcpu_num':10, 'vcpu_used':2}
    db_api.op_hostusage_update("11111", values8)





