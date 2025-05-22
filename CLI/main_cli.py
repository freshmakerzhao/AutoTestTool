import argparse, logging, sys
from CORE.process_runner import run_task, run_vccm, run_vccm_project

def main():
    parser = argparse.ArgumentParser(description="Auto Process")
    parser.add_argument('--file', type=str, help="输入 bit/rbt 文件")
    parser.add_argument('--device', default="MC1P110")
    parser.add_argument('--file_suffix', type=str ,help="新文件后缀名称")
    parser.add_argument('--PCIE', action='store_true')
    parser.add_argument('--GTP', action='store_true')
    parser.add_argument('--CRC', action='store_true')
    parser.add_argument('--COMPRESS', action='store_true')
    parser.add_argument('--TRIM', action='store_true')
    parser.add_argument('--DELETE_GHIGH', action='store_true')
    parser.add_argument('--readback_refresh', type=str ,help="启用回读刷新，指定发生两比特错误次数的阈值")
    parser.add_argument('--timer_refresh', type=str ,help="启用定时刷新，指定刷新周期")
    
    # ------------- VCCM ----------------
    parser.add_argument('--process_vccm_file', type=str, help="VCCM 处理文件或文件夹路径，传入后将仅处理 VCCM，无需 --file")
    parser.add_argument('--process_vccm_project', type=str, help="项目级批处理：对该路径下的一级子文件夹使用process_vccm_file")
    parser.add_argument(
        '--vccm_values',
        type=int,
        nargs='+',  #  接受多个值，如 105 106 110
        help="指定要处理的 VCCM 电压值（用空格分隔），如：--vccm_values 105 106"
    )
    # ------------- VCCM ----------------

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    
    # ------------- 参数逻辑校验 ----------------
    
    if not args.file and not (args.process_vccm_file or args.process_vccm_project):
        parser.error("必须至少提供 --file 或 --process_vccm_file/process_vccm_project 之一")
        
    if args.vccm_values and not (args.process_vccm_file or args.process_vccm_project):
        parser.error("--vccm_values 必须与 --process_vccm_file 或 --process_vccm_project 搭配使用")
        
    if args.process_vccm_file and args.process_vccm_project:
        parser.error("请勿同时使用 --process_vccm_file 和 --process_vccm_project")
        
    if args.vccm_values:
        for v in args.vccm_values:
            if v < 105 or v > 112:
                parser.error(f"VCCM 电压值仅支持 105~112 之间（非法值：{v}）")
    # ------------- 参数逻辑校验 ----------------

    if args.process_vccm_file:
        try:
            stats = run_vccm(args.process_vccm_file, vccm_values=args.vccm_values)
            if not stats:
                # None时表示路径无效
                return
            if stats["success_count"] == 0:
                logging.error(f"[VCCM ERROR] VCCM 处理失败，请查看日志文件：{stats['log_path']}")
            else:
                logging.info("[VCCM INFO] VCCM 处理成功")
        except Exception as exc:
            logging.error("[VCCM ERROR] %s", exc)
        return
    
    if args.process_vccm_project:
        run_vccm_project(args.process_vccm_project, vccm_values=args.vccm_values)
        return

    try:
        out_path = run_task(
            file = args.file,
            device = args.device,
            file_suffix = args.file_suffix,
            pcie = args.PCIE,
            gtp = args.GTP,
            crc = args.CRC,
            compress = args.COMPRESS,
            trim = args.TRIM,
            delete_ghigh = args.DELETE_GHIGH,
            readback_refresh = args.readback_refresh,
            timer_refresh = args.timer_refresh
        )
        print(f"✅ 输出文件保存至: {out_path}")
    except Exception as exc:
        logging.error("[错误] %s", exc)
        return

if __name__ == "__main__":
    main()
