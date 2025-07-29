# 导入ibert库
source "./ibert_api.tcl"

# 添加链路清理函数
proc cleanup_all_links {} {
    puts "🧹 清理现有链路..."
    set existing_links [get_hw_sio_links]
    if {[llength $existing_links] > 0} {
        foreach link $existing_links {
            set link_name [get_property DESCRIPTION $link]
            puts "  清理链路: $link_name"
        }
        remove_hw_sio_link $existing_links
        puts "✅ 清理了 [llength $existing_links] 个链路"
    } else {
        puts "✅ 没有需要清理的链路"
    }
}

# =================== 设备连接（一次性）===================
puts "🚀 开始IBERT四轮测试..."

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

puts "✅ 设备连接完成"

# =================== 第一次测试 ===================
puts ""
puts "🔄 第一次测试开始..."

# 清理现有链路（如果有）
cleanup_all_links

# 创建链路
create_link -tx_nub 0 -rx_nub 0 -link_name "Link 0"
create_link -tx_nub 1 -rx_nub 1 -link_name "Link 1"
create_link -tx_nub 2 -rx_nub 2 -link_name "Link 2"
create_link -tx_nub 3 -rx_nub 3 -link_name "Link 3"

# 配置链路
set_link_property -tx_pattern "PRBS 15-bit"
set_link_property -rx_pattern "PRBS 15-bit"

# 扫描
scan_multi_links \
    -link_names {"Link 0" "Link 1" "Link 2" "Link 3"} \
    -scan_name_prefix "Channel" \
    -scan_type 2d_full_eye \
    -dwell_ber 1e-9 \
    -result_path "./all_channels_result1.csv"

puts "✅ 第一次测试完成"

# =================== 第二次测试 ===================
puts ""
puts "🔄 第二次测试开始..."

# 清理链路
cleanup_all_links

# 重新创建链路
create_link -tx_nub 0 -rx_nub 0 -link_name "Link 0"
create_link -tx_nub 1 -rx_nub 1 -link_name "Link 1"
create_link -tx_nub 2 -rx_nub 2 -link_name "Link 2"
create_link -tx_nub 3 -rx_nub 3 -link_name "Link 3"

# 配置链路
set_link_property -tx_pattern "PRBS 15-bit"
set_link_property -rx_pattern "PRBS 15-bit"

# 扫描
scan_multi_links \
    -link_names {"Link 0" "Link 1" "Link 2" "Link 3"} \
    -scan_name_prefix "Channel" \
    -scan_type 2d_full_eye \
    -dwell_ber 1e-9 \
    -result_path "./all_channels_result2.csv"

puts "✅ 第二次测试完成"

# =================== 第三次测试 ===================
puts ""
puts "🔄 第三次测试开始..."

cleanup_all_links

create_link -tx_nub 0 -rx_nub 0 -link_name "Link 0"
create_link -tx_nub 1 -rx_nub 1 -link_name "Link 1"
create_link -tx_nub 2 -rx_nub 2 -link_name "Link 2"
create_link -tx_nub 3 -rx_nub 3 -link_name "Link 3"

set_link_property -tx_pattern "PRBS 15-bit"
set_link_property -rx_pattern "PRBS 15-bit"

scan_multi_links \
    -link_names {"Link 0" "Link 1" "Link 2" "Link 3"} \
    -scan_name_prefix "Channel" \
    -scan_type 2d_full_eye \
    -dwell_ber 1e-9 \
    -result_path "./all_channels_result3.csv"

puts "✅ 第三次测试完成"

# =================== 第四次测试 ===================
puts ""
puts "🔄 第四次测试开始..."

cleanup_all_links

create_link -tx_nub 0 -rx_nub 0 -link_name "Link 0"
create_link -tx_nub 1 -rx_nub 1 -link_name "Link 1"
create_link -tx_nub 2 -rx_nub 2 -link_name "Link 2"
create_link -tx_nub 3 -rx_nub 3 -link_name "Link 3"

set_link_property -tx_pattern "PRBS 15-bit"
set_link_property -rx_pattern "PRBS 15-bit"

scan_multi_links \
    -link_names {"Link 0" "Link 1" "Link 2" "Link 3"} \
    -scan_name_prefix "Channel" \
    -scan_type 2d_full_eye \
    -dwell_ber 1e-9 \
    -result_path "./all_channels_result4.csv"

puts "✅ 第四次测试完成"

# =================== metadata合并 ===================
puts ""
puts "📊 开始合并metadata..."

# 初始化metadata文件列表
clear_metadata_list

# 添加四次测试的metadata文件
auto_add_latest_metadata "./all_channels_result1" 1
auto_add_latest_metadata "./all_channels_result2" 2  
auto_add_latest_metadata "./all_channels_result3" 3
auto_add_latest_metadata "./all_channels_result4" 4

# 显示收集到的文件
show_metadata_list

# 生成合并总表
set final_output "./all_tests_combined_metadata.csv"

if {[generate_metadata_report $final_output]} {
    puts ""
    puts "🎉 四次IBERT测试全部完成！"
    puts "📄 合并总表: $final_output"
} else {
    puts "❌ metadata合并失败"
}

puts ""
puts "✅ 脚本执行完毕！"