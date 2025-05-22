# main_cli.py
import argparse
import logging
from cli_base import run_base_cli
from cli_vccm import run_vccm_cli
from cli_convert import run_convert_cli

def main():
    parser = argparse.ArgumentParser(prog="bitcli", description="Bitstream Tool CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # base 模块
    base_parser = subparsers.add_parser("base", help="基础功能：烧录/分析等")
    base_parser.add_argument('--file', required=True)
    base_parser.add_argument('--device', default="MC1P110")
    base_parser.add_argument('--file_suffix', type=str)
    base_parser.add_argument('--PCIE', action='store_true')
    base_parser.add_argument('--GTP', action='store_true')
    base_parser.add_argument('--CRC', action='store_true')
    base_parser.add_argument('--COMPRESS', action='store_true')
    base_parser.add_argument('--TRIM', action='store_true')
    base_parser.add_argument('--DELETE_GHIGH', action='store_true')
    base_parser.add_argument('--readback_refresh', type=str)
    base_parser.add_argument('--timer_refresh', type=str)
    base_parser.set_defaults(func=run_base_cli)

    # vccm 模块
    vccm_parser = subparsers.add_parser("vccm", help="VCCM 电压批处理")
    vccm_parser.add_argument('--file', type=str, help="处理单个文件或文件夹")
    vccm_parser.add_argument('--project', type=str, help="处理整个项目路径")
    vccm_parser.add_argument('--vccm_values', type=int, nargs='+', help="电压值，例如 105 106 107")
    vccm_parser.set_defaults(func=run_vccm_cli)

    # convert 模块
    convert_parser = subparsers.add_parser("convert", help="码流格式转换")
    convert_parser.add_argument('--file', required=True)
    convert_parser.add_argument('--from_fmt', required=True, choices=["bit", "rbt", "bin"])
    convert_parser.add_argument('--to_fmt', required=True, choices=["bit", "rbt", "bin"])
    convert_parser.set_defaults(func=run_convert_cli)

    # 解析参数并分发
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args.func(args)

if __name__ == "__main__":
    main()
