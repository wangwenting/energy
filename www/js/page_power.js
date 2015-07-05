var linedata=[];
var vms = [];
var host_usage = [];
var vmupdate_flag = 0;
var host_usgage_update_flag = 0;
var vcpuused = 0;
var mig_enable = null;
var asm_enable = null;
var asm_threshold = null;

var compositesetting={

    url_api: 'http://10.239.52.36:8080',
    flgcolor_indicator: true,
    flgcolor_highlight: true,
    prex_host: 'canvas_host_',
    prex_chart: 'chart_line_',
    show_message_st: null,
    load_times: 0
};


function initpage() {
    $('#nav_bar_div').children().andSelf().hide();
    $('#logo>label').hide();
    $('#header_title').html('Intelligent Thermal Management Using Real Time Telemetry -- Based on Intel&reg; Grantley Systems');

    $('#content_div').width(document.body.clientWidth-$('#brief_div').width()-50);

    setheight();

    $('#img_config_asm').click(function(event){  actionConfig(0);   event.stopPropagation();   });
    $('#cbs_tbl img[src*=arrow_back]').click(function() { slide_brokenline(this,1); });
    $('#cbs_tbl img[src*=arrow_next]').click(function() { slide_brokenline(this,2); });
    $('#cbs_config_div img').click(function(){ toggle_scheduler(this); });
    $('#sel_scheduler').change(function(){ change_scheduler(this); }).change();

    google.load("visualization", "1", {packages:["corechart"]});


    getvminfo();
    gethost_usage();
    showdatacenterinfo();
    showscheduleinfo();
    flash_nodes(1);
    flash_nodes(2);
    read_data();
    paint_brokenline();

}


function getvminfo(){
    $.ajax({
        url : compositesetting.url_api+"/v1/openstack/vm",
        type : 'GET',
        dataType : 'jsonp',
        jsonp : 'callback',
        crossDomain : true,
        error : function(xhr, textStatus, errorThrown) {
            if($.console()) console.log("error at /openstack/vm: " + errorThrown);
        },
        success : function(res, textStatus, xhr) {
            if(!res) return;
        vms = res.vm;
        }
   });
   vmupdate_flag = 1;
   setTimeout(getvminfo, 1000);

}

function gethost_usage(){
   $.ajax({
        url : compositesetting.url_api+"/v1/openstack/host_usage",
        type : 'GET',
        dataType : 'jsonp',
        jsonp : 'callback',
        crossDomain : true,
        error : function(xhr, textStatus, errorThrown) {
            if($.console()) console.log("error at /openstack/host_usage: " + errorThrown);
        },
        success : function(res, textStatus, xhr) {
	var tmp_vcpuused = 0
        if(!res) return;
        host_usage = res.host_usage;
        for (var i = 0; i < res.host_usage.length; i++){
        tmp_vcpuused += parseInt(res.host_usage[i].vcpu_used || 0);
        }
        vcpuused = tmp_vcpuused;
        }
   });
   host_usgage_update_flag = 1;
   setTimeout(gethost_usage, 1000);

}


function showdatacenterinfo(){


   $.ajax({
        url : compositesetting.url_api+"/v1/common/host",
        type : 'GET',
        dataType : 'jsonp',
        jsonp : 'callback',
        crossDomain : true,
        error : function(xhr, textStatus, errorThrown) {
            if($.console()) console.log("error at /common/host: " + errorThrown);
        },
        success : function(res, textStatus, xhr) {
            if(!res) return;
//            alert(JSON.stringify(res.host_info[0].hostname));
            var vcpuactive = 0;
            var cpucores = 0;
            var memsize = 0;
            var activehosts = 0;
            var standbyhosts = 0;
	    var host_info = [];
            for(var i = 0; i < res.host.length; i++){
//		alert(res.host_info.length);
//		console.log(JSON.stringify(res.host_info[i]));
//                alert(JSON.stringify(res.host_info[i]));
		// Or 0 to avoid NaN
                cpucores += parseInt(res.host[i].cpu_info.cpus || 0);
                vcpuactive += 'dont_ctrl,active'.indexOf(res.host[i].status.toLowerCase()) >= 0 ? parseInt(res.host[i].cpu_info.cpus || 0) : 0;
                memsize+=parseInt(res.host[i].mem_in_mb || 0 );
                activehosts+=res.host[i].status.toLowerCase()=='active' ? 1 : 0;
                activehosts+=res.host[i].status.toLowerCase()=='dont_ctrl' ? 1 : 0;
                standbyhosts+=res.host[i].status.toLowerCase()=='standby' ? 1 : 0;
//                standbyhosts+=res.host_info[i].status.toLowerCase()=='lose' ? 1 : 0;
//                standbyhosts+=res.host_info[i].status.toLowerCase()=='error' ? 1 : 0;
            }
            $('#brief_div tr:eq(1)').children('td:last').text(res.host.length)
                              .end().next().children('td:last').text(cpucores)
                              .end().next().children('td:last').text(memsize)
                              .end().next().children('td:last').text(activehosts)
                              .end().next().children('td:last').text(standbyhosts)
                              .end().next().children('td:last').text(Math.round(100*vcpuused/vcpuactive)+'%');
	    host_info = res.host;
 	    for(var host_index = 0; host_index < host_info.length; host_index++){
    			host_info[host_index].instances = [];
			host_info[host_index].vcpu_used = 0;
			host_info[host_index].vm_num = 0;
			host_info[host_index].vcpu = 0;
	    		for(var i = 0; i < vms.length; i++){
				if (host_info[host_index].hostname == vms[i].host){
					host_info[host_index].instances.push({
						status: vms[i].status,
						host: vms[i].host,
						uuid: vms[i].uuid,
						name: vms[i].name
					});
				}
			}

		       for(var i = 0; i < host_usage.length; i++){
				if (host_info[host_index].hostname == host_usage[i].hostname){
					host_info[host_index].vcpu = host_usage[i].vcpu_num;
					host_info[host_index].vcpu_used = host_usage[i].vcpu_used;
					host_info[host_index].vm_num = host_usage[i].running_vms;
				}
		       }
	    }	
	    if (vmupdate_flag == 1 && host_usgage_update_flag == 1){
                paint_nodes(host_info);
            }
        }
    });

    setTimeout(showdatacenterinfo, 1000);
}


