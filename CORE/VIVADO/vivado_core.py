import os
import sys
import time
import logging
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from COMMON import utils

@dataclass
class VivadoJobResult:
    ok: bool
    returncode: int
    cmd: List[str]
    stdout_snippet: str = ""
    stderr_snippet: str = ""

def _resolve_vivado_exe(vivado_bin_path: str) -> str:
    """
    返回 Vivado 可执行文件路径：
      - Windows: <vivado_bin_path>/vivado.bat
    """
    exe = os.path.join(vivado_bin_path, "vivado.bat")
    return exe

# 查询待执行文件是否存在
def _ensure_exists(path: str, what: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{what} 未找到: {path}")

# 统一资源路径解析
def _resource_path(relpath: str) -> str:
    """
    """
    return utils.resource_path(relpath)

def run_vivado_tcl(
    vivado_bin_path: str,
    tcl_script_path: str,
    tcl_args: Optional[List[str]] = None,
    log_path: Optional[str] = None,
    out_csv_dir: str = "",
    timeout: Optional[float] = None,
    env: Optional[Dict[str, str]] = None,
    extra_args: Optional[List[str]] = None
) -> VivadoJobResult:
    """
    以 batch 模式运行 Vivado 并指定 tcl 脚本和参数。
    - _vivado_bin_path: Vivado bin 目录
    - _tcl_script_path: tcl 文件绝对路径
    - tcl_args: 传给 -tclargs 的参数列表
    - _log_path: 把 stdout/stderr 写入文件
    - timeout: 超时秒
    - env: 额外环境变量
    - extra_args: 额外 Vivado 参数
    """
    # 获取vivado.bat路径
    vivado_bat = _resolve_vivado_exe(vivado_bin_path)
    _ensure_exists(vivado_bat, "Vivado.bat")
    _ensure_exists(tcl_script_path, "tcl 脚本")
    tcl_dir = os.path.dirname(tcl_script_path)
    os.environ["MAIN_TCL_DIR"] = tcl_dir
    if out_csv_dir:
        os.environ["OUT_CSV_DIR"] = out_csv_dir
    else:
        os.environ["OUT_CSV_DIR"] = tcl_dir
    os.system("chcp 65001 >NUL")
    cmd = [
        vivado_bat,
        "-mode", "batch",
        "-log", "NUL", "-journal", "NUL",
        "-source", tcl_script_path,
    ]

    if tcl_args:
        cmd += ["-tclargs"] + list(map(str, tcl_args))

    if extra_args:
        cmd += extra_args

    # Windows 隐藏窗口
    startupinfo = None
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    try:
        # 捕获输出，便于写入日志
        proc = subprocess.run(
            cmd,
            capture_output=True, 
            startupinfo=startupinfo,
            env=os.environ,
        )
    except subprocess.TimeoutExpired as te:
        raise TimeoutError(f"Vivado 执行超时（{timeout}s）") from te

    # 输出到log文件
    if log_path:
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write("\n=== Vivado Run ===\n")
                f.write("CMD: " + " ".join(cmd) + "\n")
                f.write(proc.stdout or "")
                if proc.stderr:
                    f.write("\n[STDERR]\n")
                    f.write(proc.stderr)
        except Exception as fe:
            logging.warning("写入 Vivado log 文件失败: %s", fe)

    ok = (proc.returncode == 0)
    return VivadoJobResult(
        ok=ok,
        returncode=proc.returncode,
        cmd=cmd,
        stdout_snippet=(proc.stdout or "")[-1000:],
        stderr_snippet=(proc.stderr or "")[-1000:]
    )


# ===============================================================================================================================================================
# ===============================================================================================================================================================
# ===========================================================================业务================================================================================    
# ===============================================================================================================================================================     
# ===============================================================================================================================================================         

def program_bitstream(
    vivado_bin_path: str,
    bitstream_file: str,
    log_path: Optional[str] = None,
    timeout: Optional[float] = None
) -> VivadoJobResult:
    """
    烧写 bitstream_file
    使用 RESOURCE/SCRIPTS/TCL/program.tcl
    """
    # 资源脚本
    _tcl_script_path = _resource_path("RESOURCE/SCRIPTS/TCL/program.tcl")

    # 校验文件存在
    _ensure_exists(bitstream_file, "bitstream 文件")

    logging.info("[Program] 开始处理")
    logging.info("vivado_bin_path = %s", vivado_bin_path)
    logging.info("bit_file_path   = %s", bitstream_file)
    logging.info("tcl_script_path   = %s", _tcl_script_path)

    result = run_vivado_tcl(
        vivado_bin_path=vivado_bin_path,
        tcl_script_path=_tcl_script_path,
        tcl_args=[bitstream_file],
        log_path=log_path,
        timeout=timeout,
    )

    if not result.ok:
        raise RuntimeError(f"烧写 bitstream 失败（ret={result.returncode}）")
    return result

def program_flash(
    vivado_bin_path: str,
    bitstream_file: str,
    flash_part: str,
    log_path: Optional[str] = None,
    timeout: Optional[float] = None
) -> VivadoJobResult:
    """
    烧写到 Flash
    使用 RESOURCE/SCRIPTS/TCL/program_flash.tcl
    """
    _tcl_script_path = _resource_path("RESOURCE/SCRIPTS/TCL/program_flash.tcl")

    _ensure_exists(bitstream_file, "bit/mcs 文件")

    logging.info("[Program-Flash] 开始处理")
    logging.info("vivado_bin_path = %s", vivado_bin_path)
    logging.info("file_path       = %s", bitstream_file)
    logging.info("flash_part      = %s", flash_part)
    logging.info("tcl_script_path   = %s", _tcl_script_path)

    result = run_vivado_tcl(
        vivado_bin_path=vivado_bin_path,
        tcl_script_path=_tcl_script_path,
        tcl_args=[bitstream_file, flash_part],
        log_path=log_path,
        timeout=timeout
    )

    if not result.ok:
        raise RuntimeError(f"烧写 Flash 失败（ret={result.returncode}）")
    return result

def readback_to_file(
        vivado_bin_path: str,
        out_rbd_path: str,
        log_path: Optional[str] = None, 
        timeout: Optional[float] = None
) -> VivadoJobResult:
    """从 FPGA 回读 bitstream 到 rbd 文件"""
    _tcl_script_path = _resource_path("RESOURCE/SCRIPTS/TCL/readback.tcl")

    logging.info("[Readback] 开始处理")
    logging.info("vivado_bin_path = %s", vivado_bin_path)
    logging.info("out_rbd_path       = %s", out_rbd_path)
    logging.info("tcl_script_path   = %s", _tcl_script_path)

    out_dir = os.path.dirname(out_rbd_path) or "."
    os.makedirs(out_dir, exist_ok=True)
    # 先删旧文件
    try:
        if os.path.exists(out_rbd_path):
            os.remove(out_rbd_path)
    except Exception as e:
        logging.warning("无法删除现有回读文件 %s: %s", out_rbd_path, e)
    
    res = run_vivado_tcl(vivado_bin_path, _tcl_script_path, [out_rbd_path], log_path, timeout)
    if not res.ok:
        raise RuntimeError(f"回读 rbd 失败（ret={res.returncode}）")
    logging.info("[Vivado] Readback 完成：%s", out_rbd_path)
    return res
# ===============================================================================================================================================================
# ===============================================================================================================================================================
# ===========================================================================业务================================================================================    
# ===============================================================================================================================================================     
# ===============================================================================================================================================================         
