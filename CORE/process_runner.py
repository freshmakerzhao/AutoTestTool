import logging
import COMMON.frame_structure as frame_structure
from CORE.bitstream_parser import BitstreamParser
from CORE import module_base, module_crc, module_refresh, module_vccm, module_convert
import os,copy, traceback
from typing import List, Dict

FILE_ENDWITH = "_new"

def run_base_task(
    file, 
    device = "MC1P110", 
    file_suffix = FILE_ENDWITH,
    pcie = False, 
    gtp = False, 
    crc = False, 
    compress = False,
    trim = False, 
    delete_ghigh = False,
    readback_refresh = None, 
    timer_refresh=None,
):
    dev = frame_structure.DEVICE_MAP.get(device.upper(), "MC1P110")
    bitstream_obj = BitstreamParser(dev, file, crc)

    if gtp:
        module_base.process_gtp_config(bitstream_obj)

    if pcie:
        module_base.process_pcie_config(bitstream_obj)

    if trim:
        module_base.process_trim(bitstream_obj)

    if delete_ghigh:
        module_base.delete_ghigh(bitstream_obj)

    if timer_refresh:
        module_refresh.timer_refresh(bitstream_obj, timer_refresh)

    if readback_refresh:
        module_refresh.readback_refresh(bitstream_obj, readback_refresh)

    if crc:
        module_crc.calculate_crc(bitstream_obj)
    else:
        module_crc.disable_crc(bitstream_obj)

    if compress:
        module_base.process_compress(bitstream_obj)
        
    if file_suffix is None:
        file_suffix = FILE_ENDWITH
    return bitstream_obj.save_file(file_suffix)

VCCM_VALUES_LIST = [
    {"vccm_value": 105, "file_suffix": "vccm_1p05"},
    {"vccm_value": 106, "file_suffix": "vccm_1p06"},
    {"vccm_value": 107, "file_suffix": "vccm_1p07"},
    {"vccm_value": 108, "file_suffix": "vccm_1p08"},
    {"vccm_value": 109, "file_suffix": "vccm_1p09"},
    {"vccm_value": 110, "file_suffix": "vccm_1p10"},
    {"vccm_value": 111, "file_suffix": "vccm_1p11"},
    {"vccm_value": 112, "file_suffix": "vccm_1p12"},
    {"vccm_value": 115, "file_suffix": "vccm_1p15"},
]

VSWL_FILE_SUFFIX_MAP = {
    "1075": "wl_1p075",
    "1100": "wl_1p100",
    "1125": "wl_1p125",
    "1150": "wl_1p150",
    "1175": "wl_1p175",
    "1200": "wl_1p200",
    "1225": "wl_1p225",
    "1250": "wl_1p250",
    "1275": "wl_1p275",
    "1300": "wl_1p300",
    "1325": "wl_1p325",
    "1350": "wl_1p350",
    "1375": "wl_1p375",
    "1400": "wl_1p400",
    "1425": "wl_1p425",
    "1450": "wl_1p450",
    "1475": "wl_1p475",
    "1500": "wl_1p500",
}

# vccm_values 可选
def run_vccm_task(file_path: str, vccm_values: List[int] = None, vswl_selected: int = 1050):
    vccm_items = _filter_vccm_items(vccm_values)
    stats = None
    # 单个文件时
    if os.path.isfile(file_path):
        try:
            isSuccuss = _process_one_file(file_path, os.path.dirname(file_path), vccm_items, error_log_path=None, vswl_selected=vswl_selected)
            if isSuccuss:
                stats = {"total_files": 1, "success_count": 1, "fail_count": 0, "error_log_path": None}
            else:
                stats = {"total_files": 1, "success_count": 0, "fail_count": 1, "error_log_path": os.path.join(os.path.dirname(file_path), "vccm_error.log")}
        except Exception:
            stats = {"total_files": 1, "success_count": 0, "fail_count": 1, "error_log_path": os.path.join(os.path.dirname(file_path), "vccm_error.log")}
    # 文件夹时
    elif os.path.isdir(file_path):
        stats = _process_folder(file_path, vccm_items, vswl_selected=vswl_selected)
    else:
        logging.error(f"[VCCM ERROR] 无效路径：{file_path}")
    return stats

def run_vccm_project(project_root: str, vccm_values: List[int] = None, vswl_selected: int = 1050):
    if not os.path.isdir(project_root):
        logging.error(f"[VCCM ERROR] 非法目录：{project_root}")
        return

    # 这里只向下找一级
    subdirs = [d for d in os.listdir(project_root)
               if os.path.isdir(os.path.join(project_root, d))]

    logging.info(f"[VCCM INFO] 扫描子模块目录：{len(subdirs)} 个")

    project_total, project_success, project_fail = 0, 0, 0
    project_stats = {}
    for sub in subdirs:
        sub_path = os.path.join(project_root, sub)
        logging.info(f"[VCCM INFO] ▶ 开始处理子目录：{sub}")
        stats = run_vccm_task(sub_path, vccm_values=vccm_values, vswl_selected=vswl_selected)
        if stats:
            project_total += stats["total_files"]
            project_success += stats["success_count"]
            project_fail += stats["fail_count"]
    project_stats["project_subdirs"] = len(subdirs)
    project_stats["total_files"] = project_total
    project_stats["success_count"] = project_success
    project_stats["fail_count"] = project_fail
    summary = (
        f"[VCCM 批处理完成]\n"
        f"共处理模块目录: {len(subdirs)}\n"
        f"总文件数:   {project_total}\n"
        f"成功处理:   {project_success}\n"
        f"失败跳过:   {project_fail}"
    )
    logging.info("\n" + summary)
    return project_stats