function showscheduleinfo(){
    $.ajax({
        url : compositesetting.url_api+"/v1/openstack/config",
        type : 'GET',
        dataType : 'jsonp',
        jsonp : 'callback',
        crossDomain : true,
        error : function(xhr, textStatus, errorThrown) {
            if($.console()) console.log("error at /openstack/config: " + textStatus);
        },
        success : function(schedulerinfo, textStatus, xhr) {
            if(!schedulerinfo || !schedulerinfo.config) return;

            var tbd=$('#tbl_scheduler>tbody');
	    if (schedulerinfo.config.mig_enabled == true){
		    switch(schedulerinfo.config.dispatch){
			case "THERMAL":
			    tbd.children('tr:eq(1)').children('td:last').text('Thermal');
			    tbd.children('tr:gt(2)').remove();
			    switch(schedulerinfo.config.migration){
				case "AIRFLOW":
				    tbd.children('tr:eq(2)').children('td:last').text(' Airflow');
				    tbd.append('<tr><td style="font-weight:bold !important;">Threshold:</td><td></td></tr>');
				    tbd.append('<tr><td>Airflow:</td><td>'+schedulerinfo.config.mig_threshold.airflow+'</td></tr>');
				    tbd.append('<tr><td>Inlet Temp:</td><td>'+schedulerinfo.config.mig_threshold.inlet_temp+'</td></tr>');
				    tbd.append('<tr><td>Power Consump:</td><td>'+schedulerinfo.config.mig_threshold.power_consumption+'</td></tr>');
				    break;
				case "OUTLETTEMP":
				    tbd.children('tr:eq(2)').children('td:last').text('Outlet Temp');
				    tbd.append('<tr><td style="font-weight:bold !important;">Threshold:</td><td></td></tr>');
				    tbd.append('<tr><td>Outlet Temp:</td><td>'+schedulerinfo.config.mig_threshold.outlet_temp+'</td></tr>');
				    break;
				case "SENIOROUTLETTEMP":
				    tbd.children('tr:eq(2)').children('td:last').text('Senior Outlet Temp');
				    tbd.append('<tr><td style="font-weight:bold !important;">Threshold:</td><td></td></tr>');
				    break;
			    }
			    break;
			case "CUPS":
			    tbd.children('tr:eq(1)').children('td:last').text('CUPS');
			    tbd.children('tr:gt(2)').remove();
			    switch(schedulerinfo.config.migration){
				case "SIMPLEBALANCE":
				    tbd.children('tr:eq(2)').children('td:last').text('Simple Balance');
				    tbd.append('<tr><td style="font-weight:bold !important;">Threshold:</td><td></td></tr>');
				    tbd.append('<tr><td>Workload:</td><td>'+schedulerinfo.config.mig_threshold.workload+'</td></tr>');
				    break;
				case "POWERBALANCE":
				    tbd.children('tr:eq(2)').children('td:last').text('Power Balance');
				    tbd.append('<tr><td style="font-weight:bold !important;">Threshold:</td><td></td></tr>');
				    tbd.append('<tr><td>Power Increase:</td><td>'+schedulerinfo.config.mig_threshold.power_increase+' W / 5%</td></tr>');
				    break;
			    }
			    break;
		    }
		}
	 else{
			    tbd.children('tr:gt(2)').remove();
	 }
         tbd.append('<tr><td style="font-weight:bold !important;">ASM Enabled:</td><td>' + schedulerinfo.config.asm_enabled.toString().toUpperCase() + '</td></tr>');
//	 mig_enable = schedulerinfo.config.mig_enabled;
//	 asm_enable = schedulerinfo.config.asm_enabled;
	 var mig_checkbox = document.getElementById("mig");
	 var asm_checkbox = document.getElementById("asm");
	 var asm_threshold_local = document.getElementById("txt_loading_threshold");
         mig_checkbox = $(mig_checkbox);
	 asm_checkbox = $(asm_checkbox);
         asm_threshold_local.value =  schedulerinfo.config.asm_threshold;
	 if (schedulerinfo.config.mig_enabled){
		mig_checkbox.children('img')[0].style.display = "none";
		mig_checkbox.children('img')[1].style.display = "initial";
		mig_enable = 1;
	 }
         else{
		mig_checkbox.children('img')[1].style.display = "none";
		mig_checkbox.children('img')[0].style.display = "initial";
		mig_enable = 0;
         }


	 if (schedulerinfo.config.asm_enabled){
		asm_checkbox.children('img')[0].style.display = "none";
		asm_checkbox.children('img')[1].style.display = "initial";
		asm_threshold_local.parentNode.style.display = "initial";
		asm_enable = 1;
		asm_threshold = asm_threshold_local.value;
	 }
         else{
		asm_checkbox.children('img')[1].style.display = "none";
		asm_checkbox.children('img')[0].style.display = "initial";
		asm_threshold_local.parentNode.style.display = "none";
		asm_enable = 0;
        }


	
        }
    });

}


