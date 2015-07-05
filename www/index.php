<?php
	const API_URL = "http://127.0.0.1:8080/v1";

	function curl_get_request($url) {
	    $ch = curl_init();
	    curl_setopt($ch, CURLOPT_URL, $url);
	    curl_setopt($ch, CURLOPT_HEADER, false);
	    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
	    curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 20);
	    $data = curl_exec($ch);
	    curl_close($ch);
	    return $data;
	}

	function curl_post_request($url,$post) {
	    $ch = curl_init();
	    curl_setopt($ch, CURLOPT_URL, $url);
	    curl_setopt($ch, CURLOPT_HEADER, false);
	    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
	    curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 20);
	    curl_setopt($ch, CURLOPT_POST, true);
	    curl_setopt($ch, CURLOPT_POSTFIELDS, $post);
	    $data = curl_exec($ch);
	    curl_close($ch);
	    return $data;
	}
	header('Access-Control-Allow-Origin: *');
?>

<html>
    <head>
        <link rel="icon" href="images/title3.ico" mce_href="images/title3.ico" type="image/x-icon">
        <link rel="SHORTCUT ICON" href="images/title3.ico">
        <link rel="ICON" href="images/title3.ico">
        <title>Intelligent Thermal Management Using Real Time Telemetry</title>
        <style type="text/css" title="currentStyle">
            @import "css/common.css";
            @import "css/jquery-ui-1.10.0.custom.css";
            @import "css/jquery.dataTables_themeroller.css";
            @import "css/google-charts-tooltip.css";
            @import "css/page_power.css";
        </style>

        <script type="text/javascript" src="js/jquery-1.10.2.min.js"></script>
        <script type="text/javascript" src="js/json2.js"></script>
        <script type="text/javascript" src="js/google-charts-jsapi.js"></script>
        <script type="text/javascript" src="js/common.js"></script>
        <script type="text/javascript" src="js/page_power.js"></script>
        <script type="text/javascript">
            $(document).ready(function() {
                initpage();
            });
        </script>
    </head>

    <body>
	<header>
	    <label id="header_title"></label>
	    <div id="logo">
		<img src="images/intel.png" />
		<label>EnergyPackage</label>
	    </div>
	</header>
	<script type="text/javascript">
	    var headheight = 70;
	</script>
		<div id="selection_bar_div">
			<div id="selection_bar_header_div">
				<table border="0">
					<tr><th colspan="2" style="height:36px;" valing="middle">Datacenter info:</th></tr>
					<tr><td>Total Hosts:</td><td>5</td></tr>
					<tr><td>CPU Cores:</td><td>80</td></tr>
					<tr><td>Mem (MB):</td><td>10240</td></tr>
					<tr><td>Active Hosts:</td><td>3</td></tr>
					<tr><td>Standby Hosts:</td><td>2</td></tr>
				</table>
			</div>
            <div id="submenu_list_div">
                <ul id="submenu_list_ul">
                   <li><span class="submenu submenu_selected" onclick="switchtosection(this,1)">Content Based Scheduling</span></li>
                   <li><span class="submenu" onclick="switchtosection(this,2)">Active Standby Management (ASM)</span></li>
                   <li><span class="submenu" onclick="switchtosection(this,3)">Policy Based&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Migration (PBM)</span></li>
              </ul>
            </div>
		</div>

        <div id="content_div">
            <div id="content_header_div">
            	<img id="img_config_asm" src="images/setting.jpg" style="width:30px; height:30px; cursor:pointer;" />
            </div>

            <div id="un_panel_div">

    			<table cellpadding="0" cellspacing="0" border="0" id="cbs_tbl">
    				<thead style="display:none;">
    					<tr>
    						<th colspan="4" align="left" valign="middle" style="height:40px;">Content Based Scheduling:</th>
    					</tr>
    				</thead>
    				<tbody>
    					<tr>
    						<td style="padding:5 0 0 10;" colspan="4">
    							<select style="float: left; width:150px;" id="sel_scheduler">
    									<option value="1">Thermal</option>
    									<option value="2">CUPS</option>
    							</select>
    							<div style="padding-left:20px; padding-top: 8px; font-size:12px;float:left;">
    								<p for="1">
    									Avoid any overheating. Data gathering is provided by a periodicity task from energy package services.
    								</p>
    								<p for="2" style="display:none;">
    									Avoid any overloading. Data gathering is provided by a periodicity task from energy package services.
    								</p>
    							</div>
    						</td>
    					</tr>
    					<tr>
    						<td style="color:#0071c5; font-size: 14px; height: 60px; padding-left:32px; padding-bottom:15px;" align="left" valign="bottom">Nodes in Cluster:</td>
    						<td style="color:#0071c5; font-size: 14px; padding-left:88px;" align="left" colspan="3" valign="bottom">Power, Airflow, Compute Usage Per Second (CUPS) Data from<br />Intel&reg; Intelligent Power Node Manager 3.0 PTAS Feature:</td>
    					</tr>
    					<tr>
    						<td align="center" style="padding:15px 0 10px 30px;">
            					<canvas id="canvas_host" width="254" height="324"></canvas>
    						</td>
    						<td style="width:30px;"><img src="images/arrow_back.png" align="right" style="cursor:pointer; margin-right:-45px; position:relative; z-index:1;" /></td>
    						<td valign="center">
    							<div id="chart_line" style="width: 750px; height: 230px;">
    								<div class="chart_line_temperature linechart"></div>
    								<div class="chart_line_power linechart" style="display:none;"></div>
    								<div class="chart_line_airflow linechart" style="display:none;"></div>
    								<div class="chart_line_cups linechart" style="display:none;"></div>
    								<div class="chart_line_fanspeed linechart" style="display:none;"></div>
    								<div class="chart_line_thermal linechart" style="display:none;"></div>
    							</div>
    							<ul class="ul_selection"><li class="selected"></li><li class="unselected"></li><li class="unselected"></li><li class="unselected"></li><li class="unselected"></li><li class="unselected"></li></ul>
    						</td>
    						<td><img src="images/arrow_next.png" align="left" style="cursor:pointer; margin-left:-75px; position:relative;" /></td>
    					</tr>
    				</tbody>
    			</table>


                <div id="cbs_config_div">
                    <table border="0" cellpadding="0" cellspacing="0" height="100%" width="550" style="position:absolute; left:-999; padding:0 15;">
                        <tr>
                            <td style="height:80px;" valign="middle" colspan="5">Settings of Migration Policy:</td>
                            <td rowspan="4" valign="middle"><div class="to_left_arrow_panel" onclick="actionConfig(2)"></div></td>
                        </tr>
                        <tr style="font-weight: normal; display:none;">
                            <td style="height:70px; width:90px;" align="center" valign="middle">Dispatch:</td>
                            <td style="width:60px; padding:5 5 0 0;" align="right" valign="middle">
                                <img src="images/radio_unchecked.png" align="absmiddle" val="dispatch_10" style="display: none;" />
                                <img src="images/radio_checked.png" align="absmiddle" val="dispatch_11" /></td>
                            <td align="left" valign="middle" style="width:100px;">Thermal</td>
                            <td style="width:30px; padding:5 5 0 0;" align="right">
                                <img src="images/radio_unchecked.png" align="absmiddle" val="dispatch_20" />
                                <img src="images/radio_checked.png" align="absmiddle" val="dispatch_21" style="display: none;" />
                            </td>
                            <td align="left" valign="middle" style="">Cups</td>
                        </tr>
                        <tr>
                            <td style="padding:20 0 0 45; height:60px;" colspan="6">
                                <div onclick="togglebutton(this)" id="mig" style="color:#EEEEEE">
                                <img src="images/checkbox_unselected.png" align="absmiddle" />
                                <img src="images/checkbox_selected.png" align="absmiddle" style="display: none;" />
                                Enable Migration
                                </div>
                            </td>
                        </tr>
                        <tr>
                        <td style="padding:20 0 50 45; height:60px;" colspan="6">
                                <div onclick="togglebutton(this)" id="asm" style="color:#EEEEEE">
                                <img src="images/checkbox_unselected.png" align="absmiddle" />
                                <img src="images/checkbox_selected.png" align="absmiddle" style="display: none;" />
                                Enable Active Standby Management
                                </div>
                                <div style="display:none;" id="load_thres_div">
                                      	<label id="load_thres_label">Loading Threshold: </label><input type="text" class="inputblue" id="txt_loading_threshold" maxlength="8" onkeyup="this.value=this.value.replace(/[^0-9\.]/g,'')" onafterpaste="this.value=this.value.replace(/[^0-9\.]/g,'')" />
                                </div>
                            </td>
                        </tr>
                        <tr style="font-weight: normal;">
                            <td style="width:90px;" align="right" valign="top">Migration:</td>
                            <td colspan="4" valign="top" style="padding:0 0 0 45;">
                                 <ul id="ul_migration">
                                     <li>
                                         <img src="images/radio_unchecked.png" align="absmiddle" val="migration_10" />
                                         <img src="images/radio_checked.png" align="absmiddle" val="migration_11" style="display: none;" />
                                         <h4 style="display: inline;">Airflow</h4>
                                         <p>Migration workload when volumetric airflow is high.</p>
                                         <div style="display:none;">
                                         	<label>Airflow: </label><input type="text" class="inputblue" id="txt_airflow" maxlength="8" onkeyup="this.value=this.value.replace(/[^0-9\.]/g,'')" onafterpaste="this.value=this.value.replace(/[^0-9\.]/g,'')" /><br />
                                         	<label>Inlet Temp: </label><input type="text" class="inputblue" id="txt_inlet_temp" maxlength="8" onkeyup="this.value=this.value.replace(/[^0-9\.]/g,'')" onafterpaste="this.value=this.value.replace(/[^0-9\.]/g,'')" /><br />
                                         	<label>Power Consumption: </label><input type="text" class="inputblue" id="txt_power_consumption" maxlength="8" onkeyup="this.value=this.value.replace(/[^0-9\.]/g,'')" onafterpaste="this.value=this.value.replace(/[^0-9\.]/g,'')" />
                                         </div>
                                     </li>
                                     <li>
                                         <img src="images/radio_unchecked.png" align="absmiddle" val="migration_20" />
                                         <img src="images/radio_checked.png" align="absmiddle" val="migration_21" style="display: none;" />
                                         <h4 style="display: inline;">Outlet Temperature</h4>
                                         <p>Migration when outlet temperature is higher than threshold.</p>
                                         <div style="display:none;">
                                         	<label>Outlet Temp: </label><input type="text" class="inputblue" id="txt_outlet_temp" maxlength="8" onkeyup="this.value=this.value.replace(/[^0-9\.]/g,'')" onafterpaste="this.value=this.value.replace(/[^0-9\.]/g,'')" />
                                         </div>
                                     </li>
                                     <li style="display:none;">
                                         <img src="images/radio_unchecked.png" align="absmiddle" val="migration_30" />
                                         <img src="images/radio_checked.png" align="absmiddle" val="migration_31" style="display: none;" />
                                         <h4 style="display: inline;">Simple Balance</h4>
                                         <p>Migration when workload is heavier than threshold workload.</p>
                                         <div style="display:none;">
                                         	<label>Workload: </label><input type="text" class="inputblue" id="txt_workload" maxlength="8" onkeyup="this.value=this.value.replace(/[^0-9\.]/g,'')" onafterpaste="this.value=this.value.replace(/[^0-9\.]/g,'')" />
                                         </div>
                                     </li>
                                     <li style="display:none;">
                                         <img src="images/radio_unchecked.png" align="absmiddle" val="migration_40" />
                                         <img src="images/radio_checked.png" align="absmiddle" val="migration_41" style="display: none;" />
                                         <h4 style="display: inline;">Power Balance</h4>
                                         <p>Migration when power increase is larger than threshold.</p>
                                         <div style="display:none;">
                                         	<label>Power Increase: </label><input type="text" class="inputblue" id="txt_power_increase" maxlength="8" onkeyup="this.value=this.value.replace(/[^0-9\.]/g,'')" onafterpaste="this.value=this.value.replace(/[^0-9\.]/g,'')" />
                                         	<label style="display:inline; padding-left:2px;">W &nbsp; / 5%</label>
                                         </div>
                                     </li>
                                     <li>
                                         <img src="images/radio_unchecked.png" align="absmiddle" val="migration_50" />
                                         <img src="images/radio_checked.png" align="absmiddle" val="migration_51" style="display: none;" />
                                         <h4 style="display: inline;">Senior Outlet Temperature</h4>
                                         <p>Migrate workload to achieve uniform outlet temperature.</p>
                                         <div style="display:none;">
                                         </div>
                                     </li>
                                 </ul>
                            </td>
                        </tr>

                        <tr>
                            <td colspan="5" valign="top" align="center" style="padding-top: 20px;">
                                <button class="button blue" onclick="actionConfig(1)">Update</button>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                                <button class="button blue" onclick="actionConfig(2)">Cancel</button>
                            </td>
                        </tr>
                    </table>
                    <div id="div_msg" style="display:none;"></div>
                </div>


			</div>


            </div>

        <div id="brief_div">
			<table border="0">
				<tr><th colspan="2" style="height:46px; padding-left:5px;" valing="middle">Datacenter info:</th></tr>
				<tr><td style="width:110px;">Total Hosts:</td><td></td></tr>
				<tr><td>CPU Cores:</td><td></td></tr>
				<tr><td>Mem (MB):</td><td></td></tr>
				<tr><td>Active Hosts:</td><td></td></tr>
				<tr><td>Standby Hosts:</td><td></td></tr>
				<tr><td>VCPU Utilization:</td><td></td></tr>
				</table>
			<table id="tbl_scheduler" border="0">
				<tr><th colspan="2" style="height:46px; padding-left:5px;" valing="middle">Scheduler info:</th></tr>
				<tr><td style="width:70px;">Dispatch:</td><td>Thermal</td></tr>
				<tr><td>Migration:</td><td></td></tr>
			</table>
		</div>



        <div id="forcover"></div>
	</body>
</html>
