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
  