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
            self.variables[k] = v
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
        print("  无参数(交互模式): python main_shell.py")
        print("  单命令模式: python main_shell.py -c \"命令\"")
        print("  多命令模式: python main_shell.py -c \"命令1\" -c \"命令2\"")
        print("  脚本模式: python main_shell.py script.txt")

if __name__ == "__main__":
    main()