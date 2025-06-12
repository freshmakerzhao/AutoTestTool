import logging
from CORE.process_runner import run_vccm_task, run_vccm_project

def run_vccm_cli(args):
    # 如果output_path未传，则为 ""

    if args.output_path is None:
        args.output_path = ""

    if args.file and args.project:
        logging.error("[ERROR] file 与 project 参数不能同时存在")
        return
    if args.file:
        try:
            stats = run_vccm_task(args.file, vccm_values=[115], vswl_selected=125, output_path=args.output_path)
            if not stats:
                logging.error("[ERROR] 文件路径无效或处理失败")
            elif stats["success_count"] == 0:
                logging.error(f"[ERROR] 所有文件均处理失败，详情见日志文件：{stats['log_path']}")
            else:
                logging.info("[INFO] 处理成功")
        except Exception as exc:
            logging.error("[ERROR] %s", exc)

    elif args.project:
        stats = run_vccm_task(args.project, vccm_values=[115], vswl_selected=125, output_path=args.output_path)
        if stats:
            summary = (
                f"[目录处理完成]\n"
                f"总文件数:   {stats['total_files']}\n"
                f"成功处理数: {stats['success_count']}\n"
                f"失败跳过数: {stats['fail_count']}\n"
                f"错误日志: {stats['error_log_path']}"
            )
            logging.info(summary)
    else:
        logging.warning("[WARNING] 未提供 --file 或 --project 参数")