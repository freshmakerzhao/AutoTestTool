# CORE/run_vivado_tcl.py
import os
import subprocess
import logging
from typing import List, Optional
import COMMON.utils as utils


def run_script_tcl(
    vivado_bin_path: str,
    tcl_script_path: str,
    tcl_args: Optional[List[str]] = None,
    log_file: str = "NUL",
    journal_file: str = "NUL",
    mode: str = "batch",
    capture_output: bool = False
) -> subprocess.CompletedProcess:
    """
    执行Vivado TCL脚本的通用函数
    
    Args:
        vivado_bin_path: Vivado安装目录路径
        tcl_script_path: TCL脚本文件路径
        tcl_args: TCL脚本参数列表，可选
        log_file: 日志文件路径，默认为"NUL"（不输出日志）
        journal_file: Journal文件路径，默认为"NUL"（不输出journal）
        mode: Vivado执行模式，默认为"batch"
        capture_output: 是否捕获输出，默认False
        
    Returns:
        subprocess.CompletedProcess: 执行结果
        
    Raises:
        RuntimeError: 当Vivado可执行文件或TCL脚本不存在时
        subprocess.CalledProcessError: 当执行失败时
    """
    # 验证Vivado路径
    vivado_bat_path = os.path.join(vivado_bin_path, "vivado.bat")
    if not os.path.exists(vivado_bat_path):
        raise RuntimeError(f"Vivado.bat 文件未找到: {vivado_bat_path}")
    
    # 验证TCL脚本路径
    if not os.path.exists(tcl_script_path):
        raise RuntimeError(f"TCL脚本文件未找到: {tcl_script_path}")
    
    # 构建命令
    cmd = [
        vivado_bat_path,
        "-mode", mode,
        "-log", log_file,
        "-journal", journal_file,
        "-source", tcl_script_path
    ]
    
    # 添加TCL参数
    if tcl_args:
        cmd.extend(["-tclargs"] + tcl_args)
    
    # 记录执行信息
    logging.info("=======================================================")
    logging.info(f"[run_script_tcl] 执行参数:")
    logging.info(f"  vivado_bin_path = {vivado_bin_path}")
    logging.info(f"  tcl_script_path = {tcl_script_path}")
    logging.info(f"  tcl_args = {tcl_args}")
    logging.info(f"  log_file = {log_file}")
    logging.info(f"  journal_file = {journal_file}")
    logging.info(f"  mode = {mode}")
    logging.info(f"  命令: {' '.join(cmd)}")
    logging.info("=======================================================")
    
    # 执行命令
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=False  # 不自动抛出异常，让调用者处理
        )
        
        if result.returncode == 0:
            logging.info(f"[run_script_tcl] TCL脚本执行成功: {tcl_script_path}")
        else:
            logging.error(f"[run_script_tcl] TCL脚本执行失败: {tcl_script_path}, 返回码: {result.returncode}")
            if capture_output and result.stderr:
                logging.error(f"错误输出: {result.stderr}")
        
        return result
        
    except Exception as e:
        logging.error(f"[run_script_tcl] 执行过程中发生异常: {e}")
        raise


def run_program_bitstream(
    vivado_bin_path: str,
    bitstream_file: str,
    log_file: str = "NUL",
    journal_file: str = "NUL"
) -> bool:
    """
    烧写bitstream文件到FPGA
    
    Args:
        vivado_bin_path: Vivado安装目录
        bitstream_file: bitstream文件路径
        log_file: 日志文件路径
        journal_file: Journal文件路径
        
    Returns:
        bool: 执行成功返回True，失败返回False
    """
    try:
        program_script = utils.resource_path("RESOURCE/SCRIPTS/program.tcl")
        result = run_script_tcl(
            vivado_bin_path=vivado_bin_path,
            tcl_script_path=program_script,
            tcl_args=[bitstream_file],
            log_file=log_file,
            journal_file=journal_file
        )
        return result.returncode == 0
    except Exception as e:
        logging.error(f"[run_program_bitstream] 烧写失败: {e}")
        return False


def run_program_flash(
    vivado_bin_path: str,
    bitstream_file: str,
    flash_part: str,
    log_file: str = "NUL",
    journal_file: str = "NUL"
) -> bool:
    """
    烧写bitstream文件到Flash
    
    Args:
        vivado_bin_path: Vivado安装目录
        bitstream_file: bitstream文件路径
        flash_part: Flash器件型号
        log_file: 日志文件路径
        journal_file: Journal文件路径
        
    Returns:
        bool: 执行成功返回True，失败返回False
    """
    try:
        program_flash_script = utils.resource_path("RESOURCE/SCRIPTS/program_flash.tcl")
        result = run_script_tcl(
            vivado_bin_path=vivado_bin_path,
            tcl_script_path=program_flash_script,
            tcl_args=[bitstream_file, flash_part],
            log_file=log_file,
            journal_file=journal_file
        )
        return result.returncode == 0
    except Exception as e:
        logging.error(f"[run_program_flash] 烧写Flash失败: {e}")
        return False


