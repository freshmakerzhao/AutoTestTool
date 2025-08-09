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
        puts "tx number $params(-tx_nub) error"
        return 0
    }
    if {$params(-rx_nub) >= [llength [get_hw_sio_rxs]]} {
        puts "rx number $params(-rx_nub) error"
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

# ============= CSV合并功能（新增部分）=============

# 全局变量：存储metadata文件列表
set global_metadata_list {}

# 添加metadata文件到全局列表
proc add_metadata_file {metadata_file test_round} {
    global global_metadata_list
    
    if {[file exists $metadata_file]} {
        lappend global_metadata_list [list $metadata_file $test_round]
        puts "已添加metadata文件: $metadata_file (测试轮次: $test_round)"
        return 1
    } else {
        puts "警告: metadata文件不存在: $metadata_file"
        return 0
    }
}

# 显示当前metadata文件列表
proc show_metadata_list {} {
    global global_metadata_list
    
    puts "当前metadata文件列表:"
    if {[llength $global_metadata_list] == 0} {
        puts "  (空列表)"
    } else {
        set index 1
        foreach entry $global_metadata_list {
            set file [lindex $entry 0]
            set round [lindex $entry 1]
            puts "  $index. [file tail $file] (测试轮次: $round)"
            incr index
        }
    }
}

# 清空metadata文件列表
proc clear_metadata_list {} {
    global global_metadata_list
    set global_metadata_list {}
    puts "metadata文件列表已清空"
}

proc merge_all_metadata {output_file} {
    global global_metadata_list

    puts "开始合并metadata文件..."
    if {![info exists global_metadata_list] || [llength $global_metadata_list] == 0} {
        puts "错误: 没有metadata文件需要合并"
        return 0
    }

    # 确保输出目录存在
    set outdir [file dirname [file normalize $output_file]]
    if {![file exists $outdir]} {
        file mkdir $outdir
    }

    set header_written   0
    set total_rows       0
    set processed_files  0

    # 按测试轮次排序（entry: {metadata_file test_round}）
    set sorted_list [lsort -integer -index 1 $global_metadata_list]
    puts "待合并文件数量: [llength $sorted_list]"

    # 打开输出文件
    set openOutRC [catch {open $output_file w} output_fd]
    if {$openOutRC != 0} {
        puts "错误: 无法写入输出文件: $output_file ($output_fd)"
        return 0
    }
    fconfigure $output_fd -encoding utf-8 -translation lf

    # —— 主循环 —— #
    foreach entry $sorted_list {
        set metadata_file [lindex $entry 0]
        set test_round    [lindex $entry 1]

        puts "处理文件: [file tail $metadata_file] (测试轮次: $test_round)"

        if {![file exists $metadata_file]} {
            puts "警告: 文件不存在，跳过: $metadata_file"
            continue
        }

        # 打开输入文件
        set openInRC [catch {open $metadata_file r} input_fd]
        if {$openInRC != 0} {
            puts "警告: 无法打开，跳过: $metadata_file ($input_fd)"
            continue
        }
        fconfigure $input_fd -encoding utf-8 -translation auto

        # 读取与写入
        set line_num        0
        set wrote_this_file 0
        while {[gets $input_fd line] >= 0} {
            incr line_num
            set clean_line [string trim $line]

            if {$clean_line eq ""} {
                continue
            }

            if {$line_num == 1} {
                # 表头：仅第一次写入，并加上 Test_Round 列
                if {!$header_written} {
                    puts $output_fd "Test_Round,$clean_line"
                    set header_written 1
                }
                continue
            } else {
                puts $output_fd "$test_round,$clean_line"
                incr total_rows
                set wrote_this_file 1
            }
        }

        # 关闭输入
        catch {close $input_fd}

        if {$wrote_this_file} {
            incr processed_files
        }
    }

    # 关闭输出
    catch {close $output_fd}

    if {!$header_written} {
        puts "错误: 未找到任何有效的表头，未生成输出。"
        return 0
    }

    puts "metadata合并完成！"
    puts "输出文件: $output_file"
    puts "包含测试轮次: $processed_files"
    puts "总数据行数: $total_rows"
    puts "表格格式: Test_Round + 原始CSV列"
    return 1
}

# 生成 OUT_CSV_DIR 下的 _metadata.csv 路径
proc get_metadata_csv_path {base_name} {
    # 拼到 OUT_CSV_DIR 目录下
    set base_dir $::env(OUT_CSV_DIR)
    set filename "${base_name}_metadata.csv"
    return [file normalize [file join $base_dir $filename]]
}

# 智能检测并添加最新的metadata文件
proc auto_add_latest_metadata {base_name test_round} {
    set metadata_file [get_metadata_csv_path $base_name]
    
    if {[add_metadata_file $metadata_file $test_round]} {
        puts "自动添加成功: [file tail $metadata_file]"
        return 1
    } else {
        puts "自动添加失败: [file tail $metadata_file]"
        return 0
    }
}

# 生成最终合并报告
proc generate_metadata_report {output_file} {
    global global_metadata_list
    
    if {[merge_all_metadata $output_file]} {
        puts ""
        puts "Metadata合并报告生成成功！"
        puts ""
        puts "测试统计："
        puts "  测试轮次: [llength $global_metadata_list]"
        puts "  预期数据行: [expr {[llength $global_metadata_list] * 4}] (每轮4通道)"
        puts "  输出文件: $output_file"
        puts ""
        puts "文件格式："
        puts "  第1列: Test_Round (测试轮次)"
        puts "  第2-19列: 原始18项测试参数"
        puts "  每轮次包含4行数据 (Link 0-3)"
        puts ""
        puts ""
        return 1
    } else {
        puts "Metadata合并失败"
        return 0
    }
}