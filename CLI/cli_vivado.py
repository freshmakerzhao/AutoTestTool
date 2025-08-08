# CLI/cli_vivado.py
import argparse
import sys
import os
import logging
from pathlib import Path
from typing import List, Optional

# 添加项目根目录到路径，以便导入模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from CORE.run_vivado_tcl import (
    run_script_tcl,
    run_program_bitstream,
    run_program_flash,
    run_readback,
    run_custom_tcl,
    test_vivado_installation,
    get_supported_flash_parts
)


def setup_logging(verbose: bool = False):
    """设置日志输出"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def cmd_program(args):
    """烧写bitstream到FPGA"""
    success = run_program_bitstream(
        vivado_bin_path=args.vivado_path,
        bitstream_file=args.bitstream,
        log_file=args.log_file,
        journal_file=args.journal_file
    )
    
    if success:
        print(f"✓ 成功烧写bitstream到FPGA: {args.bitstream}")
        return 0
    else:
        print(f"✗ 烧写bitstream失败: {args.bitstream}")
        return 1


def cmd_program_flash(args):
    """烧写bitstream到Flash"""
    success = run_program_flash(
        vivado_bin_path=args.vivado_path,
        bitstream_file=args.bitstream,
        flash_part=args.flash_part,
        log_file=args.log_file,
        journal_file=args.journal_file
    )
    
    if success:
        print(f"✓ 成功烧写bitstream到Flash: {args.bitstream}")
        return 0
    else:
        print(f"✗ 烧写bitstream到Flash失败: {args.bitstream}")
        return 1


def cmd_readback(args):
    """从FPGA回读bitstream"""
    success = run_readback(
        vivado_bin_path=args.vivado_path,
        readback_file=args.output,
        log_file=args.log_file,
        journal_file=args.journal_file
    )
    
    if success:
        print(f"✓ 成功回读bitstream: {args.output}")
        return 0
    else:
        print(f"✗ 回读bitstream失败: {args.output}")
        return 1


def cmd_custom(args):
    """执行自定义TCL脚本"""
    tcl_args = args.tcl_args if args.tcl_args else None
    
    success = run_custom_tcl(
        vivado_bin_path=args.vivado_path,
        tcl_script_path=args.tcl_script,
        tcl_args=tcl_args,
        log_file=args.log_file,
        journal_file=args.journal_file
    )
    
    if success:
        print(f"✓ 成功执行TCL脚本: {args.tcl_script}")
        return 0
    else:
        print(f"✗ 执行TCL脚本失败: {args.tcl_script}")
        return 1


def cmd_raw(args):
    """原始TCL脚本执行（完全自定义）"""
    try:
        result = run_script_tcl(
            vivado_bin_path=args.vivado_path,
            tcl_script_path=args.tcl_script,
            tcl_args=args.tcl_args if args.tcl_args else None,
            log_file=args.log_file,
            journal_file=args.journal_file,
            mode=args.mode,
            capture_output=args.capture_output
        )
        
        if result.returncode == 0:
            print(f"✓ TCL脚本执行成功: {args.tcl_script}")
            if args.capture_output and result.stdout:
                print("标准输出:")
                print(result.stdout)
        else:
            print(f"✗ TCL脚本执行失败: {args.tcl_script}")
            if args.capture_output and result.stderr:
                print("错误输出:")
                print(result.stderr)
        
        return result.returncode
        
    except Exception as e:
        print(f"✗ 执行过程中发生异常: {e}")
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Vivado TCL脚本执行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 烧写bitstream到FPGA
  python cli_vivado.py program -v /path/to/vivado/bin -b design.bit
  
  # 烧写bitstream到Flash
  python cli_vivado.py program-flash -v /path/to/vivado/bin -b design.mcs -f mt25ql128-spi-x1_x2_x4
  
  # 从FPGA回读
  python cli_vivado.py readback -v /path/to/vivado/bin -o readback.rbd
  
  # 执行自定义TCL脚本
  python cli_vivado.py custom -v /path/to/vivado/bin -t script.tcl --tcl-args arg1 arg2
  
  # 原始TCL执行（完全自定义）
  python cli_vivado.py raw -v /path/to/vivado/bin -t script.tcl --mode gui
        """
    )
    
    # 全局参数
    parser.add_argument(
        "--verbose", "-V",
        action="store_true",
        help="详细输出模式"
    )
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 通用参数函数
    def add_common_args(p):
        p.add_argument(
            "--vivado-path", "-v",
            required=True,
            help="Vivado安装目录路径 (包含vivado.bat的bin目录)"
        )
        p.add_argument(
            "--log-file", "-l",
            default="NUL",
            help="日志文件路径 (默认: NUL)"
        )
        p.add_argument(
            "--journal-file", "-j",
            default="NUL",
            help="Journal文件路径 (默认: NUL)"
        )
    
    # program 子命令
    parser_program = subparsers.add_parser("program", help="烧写bitstream到FPGA")
    add_common_args(parser_program)
    parser_program.add_argument(
        "--bitstream", "-b",
        required=True,
        help="bitstream文件路径 (.bit/.bin/.rbt)"
    )
    parser_program.set_defaults(func=cmd_program)
    
    # program-flash 子命令
    parser_flash = subparsers.add_parser("program-flash", help="烧写bitstream到Flash")
    add_common_args(parser_flash)
    parser_flash.add_argument(
        "--bitstream", "-b",
        required=True,
        help="bitstream文件路径 (.bin/.mcs)"
    )
    parser_flash.add_argument(
        "--flash-part", "-f",
        required=True,
        choices=get_supported_flash_parts(),
        help="Flash器件型号"
    )
    parser_flash.set_defaults(func=cmd_program_flash)
    
    # readback 子命令
    parser_readback = subparsers.add_parser("readback", help="从FPGA回读bitstream")
    add_common_args(parser_readback)
    parser_readback.add_argument(
        "--output", "-o",
        required=True,
        help="回读文件保存路径 (.rbd)"
    )
    parser_readback.set_defaults(func=cmd_readback)
    
    # custom 子命令
    parser_custom = subparsers.add_parser("custom", help="执行自定义TCL脚本")
    add_common_args(parser_custom)
    parser_custom.add_argument(
        "--tcl-script", "-t",
        required=True,
        help="TCL脚本文件路径"
    )
    parser_custom.add_argument(
        "--tcl-args",
        nargs="*",
        help="传递给TCL脚本的参数"
    )
    parser_custom.set_defaults(func=cmd_custom)
    
    # raw 子命令（完全自定义）
    parser_raw = subparsers.add_parser("raw", help="原始TCL脚本执行（完全自定义）")
    add_common_args(parser_raw)
    parser_raw.add_argument(
        "--tcl-script", "-t",
        required=True,
        help="TCL脚本文件路径"
    )
    parser_raw.add_argument(
        "--tcl-args",
        nargs="*",
        help="传递给TCL脚本的参数"
    )
    parser_raw.add_argument(
        "--mode", "-m",
        choices=["batch", "tcl", "gui"],
        default="batch",
        help="Vivado执行模式 (默认: batch)"
    )
    parser_raw.add_argument(
        "--capture-output",
        action="store_true",
        help="捕获并显示输出"
    )
    parser_raw.set_defaults(func=cmd_raw)
    
    # 解析参数
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.verbose)
    
    # 验证必需参数
    if not args.command:
        parser.print_help()
        return 1
    
    # 验证Vivado路径
    if hasattr(args, 'vivado_path'):
        if not os.path.exists(args.vivado_path):
            print(f"✗ Vivado路径不存在: {args.vivado_path}")
            return 1
        
        vivado_bat = os.path.join(args.vivado_path, "vivado.bat")
        if not os.path.exists(vivado_bat):
            print(f"✗ 在指定路径中未找到vivado.bat: {vivado_bat}")
            return 1
    
    # 验证输入文件
    if hasattr(args, 'bitstream') and args.bitstream:
        if not os.path.isfile(args.bitstream):
            print(f"✗ bitstream文件不存在: {args.bitstream}")
            return 1
    
    if hasattr(args, 'tcl_script') and args.tcl_script:
        if not os.path.isfile(args.tcl_script):
            print(f"✗ TCL脚本文件不存在: {args.tcl_script}")
            return 1
    
    # 执行对应的命令函数
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n✗ 用户中断操作")
        return 130
    except Exception as e:
        print(f"✗ 发生未知错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


# =============================================================================
# 供main_shell.py调用的简化接口函数
# =============================================================================

def vivado_program_cli(vivado_path: str, bitstream_file: str, 
                      log_file: str = "NUL", journal_file: str = "NUL"):
    """
    CLI适配: 烧写bitstream到FPGA
    
    Args:
        vivado_path: Vivado bin目录路径
        bitstream_file: bitstream文件路径
        log_file: 日志文件路径
        journal_file: Journal文件路径
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    try:
        # 验证路径
        if not os.path.exists(vivado_path):
            print(f"❌ Vivado路径不存在: {vivado_path}")
            return False
            
        vivado_bat = os.path.join(vivado_path, "vivado.bat")
        if not os.path.exists(vivado_bat):
            print(f"❌ 在指定路径中未找到vivado.bat: {vivado_bat}")
            return False
            
        if not os.path.isfile(bitstream_file):
            print(f"❌ bitstream文件不存在: {bitstream_file}")
            return False
        
        print(f"🔥 开始烧写: {bitstream_file}")
        success = run_program_bitstream(
            vivado_bin_path=vivado_path,
            bitstream_file=bitstream_file,
            log_file=log_file,
            journal_file=journal_file
        )
        
        if success:
            print(f"✓ 烧写成功: {bitstream_file}")
        else:
            print(f"❌ 烧写失败: {bitstream_file}")
            
        return success
        
    except Exception as e:
        print(f"❌ 烧写过程出错: {e}")
        return False


def vivado_flash_cli(vivado_path: str, bitstream_file: str, flash_part: str,
                    log_file: str = "NUL", journal_file: str = "NUL"):
    """
    CLI适配: 烧写bitstream到Flash
    """
    try:
        # 验证路径
        if not os.path.exists(vivado_path):
            print(f"❌ Vivado路径不存在: {vivado_path}")
            return False
            
        if not os.path.isfile(bitstream_file):
            print(f"❌ bitstream文件不存在: {bitstream_file}")
            return False
        
        # 验证Flash型号
        if flash_part not in get_supported_flash_parts():
            print(f"❌ 不支持的Flash型号: {flash_part}")
            print(f"支持的型号: {', '.join(get_supported_flash_parts())}")
            return False
        
        print(f"💾 开始烧写到Flash: {bitstream_file}")
        print(f"📱 Flash型号: {flash_part}")
        
        success = run_program_flash(
            vivado_bin_path=vivado_path,
            bitstream_file=bitstream_file,
            flash_part=flash_part,
            log_file=log_file,
            journal_file=journal_file
        )
        
        if success:
            print(f"✓ Flash烧写成功: {bitstream_file}")
        else:
            print(f"❌ Flash烧写失败: {bitstream_file}")
            
        return success
        
    except Exception as e:
        print(f"❌ Flash烧写过程出错: {e}")
        return False


def vivado_readback_cli(vivado_path: str, output_file: str,
                       log_file: str = "NUL", journal_file: str = "NUL"):
    """
    CLI适配: 从FPGA回读bitstream
    """
    try:
        # 验证路径
        if not os.path.exists(vivado_path):
            print(f"❌ Vivado路径不存在: {vivado_path}")
            return False
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            print(f"📁 创建输出目录: {output_dir}")
        
        print(f"📖 开始回读到: {output_file}")
        
        success = run_readback(
            vivado_bin_path=vivado_path,
            readback_file=output_file,
            log_file=log_file,
            journal_file=journal_file
        )
        
        if success:
            print(f"✓ 回读成功: {output_file}")
            if os.path.exists(output_file):
                size = os.path.getsize(output_file)
                print(f"📄 文件大小: {size} 字节")
        else:
            print(f"❌ 回读失败: {output_file}")
            
        return success
        
    except Exception as e:
        print(f"❌ 回读过程出错: {e}")
        return False


def vivado_custom_cli(vivado_path: str, tcl_script: str, tcl_args: List[str] = None,
                     log_file: str = "NUL", journal_file: str = "NUL"):
    """
    CLI适配: 执行自定义TCL脚本
    """
    try:
        # 验证路径
        if not os.path.exists(vivado_path):
            print(f"❌ Vivado路径不存在: {vivado_path}")
            return False
            
        if not os.path.isfile(tcl_script):
            print(f"❌ TCL脚本不存在: {tcl_script}")
            return False
        
        print(f"📜 执行TCL脚本: {tcl_script}")
        if tcl_args:
            print(f"📝 脚本参数: {tcl_args}")
        
        success = run_custom_tcl(
            vivado_bin_path=vivado_path,
            tcl_script_path=tcl_script,
            tcl_args=tcl_args,
            log_file=log_file,
            journal_file=journal_file
        )
        
        if success:
            print(f"✓ TCL脚本执行成功: {tcl_script}")
        else:
            print(f"❌ TCL脚本执行失败: {tcl_script}")
            
        return success
        
    except Exception as e:
        print(f"❌ TCL脚本执行过程出错: {e}")
        return False


def vivado_test_cli(vivado_path: str):
    """
    CLI适配: 测试Vivado功能
    """
    try:
        result = test_vivado_installation(vivado_path)
        
        # 打印测试结果
        for detail in result['details']:
            print(detail)
            
        return result['vivado_valid'] and result['scripts_valid']
        
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
        return False


def print_vivado_help():
    """
    打印Vivado功能帮助信息
    """
    print("""
🔧 Vivado TCL 工具功能说明

📋 支持的操作:
  • vivado_program    : 烧写bitstream到FPGA
  • vivado_flash      : 烧写bitstream到Flash  
  • vivado_readback   : 从FPGA回读bitstream
  • vivado_custom     : 执行自定义TCL脚本
  • vivado_test       : 测试Vivado功能

💾 支持的Flash器件:
""")
    for i, part in enumerate(get_supported_flash_parts(), 1):
        print(f"  {i:2d}. {part}")
    
    print("""
📝 使用示例:
  vivado_program -v "C:\\Xilinx\\Vivado\\2023.1\\bin" -b "design.bit"
  vivado_flash -v $VIVADO_PATH -b "design.mcs" -f "mt25ql128-spi-x1_x2_x4"
  vivado_readback -v $VIVADO_PATH -o "readback.rbd"
  vivado_custom -v $VIVADO_PATH -t "script.tcl" --tcl-args "arg1" "arg2"

💡 提示:
  • 使用变量可以简化命令，如: set VIVADO_PATH "C:\\Xilinx\\Vivado\\2023.1\\bin"
  • 所有命令都支持变量替换，如: -v $VIVADO_PATH
  • 确保FPGA硬件正确连接并识别
""")

if __name__ == "__main__":
    sys.exit(main())