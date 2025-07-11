# 一、执行

## 1.1 交互模式

直接双击或在控制台中，执行

```json
autoTestTool.exe
```

## 1.2 单命令模式

在控制台中，执行

```json
autoTestTool.exe -c "vccm --file C:/Users/DELL/Desktop/test_workspace/shell/bram_36e1_2_wf_0_a.rbt --vccm_values 105"
```

## 1.3 脚本模式

在控制台中，执行

```json
autoTestTool.exe myscript.txt
```

## 1.4 UI模式

在控制台中，执行

```shell
autoTestTool.exe -ui
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

## 2.4 电压查询配置

### 2.4.1 核心命令

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

## 2.5 vivado的tcl集成

### 2.5.1 核心命令

| 命令              | 功能        | 示例                                                         |
| ----------------- | ----------- | ------------------------------------------------------------ |
| `vivado_program`  | 烧写到FPGA  | `vivado_program -v $VIVADO_PATH -b design.bit`               |
| `vivado_flash`    | 烧写到Flash | `vivado_flash -v $VIVADO_PATH -b design.mcs -f mt25ql128-spi-x1_x2_x4` |
| `vivado_readback` | 从FPGA回读  | `vivado_readback -v $VIVADO_PATH -o readback.rbd`            |
| `vivado_custom`   | 执行TCL脚本 | `vivado_custom -v $VIVADO_PATH -t script.tcl`                |
| `vivado_test`     | 测试功能    | `vivado_test -v $VIVADO_PATH`                                |
| `vivado_help`     | 显示帮助    | `vivado_help`                                                |
| `vivado_quick`    | 快速操作    | `vivado_quick test $VIVADO_PATH`                             |
