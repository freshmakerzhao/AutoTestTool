proc get_tx {tx_nub} {
    return [lindex [get_hw_sio_txs $tx_nub]]
}

proc get_rx {rx_nub} {
    return [lindex [get_hw_sio_rxs $rx_nub]]
}

proc create_link {args} {
    array set params {
        -tx_nub 0
        -rx_nub 0
        -link_name "link 0"
    }

    array set params $args

    if {$params(-tx_nub) >= [llength [get_hw_sio_txs]]} {
        puts "tx nubmer $tx_nub error"
        return 0
    }
    if {$params(-rx_nub) >= [llength [get_hw_sio_rxs]]} {
        puts "rx nubmer $rx_nub error"
        return 0
    }

    set tx [lindex [get_hw_sio_txs] $params(-tx_nub)] 
    set rx [lindex [get_hw_sio_rxs] $params(-rx_nub)]
    create_hw_sio_link -description $params(-link_name) $tx $rx
    return 1
}

proc delete_link {link_name} {
    remove_hw_sio_link [get_hw_sio_links -filte {DESCRIPTION == $link_name}]
}

proc set_link_property {args} {
    array set params $args
    if {[info exists params(-link_name)]} {
        set link [get_hw_sio_links -filter "DESCRIPTION == \"$params(-link_name)\""]
    } else {
        set link [get_hw_sio_links]
    }

    if {[info exists params(-tx_pattern)]} {
        set_property TX_PATTERN $params(-tx_pattern) $link
    }

    if {[info exists params(-rx_pattern)]} {
        set_property RX_PATTERN $params(-rx_pattern) $link
    }

    if {[info exists params(-tx_pre_cursor)]} {
        set_property TXPRE $params(-tx_pre_cursor) $link
    }

    if {[info exists params(-tx_post)]} {
        set_property TXPOST $params(-tx_diff_swing) $link
    }

    if {[info exists params(-tx_diff_swing)]} {
        set_property TXDIFFSWING $params(-tx_diff_swing) $link
    }

    if {[info exists params(-loopback_mode)]} {
        set_property LOOPBACK $params(-loopback_mode) $link
    }

    commit_hw_sio $link
}


proc rx_reset {args} {
    array set param $args
    if {[info exists param(-link_name)]} {
        set link [get_hw_sio_links -filter "DESCRIPTION == \"$param(-link_name)\""]
    } else {
        set link [get_hw_sio_links]
    }
    set_property PORT.GTRXRESET 1 $link
    commit_hw_sio $link
    set_property PORT.GTRXRESET 0 $link
    commit_hw_sio $link
}

proc tx_reset {args} {
    array set param $args
    if {[info exists param(-link_name)]} {
        set link [get_hw_sio_links -filter "DESCRIPTION == \"$param(-link_name)\""]
    } else {
        set link [get_hw_sio_links]
    }
    set_property PORT.GTRXRESET 1 $link
    commit_hw_sio $link
    set_property PORT.GTRXRESET 0 $link
    commit_hw_sio $link
}

proc ibert_reset {args} {
    array set param $args
    if {[info exists param(-link_name)]} {
        set link [get_hw_sio_links -filter "DESCRIPTION == \"$param(-link_name)\""]
    } else {
        set link [get_hw_sio_links]
    }
    set_property LOGIC.MGT_ERRCNT_RESET_CTRL 1 $link
    commit_hw_sio $link
    set_property LOGIC.MGT_ERRCNT_RESET_CTRL 0 $link
    commit_hw_sio $link
}

proc scan {args} {
    array set params {
        -link_name "link 0"
        -scan_name "scan 0"
        -scan_type 2d_full_eye 
        -dwell_ber 1e-9
        -result_path "./result.csv"
    }

    array set params $args

    set link [get_hw_sio_links -filter "DESCRIPTION == \"$params(-link_name)\""]
    set xil_newScan [create_hw_sio_scan -description $params(-scan_name) $params(-scan_type) $link]
    set_property DWELL_BER $params(-dwell_ber) $xil_newScan
    run_hw_sio_scan $xil_newScan
    wait_on_hw_sio_scan $xil_newScan
    set_property DESCRIPTION $params(-scan_name) $xil_newScan
    write_hw_sio_scan $params(-result_path) $xil_newScan -force
} 