function paint_nodes(hosts){
    hosts.sort(function(a, b){return a.hostname > b.hostname;});
    var host_existing = false;

    for(var i = 0; i < hosts.length; i++){
        host_existing = false;
//        console.log(JSON.stringify(hosts[i]));
        for(var m = 0; m < linedata.length; m++){
            if(linedata[m].host == hosts[i].hostname){
                host_existing = true;
                linedata[m].status = hosts[i].status;
                break;
            }
        }

        var id_host = compositesetting.prex_host + hosts[i].hostname;
        var id_chart = compositesetting.prex_chart + hosts[i].hostname;
        var active_status = 'active,dont_ctrl'.indexOf(hosts[i].status.toLowerCase()) >= 0;
        var error_status = 'error,standby,lose'.indexOf(hosts[i].status.toLowerCase()) >= 0;
        var warning_status = 'warning'.indexOf(hosts[i].status.toLowerCase()) >= 0;

	
        if(!host_existing){
            linedata.push({
                host: hosts[i].hostname,
                temperature: [['Time', 'Outlet Temperature', 'Inlet Temperature']],
                power: [['Time', 'System Power', 'CPU Power']],
                airflow: [['Time', 'Air Flow']],
                cups: [['Time', 'IO', 'Memory', 'Core']],
                fanspeed: [['Time', 'Sys Fan 1A', 'Sys Fan 2A']],
                thermal: [['Time', 'P1 Therm Margin', 'P1 DTS Therm Mgn']],
                show: true,
                status: hosts[i].status
            });
	    var retry = 3;
	    while(1){
		    if($('#canvas_host').length == 1){
			$('#canvas_host').attr('id', id_host);
			$('#chart_line').attr('id', id_chart);
			break;
		    }else if (retry > 0){
			retry--;
			setTimeout(function(){}, 1000);
		    }
		    else{
			var tbody=$('#cbs_tbl>tbody');
			tbody.append(tbody.children('tr:eq(2)').clone(true));
			tbody.children('tr:last').find('canvas[id^=' + compositesetting.prex_host+']').attr('id', id_host).removeData('ninfo')
					   .end().find('div[id^=' + compositesetting.prex_chart+']').attr('id', id_chart);
			break;
		    }
           }
        }

        var canvas_host = document.getElementById(id_host);
        var ctx_host = canvas_host.getContext('2d');
        var color_host = error_status ?  '#BEBEBE' : '#b4dc39';
        var color_usage = error_status ?  '#9B9999' : '#08B322';
        if(warning_status){
            color_host = '#ff6450';
            color_usage = '#B60606';
        }

        var ninfo_old = $('#' + id_host).data('ninfo');
        var arr_instances = [];
        var time_highlight = 0;
        if(ninfo_old === undefined) ninfo_old = {instances:[]};
        if(hosts[i].instances === undefined){}
        else{
            if(compositesetting.load_times === 0){
                for(var ins in hosts[i].instances){
                    arr_instances.push({
                        status: hosts[i].instances[ins].status.toLowerCase(),
                        name:   hosts[i].instances[ins].name,
                        uuid:   hosts[i].instances[ins].uuid,
                        time:   0
                    });
                }
            }else{
                for(var ins in hosts[i].instances){
                    time_highlight = 30;
                    for(var ins_old in ninfo_old.instances){
                        if(ninfo_old.instances[ins_old].uuid === hosts[i].instances[ins].uuid){
                            time_highlight = ninfo_old.instances[ins_old].time - 2;
                            time_highlight = time_highlight > 0 ? time_highlight : 0;
                            break;
                        }
                    }

                    arr_instances.push({
                        status: hosts[i].instances[ins].status.toLowerCase(),
                        name:   hosts[i].instances[ins].name,
                        uuid:   hosts[i].instances[ins].uuid,
//                        time:   0
                        time:   time_highlight
                    });
                }
            }

        }


        // IMPORTANT!!!!
//        if(hosts[i].instances !== undefined && hosts[i].instances.length != hosts[i].vm_num) hosts[i].vm_num = hosts[i].instances.length;


        $('#' + id_host).data('ninfo',{host : hosts[i].hostname, vm_num : hosts[i].vm_num, status : hosts[i].status, instances : arr_instances});

        if(active_status){
            //$(canvas_host).parent().parent().children('td:gt(0)').show();
        }else{
            //$(canvas_host).parent().parent().children('td:gt(0)').hide();
        }

        ctx_host.roundRect(0, 0, 254, 294, 7, color_host, color_host);
        ctx_host.fillStyle = "#FFF";
        ctx_host.font = "normal 17px sans-serif";
        ctx_host.fillText(hosts[i].hostname + ' (' + hosts[i].vm_num + ')', 32, 22);

        ctx_host.roundRect(10, 33, 234, 22, 2, color_usage, color_usage);

        ctx_host.fillStyle = "#FFF";
        ctx_host.font = "normal 12px sans-serif";
        ctx_host.fillText('VCPU', 70, 48);
        ctx_host.font = "normal 11px sans-serif";
        ctx_host.fillText('usage : ', 106, 47);
        ctx_host.font = "normal 12px sans-serif";
        ctx_host.fillText(Math.round(100 * parseInt(hosts[i].vcpu_used, 10) / parseInt(hosts[i].vcpu, 10)) + '%', 143, 48);

        for(var j = 0; j < arr_instances.length / 8; j++){
            for(var k = 0; k < 8 && (j * 8 + k) < arr_instances.length; k++){
                if(j * 8 + k > 31) break;
                if(j * 8 + k == 31){
                    ctx_host.roundCircle(18 + k % 8 * 30, 96 + j * 54, 2, '#fff');
                    ctx_host.roundCircle(24 + k % 8 * 30, 96 + j * 54, 2, '#fff');
                    ctx_host.roundCircle(30 + k % 8 * 30, 96 + j * 54, 2, '#fff');
                    break;
                }
                var color_background = '#fff';
                if(arr_instances[ j * 8 + k ] !== undefined && arr_instances[ j * 8 + k ].time > 0){
                    color_background = '#11B6F6';
                }
                ctx_host.roundRect(10 + k % 8 * 30, 66 + j * 54, 24, 42, 1, color_background, color_background);
                ctx_host.roundRect(13 + k % 8 * 30, 72 + j * 54, 18, 4, 1, color_host, color_host);
                ctx_host.roundRect(13 + k % 8 * 30, 80 + j * 54, 18, 1.8, 0, color_host, color_host);
                ctx_host.roundCircle(21.5 + k % 8 * 30, 100 + j * 54, 4, color_host);
            }
        }

        ctx_host.roundRect(67, 301, 120, 6, 3, color_host, color_host);
        ctx_host.roundRect(112, 298, 30, 12, 1, color_host, color_host);
        ctx_host.roundRect(124, 294, 6, 5, 0, color_host, color_host);
    }


    for(var m = 0; m < linedata.length; m++){
        linedata[m].show = false;
        for(var i = 0; i < hosts.length; i++){
            if(linedata[m].host == hosts[i].hostname){
                linedata[m].show = true;
                break;
            }
        }
        var node_id_host = compositesetting.prex_host + linedata[m].host;
        var node_tr = $('#' + node_id_host).parent().parent();
        if(linedata[m].show){
            node_tr.show().find('div.linechart').eq(node_tr.find('li.selected').index()).show().siblings().hide();
        }else{
            node_tr.hide();
        }
    }


    compositesetting.load_times = compositesetting.load_times > 1 ? 2 : (compositesetting.load_times+1);
}

