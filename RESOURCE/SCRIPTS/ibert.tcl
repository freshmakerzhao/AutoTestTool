# ibert.tcl 两个参数，测试码流和输出csv文件路径
# Argument check
if {$argc != 2} {
    puts "Usage error: Please provide the path"
    exit 1
}

set bitstream_path [lindex $argv 0]
set output_path [lindex $argv 1]

open_hw_manager
connect_hw_server
open_hw_target

set device [get_hw_devices xc7a100t_0]

set_property PARAM.FREQUENCY 6000000 [get_hw_targets]
set_property PROBES.FILE {} $device
set_property FULL_PROBES.FILE {} $device
set_property PROGRAM.FILE $bitstream_path $device
program_hw_devices $device

refresh_hw_device $device
set target [get_hw_targets]

set xil_newLinks [list]
set index 0
foreach tx [get_hw_sio_txs] {
    set rx [lindex [get_hw_sio_rxs] $index]
    set xil_new_Link [create_hw_sio_link -description  "Link $index" $tx $rx]
    lappend xil_newLinks $xil_new_Link
    incr index
}
set xil_newLinkGroup [create_hw_sio_linkgroup -description {Link Group 0} [get_hw_sio_links $xil_newLinks]]
unset xil_newLinks

set links [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]] 

set_property TX_PATTERN {PRBS 15-bit} $links
set_property RX_PATTERN {PRBS 15-bit} $links
set_property PORT.GTTXRESET 1 $links
set_property PORT.GTTXRESET 0 $links
set_property PORT.GTRXRESET 1 $links
set_property PORT.GTRXRESET 0 $links
set_property LOGIC.MGT_ERRCNT_RESET_CTRL 1 $links
set_property LOGIC.MGT_ERRCNT_RESET_CTRL 0 $links
commit_hw_sio $links

set index 0
foreach link $links {
    set xil_newScan [create_hw_sio_scan -description "Scan $index" 2d_full_eye $link]    
    set_property DWELL_BER 1e-9 $xil_newScan
    run_hw_sio_scan $xil_newScan
    wait_on_hw_sio_scan $xil_newScan
    write_hw_sio_scan "$output_path/$xil_newScan.csv" $xil_newScan -force
    set_property DESCRIPTION Channel $xil_newScan
    set_property DESCRIPTION "Channel $index" $xil_newScan
    incr index
}