import cmd
import shlex
import logging
import sys
import os
import json
import re
import argparse

from CLI.cli_vccm import run_vccm_cli
from CLI.cli_base import run_base_cli

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
            with open(filename) as f:
                for lineno, line in enumerate(f, 1):
                    line = line.strip()
                    # 脚本中可以写注释，用井号开头
                    if not line or line.startswith('#'):
                        continue
                    try:
                        self.onecmd(line)
                    except Exception as e:
                        print(f"第{lineno}行命令出错: {e}")
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
# 脚本模式：    python main_shell.py myscript.txt
def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    shell = AutoTestToolShell()
    if len(sys.argv) == 1:
        shell.cmdloop()
    elif sys.argv[1] == '-c':
        # 批量执行一条命令并退出
        cmdstr = ' '.join(sys.argv[2:])
        shell.onecmd(cmdstr)
    elif sys.argv[1].endswith('.txt'):
        shell.do_run_script(sys.argv[1])
    else:
        print("参数格式错误，支持：无参数(交互) | -c '命令' | script.txt")

if __name__ == "__main__":
    main()