function flash_nodes(fnum){
    $('#cbs_tbl canvas[id^=' + compositesetting.prex_host + ']').each(function(){
        var ninfo = $(this).data('ninfo');

        var error_status = 'error,standby,lose'.indexOf(ninfo.status.toLowerCase()) >= 0;
        var warning_status = 'warning'.indexOf(ninfo.status.toLowerCase()) >= 0;
        var ctx_host = this.getContext('2d');
        var color_host = error_status ? '#BEBEBE' : '#b4dc39';
        if(warning_status) color_host = '#ff6450';
        var color_flash = compositesetting.flgcolor_indicator ? color_host:'#FF9797';
        if(warning_status && !compositesetting.flgcolor_indicator) color_flash= '#26C7E5';

        for(var j = 0; j < ninfo.instances.length / 8; j++){
            for(var k = 0; k < 8 && ( j * 8 + k) < ninfo.instances.length; k++){
                if(j * 8 + k > 31) break;
                if(j * 8 + k == 31){
                    //ctx_host.roundCircle(18+k%8*30,96+j*54,2,'#fff');
                    //ctx_host.roundCircle(24+k%8*30,96+j*54,2,'#fff');
                    //ctx_host.roundCircle(30+k%8*30,96+j*54,2,'#fff');
                    break;
                }

                /*
                if(fnum===1 && ninfo.instances[j*8+k]!==undefined && ninfo.instances[j*8+k].time>0){
                    var color_background='#11B6F6';
                    ctx_host.roundRect(10+k%8*30,66+j*54,24,42,1,color_background,color_background);
                    ctx_host.roundRect(13+k%8*30,72+j*54,18,4,1,color_host,color_host);
                    ctx_host.roundRect(13+k%8*30,80+j*54,18,1.8,0,color_host,color_host);
                    ctx_host.roundCircle(21.5+k%8*30,100+j*54,4,color_host);
                }*/
                if(fnum === 1){
                    var color_background = '#fff';
                    if(ninfo.instances[ j * 8 + k ] !== undefined && ninfo.instances[ j * 8 + k ].time > 0){
                        color_background = '#11B6F6';
                        console.log(ninfo);
                    }else if(!compositesetting.flgcolor_highlight && ninfo.instances[ j * 8 + k] !== undefined && ninfo.instances[ j * 8 + k].status == 'migrating'){
                        color_background='#FAEB39';
                    }
                    ctx_host.roundRect(10+k%8*30,66+j*54,24,42,1,color_background,color_background);
                    ctx_host.roundRect(13+k%8*30,72+j*54,18,4,1,color_host,color_host);
                    ctx_host.roundRect(13+k%8*30,80+j*54,18,1.8,0,color_host,color_host);
                    ctx_host.roundCircle(21.5+k%8*30,100+j*54,4,color_host);
                }else if(fnum===2){
                    ctx_host.roundRect(13+k%8*30,80+j*54,18,1.8,0,color_flash,color_flash);
                }
            }
        }

        //ctx_host.roundRect(67,277,120,6,3,color_host,color_host);
        //ctx_host.roundRect(112,274,30,12,1,color_host,color_host);
        //ctx_host.roundRect(124,270,6,5,0,color_host,color_host);
    });

    var timeinterval=600;
    if(fnum===1){
        compositesetting.flgcolor_highlight=!compositesetting.flgcolor_highlight;
    }else if(fnum===2){
        timeinterval=compositesetting.flgcolor_indicator?800:3000;
        compositesetting.flgcolor_indicator=!compositesetting.flgcolor_indicator;
    }
    setTimeout(function(){ flash_nodes(fnum); }, timeinterval);
}

function read_data(){
    var now = new Date();
    var nowtime = now.getHours().padLeft()+':'+now.getMinutes().padLeft()+':'+now.getSeconds().padLeft();

    $.ajax({
        url : compositesetting.url_api+"/v1/common/power",
        type : 'GET',
        //dataType: 'json',
        dataType : 'jsonp',
        jsonp : 'callback',
        crossDomain : true,
        error : function(xhr, textStatus, errorThrown) {
            if($.console()) console.log("error at /common/power: " + errorThrown);
        },
        success : function(powerinfo, textStatus, xhr) {
            if(!powerinfo) return;
            for(var i=0; i<powerinfo.power.length; i++){
                for(var j=0; j<linedata.length; j++){
                    if(linedata[j].host!=powerinfo.power[i].hostname) continue;
                    if('active,dont_ctrl'.indexOf(linedata[j].status.toLowerCase())<0)   continue;

                    powerinfo.power[i].system_power=isNaN(parseInt(powerinfo.power[i].system_power,10))?0:parseInt(powerinfo.power[i].system_power,10);
                    powerinfo.power[i].cpu_power=isNaN(parseInt(powerinfo.power[i].cpu_power,10))?0:parseInt(powerinfo.power[i].cpu_power,10);
                    linedata[j].power.push([nowtime, powerinfo.power[i].system_power, powerinfo.power[i].cpu_power]);
                    break;
                }
            }
        }
    });


    $.ajax({
        url : compositesetting.url_api+"/v1/common/temp",
        type : 'GET',
        dataType : 'jsonp',
        jsonp : 'callback',
        crossDomain : true,
        error : function(xhr, textStatus, errorThrown) {
            if($.console()) console.log("error at /common/temp: " + errorThrown);
        },
        success : function(tempinfo, textStatus, xhr) {
            if(!tempinfo) return;
            for(var i=0; i<tempinfo.temp.length; i++){
                for(var j=0; j<linedata.length; j++){
                    if(linedata[j].host!=tempinfo.temp[i].hostname) continue;
                    if('active,dont_ctrl'.indexOf(linedata[j].status.toLowerCase())<0)   continue;

                    tempinfo.temp[i].outlet_temp=isNaN(parseInt(tempinfo.temp[i].outlet_temp,10))?0:parseInt(tempinfo.temp[i].outlet_temp,10);
                    tempinfo.temp[i].inlet_temp=isNaN(parseInt(tempinfo.temp[i].inlet_temp,10))?0:parseInt(tempinfo.temp[i].inlet_temp,10);
                    linedata[j].temperature.push([nowtime, tempinfo.temp[i].outlet_temp, tempinfo.temp[i].inlet_temp]);
                    break;
                }
            }
        }
    });

    $.ajax({
        url : compositesetting.url_api+"/v1/common/airflow",
        type : 'GET',
        dataType : 'jsonp',
        jsonp : 'callback',
        crossDomain : true,
        error : function(xhr, textStatus, errorThrown) {
            if($.console()) console.log("error at /common/airflow: " + errorThrown);
        },
        success : function(airflowinfo, textStatus, xhr) {
            if(!airflowinfo) return;
            for(var i=0; i<airflowinfo.airflow.length; i++){
                for(var j=0; j<linedata.length; j++){
                    if(linedata[j].host!=airflowinfo.airflow[i].hostname) continue;
                    if('active,dont_ctrl'.indexOf(linedata[j].status.toLowerCase())<0)   continue;

                    airflowinfo.airflow[i].airflow=isNaN(parseInt(airflowinfo.airflow[i].airflow,10))?0:parseInt(airflowinfo.airflow[i].airflow,10);
                    linedata[j].airflow.push([nowtime, airflowinfo.airflow[i].airflow]);
                    break;
                }
            }
        }
    });

    $.ajax({
        url : compositesetting.url_api+"/v1/common/cups",
        type : 'GET',
        dataType : 'jsonp',
        jsonp : 'callback',
        crossDomain : true,
        error : function(xhr, textStatus, errorThrown) {
            if($.console()) console.log("error at /common/cups: " + errorThrown);
        },
        success : function(cupsinfo, textStatus, xhr) {
            if(!cupsinfo) return;
            for(var i=0; i<cupsinfo.cups.length; i++){
                for(var j=0; j<linedata.length; j++){
                    if(linedata[j].host!=cupsinfo.cups[i].hostname) continue;
                    if('active,dont_ctrl'.indexOf(linedata[j].status.toLowerCase())<0)   continue;

                    cupsinfo.cups[i].io_cups=isNaN(parseInt(cupsinfo.cups[i].io_cups,10))?0:parseInt(cupsinfo.cups[i].io_cups,10);
                    cupsinfo.cups[i].mem_cups=isNaN(parseInt(cupsinfo.cups[i].mem_cups,10))?0:parseInt(cupsinfo.cups[i].mem_cups,10);
                    cupsinfo.cups[i].cpu_cups=isNaN(parseInt(cupsinfo.cups[i].cpu_cups,10))?0:parseInt(cupsinfo.cups[i].cpu_cups,10);
                    linedata[j].cups.push([nowtime, cupsinfo.cups[i].io_cups, cupsinfo.cups[i].mem_cups, cupsinfo.cups[i].cpu_cups]);
                    break;
                }
            }
        }
    });

    $.ajax({
        url : compositesetting.url_api+"/v1/common/fanspeed",
        type : 'GET',
        dataType : 'jsonp',
        jsonp : 'callback',
        crossDomain : true,
        error : function(xhr, textStatus, errorThrown) {
            if($.console()) console.log("error at /common/fanspeed: " + errorThrown);
        },
        success : function(faninfo, textStatus, xhr) {
            if(!faninfo) return;
//            alert(JSON.stringify(faninfo));
//            alert(faninfo.fanspeed.length);
            for(var i=0; i<faninfo.fanspeed.length; i++){

//                faninfo.fanspeed[i].speed_format=JSON.parse(faninfo.fanspeed[i].fans);
                for(var j=0; j<linedata.length; j++){
                    if(linedata[j].host!=faninfo.fanspeed[i].hostname) continue;
                    if('active,dont_ctrl'.indexOf(linedata[j].status.toLowerCase())<0)   continue;

                    var lnum=0;
                    var arr_fan=[];
                    for(var fkey in faninfo.fanspeed[i].fans){
                        arr_fan.push(fkey);
                        for(var x=0; x<linedata[j].fanspeed[0].length; x++){
                            if(fkey.toLowerCase()==linedata[j].fanspeed[0][x].toLowerCase()){
                                lnum++;
                                break;
                            }
                        }
                    }
                    if(arr_fan.length+1==linedata[j].fanspeed[0].length && arr_fan.length==lnum){
                    }else{
                        linedata[j].fanspeed[0].splice(1,100);
                        linedata[j].fanspeed[0]=linedata[j].fanspeed[0].concat(arr_fan);
                        linedata[j].fanspeed.splice(1,100);
                    }
                    arr_fan=[nowtime];
                    for(var y=1; y<linedata[j].fanspeed[0].length; y++){
                        faninfo.fanspeed[i].fans[linedata[j].fanspeed[0][y]]=isNaN(parseInt(faninfo.fanspeed[i].fans[linedata[j].fanspeed[0][y]],10))?0:parseInt(faninfo.fanspeed[i].fans[linedata[j].fanspeed[0][y]],10);
                        arr_fan.push(faninfo.fanspeed[i].fans[linedata[j].fanspeed[0][y]]);
                    }
                    linedata[j].fanspeed.push(arr_fan);
                    break;
                }
            }
        }
    });

    $.ajax({
        url : compositesetting.url_api+"/v1/common/thermal",
        type : 'GET',
        dataType : 'jsonp',
        jsonp : 'callback',
        crossDomain : true,
        error : function(xhr, textStatus, errorThrown) {
            if($.console()) console.log("error at /common/thermal: " + errorThrown);
        },
        success : function(thermalinfo, textStatus, xhr) {
            if(!thermalinfo) return;
            for(var i=0; i<thermalinfo.thermal.length; i++){
                for(var j=0; j<linedata.length; j++){
                    if(linedata[j].host!=thermalinfo.thermal[i].hostname) continue;
                    if('active,dont_ctrl'.indexOf(linedata[j].status.toLowerCase())<0)   continue;

                    var lnum=0;
                    var arr_ther=[];
                    for(var tkey in thermalinfo.thermal[i].thermal_margins){
                        arr_ther.push(tkey);
                        for(var x=0; x<linedata[j].thermal[0].length; x++){
                            if(tkey.toLowerCase()==linedata[j].thermal[0][x].toLowerCase()){
                                lnum++;
                                break;
                            }
                        }
                    }
                    if(arr_ther.length+1==linedata[j].thermal[0].length && arr_ther.length==lnum){
                    }else{
                        linedata[j].thermal[0].splice(1,100);
                        linedata[j].thermal[0]=linedata[j].thermal[0].concat(arr_ther);
                        linedata[j].thermal.splice(1,100);
                    }
                    arr_ther=[nowtime];
                    for(var y=1; y<linedata[j].thermal[0].length; y++){
                        thermalinfo.thermal[i].thermal_margins[linedata[j].thermal[0][y]]=isNaN(parseInt(thermalinfo.thermal[i].thermal_margins[linedata[j].thermal[0][y]],10))?0:parseInt(thermalinfo.thermal[i].thermal_margins[linedata[j].thermal[0][y]],10);
                        arr_ther.push(thermalinfo.thermal[i].thermal_margins[linedata[j].thermal[0][y]]);
                    }
                    linedata[j].thermal.push(arr_ther);
                    break;
                }
            }
        }
    });

    setTimeout(read_data, 3000);
}

