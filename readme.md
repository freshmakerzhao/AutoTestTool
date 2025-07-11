# 一、执行模式

## 1.1 交互模式

```json
python main_shell.py
```

## 1.2 单命令模式

```json
python main_shell.py -c "vccm --file C:/Users/DELL/Desktop/test_workspace/shell/bram_36e1_2_wf_0_a.rbt --vccm_values 105"
```

## 1.3 脚本模式

```json
python main_shell.py myscript.txt
```

# 二、常用命令

## 2.1 基础功能
### 压缩位流
base --file 文件路径 --device MC1P110 --COMPRESS

- device
  - MC1P110
  - MC1P170
  - MC1P210

## 2.2 VCCM

```shell
vccm电压值支持多个电压值，多个电压值时用','隔开，目前支持：
105
106
107
108
109
110
111
112
115
vswl只支持传入一个电压值,目前支持：
1075
1100
1125
1150
1175
1200
1225
1250
1275
1300
1325
1350
1375
1400
1425
1450
1475
1500
```

### 2.2.1 处理单个文件或单个路径

```shell
vccm --file rbt文件路径/bit文件路径/文件路径 --vccm_values vccm电压值 --vswl_selected vswl电压值
传入单个文件：处理结果保存在所在文件夹的对应电压文件夹下
传入一个路径：处理结果保存在路径下的对应电压文件夹下
```

### 2.2.2 处理项目

```shell
vccm --project 项目路径 --vccm_values vccm电压值 --vswl_selected vswl电压值

这里项目的意思是，对这个项目路径下每个文件夹单独处理，将结果生成到每个文件夹下。
```

## 2.3 (异步)串口监视器

### **2.3.1 主要特性**

1. 基于原始main_shell.py
   - ✅ 多命令模式
   - ✅ 完全保留原有所有内容
   - ✅ 只添加异步监听相关功能
   - ✅ 不修改任何原有代码
2. 异步监听功能
   - ✅ 后台监听，不阻塞shell交互
   - ✅ 默认不在终端显示数据，只缓存
   - ✅ 可选择性启用文件日志
   - ✅ 支持动态开启/关闭日志
3. **新增的Shell命令**：

#### **基础串口功能**

- `ports` - 列出可用串口
- `test` - 测试串口连接
- `listen` - 同步监听模式（阻塞）
- `interactive` - 交互式终端
- `send` - 发送文本数据
- `stats` - 获取统计信息

#### **异步监听功能**

- `start_monitor` - **开始后台监听**：不阻塞shell，数据缓存在内存，可选文件日志
- `stop_monitor` - **停止后台监听**：断开连接，显示统计信息
- `monitor_status` - **查看监听状态**：运行状态、连接信息、统计数据
- `show_data` - **显示缓存数据**：查看内存中的接收数据
- `enable_log` - **动态开启日志**：在监听过程中开始记录文件日志
- `disable_log` - **动态关闭日志**：停止文件记录，但继续监听
- `save_log` - **保存缓存到文件**：导出内存中的所有数据
- `clear_cache` - **清空数据缓存**：清理内存，准备新的测试

#### **对外接口函数**（供main_shell.py调用）

每个函数都有详细的文档说明其作用和参数。

#### **基础异步监听**

```bash
(AutoTestTool) start_monitor COM3 115200
✓ 后台串口监听已启动: COM3@115200
💾 数据缓存在内存中

(AutoTestTool) base --file test.bit --device MC1P110 --CRC
# 同时进行串口监听和基础功能

(AutoTestTool) enable_log voltage_test.log
✓ 文件日志已启用: voltage_test.log

(AutoTestTool) vccm --file test.bit --vccm_values 105 110
# 电压变化被记录到日志

(AutoTestTool) show_data 10
# 查看最近10条数据

(AutoTestTool) stop_monitor
✓ 后台串口监听已停止
```

### **2.3.2 架构优势**

1. **完全兼容**：与原有shell功能100%兼容
2. **真正异步**：监听不阻塞其他操作
3. **灵活控制**：可随时开启/关闭日志记录
4. **数据安全**：环形缓冲区确保数据不丢失
5. **资源可控**：缓存大小限制，防止内存溢出

