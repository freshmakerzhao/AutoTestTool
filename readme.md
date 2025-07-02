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
  
实际调用流程：
- UI
  - 用户在页面点击执行后，在page层将各项执行参数汇总，传递给core，由core做具体操作；
- CLI（命令行接口）
  - 用户通过控制台执行时，由main_shell做分配，分配给cli_xxx模块做参数解析，再传递给core做具体操作。