function paint_brokenline(){

    for(var m=0; m<linedata.length; m++){
        if('active,dont_ctrl'.indexOf(linedata[m].status.toLowerCase())<0){
            $('#'+compositesetting.prex_chart+linedata[m].host+'>.linechart').css('background-image','url("images/inactive1.png")');
            continue;
        }

        if(linedata[m].power.length>1){
            if(linedata[m].power.length>35) linedata[m].power.splice(1,linedata[m].power.length-35);
            if(typeof linedata[m].chart_line_power_jquery=='undefined')
                linedata[m].chart_line_power_jquery = $('#'+compositesetting.prex_chart+linedata[m].host+'>.chart_line_power');
            if(typeof linedata[m].chart_line_power=='undefined')
                linedata[m].chart_line_power = new google.visualization.LineChart(linedata[m].chart_line_power_jquery[0]);
            if(typeof linedata[m].chart_options_power=='undefined')
                linedata[m].chart_options_power = {
                    title: 'Power',
                    titleTextStyle: { color: '#A8A8A8', fontSize: 16 },
                    legend: { position: 'bottom' },
                    //hAxis: { textPosition: 'none' },
                    width: 750,
                    height: 230,
                    hAxis: {textStyle:{fontSize:10}, showTextEvery:5},
                    series: { 0:{color: '#1c91c0'}, 1:{color: '#f1ca3a'} }
                };

            linedata[m].chart_line_power_jquery.show();
            linedata[m].chart_line_power.draw(google.visualization.arrayToDataTable(linedata[m].power), linedata[m].chart_options_power);

            var title_power = linedata[m].chart_line_power_jquery.find('text:contains("Power")').first();
            title_power.attr('x',750/2-title_power.width()/2-25);
            title_power.after(title_power.clone().text('(watts)').attr({x:parseInt(title_power.attr('x'),10)+52, 'font-size':13, 'font-weight':'normal'}));

            linedata[m].chart_line_power_jquery.find('svg').children('g').eq(1).children('g').each(function(){
                var rect_icon = $(this).children('rect:last');
                rect_icon.attr({ height:3,width:25,y:parseInt(rect_icon.attr('y'),10)+6,x:parseInt(rect_icon.attr('x'),10)-12 });
            });

            if(linedata[m].chart_line_power_jquery.siblings('.linechart:visible').length!=0) linedata[m].chart_line_power_jquery.hide();
        }

        if(linedata[m].temperature.length>1){
            if(linedata[m].temperature.length>35) linedata[m].temperature.splice(1,linedata[m].temperature.length-35);
            if(typeof linedata[m].chart_line_temp_jquery=='undefined')
                linedata[m].chart_line_temp_jquery = $('#'+compositesetting.prex_chart+linedata[m].host+'>.chart_line_temperature');
            if(typeof linedata[m].chart_line_temp=='undefined')
                linedata[m].chart_line_temp = new google.visualization.LineChart(linedata[m].chart_line_temp_jquery[0]);
            if(typeof linedata[m].chart_options_temp=='undefined')
                linedata[m].chart_options_temp = {
                    title: 'Temperature',
                    titleTextStyle: { color: '#A8A8A8', fontSize: 16 },
                    legend: { position: 'bottom' },
                    //hAxis: { textPosition: 'none' },
                    width: 750,
                    height: 230,
                    hAxis: {textStyle:{fontSize:10}, showTextEvery:5},
                    series: { 0:{color: '#1c91c0'}, 1:{color: '#f1ca3a'} }
                };

            linedata[m].chart_line_temp_jquery.show();
            linedata[m].chart_line_temp.draw(google.visualization.arrayToDataTable(linedata[m].temperature), linedata[m].chart_options_temp);

            var title_temp = linedata[m].chart_line_temp_jquery.find('text:contains("Temperature")').first();
            title_temp.attr('x',750/2-title_temp.width()/2-28);
            title_temp.after(title_temp.clone().text('(Degrees C)').attr({x:parseInt(title_temp.attr('x'),10)+104, 'font-size':13, 'font-weight':'normal'}));

            linedata[m].chart_line_temp_jquery.find('svg').children('g').eq(1).children('g').each(function(){
                var rect_icon = $(this).children('rect:last');
                rect_icon.attr({ height:3,width:25,y:parseInt(rect_icon.attr('y'),10)+6,x:parseInt(rect_icon.attr('x'),10)-12 });
            });

            if(linedata[m].chart_line_temp_jquery.siblings('.linechart:visible').length!=0) linedata[m].chart_line_temp_jquery.hide();
        }

        if(linedata[m].airflow.length>1){
            if(linedata[m].airflow.length>35) linedata[m].airflow.splice(1,linedata[m].airflow.length-35);
            if(typeof linedata[m].chart_line_air_jquery=='undefined')
                linedata[m].chart_line_air_jquery = $('#'+compositesetting.prex_chart+linedata[m].host+'>.chart_line_airflow');
            if(typeof linedata[m].chart_line_air=='undefined')
                linedata[m].chart_line_air = new google.visualization.LineChart(linedata[m].chart_line_air_jquery[0]);
            if(typeof linedata[m].chart_options_air=='undefined')
                linedata[m].chart_options_air = {
                    title: 'Airflow',
                    titleTextStyle: { color: '#A8A8A8', fontSize: 16 },
                    legend: { position: 'bottom' },
                    //hAxis: { textPosition: 'none' },
                    width: 750,
                    height: 230,
                    hAxis: {textStyle:{fontSize:10}, showTextEvery:5},
                    series: { 0:{color: '#1c91c0'} }
                };

            linedata[m].chart_line_air_jquery.show();
            linedata[m].chart_line_air.draw(google.visualization.arrayToDataTable(linedata[m].airflow), linedata[m].chart_options_air);

            var title_air = linedata[m].chart_line_air_jquery.find('text:contains("Airflow")').first();
            title_air.attr('x',750/2-title_air.width()/2-23);
            title_air.after(title_air.clone().text('(1/10 CFM)').attr({x:parseInt(title_air.attr('x'),10)+60, 'font-size':13, 'font-weight':'normal'}));

            linedata[m].chart_line_air_jquery.find('svg').children('g').eq(1).children('g').each(function(){
                var rect_icon = $(this).children('rect:last');
                rect_icon.attr({ height:3,width:25,y:parseInt(rect_icon.attr('y'),10)+6,x:parseInt(rect_icon.attr('x'),10)-12 });
            });

            if(linedata[m].chart_line_air_jquery.siblings('.linechart:visible').length!=0) linedata[m].chart_line_air_jquery.hide();
        }

        if(linedata[m].cups.length>1){
            if(linedata[m].cups.length>35) linedata[m].cups.splice(1,linedata[m].cups.length-35);
            if(typeof linedata[m].chart_line_cup_jquery=='undefined')
                linedata[m].chart_line_cup_jquery = $('#'+compositesetting.prex_chart+linedata[m].host+'>.chart_line_cups');
            if(typeof linedata[m].chart_line_cup=='undefined')
                linedata[m].chart_line_cup = new google.visualization.LineChart(linedata[m].chart_line_cup_jquery[0]);
            if(typeof linedata[m].chart_options_cup=='undefined')
                linedata[m].chart_options_cup = {
                    title: 'CUPS',
                    titleTextStyle: { color: '#A8A8A8', fontSize: 16 },
                    legend: { position: 'bottom' },
                    //hAxis: { textPosition: 'none' },
                    width: 750,
                    height: 230,
                    hAxis: {textStyle:{fontSize:10}, showTextEvery:5},
                    series: { 0:{color: '#1c91c0'}, 1:{color: '#f1ca3a'}, 2:{color: '#9D9D9D'} }
                };

            linedata[m].chart_line_cup_jquery.show();
            linedata[m].chart_line_cup.draw(google.visualization.arrayToDataTable(linedata[m].cups), linedata[m].chart_options_cup);

            var title_cup = linedata[m].chart_line_cup_jquery.find('text:contains("CUPS")').first();
            title_cup.attr('x',750/2-title_cup.width());
            //title_cup.after(title_cup.clone().text('(%)').attr({x:parseInt(title_cup.attr('x'),10)+42, 'font-size':13, 'font-weight':'normal'}));

            linedata[m].chart_line_cup_jquery.find('svg').children('g').eq(1).children('g').each(function(){
                var rect_icon = $(this).children('rect:last');
                rect_icon.attr({ height:3,width:25,y:parseInt(rect_icon.attr('y'),10)+6,x:parseInt(rect_icon.attr('x'),10)-12 });
            });

            if(linedata[m].chart_line_cup_jquery.siblings('.linechart:visible').length!=0) linedata[m].chart_line_cup_jquery.hide();
        }

        if(linedata[m].fanspeed.length>1){
            if(linedata[m].fanspeed.length>35) linedata[m].fanspeed.splice(1,linedata[m].fanspeed.length-35);
            if(typeof linedata[m].chart_line_fan_jquery=='undefined')
                linedata[m].chart_line_fan_jquery = $('#'+compositesetting.prex_chart+linedata[m].host+'>.chart_line_fanspeed');
            if(typeof linedata[m].chart_line_fan=='undefined')
                linedata[m].chart_line_fan = new google.visualization.LineChart(linedata[m].chart_line_fan_jquery[0]);
            if(typeof linedata[m].chart_options_fan=='undefined')
                linedata[m].chart_options_fan = {
                    title: 'Fan Speed',
                    titleTextStyle: { color: '#A8A8A8', fontSize: 16 },
                    legend: { position: 'bottom' },
                    //hAxis: { textPosition: 'none' },
                    width: 750,
                    height: 230,
                    hAxis: {textStyle:{fontSize:10}, showTextEvery:5},
                    series: { 0:{color: '#1c91c0'}, 1:{color: '#f1ca3a'} }
                };

            linedata[m].chart_line_fan_jquery.show();
            linedata[m].chart_line_fan.draw(google.visualization.arrayToDataTable(linedata[m].fanspeed), linedata[m].chart_options_fan);

            var title_fan = linedata[m].chart_line_fan_jquery.find('text:contains("Fan Speed")').first();
            title_fan.attr('x',750/2-title_fan.width()/2-25);
            title_fan.after(title_fan.clone().text('(RPM)').attr({x:parseInt(title_fan.attr('x'),10)+85, 'font-size':13, 'font-weight':'normal'}));

            linedata[m].chart_line_fan_jquery.find('svg').children('g').eq(1).children('g').each(function(){
                var rect_icon = $(this).children('rect:last');
                rect_icon.attr({ height:3,width:25,y:parseInt(rect_icon.attr('y'),10)+6,x:parseInt(rect_icon.attr('x'),10)-12 });
            });

            if(linedata[m].chart_line_fan_jquery.siblings('.linechart:visible').length!=0) linedata[m].chart_line_fan_jquery.hide();
        }

        if(linedata[m].thermal.length>1){
            if(linedata[m].thermal.length>35) linedata[m].thermal.splice(1,linedata[m].thermal.length-35);
            if(typeof linedata[m].chart_line_thermal_jquery=='undefined')
                linedata[m].chart_line_thermal_jquery = $('#'+compositesetting.prex_chart+linedata[m].host+'>.chart_line_thermal');
            if(typeof linedata[m].chart_line_thermal=='undefined')
                linedata[m].chart_line_thermal = new google.visualization.LineChart(linedata[m].chart_line_thermal_jquery[0]);
            if(typeof linedata[m].chart_options_thermal=='undefined')
                linedata[m].chart_options_thermal = {
                    title: 'Thermal Margin',
                    titleTextStyle: { color: '#A8A8A8', fontSize: 16 },
                    legend: { position: 'bottom' },
                    //hAxis: { textPosition: 'none' },
                    width: 750,
                    height: 230,
                    hAxis: {textStyle:{fontSize:10}, showTextEvery:5},
                    series: { 0:{color: '#1c91c0'}, 1:{color: '#f1ca3a'} }
                };

            linedata[m].chart_line_thermal_jquery.show();
            linedata[m].chart_line_thermal.draw(google.visualization.arrayToDataTable(linedata[m].thermal), linedata[m].chart_options_thermal);

            var title_thermal = linedata[m].chart_line_thermal_jquery.find('text:contains("Thermal Margin")').first();
            title_thermal.attr('x',750/2-title_thermal.width()/2-3);

            linedata[m].chart_line_thermal_jquery.find('svg').children('g').eq(1).children('g').each(function(){
                var rect_icon = $(this).children('rect:last');
                rect_icon.attr({ height:3,width:25,y:parseInt(rect_icon.attr('y'),10)+6,x:parseInt(rect_icon.attr('x'),10)-12 });
            });

            if(linedata[m].chart_line_thermal_jquery.siblings('.linechart:visible').length!=0) linedata[m].chart_line_thermal_jquery.hide();
        }


    }

    setTimeout(paint_brokenline, 3000);

}