# 处理单个文件，error_log_path为None时，错误日志与file_path同级
def _process_one_file(file_path: str, root_folder: str, vccm_items:List[Dict], error_log_path=None, vswl_selected: int = 1050):
    try:
        bitstream_obj = BitstreamParser("MC1P110", file_path, False)
        logging.info(f"[VCCM INFO] 正在处理：{file_path}")

        file_name = os.path.basename(file_path)
        file_name_no_type = os.path.splitext(file_name)[0]  # 去掉扩展名
        parent_dir = os.path.basename(os.path.dirname(file_path)) # 获取上一级文件夹名称

        all_failed = True  # 记录是否所有电压值都失败

        for item in vccm_items:
            try:
                new_obj = copy.deepcopy(bitstream_obj)
                module_vccm.process_vccm_and_vswl(new_obj, item["vccm_value"], vswl_selected)

                # 输出目录为 root_folder/vccm_1pXX/
                file_suffix = item["file_suffix"]
                if str(vswl_selected) in VSWL_FILE_SUFFIX_MAP:
                    file_suffix = f"{file_suffix}_{VSWL_FILE_SUFFIX_MAP[str(vswl_selected)]}"
                output_dir = os.path.join(root_folder, file_suffix)
                os.makedirs(output_dir, exist_ok=True)
                # 不带文件类型的path
                out_path = os.path.join(
                    output_dir,
                    f"{parent_dir}_{file_name_no_type}_{file_suffix}"
                )
                # 关闭crc
                module_crc.disable_crc(new_obj)
                new_obj.save_file(output_file_path=out_path)
                logging.info(f"[VCCM INFO] {out_path} OK")
                all_failed = False
            except Exception as ve:
                _write_error_log(file_path, item["vccm_value"], ve, error_log_path)
        return not all_failed  # 返回 True 表示至少一个电压值处理成功
    except Exception as e:
        _write_error_log(file_path, None, e, error_log_path)
        return False  # 整个文件一开始就处理失败

def _process_folder(root_folder: str, vccm_items:List[Dict], vswl_selected: int = 1050):
    logging.info(f"[VCCM INFO] 正在处理目录：{root_folder}")

    error_log_path = os.path.join(root_folder, "vccm_error.log")
    if os.path.exists(error_log_path):
        os.remove(error_log_path)
        logging.warning(f"[VCCM WARNING] 已清理旧日志：{error_log_path}")

    # 初始化计数器
    total_files = 0
    success_count = 0
    fail_count = 0

    for dirpath, dirnames, filenames in os.walk(root_folder):
        # 跳过以 vccm_ 开头的子目录
        dirnames[:] = [d for d in dirnames if not d.startswith("vccm_")]
        for fname in filenames:
            if fname.endswith((".bit", ".bin", ".rbt")):
                full_path = os.path.join(dirpath, fname)
                total_files += 1
                
                ok = _process_one_file(full_path, root_folder, vccm_items, error_log_path, vswl_selected)
                if ok:
                    success_count += 1
                else:
                    fail_count += 1
    return {
        "total_files": total_files,
        "success_count": success_count,
        "fail_count": fail_count,
        "error_log_path": error_log_path if fail_count > 0 else None
    }

# 记录报错日志
def _write_error_log(file_path: str, vccm_value, exception_obj, log_file_path=None):
    log_file = log_file_path or os.path.join(os.path.dirname(file_path), "vccm_error.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n[VCCM ERROR] file: {file_path}\n")
        if vccm_value:
            f.write(f"  ➤ vccm_value: {vccm_value}\n")
        f.write(f"  ➤ error: {str(exception_obj)}\n")
        import traceback
        f.write(traceback.format_exc())
        f.write("-" * 60 + "\n")
    logging.warning(f"[VCCM WARNING] 处理出错：{file_path}（已记录）")

def _filter_vccm_items(selected_values: None):
    # 如果没有传入值，则使用所有电压
    if not selected_values:
        return VCCM_VALUES_LIST
    # 仅支持列出来的值
    return [item for item in VCCM_VALUES_LIST if item["vccm_value"] in selected_values]

def run_convert_task(file_path: str, to_fmt: str, output_path: str = None):
    try:
        logging.info(f"[CONVERT INFO] 正在处理文件：{file_path}")
        bitstream_obj = BitstreamParser("MC1P110", file_path, False)

        stats = module_convert.process_convert(bitstream_obj, to_fmt)
        if stats.get("code",400) == 400:
            logging.error(f"[CONVERT ERROR] {stats['msg']}")
            return stats

    except Exception as e:
        logging.error(f"[CONVERT ERROR] {e}")
    