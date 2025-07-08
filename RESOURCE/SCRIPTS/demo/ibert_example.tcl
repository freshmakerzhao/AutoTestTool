#导入ibert库
# source "./iber.tcl"
source "E:\\workspace\\AutoTestTool\\iber.tcl"

# ---------- 连接器件烧写测试码流 ---------------------
open_hw_manager
connect_hw_server
open_hw_target

set device [get_hw_devices xc7a100t_0]

set_property PARAM.FREQUENCY 6000000 [get_hw_targets]
set_property PROBES.FILE {} $device
set_property FULL_PROBES.FILE {} $device
set_property PROGRAM.FILE "./example_ibert_6p25g.rbt_HybrdChip_Trim_invscanclk.rbt" $device
program_hw_devices $device

refresh_hw_device $device
set target [get_hw_targets]
# ------------------------------------------------------------

# -----------测试流程---------------------------------------

# 根据tx rx编号创建link(可通过get_tx <编号>获取编号对应的tx名称)
create_link -tx_nub 0 -rx_nub 0 -link_name "Link 0"
create_link -tx_nub 1 -rx_nub 1 -link_name "Link 1"
create_link -tx_nub 2 -rx_nub 2 -link_name "Link 2"
create_link -tx_nub 3 -rx_nub 3 -link_name "Link 3"

# 设置link的各项参数。当不指定link_name时,对所有link生效
# 支持的参数设置有 -tx_pattern -rx_pattern -tx_pre_cursor -tx_post -tx_diff_swing -loopback_mode

# 对所有的link的tx pattern设置为 PRBS 15-bit
set_link_property -tx_pattern "PRBS 15-bit"

# 对Link 0的tx pattern设置为 PRBS 7-bit
set_link_property -link_name "Link 0" -tx_pattern "PRBS 7-bit"

# 对link进行复位。当不指定link_name时,对所有link生效

# 只对Link 0 进行复位
ibert_reset -link_name "Link 0"
rx_reset -link_name "Link 0"
tx_reset -link_name "Link 0"

# 对所有link 进行iber复位
ibert_reset 
rx_reset
tx_reset

# 运行眼图扫描，将测试结果保存到-resul_path指定的文件中
scan -link_name "Link 0" -scan_name "Channel 0" -scan_type 2d_full_eye -dwell_ber 1e-9 -result_path "./result 0.csv"
scan -link_name "Link 1" -scan_name "Channel 1" -scan_type 2d_full_eye -dwell_ber 1e-9 -result_path "./result 1.csv"
scan -link_name "Link 2" -scan_name "Channel 2" -scan_type 2d_full_eye -dwell_ber 1e-9 -result_path "./result 2.csv"
scan -link_name "Link 3" -scan_name "Channel 3" -scan_type 2d_full_eye -dwell_ber 1e-9 -result_path "./result 3.csv"
# ------------------------------------------------------------