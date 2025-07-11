import cmd
import shlex
import logging
import sys
import os
import json
import re
import argparse
import time
from datetime import datetime

from CLI.cli_vccm import run_vccm_cli
from CLI.cli_base import run_base_cli
from CLI.cli_moni import run_moni_cli
# 导入异步监听接口函数
from CLI.cli_moni import (
    start_monitor, stop_monitor, get_monitor_status, show_cached_data,
    enable_logging, disable_logging, save_cache_to_file, clear_cache, is_monitoring
)
# 导入电压控制接口函数
from CLI.cli_voltage import (
    run_voltage_cli, get_voltage_status_from_monitor, set_voltage_to_monitor, 
    get_voltage_specs, is_voltage_available, validate_voltage_values, VOLTAGE_SPECS
)
# 导入vivado tcl命令行接口
"""
vivado_program    # 烧写到FPGA  
vivado_flash      # 烧写到Flash
vivado_readback   # 从FPGA回读
vivado_custom     # 执行TCL脚本
vivado_test       # 测试功能
vivado_help       # 显示帮助
vivado_quick      # 快速操作
"""
from CLI.cli_vivado import (
    vivado_program_cli, vivado_flash_cli, vivado_readback_cli, 
    vivado_custom_cli, vivado_test_cli, print_vivado_help,
    get_supported_flash_parts
)

