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

from CLI.cli_serial import run_serial_cli
from CLI.cli_vccm import run_vccm_cli
from CLI.cli_base import run_base_cli

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

# ===============================================================================================================================================================
# ===============================================================================================================================================================
# ===========================================================================调用各模块 CLI=======================================================================    
# ===============================================================================================================================================================     
# ===============================================================================================================================================================         

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

    # --- SERIAL ---
    def do_serial(self, line):
        line = self._substitute_variables(line)
        parser = self.get_serial_parser()
        try:
            args = parser.parse_args(shlex.split(line))
            run_serial_cli(args)
        except SystemExit:
            pass
        except Exception as e:
            print(f"执行 serial 命令出错: {e}")

# ===============================================================================================================================================================
# ===============================================================================================================================================================
# ===========================================================================调用各模块 CLI=======================================================================    
# ===============================================================================================================================================================     
# ===============================================================================================================================================================  

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

# ===============================================================================================================================================================
# ===============================================================================================================================================================
# ===========================================================================命令行参数===========================================================================    
# ===============================================================================================================================================================     
# ===============================================================================================================================================================  

    # 串口命令行参数
    def get_serial_parser(self):
        parser = argparse.ArgumentParser(prog="serial")
        parser.add_argument("--connect_only", action="store_true", help="仅连接串口")
        parser.add_argument("--port", required=True, help="串口号，如 COM3")
        parser.add_argument("--clock_config_path", help="发送时钟配置文件")
        # parser.add_argument("--wait", type=float, default=1.0, help="等待接收时间，单位秒")
        # parser.add_argument("--send_text", help="发送文本")
        # parser.add_argument("--send_hex", help="发送十六进制字符串")

        return parser
    
    # 串口命令行参数
    def get_vccm_parser(self):
        parser = argparse.ArgumentParser(prog="vccm")
        parser.add_argument('--file', type=str)
        parser.add_argument('--project', type=str)
        parser.add_argument('--vccm_values', type=int, nargs='+')
        return parser
    
    # base模块命令行参数
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

# ===============================================================================================================================================================
# ===============================================================================================================================================================
# ===========================================================================命令行参数===========================================================================    
# ===============================================================================================================================================================     
# =============================================================================================================================================================== 
    
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