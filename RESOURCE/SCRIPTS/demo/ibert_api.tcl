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
    remove_hw_sio_link [get_hw_sio_links -filter "DESCRIPTION == $link_name"]
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
        set_property TXPOST $params(-tx_post) $link
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
    set_property PORT.GTTXRESET 1 $link
    commit_hw_sio $link
    set_property PORT.GTTXRESET 0 $link
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

# 新增：多链路批量扫描函数（串行执行）
proc scan_multi_links {args} {
    array set params {
        -link_names {"Link 0" "Link 1" "Link 2" "Link 3"}
        -scan_name_prefix "Channel"
        -scan_type 2d_full_eye 
        -dwell_ber 1e-9
        -result_path "./multi_channel_result.csv"
        -temp_dir "./temp_scans"
    }

    array set params $args
    
    # 创建临时目录
    file mkdir $params(-temp_dir)
    
    set temp_files {}
    set valid_link_names {}
    
    # 串行执行每个链路的扫描
    set channel_index 0
    foreach link_name $params(-link_names) {
        puts "Starting scan for $link_name..."
        
        set link [get_hw_sio_links -filter "DESCRIPTION == \"$link_name\""]
        if {[llength $link] == 0} {
            puts "Warning: Link $link_name not found, skipping..."
            incr channel_index
            continue
        }
        
        set scan_name "$params(-scan_name_prefix) $channel_index"
        set temp_file "$params(-temp_dir)/temp_$channel_index.csv"
        
        # 创建、运行并等待单个扫描完成
        set xil_newScan [create_hw_sio_scan -description $scan_name $params(-scan_type) $link]
        set_property DWELL_BER $params(-dwell_ber) $xil_newScan
        
        puts "  Running scan for $link_name (Channel $channel_index)..."
        run_hw_sio_scan $xil_newScan
        wait_on_hw_sio_scan $xil_newScan
        
        # 保存扫描结果
        write_hw_sio_scan $temp_file $xil_newScan -force
        puts "  Completed scan for $link_name"
        
        lappend temp_files $temp_file
        lappend valid_link_names $link_name
        
        incr channel_index
    }
    
    # 生成两种格式的输出文件
    if {[llength $temp_files] > 0} {
        # 1. 生成横向元数据格式
        set metadata_file [file rootname $params(-result_path)]_metadata.csv
        merge_metadata_horizontal $temp_files $metadata_file $valid_link_names
        puts "Metadata format saved to: $metadata_file"
        
        # 2. 生成完整数据格式（包括2D数据）
        merge_csv_files_complete $temp_files $params(-result_path) $valid_link_names
        puts "Complete data format saved to: $params(-result_path)"
        
        puts "Multi-link scan completed with dual output formats!"
    } else {
        puts "No valid links found for scanning."
    }
    
    # 清理临时文件
    file delete -force $params(-temp_dir)
}

# 新增：提取元数据的函数
proc extract_metadata {csv_file} {
    if {![file exists $csv_file]} {
        puts "Warning: File $csv_file not found"
        return [list {} {}]
    }
    
    set input_fd [open $csv_file r]
    set attributes {}
    set values {}
    
    while {[gets $input_fd line] >= 0} {
        set clean_line [string trim $line]
        
        # 跳过空行
        if {$clean_line eq ""} continue
        
        # 停止条件：遇到2d statistical或Scan Start就停止
        if {[string match "*2d statistical*" $clean_line]} break
        if {[string match "*Scan Start*" $clean_line]} break
        
        # 跳过特殊行
        if {[string match "*Misc Info*" $clean_line]} continue
        
        # 解析属性-值对
        set parts [split $clean_line ","]
        if {[llength $parts] >= 2} {
            set attr [string trim [lindex $parts 0] "\r\n "]
            set val [string trim [lindex $parts 1] "\r\n "]
            
            lappend attributes $attr
            lappend values $val
        }
    }
    
    close $input_fd
    return [list $attributes $values]
}

# 修改后的CSV合并函数：横向元数据格式
proc merge_metadata_horizontal {temp_files output_file link_names} {
    set output_fd [open $output_file w]
    
    set all_attributes {}
    set all_link_data {}
    
    # 处理每个临时文件
    foreach temp_file $temp_files link_name $link_names {
        puts "Processing metadata for $link_name..."
        
        set metadata_result [extract_metadata $temp_file]
        set attributes [lindex $metadata_result 0]
        set values [lindex $metadata_result 1]
        
        # 第一个文件：设置属性名作为表头
        if {[llength $all_attributes] == 0} {
            set all_attributes $attributes
        }
        
        # 存储每个链路的数据
        lappend all_link_data [list $link_name $values]
    }
    
    # 写入表头（属性名）
    if {[llength $all_attributes] > 0} {
        puts -nonewline $output_fd [lindex $all_attributes 0]
        for {set i 1} {$i < [llength $all_attributes]} {incr i} {
            puts -nonewline $output_fd ",[lindex $all_attributes $i]"
        }
        puts $output_fd ""
        
        # 写入每个链路的数据行
        foreach link_data $all_link_data {
            set link_name [lindex $link_data 0]
            set values [lindex $link_data 1]
            
            if {[llength $values] > 0} {
                puts -nonewline $output_fd [lindex $values 0]
                for {set i 1} {$i < [llength $values]} {incr i} {
                    set val [lindex $values $i]
                    # 如果值包含逗号，用引号包围
                    if {[string match "*,*" $val]} {
                        puts -nonewline $output_fd ",\"$val\""
                    } else {
                        puts -nonewline $output_fd ",$val"
                    }
                }
                puts $output_fd ""
            }
        }
        
        puts "Horizontal metadata format created successfully!"
        puts "- Header row: [llength $all_attributes] attributes"
        puts "- Data rows: [llength $all_link_data] links"
    } else {
        puts "No metadata found in input files."
    }
    
    close $output_fd
}

# 新增：完整CSV合并函数（保留原始格式，包括2D数据）
proc merge_csv_files_complete {temp_files output_file link_names} {
    set output_fd [open $output_file w]
    
    set first_file 1
    set channel_index 0
    
    foreach temp_file $temp_files link_name $link_names {
        if {![file exists $temp_file]} {
            puts "Warning: Temp file $temp_file not found"
            incr channel_index
            continue
        }
        
        set input_fd [open $temp_file r]
        set line_num 0
        
        while {[gets $input_fd line] >= 0} {
            incr line_num
            
            # 处理头部
            if {$line_num == 1} {
                if {$first_file} {
                    # 第一个文件：添加Channel列并写入头部
                    puts $output_fd "Channel,$line"
                    set first_file 0
                }
                continue
            }
            
            # 处理数据行：添加通道信息
            if {$line != ""} {
                puts $output_fd "$link_name,$line"
            }
        }
        
        close $input_fd
        incr channel_index
    }
    
    close $output_fd
    puts "Complete data format created successfully!"
    puts "- Includes all metadata and 2D eye diagram data"
    puts "- Channel column added for identification"
}