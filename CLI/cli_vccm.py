import logging
from CORE.process_runner import run_vccm_task, run_vccm_project

def run_vccm_cli(args):
    if args.vccm_values:
        for v in args.vccm_values:
            if v < 105 or v > 115:
                raise ValueError(f"非法电压值: {v}，仅支持 105~115")

    if args.file:
        try:
            stats = run_vccm_task(args.file, vccm_values=args.vccm_values)
            if not stats:
                logging.error("[VCCM ERROR] 文件路径无效或处理失败")
            elif stats["success_count"] == 0:
                logging.error(f"[VCCM ERROR] 所有文件均处理失败，详情见日志文件：{stats['log_path']}")
            else:
                logging.info("[VCCM INFO] VCCM 处理成功")
        except Exception as exc:
            logging.error("[VCCM ERROR] %s", exc)

    elif args.project:
        stats = run_vccm_project(args.project, vccm_values=args.vccm_values)
        if stats:
            summary = (
                f"[VCCM 项目处理完成]\n"
                f"模块目录数: {stats['project_subdirs']}\n"
                f"总文件数:   {stats['total_files']}\n"
                f"成功处理数: {stats['success_count']}\n"
                f"失败跳过数: {stats['fail_count']}"
            )
            logging.info(summary)
    else:
        logging.warning("[VCCM WARNING] 未提供 --file 或 --project 参数")

