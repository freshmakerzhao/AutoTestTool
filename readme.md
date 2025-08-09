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
### 2.1.1压缩位流
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

## 2.3 电压、时钟配置

### 2.3.1 端口号

- --port COM4
- 端口号可在设备管理器的 ”端口“ 中查看；
- 每次进行串口相关操作时，都需要指定串口号，如果执行过程中串口已连接，不会重复连接。如果串口未连接，会默认进行重连；

### 2.3.2 发送时钟配置

```shell
serial --port COM4 --clock_config_path "D:\a\b\c.txt"
```

- path必须被双引号包裹；
- 路径中的斜线可以是`'/'`、`'\'`、`'\\'`；

### 2.3.3 显示电压

```shell
serial --port COM4 --voltage_show
```

- 格式如下：

```
[CLISerialHandler Info] voltage is {'VCCO_0': '2620', 'VCCBRAM': '0900', 'VCCAUX': '1800', 'VCCINT': '0800', 'VCCO_16': '3300', 'VCCO_15': '3300', 'VCCO_14': '3300', 'VCCO_13': '3300', 'VCCO_34': '1500', 'MGTAVTT': '1200', 'MGTAVCC': '1000', 'VCCADC': '1', 'VCCREF': '0'}
```

### 2.3.4 配置电压

```shell
serial --port COM4 --voltage_set 2620 0900 1800 0800 3300 3300 3300 3300 1500 1200 1000 1 0
```

- 前11路严格限制元素长度，每个元素长度为4，后面两路长度为1
- 按照显示电压中的顺序进行电压配置，全部是整数，范围如下图：

![image-20250806212325009](./assets/image-20250806212325009.png)

## 2.4 Vivado相关功能

所有功能都支持设置超时中断时间：

- --timeout
  - 单位：秒

### 2.4.1 烧写bitstream

```
vivado --mode program --vivado_bin "E:\Application_Vivado\Vivado\2020.1\bin" --bit_path "C:\Users\DELL\Desktop\test_workspace\CLI_test\led_run.bit"
```

### 2.4.2 烧写flash

```shell
vivado --mode flash --vivado_bin "E:\Application_Vivado\Vivado\2020.1\bin" --bit_path "C:\Users\DELL\Desktop\test_workspace\CLI_test\led_run.bit" --flash_part "mt25ql128-spi-x1_x2_x4"

```

### 2.4.3 回读FPGA

```shell
vivado --mode readback --vivado_bin "E:\Application_Vivado\Vivado\2020.1\bin" --out_rbd_path "C:\Users\DELL\Desktop\test_workspace\CLI_test\readback.rbd"
```

### 2.4.4 仅对比回读是否成功（Only Compare）

```shell
# 特征值位流比对（special compare）
vivado --mode compare --mask_path "C:\Users\DELL\Desktop\test_workspace\vccm\for_vivado\00_55_AA_FF.msd" --readback_path "C:\Users\DELL\Desktop\test_workspace\vccm\for_vivado\00.rbd" --gold_path "C:\Users\DELL\Desktop\test_workspace\vccm\for_vivado\gold_00.rbt" --special "00" --vivado_bin "E:\Application_Vivado\Vivado\2020.1\bin"

# 功能位流比对（functional compare）
vivado --mode compare --mask_path "C:\Users\DELL\Desktop\test_workspace\vccm\for_vivado\led_run.msd" --readback_path "C:\Users\DELL\Desktop\test_workspace\vccm\for_vivado\led_run_readback.rbd" --gold_path "C:\Users\DELL\Desktop\test_workspace\vccm\for_vivado\gold_led_run.rbt" --vivado_bin "E:\Application_Vivado\Vivado\2020.1\bin"
```

### 2.4.5 执行自定义TCL（如ibert）

```shell
vivado --mode raw --vivado_bin "E:\Application_Vivado\Vivado\2020.1\bin" --tcl_path "E:\workspace\AutoTestTool\RESOURCE\SCRIPTS\demo\ibert_example_all.tcl"
```

- 可选参数
  - --tcl_args
    - 支持传参，空格断开