function slide_brokenline(obj,num){
    var obj=$(obj);
    var lisel=obj.parent().parent().find('li.selected').removeClass('selected').addClass('unselected');
    var lisel_new=(num==1)?lisel.prev():lisel.next();
    if(lisel_new.length==0) lisel_new=(num==1)?lisel.siblings().last():lisel.siblings().first();
    lisel_new.removeClass('unselected').addClass('selected');
    obj.parent().parent().find('.linechart:eq('+lisel.index()+')').hide()
                   .end().find('.linechart:eq('+lisel_new.index()+')').show();
}

function change_scheduler(obj){
    var sel_obj=$(obj);
    sel_obj.next().children('p[for='+sel_obj.val()+']').show().siblings().hide();
    $('#cbs_config_div img[val=dispatch_'+sel_obj.val()+'0]').click();
}

function actionConfig(num){
    var isel = $('#submenu_list_ul li span.submenu_selected').parent().index();
    var contentdiv = $('#content_div');
    var configdiv = isel==0 ? $('#cbs_config_div') : (isel==1 ? $('#asm_config_div') :$('#pbm_config_div'));
    var clientHeight=$('body')[0].clientHeight;

    switch(num){
        case 0:
            configdiv.children('table').animate({ 'left': 0 }, 1000);
            configdiv.css({
                'width' : 0,
                'height' : clientHeight-130,
                'left' : contentdiv.offset().left,
                'top' : 130
            }).animate({                width : '550px'            }, 1000, function(){
                $('#forcover').css({width:contentdiv.width(), height: document.body.scrollHeight-70, top: 70}).appendTo(contentdiv).show();
            });
            break;
        case 1:
            
            var sdata = null;
            if (asm_threshold != null){
	        sdata = { "dispatch":"", "migration":"", "mig_enabled":mig_enable.toString(), "asm_enabled":asm_enable.toString(), "asm_threshold": asm_threshold.toString()};
            }
	    else{
	        sdata = { "dispatch":"", "migration":"", "mig_enabled":mig_enable.toString(), "asm_enabled":asm_enable.toString()};
	    }

            var img_dispatch=$('#cbs_config_div img[val^=dispatch]');
            if(img_dispatch.eq(1)[0].style.display=='none' && img_dispatch.eq(3)[0].style.display=='none'){
                show_message('Please select a dispatch policy.');
                break;
            }
            var ul=$('#ul_migration');
            if(img_dispatch.eq(1)[0].style.display!='none'){
                if(ul.find('img[val=migration_11]')[0].style.display=='none' &&
                   ul.find('img[val=migration_21]')[0].style.display=='none' &&
                   ul.find('img[val=migration_51]')[0].style.display=='none'){
                    show_message('Please select a migration policy.');
                    break;
                }
                sdata.dispatch="THERMAL";
                if(ul.find('img[val=migration_11]')[0].style.display!='none'){
                    var val_airflow = $.trim($('#txt_airflow').val());
                    var val_inlet_temp = $.trim($('#txt_inlet_temp').val());
                    var val_power_consumption = $.trim($('#txt_power_consumption').val());
                    if(val_airflow==''){
                        show_message('Please input Airflow threshold value.');
                        $('#txt_airflow').focus();
                        break;
                    }else sdata.airflow = val_airflow;
                    if(val_inlet_temp==''){
                        show_message('Please input Inlet Temp.');
                        $('#txt_inlet_temp').focus();
                        break;
                    }else sdata.inlet_temp = val_inlet_temp;
                    if(val_power_consumption==''){
                        show_message('Please input Power Consumption.');
                        $('#txt_power_consumption').focus();
                        break;
                    }else sdata.power_consumption = val_power_consumption;

	            sdata.migration="AIRFLOW";
                }else if(ul.find('img[val=migration_21]')[0].style.display!='none'){
                    var val_outlet_temp = $.trim($('#txt_outlet_temp').val());
                    if(val_outlet_temp==''){
                        show_message('Please input Outlet Temp.');
                        $('#txt_outlet_temp').focus();
                        break;
                    }else sdata.outlet_temp = val_outlet_temp;

                    sdata.migration="OUTLETTEMP";
                }else if(ul.find('img[val=migration_51]')[0].style.display!='none'){
                    sdata.migration="SENIOROUTLETTEMP";
                }
            }else if(img_dispatch.eq(3)[0].style.display!='none'){
                if(ul.find('img[val=migration_31]')[0].style.display=='none' &&
                   ul.find('img[val=migration_41]')[0].style.display=='none'){
                        show_message('Please select a migration.');
                        break;
                }
                sdata.dispatch="CUPS";
                if(ul.find('img[val=migration_31]')[0].style.display!='none'){
                    var val_workload = $.trim($('#txt_workload').val());
                    if(val_workload==''){
                        show_message('Please input Workload.');
                        $('#txt_workload').focus();
                        break;
                    }else sdata.workload = val_workload;

                    sdata.migration="SIMPLEBALANCE";
                }else if(ul.find('img[val=migration_41]')[0].style.display!='none'){
                    var val_power_increase = $.trim($('#txt_power_increase').val());
                    if(val_power_increase==''){
                        show_message('Please input Power Increase.');
                        $('#txt_power_increase').focus();
                        break;
                    }else sdata.power_increase = val_power_increase;

                    sdata.migration="POWERBALANCE";
                }
            }else{
                show_message('Please select a migration.');
                break;
            }
	     sdata.asm_threshold = $.trim($('#txt_loading_threshold').val());
	     var posting = $.post(compositesetting.url_api+"/v1/openstack/config", sdata); // Put the results in a div
//	     posting.done(function(data){
//                    configdiv.children('table').animate({ 'left': -999 }, 1800);
//                    configdiv.animate({                width : '0px'            }, 1000, function() {
//                        $('#forcover').hide().appendTo($('body'));
//                        showscheduleinfo();
//                    });
//                    $('#div_msg').fadeOut();
//
//	     });
//            break;
        case 2:
            configdiv.children('table').animate({ 'left': -999 }, 1800);
            configdiv.animate({                width : '0px'            }, 1000, function() {
                $('#forcover').hide().appendTo($('body'));
                        showscheduleinfo();
            });
            $('#div_msg').fadeOut();
            break;
    }
}