### 2.3.3 修复消息完整性

1.新增 MessageBuffer 类：

用于缓冲串口接收的数据片段
按换行符 \n 分割消息，确保只处理完整的消息
使用线程锁保证数据安全


2.修改事件处理器：

CLIEventHandler 和 AsyncSerialMonitor 都集成了消息缓冲器
只有接收到完整的以换行符结尾的消息时，才进行显示和日志记录

3.消息完整性保证：

串口数据分批接收时，会暂存在缓冲区中
只有遇到换行符时，才认为消息完整并进行处理
避免了消息被分割成多行的问题



## 2.4 电压查询配置

修改与添加文件如下：
命令行模式电压查询设置支持添加到：CLI/main_shell.py
测试demo脚本：RESOURCE/SCRIPTS/demo_test/test_voltage.txt

**test_voltage.txt**

- **30个测试步骤**，全面验证电压控制功能
- 测试内容：连接检查、规格显示、状态查看、默认设置、自定义设置、步进校正、边界测试等
- 运行时间：3-5分钟
- 生成文件：完整会话日志、详细操作日志、测试数据导出

```python
python main_shell.py C:\path\to\test_voltage.txt
```

### 2.4.1 🔧 核心命令

```
使用前提：必须先启动串口监听服务
  start_monitor COM3 115200        # 启动串口监听

电压控制功能:
  voltage status                   # 显示当前电压状态(优先缓存)
  voltage status --live            # 主动查询电压状态  
  voltage set --defaults           # 设置默认电压值
  voltage set --values 3300 1000 1800 ...  # 设置指定电压值
  voltage specs                    # 显示电压规格
  voltage test                     # 测试电压功能
  voltage interactive              # 交互式电压设置
  
电压参数说明:
  - 11路电压固定顺序: VCCO_0、VCCBRAM、VCCAUX、VCCINT、VCCO_16、VCCO_15、VCCO_14、VCCO_13、VCCO_34、MGTAVTT、MGTAVCC
  - 电压单位: mV (毫伏)
  - 步进值: 根据电压类型自动校正
  - 支持VCCADC和VCCREF使能控制
```



### 2.4.2 📊 **预期测试结果**

```
📊 电压功能检查:
  串口监听: ✓ 运行中
  设备通信: ✓ 正常
  电压路数: 11

📊 MC1P110电压状态:
Bank名称     设定值(mV)   实际值(mV)   差值(mV)     状态
VCCO_0       3300         3296.3       -3.7         ✓正常
VCCBRAM      1000         1000.0       0.0          ✓正常
...

✓ 电压设置成功
📏 VCCO_0: 3303mV → 3300mV (步进校正)
```



## 2.5 vivado的tcl集成

修改与添加文件如下：
命令行：CLI/cli_vivado.py
统一入口：CLI/main_shell.py
核心run_vivado_tcl（集成烧写bit、bin、mcs，回读，执行自定义的vivado tcl脚本）：CORE/run_vivado_tcl.py
测试demo脚本：RESOURCE/SCRIPTS/demo_test/test_vivado_api.txt

```python
python main_shell.py test_vivado_api.txt
```

### 2.5.1 🔧 核心命令

| 命令              | 功能        | 示例                                                         |
| ----------------- | ----------- | ------------------------------------------------------------ |
| `vivado_program`  | 烧写到FPGA  | `vivado_program -v $VIVADO_PATH -b design.bit`               |
| `vivado_flash`    | 烧写到Flash | `vivado_flash -v $VIVADO_PATH -b design.mcs -f mt25ql128-spi-x1_x2_x4` |
| `vivado_readback` | 从FPGA回读  | `vivado_readback -v $VIVADO_PATH -o readback.rbd`            |
| `vivado_custom`   | 执行TCL脚本 | `vivado_custom -v $VIVADO_PATH -t script.tcl`                |
| `vivado_test`     | 测试功能    | `vivado_test -v $VIVADO_PATH`                                |
| `vivado_help`     | 显示帮助    | `vivado_help`                                                |
| `vivado_quick`    | 快速操作    | `vivado_quick test $VIVADO_PATH`                             |

