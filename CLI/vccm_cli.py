# main_cli.py
import argparse
import logging
from CLI.cli_vccm import run_vccm_cli

def main():
    parser = argparse.ArgumentParser(prog="bit_tool", description="Bitstream Tool CLI")

    # vccm 模块
    parser.add_argument('--file', type=str, help="处理单个文件或文件夹")
    parser.add_argument('--project', type=str, help="处理整个项目路径")
    parser.add_argument('--output_path', type=str, help="输出文件存储目录")

    # 解析参数并分发
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_vccm_cli(args)  # 直接调用

if __name__ == "__main__":
    main()