def run_readback(
    vivado_bin_path: str,
    readback_file: str,
    log_file: str = "NUL",
    journal_file: str = "NUL"
) -> bool:
    """
    从FPGA回读bitstream
    
    Args:
        vivado_bin_path: Vivado安装目录
        readback_file: 回读文件保存路径
        log_file: 日志文件路径
        journal_file: Journal文件路径
        
    Returns:
        bool: 执行成功返回True，失败返回False
    """
    try:
        readback_script = utils.resource_path("RESOURCE/SCRIPTS/readback.tcl")
        result = run_script_tcl(
            vivado_bin_path=vivado_bin_path,
            tcl_script_path=readback_script,
            tcl_args=[readback_file],
            log_file=log_file,
            journal_file=journal_file
        )
        return result.returncode == 0
    except Exception as e:
        logging.error(f"[run_readback] 回读失败: {e}")
        return False


def run_custom_tcl(
    vivado_bin_path: str,
    tcl_script_path: str,
    tcl_args: Optional[List[str]] = None,
    log_file: str = "NUL",
    journal_file: str = "NUL"
) -> bool:
    """
    执行自定义TCL脚本
    
    Args:
        vivado_bin_path: Vivado安装目录
        tcl_script_path: TCL脚本文件路径
        tcl_args: TCL脚本参数列表
        log_file: 日志文件路径
        journal_file: Journal文件路径
        
    Returns:
        bool: 执行成功返回True，失败返回False
    """
    try:
        result = run_script_tcl(
            vivado_bin_path=vivado_bin_path,
            tcl_script_path=tcl_script_path,
            tcl_args=tcl_args,
            log_file=log_file,
            journal_file=journal_file
        )
        return result.returncode == 0
    except Exception as e:
        logging.error(f"[run_custom_tcl] 自定义TCL执行失败: {e}")
        return False


def test_vivado_installation(vivado_path: str):
    """
    测试Vivado安装和TCL脚本
    
    Args:
        vivado_path: Vivado bin目录路径
        
    Returns:
        dict: 测试结果字典
    """
    result = {
        'vivado_valid': False,
        'scripts_valid': False,
        'details': []
    }
    
    try:
        print("🧪 开始Vivado功能测试")
        
        # 测试1: 验证Vivado安装
        print("\n📁 测试1: 验证Vivado安装")
        if not os.path.exists(vivado_path):
            result['details'].append(f"❌ Vivado路径不存在: {vivado_path}")
            return result
        
        vivado_bat = os.path.join(vivado_path, "vivado.bat")
        if not os.path.exists(vivado_bat):
            result['details'].append(f"❌ 在指定路径中未找到vivado.bat: {vivado_bat}")
            return result
        
        result['vivado_valid'] = True
        result['details'].append(f"✓ Vivado安装路径有效: {vivado_path}")
        
        # 测试2: 检查TCL脚本
        print("\n📜 测试2: 检查TCL脚本")
        
        scripts = ["program.tcl", "program_flash.tcl", "readback.tcl"]
        scripts_ok = 0
        
        for script_name in scripts:
            try:
                script_path = utils.resource_path(f"RESOURCE/SCRIPTS/{script_name}")
                if os.path.exists(script_path):
                    result['details'].append(f"✓ {script_name}: 存在")
                    scripts_ok += 1
                else:
                    result['details'].append(f"❌ {script_name}: 不存在")
            except Exception as e:
                result['details'].append(f"❌ {script_name}: 检查失败 ({e})")
        
        result['scripts_valid'] = (scripts_ok == len(scripts))
        
        # 测试3: 硬件连接检查
        print("\n🔌 测试3: 硬件连接检查")
        result['details'].append("💡 硬件连接需要实际设备，请确保:")
        result['details'].append("   • FPGA开发板已连接")
        result['details'].append("   • USB线缆连接正常")
        result['details'].append("   • 驱动程序已安装")
        
        # 总结
        if result['vivado_valid'] and result['scripts_valid']:
            result['details'].append("\n✓ Vivado功能测试通过，可以正常使用")
        else:
            result['details'].append("\n❌ Vivado功能测试未完全通过，请检查配置")
        
        return result
        
    except Exception as e:
        result['details'].append(f"❌ 测试过程出错: {e}")
        return result


def get_supported_flash_parts():
    """
    获取支持的Flash器件型号列表
    
    Returns:
        list: Flash器件型号列表
    """
    return [
        "28f00ap30t-bpi-x16",
        "28f512p30t-bpi-x16", 
        "28f256p30t-bpi-x16",
        "28f512p30e-bpi-x16",
        "mt28gu256aax1e-bpi-x16",
        "mt28fw02gb-bpi-x16",
        "mt25ql128-spi-x1_x2_x4"
    ]