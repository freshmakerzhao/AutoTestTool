import logging
from CORE.process_runner import run_base_task

def run_base_cli(args):
    try:
        out_path = run_base_task(
            file=args.file,
            device=args.device,
            file_suffix=args.file_suffix,
            pcie=args.PCIE,
            gtp=args.GTP,
            crc=args.CRC,
            compress=args.COMPRESS,
            trim=args.TRIM,
            delete_ghigh=args.DELETE_GHIGH,
            readback_refresh=args.readback_refresh,
            timer_refresh=args.timer_refresh
        )
        logging.info(f"输出文件保存至: {out_path}")
    except Exception as exc:
        logging.error("[BASE ERROR] %s", exc)
