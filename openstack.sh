NOVA_SOURCE_CODE=/usr/lib/python2.7/dist-packages/nova
TOPDIR=/home/ubuntu/energy/software

function install_thermal_strategy() {
cnt=`cat /etc/nova/nova.conf | grep ThermalScheduler | wc -l`
if [[ $cnt -eq 0 ]]; then
[[ ! -e /opt/old_scheduler ]] && cp -rf $NOVA_SOURCE_CODE/scheduler /opt/old_scheduler
cp -rf $TOPDIR/scheduler_j/* $NOVA_SOURCE_CODE/scheduler/
cp -rf $TOPDIR/scheduler_j/* /usr/lib/python2.7/dist-packages/nova/scheduler/
sed -i "/scheduler_driver/d" /etc/nova/nova.conf
sed -i "/scheduler_available_filters/d" /etc/nova/nova.conf
sed -i "/scheduler_default_filters/d" /etc/nova/nova.conf

cat <<"EOF" >> /etc/nova/nova.conf
#----------------------------------------------------------------------
# Scheduler
#----------------------------------------------------------------------
scheduler_driver=nova.scheduler.thermal.ThermalScheduler
compute_scheduler_driver=nova.scheduler.thermal.ThermalScheduler
#scheduler_available_filters=nova.scheduler.filters.all_filters
#scheduler_default_filters=CoreFilter,ComputeFilter,SpecifiedHostFilter

energy_ip=10.10.20.51
energy_port=10009
EOF
fi
}

install_thermal_strategy
