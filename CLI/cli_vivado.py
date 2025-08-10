import logging
from typing import Optional, List

# === 调用核心能力 ===
from CORE.VIVADO.vivado_core import (
    run_vivado_tcl,
    program_bitstream,
    program_flash,
    readback_to_file,
)
from CORE.process_rdcheck import compare_dispatch

def run_vivado_cli(args):
    try:
        mode = args.mode
        if mode == "program":
            _do_program(
                vivado_bin=args.vivado_bin,
                bit_path=args.bit_path,
                timeout=args.timeout
            )

        elif mode == "flash":
            _do_flash(
                vivado_bin=args.vivado_bin,
                bit_path=args.bit_path,
                flash_part=args.flash_part,
                timeout=args.timeout
            )

        elif mode == "readback":
            _do_readback(
                vivado_bin=args.vivado_bin,
                out_rbd_path=args.out_rbd_path,
                timeout=args.timeout
            )

        elif mode == "compare":
            _do_compare(
                mask_path=args.mask_path,
                readback_path=args.readback_path,
                gold_path=args.gold_path,
                special=args.special,
                result_path=args.result_path or None,
            )

        elif mode == "raw":
            _do_raw(
                vivado_bin=args.vivado_bin,
                tcl_path=args.tcl_path,
                tcl_args=args.tcl_args,
                out_csv_dir=args.out_csv_dir,
                timeout=args.timeout
            )

        else:
            logging.error(f"未知 vivado 模式: {mode}")
            return

    except Exception as e:
        logging.error("[vivado cli] 失败: %s", e, exc_info=True)
        # 往上抛，让上层统一弹窗/打印
        return

# ------------------ 具体动作 ------------------
def _require_path(val: Optional[str], what: str):
    if not val:
        raise ValueError(f"缺少参数：{what}")

def _do_program(vivado_bin: str, bit_path: str, timeout: float):
    _require_path(vivado_bin, "vivado_bin")
    _require_path(bit_path, "bit_path")
    logging.info("[vivado program] start")
    result = program_bitstream(
        vivado_bin_path=vivado_bin,
        bitstream_file=bit_path,
        log_path=None,
        timeout=timeout
    )
    if not result.ok:
        raise RuntimeError(f"烧写 bit 失败（ret={result.returncode}）")
    logging.info("[vivado program] ok")

def _do_flash(
    vivado_bin: str,
    bit_path: str,
    flash_part: str,
    timeout: float
):
    _require_path(vivado_bin, "vivado_bin")
    _require_path(bit_path, "bit_path")
    _require_path(flash_part, "flash_part")
    logging.info("[vivado flash] start")
    result = program_flash(
        vivado_bin_path=vivado_bin,
        bitstream_file=bit_path,
        flash_part=flash_part,
        log_path=None,
        timeout=timeout
    )
    if not result.ok:
        raise RuntimeError(f"烧写 Flash 失败（ret={result.returncode}）")
    logging.info("[vivado flash] ok")


def _do_readback(
    vivado_bin: str,
    out_rbd_path: str,
    timeout: float
):
    _require_path(vivado_bin, "vivado_bin")
    _require_path(out_rbd_path, "out_rbd_path")
    logging.info("[vivado readback] start")
    result = readback_to_file(
        vivado_bin_path=vivado_bin,
        out_rbd_path=out_rbd_path,
        log_path=None,
        timeout=timeout
    )
    if not result.ok:
        raise RuntimeError(f"回读失败（ret={result.returncode}）")
    logging.info("[vivado readback] ok -> %s", out_rbd_path)

def _do_compare(
    mask_path: str,
    readback_path: str,
    gold_path: str,
    special: str,
    result_path: Optional[str],
):
    _require_path(mask_path, "mask_path")
    _require_path(readback_path, "readback_path")
    _require_path(gold_path, "gold_path")

    logging.info("[vivado compare] start (special=%s)", special or "<functional>")
    ok, detail = compare_dispatch(
        mask_file=mask_path,
        readback_file=readback_path,
        gold_file=gold_path,
        special_value=(special or ""),
        result_path=result_path,
    )
    if not ok:
        raise RuntimeError(f"比对失败：{detail}")
    logging.info("[vivado compare] PASS")

def _do_raw(
    vivado_bin: str,
    tcl_path: str,
    tcl_args: Optional[List[str]],
    out_csv_dir: str,
    timeout: float
):
    _require_path(vivado_bin, "vivado_bin")
    _require_path(tcl_path, "tcl_path")
    args = tcl_args or []
    logging.info("[vivado raw] start: %s args=%s", tcl_path, args)

    result = run_vivado_tcl(
        vivado_bin_path=vivado_bin,
        tcl_script_path=tcl_path,
        tcl_args=args,
        log_path=None,
        out_csv_dir=out_csv_dir,
        timeout=timeout
    )
    if not result.ok:
        raise RuntimeError(f"raw 执行失败（ret={result.returncode}）")
    logging.info("[vivado raw] ok")