function toggle_scheduler(obj){
    if (obj.src.indexOf("checkbox") > -1){
	return;
    }
    obj=$(obj);
    var val=obj.attr('val');
    var type=val.substr(0, val.indexOf('_'));
    var num=parseInt(val.substr(val.indexOf('_')+1), 10);

    var lis=$('#ul_migration>li');

    switch(type){
        case 'dispatch':
            switch(num){
                case 10:
                //case 11:
                    obj.parent().next().next().children('img').first().show().next().hide();
                    obj.parent().children('img').first().hide().next().show();
                    lis.first().slideDown().next().slideDown().next().slideUp().next().slideUp().next().slideDown();
                    lis.find('img:odd').hide().end().find('img:even').show().end().find('div').hide();
                    break;
                case 20:
                //case 21:
                    obj.parent().prev().prev().children('img').first().show().next().hide();
                    obj.parent().children('img').first().hide().next().show();
                    lis.first().slideUp().next().slideUp().next().slideDown().next().slideDown().next().slideUp();
                    lis.find('img:odd').hide().end().find('img:even').show().end().find('div').hide();
                    break;
            }
            break;
        case 'migration':
            obj.parent().children('img').first().hide().next().show();
            obj.parent().siblings().find('img:odd').hide().end().find('img:even').show().end().find('div').slideUp();
            obj.nextAll('div').slideDown();
            break;
    }
}