class AutoTestToolShell(cmd.Cmd):
    intro = "AutoTestTool Shell，输入 help 查看可用命令，输入 exit 退出。"
    prompt = "(AutoTestTool) "

    def __init__(self):
        super().__init__()
        self.variables = {}

    def do_base(self, line):
        """
        基础功能：烧录/分析等
        示例：base --file a.bit --device MC1P110 --CRC
        支持变量替换，如 --file $FILENAME
        """
        line = self._substitute_variables(line)
        parser = self.get_base_parser()
        try:
            args = parser.parse_args(shlex.split(line))
            run_base_cli(args)
        except SystemExit:
            pass
        except Exception as e:
            print(f"执行 base 命令出错: {e}")

    # --- VCCM ---
    def do_vccm(self, line):
        """
        VCCM 电压批处理
        示例：vccm --file in.bit --vccm_values 105 110
        支持变量替换，如 --file $FILENAME
        """
        line = self._substitute_variables(line)
        parser = self.get_vccm_parser()
        try:
            args = parser.parse_args(shlex.split(line))
            run_vccm_cli(args)
        except SystemExit:
            pass
        except Exception as e:
            print(f"执行 vccm 命令出错: {e}")

    # --- 串口监视器 ---
    def do_moni(self, line):
        """
        串口监视器功能
        
        示例:
          moni ports                           # 列出端口
          moni test COM3 115200               # 测试连接
          moni listen COM3 115200             # 监听模式
          moni interactive COM3 115200        # 交互模式
          moni send COM3 115200 "hello"       # 发送文本
          moni stats COM3 115200              # 获取统计信息
          
          # 异步监听功能
          moni start_monitor COM3 115200      # 开始后台监听
          moni stop_monitor                   # 停止后台监听
          moni monitor_status                 # 查看监听状态
          moni show_data 10                   # 显示最近10条数据
          moni enable_log test.log            # 开启日志记录
          moni disable_log                    # 关闭日志记录
        
        支持变量替换，如 moni test $PORT $BAUDRATE
        """
        line = self._substitute_variables(line)
        try:
            args_list = shlex.split(line) if line.strip() else []
            run_moni_cli(args_list)
        except Exception as e:
            print(f"执行 moni 命令出错: {e}")

    # =============================================================================
    # 异步串口监听命令 (调用CLI层接口)
    # =============================================================================
    
    def do_start_monitor(self, line):
        """
        开始后台串口监听
        
        示例:
          start_monitor COM3 115200                    # 开始监听，数据缓存在内存
          start_monitor COM3 115200 --log data.log    # 开始监听并记录日志
          start_monitor $PORT $BAUDRATE --log $LOGFILE # 使用变量
        
        参数:
          port        : 串口号
          baudrate    : 波特率
          --log FILE  : 可选，日志文件路径
        """
        line = self._substitute_variables(line)
        parser = argparse.ArgumentParser(prog="start_monitor", add_help=False)
        parser.add_argument("port", help="串口号")
        parser.add_argument("baudrate", type=int, help="波特率")
        parser.add_argument("--log", type=str, help="日志文件路径")
        
        try:
            args = parser.parse_args(shlex.split(line))
            start_monitor(args.port, args.baudrate, args.log)
        except (SystemExit, ValueError):
            print("用法: start_monitor <port> <baudrate> [--log <file>]")
        except Exception as e:
            print(f"❌ 启动监听失败: {e}")

    def do_stop_monitor(self, line):
        """
        停止后台串口监听
        
        示例:
          stop_monitor
        """
        stop_monitor()

    def do_monitor_status(self, line):
        """
        查看监听状态
        
        示例:
          monitor_status
        """
        status = get_monitor_status()
        
        if status['is_monitoring']:
            duration = datetime.now() - status['start_time'] if status['start_time'] else None
            print("📊 监听状态:")
            print(f"  状态: 运行中")
            print(f"  端口: {status['port']}@{status['baudrate']}")
            print(f"  运行时长: {duration}")
            print(f"  接收数据: {status['total_received']} 条")
            print(f"  缓存数据: {status['cached_count']}/1000 条")
            print(f"  文件日志: {'启用' if status['log_enabled'] else '禁用'}")
        else:
            print("📊 监听状态: 未运行")

    def do_show_data(self, line):
        """
        显示缓存的监听数据
        
        示例:
          show_data           # 显示所有缓存数据
          show_data 10        # 显示最近10条数据
        """
        try:
            count = None
            if line.strip().isdigit():
                count = int(line.strip())
            
            data_list = show_cached_data(count)
            
            if not data_list:
                print("暂无缓存数据")
                return
            
            print(f"📋 缓存数据 (显示 {len(data_list)} 条):")
            print("-" * 80)
            
            for data in data_list:
                timestamp = data['timestamp'].strftime('%H:%M:%S.%f')[:-3]
                print(f"[{timestamp}] {data['raw_text']}")
                    
        except Exception as e:
            print(f"❌ 显示数据失败: {e}")

    def do_save_log(self, line):
        """
        保存缓存数据到文件
        
        示例:
          save_log data.txt           # 保存所有缓存数据
          save_log $LOGFILE           # 使用变量
        """
        line = self._substitute_variables(line)
        if not line.strip():
            print("用法: save_log <filename>")
            return
            
        filename = line.strip()
        save_cache_to_file(filename)

    def do_enable_log(self, line):
        """
        动态开启文件日志记录
        
        示例:
          enable_log data.log         # 开启日志记录
          enable_log $LOGFILE         # 使用变量
        """
        line = self._substitute_variables(line)
        if not line.strip():
            print("用法: enable_log <filename>")
            return
            
        filename = line.strip()
        enable_logging(filename)

    def do_disable_log(self, line):
        """
        动态关闭文件日志记录
        
        示例:
          disable_log
        """
        disable_logging()

    def do_clear_cache(self, line):
        """
        清空数据缓存
        
        示例:
          clear_cache
        """
        clear_cache()

    def do_sleep(self, line):
        """
        暂停执行指定秒数 (用于脚本中的等待)
        
        示例:
          sleep 5             # 等待5秒
          sleep $WAIT_TIME    # 使用变量
        """
        line = self._substitute_variables(line)
        try:
            seconds = float(line.strip())
            print(f"⏸️  等待 {seconds} 秒...")
            time.sleep(seconds)
            print("✓ 等待结束")
        except ValueError:
            print("用法: sleep <秒数>")
        except Exception as e:
            print(f"❌ 等待失败: {e}")

    # 设置变量
    def do_set(self, line):
        """set 变量，如 set FILENAME test.bit"""
        try:
            k, v = line.split(None, 1)
            # self.variables[k] = v
            self.variables[k] = self._substitute_variables(v)
            print(f"${k} = {v}")
        except ValueError:
            print("用法：set 变量名 变量值")

    # 输出变量信息
    def do_echo(self, line):
        """echo 变量，如 echo $FILENAME"""
        for token in shlex.split(line):
            if token.startswith("$"):
                v = token[1:]
                print(self.variables.get(v, ""))
            else:
                print(token, end=" ")
        print()

    def do_run_script(self, filename):
        """批量执行命令脚本（每行一条命令）"""
        if not os.path.isfile(filename):
            print(f"文件不存在: {filename}")
            return
        try:
            # 指定UTF-8编码读取文件，避免中文编码问题
            with open(filename, 'r', encoding='utf-8') as f:
                for lineno, line in enumerate(f, 1):
                    line = line.strip()
                    # 脚本中可以写注释，用井号开头
                    if not line or line.startswith('#'):
                        continue
                    try:
                        print(f"[{lineno:03d}] 执行: {line}")
                        self.onecmd(line)
                    except Exception as e:
                        print(f"第{lineno}行命令出错: {e}")
                        # 询问是否继续执行
                        if input("是否继续执行? (y/n): ").lower() != 'y':
                            break
        except UnicodeDecodeError as e:
            print(f"文件编码错误: {e}")
            print("请确保脚本文件使用UTF-8编码保存")
        except Exception as e:
            print(f"读取脚本出错: {e}")

    def do_exit(self, arg):
        """退出 shell"""
        # 确保在退出前停止监听
        if is_monitoring():
            print("正在停止后台监听...")
            stop_monitor()
        print("Goodbye!")
        return True

    # --- 变量支持，提取每个line中使用的变量 ---
    def _substitute_variables(self, line):
        def replacer(match):
            var = match.group(1) or match.group(2)
            return self.variables.get(var, "")
        return re.sub(r"\$(\w+)|\$\{(\w+)\}", replacer, line)

    # --- 参数补全示例 ---
    def complete_set(self, text, line, begidx, endidx):
        # 补全已有变量名
        return [k for k in self.variables if k.startswith(text)]
    # --- 输出参数 ---
    def complete_echo(self, text, line, begidx, endidx):
        return [f"${k}" for k in self.variables if k.startswith(text.replace("$", ""))]

    # --- moni 命令自动补全 ---
    def complete_moni(self, text, line, begidx, endidx):
        """moni 命令自动补全"""
        subcommands = ["ports", "test", "listen", "interactive", "send", "stats", 
                      "start_monitor", "stop_monitor", "monitor_status", "show_data", 
                      "enable_log", "disable_log", "save_log", "clear_cache"]
        words = line.split()
        
        if len(words) <= 2:  # 补全子命令
            return [cmd for cmd in subcommands if cmd.startswith(text)]
        return []

    # --- 命令参数定义 ---
    def get_vccm_parser(self):
        parser = argparse.ArgumentParser(prog="vccm")
        parser.add_argument('--file', type=str)
        parser.add_argument('--project', type=str)
        parser.add_argument('--vccm_values', type=int, nargs='+')
        return parser
    
    def get_base_parser(self):
        parser = argparse.ArgumentParser(prog="base")
        parser.add_argument('--file', required=True)
        parser.add_argument('--device', default="MC1P110")
        parser.add_argument('--file_suffix', type=str)
        parser.add_argument('--PCIE', action='store_true')
        parser.add_argument('--GTP', action='store_true')
        parser.add_argument('--CRC', action='store_true')
        parser.add_argument('--COMPRESS', action='store_true')
        parser.add_argument('--TRIM', action='store_true')
        parser.add_argument('--DELETE_GHIGH', action='store_true')
        parser.add_argument('--readback_refresh', type=str)
        parser.add_argument('--timer_refresh', type=str)
        return parser
    
    def do_voltage(self, line):
        """
        MC1P110电压控制功能 (基于串口监听服务)
        
        使用前提：必须先启动串口监听
          start_monitor COM3 115200        # 启动串口监听
        
        示例:
          voltage status                   # 显示电压状态(优先缓存)
          voltage status --live            # 主动查询电压状态
          voltage set --defaults           # 设置默认电压
          voltage set --values 3300 1000 1800 1000 3300 3300 3300 3300 1500 1200 1000  # 设置指定电压
          voltage specs                    # 显示MC1P110电压规格
          voltage test                     # 测试电压功能
          voltage interactive              # 交互式设置
        
        支持变量替换，如 voltage set --values $V1 $V2 $V3 ...
        """
        line = self._substitute_variables(line)
        try:
            args_list = shlex.split(line) if line.strip() else []
            run_voltage_cli(args_list)
        except Exception as e:
            print(f"执行 voltage 命令出错: {e}")

    # =============================================================================
    # 电压控制快捷命令 (基于MC1P110规格)
    # =============================================================================
    
    def do_voltage_status(self, line):
        """
        快速显示电压状态
        
        使用前提：串口监听必须已启动
        
        示例:
          voltage_status                   # 显示电压状态(优先缓存)
          voltage_status --live            # 主动查询电压状态
          voltage_status --max-age 30      # 使用最大30秒的缓存数据
        
        参数:
          --live      : 主动查询而非使用缓存
          --max-age   : 缓存数据最大年龄(秒)，默认10秒
          --format    : 输出格式(table/json)，默认table
        """
        line = self._substitute_variables(line)
        parser = argparse.ArgumentParser(prog="voltage_status", add_help=False)
        parser.add_argument("--live", action="store_true", help="主动查询")
        parser.add_argument("--max-age", type=int, default=10, help="缓存最大年龄")
        parser.add_argument("--format", choices=["table", "json"], default="table", help="输出格式")
        
        try:
            args = parser.parse_args(shlex.split(line))
            
            if not is_voltage_available():
                print("❌ 串口监听未启动，请先执行: start_monitor <port> <baudrate>")
                return
                
            status = get_voltage_status_from_monitor(
                use_cache=not args.live, 
                max_age=args.max_age
            )
            
            if status and status['success']:
                if args.format == "json":
                    import json
                    print(json.dumps(status, indent=2, ensure_ascii=False, default=str))
                else:
                    print("✓ 电压状态获取成功:")
                    _print_voltage_status_simple(status)
            else:
                error_msg = status.get('error', '未知错误') if status else '获取失败'
                print(f"❌ 电压状态获取失败: {error_msg}")
                
        except (SystemExit, ValueError):
            print("用法: voltage_status [--live] [--max-age <seconds>] [--format table|json]")
        except Exception as e:
            print(f"❌ 获取电压状态失败: {e}")

    def do_voltage_set(self, line):
        """
        快速设置电压值
        
        使用前提：串口监听必须已启动
        
        示例:
          voltage_set --defaults                        # 设置默认值
          voltage_set --values 3300 1000 1800 1000 3300 3300 3300 3300 1500 1200 1000  # 设置指定值
          voltage_set --values $V1 $V2 $V3 $V4 $V5 $V6 $V7 $V8 $V9 $V10 $V11  # 使用变量
        
        参数:
          --defaults  : 使用MC1P110默认电压值
          --values    : 指定11路电压值 (mV)，顺序固定
          --vccadc    : VCCADC使能 (默认True)
          --vccref    : VCCREF使能 (默认True)
          --verify    : 设置后验证
        """
        line = self._substitute_variables(line)
        parser = argparse.ArgumentParser(prog="voltage_set", add_help=False)
        parser.add_argument("--defaults", action="store_true", help="使用默认电压值")
        parser.add_argument("--values", type=int, nargs=11, help="11路电压值(mV)")
        parser.add_argument("--vccadc", type=bool, default=True, help="VCCADC使能")
        parser.add_argument("--vccref", type=bool, default=True, help="VCCREF使能")
        parser.add_argument("--verify", action="store_true", help="设置后验证")
        
        try:
            args = parser.parse_args(shlex.split(line))
            
            if not is_voltage_available():
                print("❌ 串口监听未启动，请先执行: start_monitor <port> <baudrate>")
                return
            
            # 确定电压值
            if args.defaults:
                values = [spec[1] for spec in VOLTAGE_SPECS]  # 默认值
                print("📝 使用MC1P110默认电压值")
            elif args.values:
                values = args.values
                print(f"📝 使用指定电压值")
            else:
                print("❌ 必须指定 --defaults 或 --values")
                return
            
            # 验证电压值
            is_valid, corrected_values, errors = validate_voltage_values(values)
            if not is_valid:
                print("❌ 电压值验证失败:")
                for error in errors:
                    print(f"  • {error}")
                return
            
            # 显示校正信息
            for i, (original, corrected) in enumerate(zip(values, corrected_values)):
                if original != corrected:
                    name = VOLTAGE_SPECS[i][0]
                    print(f"📏 {name}: {original}mV → {corrected}mV (步进校正)")
            
            success = set_voltage_to_monitor(corrected_values, args.vccadc, args.vccref)
            
            if success:
                print("✓ 电压设置成功")
                
                if args.verify:
                    print("🔍 验证设置结果...")
                    time.sleep(2)
                    status = get_voltage_status_from_monitor(use_cache=True, max_age=5)
                    if status and status['success']:
                        _print_voltage_status_simple(status)
                    else:
                        print("⚠️  验证读取失败")
            else:
                print("❌ 电压设置失败")
                
        except (SystemExit, ValueError):
            print("用法: voltage_set [--defaults | --values v1 v2 ... v11] [--verify]")
        except Exception as e:
            print(f"❌ 设置电压失败: {e}")

    def do_voltage_specs(self, line):
        """
        显示MC1P110电压规格信息
        
        示例:
          voltage_specs                    # 显示完整规格
        """
        specs = get_voltage_specs()
        print("📋 MC1P110电压规格:")
        print("=" * 90)
        print(f"{'Bank名称':<12} {'默认值(mV)':<12} {'最大值(mV)':<12} {'最小值(mV)':<12} {'步进值(mV)':<12}")
        print("-" * 90)
        
        for name, default, max_val, min_val, step in specs:
            print(f"{name:<12} {default:<12} {max_val:<12} {min_val:<12} {step:<12}")
        
        print("-" * 90)
        print("使能控制:")
        print("  • VCCADC: 模拟电源使能控制 (1=enable, 0=disable)")
        print("  • VCCREF: 参考电源使能控制 (1=enable, 0=disable)")
        print("")
        print("重要说明:")
        print("  • 11路电压顺序固定，不可调整")
        print("  • 超出范围的参数将保持原值不变")
        print("  • 非步进值将自动校正为最近的有效值")
        print("  • 配置后设备会立即返回实际配置的参数")

    def do_voltage_test(self, line):
        """
        测试电压功能
        
        使用前提：串口监听必须已启动
        
        示例:
          voltage_test                     # 测试电压读取和设置
        """
        try:
            if not is_voltage_available():
                print("❌ 串口监听未启动，请先执行: start_monitor <port> <baudrate>")
                return
            
            print("🧪 开始MC1P110电压功能测试")
            
            # 测试1: 读取当前电压
            print("\n📖 测试1: 读取当前电压状态")
            status = get_voltage_status_from_monitor()
            if status and status['success']:
                print("✓ 读取成功")
                _print_voltage_status_simple(status)
            else:
                error_msg = status.get('error', '获取失败') if status else '获取失败'
                print(f"❌ 读取失败: {error_msg}")
                return
            
            # 测试2: 设置默认电压
            print("\n📝 测试2: 设置默认电压")
            default_values = [spec[1] for spec in VOLTAGE_SPECS]
            print(f"默认值: {default_values}")
            
            success = set_voltage_to_monitor(default_values)
            
            if success:
                print("✓ 设置成功")
                time.sleep(2)
                
                # 验证设置结果
                status = get_voltage_status_from_monitor(use_cache=True, max_age=5)
                if status and status['success']:
                    print("🔍 验证结果:")
                    _print_voltage_status_simple(status)
                else:
                    print("⚠️  验证读取失败")
            else:
                print("❌ 设置失败")
            
            print("\n✓ 电压功能测试完成")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")

    def do_voltage_check(self, line):
        """
        检查电压功能可用性和状态
        
        示例:
          voltage_check                    # 检查电压功能状态
        """
        try:
            print("📊 电压功能检查:")
            
            # 检查串口监听状态
            if is_voltage_available():
                from CLI.cli_moni import get_monitor_status
                monitor_status = get_monitor_status()
                
                print(f"  串口监听: ✓ 运行中")
                print(f"  连接端口: {monitor_status['port']}@{monitor_status['baudrate']}")
                print(f"  运行时长: {datetime.now() - monitor_status['start_time'] if monitor_status['start_time'] else 'N/A'}")
                
                # 尝试获取电压状态验证通信
                status = get_voltage_status_from_monitor(use_cache=True, max_age=30)
                if status and status['success']:
                    print(f"  设备通信: ✓ 正常")
                    print(f"  数据来源: {status['data_source']}")
                    print(f"  数据时间: {status['timestamp'].strftime('%H:%M:%S') if status.get('timestamp') else 'N/A'}")
                    print(f"  电压路数: {len(status.get('voltages', {}))}")
                else:
                    print(f"  设备通信: ⚠️  无最近数据")
                    print(f"  建议: 执行 voltage_status --live 主动查询")
                
            else:
                print(f"  串口监听: ❌ 未运行")
                print(f"  解决方法: 执行 start_monitor <port> <baudrate>")
                
            # 显示电压规格摘要
            print(f"\n📋 MC1P110电压规格摘要:")
            print(f"  支持电压: 11路 + 2路使能控制")
            print(f"  电压范围: 400mV ~ 3350mV")
            print(f"  步进精度: 5mV / 10mV")
            
        except Exception as e:
            print(f"❌ 检查失败: {e}")

    def do_voltage_quick(self, line):
        """
        快速电压操作
        
        示例:
          voltage_quick status             # 快速查看状态
          voltage_quick defaults           # 快速设置默认值
          voltage_quick check              # 快速检查功能
        
        参数:
          status      : 显示电压状态
          defaults    : 设置默认电压值
          check       : 检查功能可用性
        """
        line = self._substitute_variables(line).strip()
        
        if not line:
            print("用法: voltage_quick <status|defaults|check>")
            return
        
        action = line.lower()
        
        try:
            if action == "status":
                if not is_voltage_available():
                    print("❌ 串口监听未启动")
                    return
                status = get_voltage_status_from_monitor()
                if status and status['success']:
                    _print_voltage_status_simple(status, compact=True)
                else:
                    print("❌ 获取状态失败")
                    
            elif action == "defaults":
                if not is_voltage_available():
                    print("❌ 串口监听未启动")
                    return
                default_values = [spec[1] for spec in VOLTAGE_SPECS]
                success = set_voltage_to_monitor(default_values)
                if success:
                    print("✓ 默认电压设置成功")
                else:
                    print("❌ 设置失败")
                    
            elif action == "check":
                available = is_voltage_available()
                print(f"电压功能: {'✓ 可用' if available else '❌ 不可用'}")
                if available:
                    from CLI.cli_moni import get_monitor_status
                    status = get_monitor_status()
                    print(f"串口: {status['port']}@{status['baudrate']}")
                    
            else:
                print(f"❌ 未知操作: {action}")
                print("支持的操作: status, defaults, check")
                
        except Exception as e:
            print(f"❌ 操作失败: {e}")


    def do_vivado_program(self, line):
        """
        烧写bitstream到FPGA
        
        示例:
          vivado_program -v "C:\\Xilinx\\Vivado\\2023.1\\bin" -b "design.bit"
          vivado_program -v $VIVADO_PATH -b $BITSTREAM_FILE -l "program.log"
        
        参数:
          -v, --vivado-path   : Vivado bin目录路径 (必需)
          -b, --bitstream     : bitstream文件路径 (必需)
          -l, --log-file      : 日志文件路径 (可选，默认NUL)
          -j, --journal-file  : Journal文件路径 (可选，默认NUL)
        
        支持变量替换，如 -v $VIVADO_PATH -b $BITSTREAM_FILE
        """
        line = self._substitute_variables(line)
        parser = argparse.ArgumentParser(prog="vivado_program", add_help=False)
        parser.add_argument("-v", "--vivado-path", required=True, help="Vivado bin目录路径")
        parser.add_argument("-b", "--bitstream", required=True, help="bitstream文件路径")
        parser.add_argument("-l", "--log-file", default="NUL", help="日志文件路径")
        parser.add_argument("-j", "--journal-file", default="NUL", help="Journal文件路径")
        
        try:
            args = parser.parse_args(shlex.split(line))
            vivado_program_cli(
                vivado_path=args.vivado_path,
                bitstream_file=args.bitstream,
                log_file=args.log_file,
                journal_file=args.journal_file
            )
        except (SystemExit, ValueError):
            print("用法: vivado_program -v <vivado_path> -b <bitstream_file> [-l <log_file>] [-j <journal_file>]")
        except Exception as e:
            print(f"❌ 烧写命令执行失败: {e}")

    def do_vivado_flash(self, line):
        """
        烧写bitstream到Flash
        
        示例:
          vivado_flash -v $VIVADO_PATH -b "design.mcs" -f "mt25ql128-spi-x1_x2_x4"
          vivado_flash -v $VIVADO_PATH -b $MCS_FILE -f $FLASH_PART
        
        参数:
          -v, --vivado-path   : Vivado bin目录路径 (必需)
          -b, --bitstream     : bitstream文件路径 (必需)
          -f, --flash-part    : Flash器件型号 (必需)
          -l, --log-file      : 日志文件路径 (可选，默认NUL)
          -j, --journal-file  : Journal文件路径 (可选，默认NUL)
        
        支持的Flash型号: 28f00ap30t-bpi-x16, 28f512p30t-bpi-x16, 28f256p30t-bpi-x16,
                       28f512p30e-bpi-x16, mt28gu256aax1e-bpi-x16, mt28fw02gb-bpi-x16,
                       mt25ql128-spi-x1_x2_x4
        """
        line = self._substitute_variables(line)
        parser = argparse.ArgumentParser(prog="vivado_flash", add_help=False)
        parser.add_argument("-v", "--vivado-path", required=True, help="Vivado bin目录路径")
        parser.add_argument("-b", "--bitstream", required=True, help="bitstream文件路径")
        parser.add_argument("-f", "--flash-part", required=True, 
                          choices=get_supported_flash_parts(), help="Flash器件型号")
        parser.add_argument("-l", "--log-file", default="NUL", help="日志文件路径")
        parser.add_argument("-j", "--journal-file", default="NUL", help="Journal文件路径")
        
        try:
            args = parser.parse_args(shlex.split(line))
            vivado_flash_cli(
                vivado_path=args.vivado_path,
                bitstream_file=args.bitstream,
                flash_part=args.flash_part,
                log_file=args.log_file,
                journal_file=args.journal_file
            )
        except (SystemExit, ValueError):
            print("用法: vivado_flash -v <vivado_path> -b <bitstream_file> -f <flash_part>")
            print(f"支持的Flash型号: {', '.join(get_supported_flash_parts())}")
        except Exception as e:
            print(f"❌ Flash烧写命令执行失败: {e}")

    def do_vivado_readback(self, line):
        """
        从FPGA回读bitstream
        
        示例:
          vivado_readback -v $VIVADO_PATH -o "readback.rbd"
          vivado_readback -v $VIVADO_PATH -o $READBACK_FILE -l "readback.log"
        
        参数:
          -v, --vivado-path   : Vivado bin目录路径 (必需)
          -o, --output        : 回读文件保存路径 (必需)
          -l, --log-file      : 日志文件路径 (可选，默认NUL)
          -j, --journal-file  : Journal文件路径 (可选，默认NUL)
        
        支持变量替换，如 -v $VIVADO_PATH -o $READBACK_FILE
        """
        line = self._substitute_variables(line)
        parser = argparse.ArgumentParser(prog="vivado_readback", add_help=False)
        parser.add_argument("-v", "--vivado-path", required=True, help="Vivado bin目录路径")
        parser.add_argument("-o", "--output", required=True, help="回读文件保存路径")
        parser.add_argument("-l", "--log-file", default="NUL", help="日志文件路径")
        parser.add_argument("-j", "--journal-file", default="NUL", help="Journal文件路径")
        
        try:
            args = parser.parse_args(shlex.split(line))
            vivado_readback_cli(
                vivado_path=args.vivado_path,
                output_file=args.output,
                log_file=args.log_file,
                journal_file=args.journal_file
            )
        except (SystemExit, ValueError):
            print("用法: vivado_readback -v <vivado_path> -o <output_file>")
        except Exception as e:
            print(f"❌ 回读命令执行失败: {e}")

    def do_vivado_custom(self, line):
        """
        执行自定义TCL脚本
        
        示例:
          vivado_custom -v $VIVADO_PATH -t "my_script.tcl"
          vivado_custom -v $VIVADO_PATH -t $TCL_SCRIPT --tcl-args "arg1" "arg2"
        
        参数:
          -v, --vivado-path   : Vivado bin目录路径 (必需)
          -t, --tcl-script    : TCL脚本文件路径 (必需)
          --tcl-args          : TCL脚本参数 (可选)
          -l, --log-file      : 日志文件路径 (可选，默认NUL)
          -j, --journal-file  : Journal文件路径 (可选，默认NUL)
        
        支持变量替换，如 -v $VIVADO_PATH -t $TCL_SCRIPT
        """
        line = self._substitute_variables(line)
        parser = argparse.ArgumentParser(prog="vivado_custom", add_help=False)
        parser.add_argument("-v", "--vivado-path", required=True, help="Vivado bin目录路径")
        parser.add_argument("-t", "--tcl-script", required=True, help="TCL脚本文件路径")
        parser.add_argument("--tcl-args", nargs="*", help="TCL脚本参数")
        parser.add_argument("-l", "--log-file", default="NUL", help="日志文件路径")
        parser.add_argument("-j", "--journal-file", default="NUL", help="Journal文件路径")
        
        try:
            args = parser.parse_args(shlex.split(line))
            vivado_custom_cli(
                vivado_path=args.vivado_path,
                tcl_script=args.tcl_script,
                tcl_args=args.tcl_args,
                log_file=args.log_file,
                journal_file=args.journal_file
            )
        except (SystemExit, ValueError):
            print("用法: vivado_custom -v <vivado_path> -t <tcl_script> [--tcl-args arg1 arg2 ...]")
        except Exception as e:
            print(f"❌ 自定义TCL命令执行失败: {e}")

    def do_vivado_test(self, line):
        """
        测试Vivado功能 (验证安装和配置)
        
        示例:
          vivado_test -v $VIVADO_PATH
          vivado_test -v "C:\\Xilinx\\Vivado\\2023.1\\bin"
        
        参数:
          -v, --vivado-path   : Vivado bin目录路径 (必需)
        
        测试内容:
          • 验证Vivado安装路径
          • 检查vivado.bat存在性
          • 验证TCL脚本文件
          • 提供硬件连接建议
        """
        line = self._substitute_variables(line)
        parser = argparse.ArgumentParser(prog="vivado_test", add_help=False)
        parser.add_argument("-v", "--vivado-path", required=True, help="Vivado bin目录路径")
        
        try:
            args = parser.parse_args(shlex.split(line))
            vivado_test_cli(args.vivado_path)
        except (SystemExit, ValueError):
            print("用法: vivado_test -v <vivado_path>")
        except Exception as e:
            print(f"❌ 测试命令执行失败: {e}")

    def do_vivado_help(self, line):
        """
        显示Vivado功能帮助信息
        
        示例:
          vivado_help
        
        内容包括:
          • 支持的操作列表
          • Flash器件型号
          • 使用示例
          • 常用技巧
        """
        print_vivado_help()

    def do_vivado_quick(self, line):
        """
        Vivado快速操作
        
        示例:
          vivado_quick program $VIVADO_PATH design.bit           # 快速烧写
          vivado_quick readback $VIVADO_PATH readback.rbd        # 快速回读
          vivado_quick test $VIVADO_PATH                         # 快速测试
        
        支持的操作:
          program <vivado_path> <bitstream>     : 快速烧写
          readback <vivado_path> <output>       : 快速回读
          test <vivado_path>                    : 快速测试
        """
        line = self._substitute_variables(line).strip()
        
        if not line:
            print("用法: vivado_quick <program|readback|test> <参数...>")
            print("详细说明: help vivado_quick")
            return
        
        parts = shlex.split(line)
        if len(parts) < 2:
            print("❌ 参数不足")
            return
        
        action = parts[0].lower()
        
        try:
            if action == "program":
                if len(parts) < 3:
                    print("用法: vivado_quick program <vivado_path> <bitstream>")
                    return
                vivado_path, bitstream = parts[1], parts[2]
                vivado_program_cli(vivado_path, bitstream)
                
            elif action == "readback":
                if len(parts) < 3:
                    print("用法: vivado_quick readback <vivado_path> <output>")
                    return
                vivado_path, output = parts[1], parts[2]
                vivado_readback_cli(vivado_path, output)
                
            elif action == "test":
                if len(parts) < 2:
                    print("用法: vivado_quick test <vivado_path>")
                    return
                vivado_path = parts[1]
                vivado_test_cli(vivado_path)
                    
            else:
                print(f"❌ 未知操作: {action}")
                print("支持的操作: program, readback, test")
                
        except Exception as e:
            print(f"❌ 快速操作失败: {e}")
    # =============================================================================
    # Vivado 命令自动补全功能 (在现有补全方法之后添加)
    # =============================================================================

    def complete_vivado_program(self, text, line, begidx, endidx):
        """vivado_program 命令自动补全"""
        return [f"${k}" for k in self.variables if k.startswith(text.replace("$", ""))]

    def complete_vivado_flash(self, text, line, begidx, endidx):
        """vivado_flash 命令自动补全"""
        if "--flash-part" in line or "-f" in line:
            return [part for part in get_supported_flash_parts() if part.startswith(text)]
        return [f"${k}" for k in self.variables if k.startswith(text.replace("$", ""))]

    def complete_vivado_readback(self, text, line, begidx, endidx):
        """vivado_readback 命令自动补全"""
        return [f"${k}" for k in self.variables if k.startswith(text.replace("$", ""))]

    def complete_vivado_custom(self, text, line, begidx, endidx):
        """vivado_custom 命令自动补全"""
        return [f"${k}" for k in self.variables if k.startswith(text.replace("$", ""))]

    def complete_vivado_test(self, text, line, begidx, endidx):
        """vivado_test 命令自动补全"""
        return [f"${k}" for k in self.variables if k.startswith(text.replace("$", ""))]

    def complete_vivado_quick(self, text, line, begidx, endidx):
        """vivado_quick 命令自动补全"""
        words = line.split()
        
        if len(words) <= 2:  # 补全操作类型
            actions = ["program", "readback", "test"]
            return [action for action in actions if action.startswith(text)]
        else:  # 补全变量
            return [f"${k}" for k in self.variables if k.startswith(text.replace("$", ""))]

    # --- voltage 命令自动补全 ---
    def complete_voltage(self, text, line, begidx, endidx):
        """voltage 命令自动补全"""
        subcommands = ["status", "set", "specs", "test", "interactive"]
        words = line.split()
        
        if len(words) <= 2:  # 补全子命令
            return [cmd for cmd in subcommands if cmd.startswith(text)]
        return []

    def complete_voltage_set(self, text, line, begidx, endidx):
        """voltage_set 命令自动补全"""
        return [f"${k}" for k in self.variables if k.startswith(text.replace("$", ""))]

    def complete_voltage_quick(self, text, line, begidx, endidx):
        """voltage_quick 命令自动补全"""
        actions = ["status", "defaults", "check"]
        return [action for action in actions if action.startswith(text)]