### 2.5.2 📊 **预期测试结果**

连接上100t_484的开发板后，能够将准备好的.bit、.bin、.mcs等文件进行烧写，也可以从FPGA中回读出rbd文件。实际烧写成功后，根据码流功能，开发板显示对应状态。

```
PS C:\Users\win\Desktop\HybrdchipGUI\merge_zhiwei\AutoTestTool>  & 'd:\Miniconda3\python.exe' 'c:\Users\win\.vscode\extensions\ms-python.debugpy-2025.8.0-win32-x64\bundled\libs\debugpy\launcher' '65472' '--' 'C:\Users\win\Desktop\HybrdchipGUI\merge_zhiwei\AutoTestTool\CLI\main_shell_cli_vivado.py' 'C:\Users\win\Desktop\HybrdchipGUI\merge_zhiwei\AutoTestTool\RESOURCE\SCRIPTS\actual_vivado_test.txt' 
[004] 执行: echo "🔥 开始实际Vivado全功能硬件测试"
🔥 开始实际Vivado全功能硬件测试 
[005] 执行: echo ""
 
[006] 执行: echo "⚠️  警告：此脚本将实际操作FPGA硬件！"
⚠️  警告：此脚本将实际操作FPGA硬件！ 
[007] 执行: echo "   请确保：1) FPGA开发板已连接  2) 驱动已安装  3) bit文件有效"
   请确保：1) FPGA开发板已连接  2) 驱动已安装  3) bit文件有效 
[008] 执行: echo ""
 
[014] 执行: echo "📝 设置实际测试环境..."
📝 设置实际测试环境... 
[015] 执行: set VIVADO_PATH "C:\\Xilinx\\Vivado\\2020.1\\bin"
$VIVADO_PATH = "C:\\Xilinx\\Vivado\\2020.1\\bin"
[016] 执行: set BASE_PATH "C:\\Users\\win\\Desktop\\HybrdchipGUI\\merge_zhiwei\\AutoTestTool"
$BASE_PATH = "C:\\Users\\win\\Desktop\\HybrdchipGUI\\merge_zhiwei\\AutoTestTool"
[017] 执行: set LOG_DIR "$BASE_PATH\\logs\\vivado_log"
$LOG_DIR = "$BASE_PATH\\logs\\vivado_log"
[020] 执行: set BITSTREAM_FILE "$BASE_PATH\\RESOURCE\\SCRIPTS\\top.bit"
$BITSTREAM_FILE = "$BASE_PATH\\RESOURCE\\SCRIPTS\\top.bit"
[021] 执行: set MCS_FILE "$BASE_PATH\\RESOURCE\\SCRIPTS\\top_yasuo.mcs"
$MCS_FILE = "$BASE_PATH\\RESOURCE\\SCRIPTS\\top_yasuo.mcs"
[022] 执行: set BIN_FILE "$BASE_PATH\\RESOURCE\\SCRIPTS\\top.bin"
$BIN_FILE = "$BASE_PATH\\RESOURCE\\SCRIPTS\\top.bin"
[023] 执行: set RBT_FILE "$BASE_PATH\\RESOURCE\\SCRIPTS\\top.rbt"
$RBT_FILE = "$BASE_PATH\\RESOURCE\\SCRIPTS\\top.rbt"
[024] 执行: set READBACK_FILE "$BASE_PATH\\RESOURCE\\SCRIPTS\\top.rbd"
$READBACK_FILE = "$BASE_PATH\\RESOURCE\\SCRIPTS\\top.rbd"
[025] 执行: set CUSTOM_TCL "$BASE_PATH\\RESOURCE\\SCRIPTS\\custom_test.tcl"
$CUSTOM_TCL = "$BASE_PATH\\RESOURCE\\SCRIPTS\\custom_test.tcl"
[028] 执行: set PROGRAM_LOG "$LOG_DIR\\program.log"
$PROGRAM_LOG = "$LOG_DIR\\program.log"
[029] 执行: set PROGRAM_JOU "$LOG_DIR\\program.jou"
$PROGRAM_JOU = "$LOG_DIR\\program.jou"
[030] 执行: set READBACK_LOG "$LOG_DIR\\readback.log"
$READBACK_LOG = "$LOG_DIR\\readback.log"
[031] 执行: set FLASH_LOG "$LOG_DIR\\flash.log"
$FLASH_LOG = "$LOG_DIR\\flash.log"
[032] 执行: set CUSTOM_LOG "$LOG_DIR\\custom.log"
$CUSTOM_LOG = "$LOG_DIR\\custom.log"
[034] 执行: echo "环境配置："
环境配置：
[035] 执行: echo "  VIVADO_PATH = $VIVADO_PATH"
  VIVADO_PATH = $VIVADO_PATH
[036] 执行: echo "  BASE_PATH = $BASE_PATH"
  BASE_PATH = $BASE_PATH
[037] 执行: echo "  LOG_DIR = $LOG_DIR"
  LOG_DIR = $LOG_DIR
[038] 执行: echo "  BITSTREAM_FILE = $BITSTREAM_FILE"
  BITSTREAM_FILE = $BITSTREAM_FILE
[039] 执行: echo "  MCS_FILE = $MCS_FILE"
  MCS_FILE = $MCS_FILE
[040] 执行: echo ""

[046] 执行: echo "🔧 测试1: 验证Vivado环境和硬件连接"
🔧 测试1: 验证Vivado环境和硬件连接
[047] 执行: vivado_test -v $VIVADO_PATH
🧪 开始Vivado功能测试

📁 测试1: 验证Vivado安装

📜 测试2: 检查TCL脚本

🔌 测试3: 硬件连接检查
✓ Vivado安装路径有效: C:\Xilinx\Vivado\2020.1\bin
✓ program.tcl: 存在
✓ program_flash.tcl: 存在
✓ readback.tcl: 存在
💡 硬件连接需要实际设备，请确保:
   • FPGA开发板已连接
   • USB线缆连接正常
   • 驱动程序已安装

✓ Vivado功能测试通过，可以正常使用
[048] 执行: echo ""

[050] 执行: echo "💡 检查硬件连接状态..."
💡 检查硬件连接状态...
[051] 执行: echo "   如果以下测试失败，请检查："
   如果以下测试失败，请检查：
[052] 执行: echo "   • FPGA板子是否已连接USB"
   • FPGA板子是否已连接USB
[053] 执行: echo "   • 板子电源是否已打开"
   • 板子电源是否已打开
[054] 执行: echo "   • Vivado驱动是否正确安装"
   • Vivado驱动是否正确安装
[055] 执行: echo ""

[057] 执行: sleep 3
⏸️  等待 3.0 秒...
✓ 等待结束
[063] 执行: echo "🔥 测试2: 基本FPGA烧写测试 (.bit文件)"
🔥 测试2: 基本FPGA烧写测试 (.bit文件)
[064] 执行: echo "执行命令: vivado_program -v $VIVADO_PATH -b $BITSTREAM_FILE -l $PROGRAM_LOG -j $PROGRAM_JOU"
执行命令: vivado_program -v $VIVADO_PATH -b $BITSTREAM_FILE -l $PROGRAM_LOG -j $PROGRAM_JOU
[065] 执行: echo ""

[067] 执行: echo "⚠️  即将开始实际烧写操作！"
⚠️  即将开始实际烧写操作！
[068] 执行: echo "请确认FPGA硬件连接正常..."
请确认FPGA硬件连接正常...
[069] 执行: sleep 2
⏸️  等待 2.0 秒...
✓ 等待结束
[072] 执行: vivado_program -v $VIVADO_PATH -b $BITSTREAM_FILE -l $PROGRAM_LOG -j $PROGRAM_JOU
🔥 开始烧写: C:\Users\win\Desktop\HybrdchipGUI\merge_zhiwei\AutoTestTool\RESOURCE\SCRIPTS\top.bit
=======================================================
[run_script_tcl] 执行参数:
  vivado_bin_path = C:\Xilinx\Vivado\2020.1\bin
  tcl_script_path = C:\Users\win\Desktop\HybrdchipGUI\merge_zhiwei\AutoTestTool\RESOURCE/SCRIPTS/program.tcl
  tcl_args = ['C:\\Users\\win\\Desktop\\HybrdchipGUI\\merge_zhiwei\\AutoTestTool\\RESOURCE\\SCRIPTS\\top.bit']
  log_file = C:\Users\win\Desktop\HybrdchipGUI\merge_zhiwei\AutoTestTool\logs\vivado_log\program.log
  journal_file = C:\Users\win\Desktop\HybrdchipGUI\merge_zhiwei\AutoTestTool\logs\vivado_log\program.jou
  mode = batch
  命令: C:\Xilinx\Vivado\2020.1\bin\vivado.bat -mode batch -log C:\Users\win\Desktop\HybrdchipGUI\merge_zhiwei\AutoTestTool\logs\vivado_log\program.log -journal C:\Users\win\Desktop\HybrdchipGUI\merge_zhiwei\AutoTestTool\logs\vivado_log\program.jou -source C:\Users\win\Desktop\HybrdchipGUI\merge_zhiwei\AutoTestTool\RESOURCE/SCRIPTS/program.tcl -tclargs C:\Users\win\Desktop\HybrdchipGUI\merge_zhiwei\AutoTestTool\RESOURCE\SCRIPTS\top.bit
=======================================================

****** Vivado v2020.1 (64-bit)
  **** SW Build 2902540 on Wed May 27 19:54:49 MDT 2020
  **** IP Build 2902112 on Wed May 27 22:43:36 MDT 2020
    ** Copyright 1986-2020 Xilinx, Inc. All Rights Reserved.

source {C:\Users\win\Desktop\HybrdchipGUI\merge_zhiwei\AutoTestTool\RESOURCE/SCRIPTS/program.tcl}
# if {$argc != 1} {
#     puts "Usage error: Please provide the path to a .bit or .rbt file"
#     puts "Example: vivado -mode batch -source program_fpga.tcl -tclargs D:/zs_prj/top.bit"
#     exit 1
# }
# set bitstream_file [lindex $argv 0]
# if {![file exists $bitstream_file]} {
#     puts "The specified file does not exist: $bitstream_file"
#     exit 1
# }
# puts "Loading file: $bitstream_file"
Loading file: C:\Users\win\Desktop\HybrdchipGUI\merge_zhiwei\AutoTestTool\RESOURCE\SCRIPTS\top.bit
# open_hw_manager
# connect_hw_server
INFO: [Labtools 27-2285] Connecting to hw_server url TCP:localhost:3121
INFO: [Labtools 27-2222] Launching hw_server...
INFO: [Labtools 27-2221] Launch Output:
....
[275] 执行: echo "🏁 ========== 全功能硬件测试完成 =========="
🏁 ========== 全功能硬件测试完成 ==========
[276] 执行: echo ""

[278] 执行: echo "📊 测试统计报告："
📊 测试统计报告：
[279] 执行: echo "  ✓ 环境验证测试     - 完成"
  ✓ 环境验证测试     - 完成
[280] 执行: echo "  ✓ FPGA烧写测试     - 完成"
  ✓ FPGA烧写测试     - 完成
[281] 执行: echo "  ✓ FPGA回读测试     - 完成"
  ✓ FPGA回读测试     - 完成
[282] 执行: echo "  ✓ Flash烧写测试    - 完成"
  ✓ Flash烧写测试    - 完成
[283] 执行: echo "  ✓ 多格式文件测试   - 完成"
  ✓ 多格式文件测试   - 完成
[284] 执行: echo "  ✓ 自定义TCL测试    - 完成"
  ✓ 自定义TCL测试    - 完成
[285] 执行: echo "  ✓ 快速操作测试     - 完成"
  ✓ 快速操作测试     - 完成
[286] 执行: echo "  ✓ 批量操作测试     - 完成"
  ✓ 批量操作测试     - 完成
[287] 执行: echo "  ✓ 性能测试         - 完成"
  ✓ 性能测试         - 完成
[288] 执行: echo "  ✓ 错误处理测试     - 完成"
  ✓ 错误处理测试     - 完成
[289] 执行: echo "  ✓ 高级功能测试     - 完成"
  ✓ 高级功能测试     - 完成
[290] 执行: echo "  ✓ 压力测试         - 完成"
  ✓ 压力测试         - 完成
[291] 执行: echo ""

[293] 执行: echo "📁 生成的文件和日志："
📁 生成的文件和日志：
[294] 执行: echo "  📄 程序日志: $PROGRAM_LOG"
  📄 程序日志: $PROGRAM_LOG
[295] 执行: echo "  📄 Journal: $PROGRAM_JOU"
  📄 Journal: $PROGRAM_JOU
[296] 执行: echo "  📄 回读文件: $READBACK_FILE"
  📄 回读文件: $READBACK_FILE
[297] 执行: echo "  📄 Flash日志: $FLASH_LOG"
  📄 Flash日志: $FLASH_LOG
[298] 执行: echo "  📄 自定义日志: $CUSTOM_LOG"
  📄 自定义日志: $CUSTOM_LOG
[299] 执行: echo "  📁 所有日志目录: $LOG_DIR"
  📁 所有日志目录: $LOG_DIR
[300] 执行: echo ""

[302] 执行: echo "🎯 硬件验证检查点："
🎯 硬件验证检查点：
[303] 执行: echo "  • FPGA板子LED状态变化  ✓"
  • FPGA板子LED状态变化  ✓
[304] 执行: echo "  • 多次烧写稳定性      ✓"
  • 多次烧写稳定性      ✓
[305] 执行: echo "  • Flash编程功能       ✓"
  • Flash编程功能       ✓
[306] 执行: echo "  • 回读验证功能        ✓"
  • 回读验证功能        ✓
[307] 执行: echo "  • 错误恢复能力        ✓"
  • 错误恢复能力        ✓
[308] 执行: echo ""

[310] 执行: echo "📈 性能评估："
📈 性能评估：
[311] 执行: echo "  • 单次烧写速度       - 查看performance.log"
  • 单次烧写速度       - 查看performance.log
[312] 执行: echo "  • 批量操作稳定性     - 查看batch*.log"
  • 批量操作稳定性     - 查看batch*.log
[313] 执行: echo "  • 连续操作可靠性     - 查看stress*.log"
  • 连续操作可靠性     - 查看stress*.log
[314] 执行: echo ""

[316] 执行: echo "🔧 建议的后续操作："
🔧 建议的后续操作：
[317] 执行: echo "  1. 检查所有日志文件，确认无错误"
  1. 检查所有日志文件，确认无错误
[318] 执行: echo "  2. 验证FPGA功能是否符合设计预期"
  2. 验证FPGA功能是否符合设计预期
[319] 执行: echo "  3. 测试不同的bit文件和Flash配置"
  3. 测试不同的bit文件和Flash配置
[320] 执行: echo "  4. 在生产环境中部署前进行长时间稳定性测试"
  4. 在生产环境中部署前进行长时间稳定性测试
[321] 执行: echo ""

[323] 执行: echo "🎉 恭喜！Vivado全功能硬件测试圆满完成！"
🎉 恭喜！Vivado全功能硬件测试圆满完成！
[324] 执行: echo "   所有核心功能都已验证，系统可以投入实际使用。"
   所有核心功能都已验证，系统可以投入实际使用。
[325] 执行: echo ""

[327] 执行: echo "📖 使用建议："
📖 使用建议：
[328] 执行: echo "  • 在自动化脚本中使用vivado_quick命令提高效率"
  • 在自动化脚本中使用vivado_quick命令提高效率
[329] 执行: echo "  • 定期使用vivado_test检查环境状态"
  • 定期使用vivado_test检查环境状态
[330] 执行: echo "  • 重要操作时启用详细日志记录"
  • 重要操作时启用详细日志记录
[331] 执行: echo "  • 批量操作时建议添加适当的延时"
  • 批量操作时建议添加适当的延时
```



# 三、开发规范

## 3.1 项目结构

项目整体分成GUI、CORE、CLI、RESOURCE四个部分

- GUI
  - 项目UI部分
  - COMPONENT
    - 自定义组件
  - PAGES
    - 每个标签页
- CORE
  - 主要功能，为GUI和shell提供api
  - 名称严格按照module_xx
- CLI
  - 各模块命令行参数解析文件；
  - 入口统一为main_shell.py。