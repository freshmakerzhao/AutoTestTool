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
from CLI.cli_vivado import run_vivado_cli


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

            
    # --- VIVADO ---
    def do_vivado(self, line):
        line = self._substitute_variables(line)
        parser = self.get_vivado_parser()
        try:
            args = parser.parse_args(shlex.split(line))
            run_vivado_cli(args)
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
        """按照脚本批量执行命令（每行一条命令）"""
        if not os.path.isfile(filename):
            print(f"文件不存在: {filename}")
            return
        try:
            # 指定UTF-8编码读取文件，避免中文编码问题
            with open(filename, 'r', encoding='utf-8') as f:
                for lineno, line in enumerate(f, 1):
                    line = line.strip()
                    # 脚本中可以写注释，用 '#' 号开头
                    if not line or line.startswith('#'):
                        continue
                    try:
                        print(f"[{lineno:03d}] 执行: {line}")
                        self.onecmd(line)
                    except Exception as e:
                        print(f"第{lineno}行命令出错: {e}")
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

    # Vivado参数
    def get_vivado_parser(self):
        parser = argparse.ArgumentParser(prog="vivado")
        parser.add_argument(
            "--mode",
            required=True,
            choices=["program", "flash", "readback", "compare", "raw"],
            help="执行模式：program/flash/readback/compare/raw",
        )
        parser.add_argument("--vivado_bin", help="Vivado 安装目录")

        # program / flash
        parser.add_argument("--bit_path", help="bit/rbt 文件路径")
        parser.add_argument("--flash_part", default="mt25ql128-spi-x1_x2_x4", help="Flash 器件名称（如 mt25ql128-spi-x1_x2_x4）")

        # readback
        parser.add_argument("--out_rbd_path", help="回读输出 rbd 文件路径")

        # compare
        parser.add_argument("--mask_path", help="掩码文件 .msd")
        parser.add_argument("--readback_path", help="回读 rbd 文件")
        parser.add_argument("--gold_path", help="gold 文件 .rbt")
        parser.add_argument(
            "--special",
            default="",
            help="特征值：00/55/AA/FF（留空即功能位流比对）",
        )
        parser.add_argument("--result_path", default="", help="输出 result 文件路径")

        # raw
        parser.add_argument("--tcl_path", help="TCL 脚本路径（raw 模式）")
        parser.add_argument(
            "--tcl_args",
            nargs="*",
            default=[],
            help="传给 TCL 的参数列表（按原样拼接）",
        )
        # out_csv_dir
        parser.add_argument(
            "--out_csv_dir",
            default="",
            help="固定 CSV 输出目录（默认tcl_path目录）"
        )

        # 其它通用
        parser.add_argument("--timeout", type=float, default=60.0, help="超时时间（秒）")
        return parser

    # 串口命令行参数
    def get_serial_parser(self):
        parser = argparse.ArgumentParser(prog="serial")
        parser.add_argument("--port", required=True, help="串口号，如 COM3")

        # 互斥操作：时钟配置 / 电压读取 / 电压设置 三选一
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument(
            "--clock_config_path",
            help="发送时钟配置文件"
        )
        action.add_argument(
            "--voltage_show",
            action="store_true",
            help="读取并显示全部电压"
        )
        action.add_argument(
            "--voltage_set",
            nargs=13,
            type=int,
            metavar=(
                "VCCO_0",  "VCCBRAM",  "VCCAUX", "VCCINT",
                "VCCO_16", "VCCO_15", "VCCO_14", "VCCO_13",
                "VCCO_34", "MGTAVTT", "MGTAVCC", "VCCADC", "VCCREF"
            ),
            help="按顺序设置 11 路电压（单位 mV）以及VCCADC、VCCREF(1表示enable，0表示disable)"
        )
        return parser
    
    # VCCM
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