# =============================================================================
# 辅助函数 (在 AutoTestToolShell 类外部添加)
# =============================================================================

def _print_voltage_status_simple(status, compact=False):
    """简化的电压状态打印函数"""
    voltages = status.get('voltages', {})
    
    if not compact:
        print(f"\n📊 MC1P110电压状态 (数据来源: {status['data_source']})")
        if status.get('timestamp'):
            print(f"⏰ 数据时间: {status['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("-" * 80)
    print(f"{'Bank名称':<12} {'设定值(mV)':<12} {'实际值(mV)':<12} {'差值(mV)':<12} {'状态'}")
    print("-" * 80)
    
    # 显示各路电压
    for i, (name, default, max_val, min_val, step) in enumerate(VOLTAGE_SPECS):
        from CLI.cli_voltage import DEVICE_VOLTAGE_MAPPING
        device_name = DEVICE_VOLTAGE_MAPPING.get(name, name)
        
        if device_name in voltages:
            actual_mv = voltages[device_name]
            diff_mv = actual_mv - default
            
            # 判断状态
            if actual_mv > max_val:
                status_str = "⚠️超限"
            elif actual_mv < min_val:
                status_str = "⚠️低限"
            elif abs(diff_mv) <= step:  # 在步进误差范围内
                status_str = "✓正常"
            else:
                status_str = "⚡变更"
                
            print(f"{name:<12} {default:<12} {actual_mv:<12.1f} {diff_mv:<12.1f} {status_str}")
        else:
            print(f"{name:<12} {default:<12} {'--':<12} {'--':<12} ❌无数据")
    
    # 显示使能状态
    if not compact:
        print("-" * 80)
        if 'VCCADC' in voltages:
            adc_voltage = voltages['VCCADC']
            adc_status = "✓使能" if adc_voltage > 0 else "✗禁用"
            print(f"{'VCCADC':<12} {'--':<12} {adc_voltage:<12.1f} {'--':<12} {adc_status}")
        else:
            print(f"{'VCCADC':<12} {'--':<12} {'--':<12} {'--':<12} ❌无数据")

# =============================================================================
# 对外提供的接口函数 (在文件末尾，main函数之前添加)
# =============================================================================

def get_device_voltage_status(use_cache: bool = True, max_age: int = 10):
    """
    获取设备电压状态 (基于串口监听服务)
    
    Args:
        use_cache: 是否优先使用缓存数据
        max_age: 缓存数据最大年龄(秒)
        
    Returns:
        Dict: 电压状态数据，失败返回None
        
    作用:
        - 通过已建立的串口监听服务获取电压状态
        - 优先使用设备主动上报的数据
        - 包含所有11路电压的实际值和状态判断
    """
    if not is_voltage_available():
        print("❌ 串口监听未启动，请先执行: start_monitor <port> <baudrate>")
        return None
    return get_voltage_status_from_monitor(use_cache, max_age)

def set_device_voltage_values(values: list, enable_adc: bool = True, enable_ref: bool = True):
    """
    设置设备电压值 (基于串口监听服务)
    
    Args:
        values: 11路电压值列表 (mV)，顺序固定
        enable_adc: VCCADC使能状态
        enable_ref: VCCREF使能状态
        
    Returns:
        bool: 设置成功返回True，失败返回False
        
    作用:
        - 通过已建立的串口监听服务设置电压
        - 自动验证和校正电压值
        - 设置命令和响应会自动记录在监听日志中
    """
    if not is_voltage_available():
        print("❌ 串口监听未启动，请先执行: start_monitor <port> <baudrate>")
        return False
    
    # 验证电压值
    is_valid, corrected_values, errors = validate_voltage_values(values)
    if not is_valid:
        print("❌ 电压值验证失败:")
        for error in errors:
            print(f"  • {error}")
        return False
    
    return set_voltage_to_monitor(corrected_values, enable_adc, enable_ref)

def get_mc1p110_voltage_specs():
    """
    获取MC1P110电压规格信息
    
    Returns:
        List[tuple]: 电压规格列表 (名称, 默认值, 最大值, 最小值, 步进值)
        
    作用:
        - 返回所有11路电压的完整规格信息
        - 包含名称、默认值、范围限制、步进精度
        - 用于验证和显示
    """
    return get_voltage_specs()

def test_mc1p110_voltage_functionality():
    """
    测试MC1P110电压功能 (基于串口监听服务)
    
    Returns:
        bool: 测试通过返回True，失败返回False
        
    作用:
        - 综合测试电压读取和设置功能
        - 验证设备响应正常
        - 基于已建立的串口连接
        - 适用于自动化测试脚本
    """
    try:
        if not is_voltage_available():
            return False
            
        # 测试读取
        status = get_voltage_status_from_monitor()
        if not status or not status['success']:
            return False
        
        # 测试设置
        default_values = [spec[1] for spec in VOLTAGE_SPECS]
        success = set_voltage_to_monitor(default_values)
        
        return success
    except Exception:
        return False

def check_mc1p110_voltage_availability():
    """
    检查MC1P110电压功能是否可用
    
    Returns:
        Dict: 包含可用性状态和详细信息的字典
        
    作用:
        - 检查串口监听服务是否已启动
        - 验证电压功能是否可以使用
        - 返回详细的状态信息
        - 用于其他模块的依赖检查
    """
    result = {
        'available': False,
        'monitor_running': False,
        'device_communicating': False,
        'error': None,
        'details': {}
    }
    
    try:
        # 检查监听状态
        result['monitor_running'] = is_voltage_available()
        
        if result['monitor_running']:
            from CLI.cli_moni import get_monitor_status
            monitor_status = get_monitor_status()
            result['details']['monitor'] = monitor_status
            
            # 检查设备通信
            voltage_status = get_voltage_status_from_monitor(use_cache=True, max_age=30)
            if voltage_status and voltage_status['success']:
                result['device_communicating'] = True
                result['details']['voltage'] = voltage_status
            
            result['available'] = result['device_communicating']
        else:
            result['error'] = "串口监听未启动"
            
    except Exception as e:
        result['error'] = str(e)
    
    return result

def quick_vivado_program(vivado_path: str, bitstream_file: str):
    """
    快速Vivado烧写函数 (供其他脚本调用)
    
    Args:
        vivado_path: Vivado bin目录路径
        bitstream_file: bitstream文件路径
        
    Returns:
        bool: 成功返回True，失败返回False
        
    使用示例:
        success = quick_vivado_program("C:\\Xilinx\\Vivado\\2023.1\\bin", "design.bit")
        if success:
            print("烧写成功")
    """
    return vivado_program_cli(vivado_path, bitstream_file)

def quick_vivado_readback(vivado_path: str, output_file: str):
    """
    快速Vivado回读函数 (供其他脚本调用)
    
    Args:
        vivado_path: Vivado bin目录路径
        output_file: 回读文件保存路径
        
    Returns:
        bool: 成功返回True，失败返回False
        
    使用示例:
        success = quick_vivado_readback("C:\\Xilinx\\Vivado\\2023.1\\bin", "readback.rbd")
        if success:
            print("回读成功")
    """
    return vivado_readback_cli(vivado_path, output_file)

def quick_vivado_flash(vivado_path: str, bitstream_file: str, flash_part: str):
    """
    快速Vivado Flash烧写函数 (供其他脚本调用)
    
    Args:
        vivado_path: Vivado bin目录路径
        bitstream_file: bitstream文件路径
        flash_part: Flash器件型号
        
    Returns:
        bool: 成功返回True，失败返回False
        
    使用示例:
        success = quick_vivado_flash(
            "C:\\Xilinx\\Vivado\\2023.1\\bin", 
            "design.mcs", 
            "mt25ql128-spi-x1_x2_x4"
        )
        if success:
            print("Flash烧写成功")
    """
    return vivado_flash_cli(vivado_path, bitstream_file, flash_part)

def quick_vivado_test(vivado_path: str):
    """
    快速Vivado测试函数 (供其他脚本调用)
    
    Args:
        vivado_path: Vivado bin目录路径
        
    Returns:
        bool: 测试成功返回True，失败返回False
        
    使用示例:
        success = quick_vivado_test("C:\\Xilinx\\Vivado\\2023.1\\bin")
        if success:
            print("Vivado配置正常")
    """
    return vivado_test_cli(vivado_path)

def get_vivado_flash_parts():
    """
    获取支持的Flash器件型号列表 (供其他脚本调用)
    
    Returns:
        list: Flash器件型号列表
        
    使用示例:
        parts = get_vivado_flash_parts()
        print(f"支持的Flash型号: {', '.join(parts)}")
    """
    return get_supported_flash_parts()

# 交互模式：    python main_shell.py
# 单命令模式：  python main_shell.py -c "base --file xxx"
# 多命令模式：  python main_shell.py -c "cmd1" -c "cmd2" -c "cmd3"
# 脚本模式：    python main_shell.py myscript.txt
def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    shell = AutoTestToolShell()
    
    if len(sys.argv) == 1:
        # 交互模式
        shell.cmdloop()
    elif sys.argv[1] == '-c':
        # 单命令或多命令模式
        commands = []
        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == '-c' and i + 1 < len(sys.argv):
                commands.append(sys.argv[i + 1])
                i += 2
            else:
                i += 1
        
        # 执行所有命令
        for cmd in commands:
            print(f"执行命令: {cmd}")
            shell.onecmd(cmd)
            
    elif sys.argv[1].endswith('.txt'):
        # 脚本模式
        shell.do_run_script(sys.argv[1])
    else:
        print("参数格式错误，支持：")
        print("  无参数(交互模式): AutoTestTool.exe")
        print("  UI: AutoTestTool.exe -ui")
        print("  单命令模式: AutoTestTool.exe -c \"命令\"")
        print("  多命令模式: AutoTestTool.exe -c \"命令1\" -c \"命令2\"")
        print("  脚本模式: AutoTestTool.exe script.txt")

if __name__ == "__main__":
    main()