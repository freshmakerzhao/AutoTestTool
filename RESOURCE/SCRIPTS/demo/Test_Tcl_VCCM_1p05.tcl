set_property PARAM.FREQUENCY 6000000 [get_hw_targets localhost:3121/xilinx_tcf/Digilent/210251A08870]
set_property PROBES.FILE {} [get_hw_devices xc7a100t_0]
set_property FULL_PROBES.FILE {} [get_hw_devices xc7a100t_0]
set_property PROGRAM.FILE {D:/minjian/example_ibert_6p25g.rbt_HybrdChip_Trim_invscanclk.rbt} [get_hw_devices xc7a100t_0]
program_hw_devices [get_hw_devices xc7a100t_0]

refresh_hw_device [lindex [get_hw_devices xc7a100t_0] 0]

set xil_newLinks [list]
set xil_newLink [create_hw_sio_link -description {Link 0} [lindex [get_hw_sio_txs localhost:3121/xilinx_tcf/Digilent/210251A08870/0_1_0/IBERT/Quad_216/MGT_X0Y4/TX] 0] [lindex [get_hw_sio_rxs localhost:3121/xilinx_tcf/Digilent/210251A08870/0_1_0/IBERT/Quad_216/MGT_X0Y4/RX] 0] ]
lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 1} [lindex [get_hw_sio_txs localhost:3121/xilinx_tcf/Digilent/210251A08870/0_1_0/IBERT/Quad_216/MGT_X0Y5/TX] 0] [lindex [get_hw_sio_rxs localhost:3121/xilinx_tcf/Digilent/210251A08870/0_1_0/IBERT/Quad_216/MGT_X0Y5/RX] 0] ]
lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 2} [lindex [get_hw_sio_txs localhost:3121/xilinx_tcf/Digilent/210251A08870/0_1_0/IBERT/Quad_216/MGT_X0Y6/TX] 0] [lindex [get_hw_sio_rxs localhost:3121/xilinx_tcf/Digilent/210251A08870/0_1_0/IBERT/Quad_216/MGT_X0Y6/RX] 0] ]
lappend xil_newLinks $xil_newLink
set xil_newLink [create_hw_sio_link -description {Link 3} [lindex [get_hw_sio_txs localhost:3121/xilinx_tcf/Digilent/210251A08870/0_1_0/IBERT/Quad_216/MGT_X0Y7/TX] 0] [lindex [get_hw_sio_rxs localhost:3121/xilinx_tcf/Digilent/210251A08870/0_1_0/IBERT/Quad_216/MGT_X0Y7/RX] 0] ]
lappend xil_newLinks $xil_newLink
set xil_newLinkGroup [create_hw_sio_linkgroup -description {Link Group 0} [get_hw_sio_links $xil_newLinks]]
unset xil_newLinks
set_property TX_PATTERN {PRBS 15-bit} [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
commit_hw_sio -non_blocking [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
set_property RX_PATTERN {PRBS 15-bit} [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
commit_hw_sio -non_blocking [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
set_property PORT.GTTXRESET 1 [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
commit_hw_sio -non_blocking [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
set_property PORT.GTTXRESET 0 [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
commit_hw_sio -non_blocking [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
set_property PORT.GTRXRESET 1 [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
commit_hw_sio -non_blocking [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
set_property PORT.GTRXRESET 0 [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
commit_hw_sio -non_blocking [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
set_property LOGIC.MGT_ERRCNT_RESET_CTRL 1 [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
commit_hw_sio -non_blocking [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
set_property LOGIC.MGT_ERRCNT_RESET_CTRL 0 [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
commit_hw_sio -non_blocking [get_hw_sio_links -of_objects [get_hw_sio_linkgroups {Link_Group_0}]]
set xil_newScan [create_hw_sio_scan -description {Scan 0} 2d_full_eye  [lindex [get_hw_sio_links localhost:3121/xilinx_tcf/Digilent/210251A08870/0_1_0/IBERT/Quad_216/MGT_X0Y4/TX->localhost:3121/xilinx_tcf/Digilent/210251A08870/0_1_0/IBERT/Quad_216/MGT_X0Y4/RX] 0 ]]
set_property DWELL_BER 1e-9 [get_hw_sio_scans $xil_newScan]
run_hw_sio_scan [get_hw_sio_scans $xil_newScan]

after 15000

set_property DESCRIPTION Channel [get_hw_sio_scans SCAN_0]
set_property DESCRIPTION Channel0 [get_hw_sio_scans SCAN_0]
set xil_newScan [create_hw_sio_scan -description {Scan 1} 2d_full_eye  [lindex [get_hw_sio_links localhost:3121/xilinx_tcf/Digilent/210251A08870/0_1_0/IBERT/Quad_216/MGT_X0Y5/TX->localhost:3121/xilinx_tcf/Digilent/210251A08870/0_1_0/IBERT/Quad_216/MGT_X0Y5/RX] 0 ]]
set_property DWELL_BER 1e-9 [get_hw_sio_scans $xil_newScan]
run_hw_sio_scan [get_hw_sio_scans $xil_newScan]

after 15000

set_property DESCRIPTION Channel [get_hw_sio_scans SCAN_1]
set_property DESCRIPTION Channel1 [get_hw_sio_scans SCAN_1]
set xil_newScan [create_hw_sio_scan -description {Scan 2} 2d_full_eye  [lindex [get_hw_sio_links localhost:3121/xilinx_tcf/Digilent/210251A08870/0_1_0/IBERT/Quad_216/MGT_X0Y6/TX->localhost:3121/xilinx_tcf/Digilent/210251A08870/0_1_0/IBERT/Quad_216/MGT_X0Y6/RX] 0 ]]
set_property DWELL_BER 1e-9 [get_hw_sio_scans $xil_newScan]
run_hw_sio_scan [get_hw_sio_scans $xil_newScan]

after 15000

set_property DESCRIPTION Channel [get_hw_sio_scans SCAN_2]
set_property DESCRIPTION {Channel 2} [get_hw_sio_scans SCAN_2]
set xil_newScan [create_hw_sio_scan -description {Scan 3} 2d_full_eye  [lindex [get_hw_sio_links localhost:3121/xilinx_tcf/Digilent/210251A08870/0_1_0/IBERT/Quad_216/MGT_X0Y7/TX->localhost:3121/xilinx_tcf/Digilent/210251A08870/0_1_0/IBERT/Quad_216/MGT_X0Y7/RX] 0 ]]
set_property DWELL_BER 1e-9 [get_hw_sio_scans $xil_newScan]
run_hw_sio_scan [get_hw_sio_scans $xil_newScan]
set_property DESCRIPTION Channel [get_hw_sio_scans SCAN_3]
set_property DESCRIPTION {Channel 3} [get_hw_sio_scans SCAN_3]
