# 一、项目概述

## 1.1 主体结构

项目整体可以分成：

- CLI
- COMMON
- CORE
- GUI

核心思想是，一套功能代码（CORE），能够适配CLI（命令行）、GUI（用户界面）多种执行模式。

## 1.2 运行模式

- 交互模式
- 单命令模式
- 批处理模式
- 窗口模式

其中交互、单命令、批处理由CLI转发到CORE，窗口模式直接调用CORE中的内容。

# 二、CLI

CLI（command-line interface）命令行接口，当程序以交互模式、单任务模式、批处理模式运行时，通过CLI转发到CORE中。

细分：

- main_shell
- cli_base
- cli_vccm
- cli_xxxx

....

其中，main_shell解析启动模式和命令，将不同类型的命令划分到不同的解析器中，不同解析器将命令拆解后，再通过命令中的执行模块找到对应的cli_xxx。

# 三、GUI

GUI（Graphical User Interface）图形用户界面，当程序以窗口模式运行时，通过GUI解析用户操作并呈现结果。

细分：

- COMPONENT
  - collapsible
    - 折叠模块，自定义的UI组件；
    - 如果需要添加其他的自定义UI组件，可以与collapsible同级；
  - thread_utils
    - 异步执行模块，GUI部分所有调用CORE的位置，都使用该模块进行调用；
- PAGES
  - page_a_xxx
  - page_b_xxx
  - ...
- app
  - 管理整个GUI部分的page_x_xxx的生命周期

# 四、CORE

- SERIAL
  - 串口类，所有串口操作均在这里。
- VIVADO
  - Vivado工具类，所有与Vivado交互的操作均在这里。
- module_xxx
  - 不同模块的处理类
- process_xxx
  - 不同模块的处理类
- run_xxx
  - 不同模块的处理类

所有的具体操作，均在CORE中，CLI和UI调用CORE中的具体函数。

# 五、COMMON

这里存放全局的工具函数、配置类、数据结构。