function switchtosection(obj, num) {
    $(obj).addClass("submenu_selected").parent().siblings().children('span').removeClass("submenu_selected");

    switch(num){
        case 1:
            $('#un_panel_div').slideDown();
            $('#openstack_panel_div').slideUp();
            $('#ceph_panel_div').slideUp();
            break;
        case 2:
            $('#un_panel_div').slideUp();
            $('#openstack_panel_div').slideDown();
            $('#ceph_panel_div').slideUp();
            break;
        case 3:
            $('#un_panel_div').slideUp();
            $('#openstack_panel_div').slideUp();
            $('#ceph_panel_div').slideDown();
            break;
    }
}

function show_message(msg){
    clearTimeout(compositesetting.show_message_st);
    $('#div_msg').css('top',0).text(msg).slideDown().animate({'top': 280}, 800);
    compositesetting.show_message_st = setTimeout(function(){$('#div_msg').fadeOut();}, 4000);
}


function togglebutton(obj){
    switch(obj.id){
	case "mig":
		obj=$(obj);
		if (obj.children('img')[0].style.display != "none"){
			obj.children('img')[0].style.display = "none";
			obj.children('img')[1].style.display = "initial";
			mig_enable = 1;
		}
		else {

			obj.children('img')[1].style.display = "none";
			obj.children('img')[0].style.display = "initial";
			mig_enable = 0;

		}
		break;
	case "asm":
		obj=$(obj);
		if (obj.children('img')[0].style.display != "none"){
			obj.children('img')[0].style.display = "none";
			obj.children('img')[1].style.display = "initial";
//			obj.parent().children('div')[1].slideDown();
			$("#load_thres_div").slideDown();
			asm_threshold = $("#txt_loading_threshold").val;
			asm_enable = 1;
		}
		else {

			obj.children('img')[1].style.display = "none";
			obj.children('img')[0].style.display = "initial";
//			obj.parent().children('div')[1].slideUp();
			$("#load_thres_div").slideUp();
			asm_enable = 0;

		}
		break;
		
    }	

}


