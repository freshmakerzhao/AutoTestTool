# bit_tool/gui/pages/page_c.py
from tkinter import ttk
import os, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from GUI.COMPONENT.thread_utils import run_in_thread
import logging
import subprocess
import COMMON.utils as utils
import json
import csv

SPECIAL_VALUE = {
    "00": "00",   
    "AA": "10",
    "55": "01",
    "FF": "11"
}

class PageDVivadoRDCheck(ttk.Frame):
    """vivado 回读测试"""
    def __init__(self, master, app_ctx, **kw):
        super().__init__(master, **kw)
        self.app_ctx = app_ctx
        self.columnconfigure(0, weight=1)
        self.build_ui()
        
    def build_ui(self):
        # --------------------- Vivado 路径选择 开始 ---------------------
        vivado_row = ttk.Frame(self)
        vivado_row.grid(row=0, column=0, sticky="ew", pady=6)
        vivado_row.columnconfigure(1, weight=1)
        ttk.Label(vivado_row, text="Vivado bin路径:").grid(row=0, column=0, sticky=tk.W)
        self.vivado_bin_path_var = tk.StringVar()
        ttk.Entry(vivado_row, textvariable=self.vivado_bin_path_var)\
            .grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(vivado_row, text="浏览...", command=self.browse_vivado_path)\
            .grid(row=0, column=2, padx=4)
        # --------------------- Vivado 路径选择 结束 ---------------------

        # === 模式选择 ===
        mode_row = ttk.Frame(self); mode_row.grid(row=1, column=0, sticky="w", pady=6)
        ttk.Label(mode_row, text="执行模式：").grid(row=1, column=0, sticky=tk.W)
        self.mode_var = tk.StringVar(value="single")
        for idx, (txt, val) in enumerate([("单文件模式", "single"), ("批处理模式", "batch"), ("仅compare模式", "compare")]):
            ttk.Radiobutton(mode_row, text=txt, variable=self.mode_var, value=val, command=self.update_mode)\
                .grid(row=1, column=idx+1, padx=6, sticky="w")

        # === 单文件输入区域 ===
        self.single_frame = ttk.Frame(self); self.single_frame.grid(row=2, column=0, sticky="ew", pady=6)
        self.single_frame.columnconfigure(0, weight=1)
        self._build_single_mode()

        # === 批处理输入区域 ===
        self.batch_frame = ttk.Frame(self); self.batch_frame.grid(row=3, column=0, sticky="ew", pady=6)
        self.batch_frame.columnconfigure(0, weight=1)
        self._build_batch_mode()
        
        # === 仅compare ===
        self.compare_frame = ttk.Frame(self); self.compare_frame.grid(row=4, column=0, sticky="ew", pady=6)
        self.compare_frame.columnconfigure(0, weight=1)
        self._build_compare_mode()

        # === 执行按钮 ===
        btn_row = ttk.Frame(self); btn_row.grid(row=5, column=0, pady=10)
        self.run_btn = ttk.Button(btn_row, text="执行回读校验", command=self.on_run)
        self.run_btn.pack(side="left", padx=6)
        self.clear_btn = ttk.Button(btn_row, text="清空日志", command=self.clear_log)
        self.clear_btn.pack(side="left", padx=6)

        # === 日志输出 ===
        self.log_text = tk.Text(self, height=10, state="disabled")
        self.log_text.grid(row=6, column=0, sticky="nsew")
        self.rowconfigure(6, weight=1)

        self.update_mode()
        
    def _build_single_mode(self):
        # --- 码流文件 bitstream_var ---
        row1 = ttk.Frame(self.single_frame)
        row1.grid(row=0, column=0, sticky="ew", pady=6)
        row1.columnconfigure(1, weight=1)
        ttk.Label(row1, text="码流文件:").grid(row=0, column=0, sticky=tk.W)
        self.bitstream_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.bitstream_var).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(row1, text="浏览...", command=self.browse_bitstream).grid(row=0, column=2, padx=4)

        # --- 掩码文件 mask_var ---
        row3 = ttk.Frame(self.single_frame)
        row3.grid(row=1, column=0, sticky="ew", pady=6)
        row3.columnconfigure(1, weight=1)
        ttk.Label(row3, text="掩码文件路径:").grid(row=0, column=0, sticky=tk.W)
        self.mask_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.mask_var).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(row3, text="浏览...", command=self.browse_mask).grid(row=0, column=2, padx=4)
        
        # --- Gold 文件路径选择 gold_var ---
        gold_row = ttk.Frame(self.single_frame)
        gold_row.grid(row=2, column=0, sticky="ew", pady=6)
        gold_row.columnconfigure(1, weight=1)
        ttk.Label(gold_row, text="GOLD 文件路径:").grid(row=0, column=0, sticky=tk.W)
        self.gold_var = tk.StringVar()
        ttk.Entry(gold_row, textvariable=self.gold_var).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(gold_row, text="浏览...", command=self.browse_gold_file).grid(row=0, column=2, padx=4)
        
        # --- 输出文件目录 output_var ---
        output_row = ttk.Frame(self.single_frame)
        output_row.grid(row=3, column=0, sticky="ew", pady=6)
        output_row.columnconfigure(1, weight=1)
        ttk.Label(output_row, text="输出文件目录:").grid(row=0, column=0, sticky=tk.W)
        self.output_var = tk.StringVar()
        ttk.Entry(output_row, textvariable=self.output_var).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(output_row, text="浏览...", command=self.browse_output).grid(row=0, column=2, padx=4)
        
        # --------------------- 特征值选择 ---------------------
        special_row = ttk.Frame(self.single_frame)
        special_row.grid(row=4, column=0, sticky="ew", pady=6)
        ttk.Label(special_row, text="特征值:").grid(row=0, column=0, sticky=tk.W)
        self.special_var = tk.StringVar(value="00")
        self.special_options = ["00", "55", "AA", "FF", "led_run"]
        self.special_combo = ttk.Combobox(special_row, textvariable=self.special_var, values=self.special_options, state="readonly", width=10)
        self.special_combo.grid(row=0, column=1, sticky="w", padx=4)

    def _build_batch_mode(self):
        row = ttk.Frame(self.batch_frame); row.grid(row=0, column=0, sticky="ew", pady=6)
        row.columnconfigure(1, weight=1)
        ttk.Label(row, text="配置文件 (batch_config.json):").grid(row=0, column=0, sticky=tk.W)
        self.batch_config_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.batch_config_var).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(row, text="浏览...", command=self.browse_batch_config).grid(row=0, column=2, padx=4)

    # 仅需要rbd、msd、gold文件和输出目录
    def _build_compare_mode(self):
        # --- 回读文件 readback_var ---
        row0 = ttk.Frame(self.compare_frame)
        row0.grid(row=0, column=0, sticky="ew", pady=6)
        row0.columnconfigure(1, weight=1)
        ttk.Label(row0, text="回读文件:").grid(row=0, column=0, sticky=tk.W)
        self.readback_var = tk.StringVar()
        ttk.Entry(row0, textvariable=self.readback_var).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(row0, text="浏览...", command=self.browse_readback).grid(row=0, column=2, padx=4)
        
        # --- 掩码文件 mask_var ---
        row1 = ttk.Frame(self.compare_frame)
        row1.grid(row=1, column=0, sticky="ew", pady=6)
        row1.columnconfigure(1, weight=1)
        ttk.Label(row1, text="掩码文件路径:").grid(row=0, column=0, sticky=tk.W)
        self.mask_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.mask_var).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(row1, text="浏览...", command=self.browse_mask).grid(row=0, column=2, padx=4)
        
        # --- Gold 文件路径选择 gold_var ---
        row2 = ttk.Frame(self.compare_frame)
        row2.grid(row=2, column=0, sticky="ew", pady=6)
        row2.columnconfigure(1, weight=1)
        ttk.Label(row2, text="GOLD 文件路径:").grid(row=0, column=0, sticky=tk.W)
        self.gold_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.gold_var).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(row2, text="浏览...", command=self.browse_gold_file).grid(row=0, column=2, padx=4)
        
        # --- 输出文件目录 output_var ---
        row3 = ttk.Frame(self.compare_frame)
        row3.grid(row=3, column=0, sticky="ew", pady=6)
        row3.columnconfigure(1, weight=1)
        ttk.Label(row3, text="输出文件目录:").grid(row=0, column=0, sticky=tk.W)
        self.output_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.output_var).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(row3, text="浏览...", command=self.browse_output).grid(row=0, column=2, padx=4)
        
        # --------------------- 特征值选择 ---------------------
        special_row = ttk.Frame(self.compare_frame)
        special_row.grid(row=4, column=0, sticky="ew", pady=6)
        ttk.Label(special_row, text="特征值:").grid(row=0, column=0, sticky=tk.W)
        self.special_var = tk.StringVar(value="00")
        self.special_options = ["00", "55", "AA", "FF", "led_run"]
        self.special_combo = ttk.Combobox(special_row, textvariable=self.special_var, values=self.special_options, state="readonly", width=10)
        self.special_combo.grid(row=0, column=1, sticky="w", padx=4)

    def update_mode(self):
        mode = self.mode_var.get()
        self.single_frame.grid_remove()
        self.batch_frame.grid_remove()
        self.compare_frame.grid_remove()
        if mode == "single":
            self.single_frame.grid()
        elif mode == "batch":
            self.batch_frame.grid()
        elif mode == "compare":
            self.compare_frame.grid()
    
    def browse_vivado_path(self):
        path = filedialog.askdirectory(title="选择 Vivado 安装目录")
        if path:
            self.vivado_bin_path_var.set(path)

    
    def browse_readback(self):
        path = filedialog.askopenfilename(
            filetypes=[("Readback file", "*.rbd")],
            title="选择回读文件"
        )
        if path:
            self.readback_var.set(path)
    
    def browse_bitstream(self):
        path = filedialog.askopenfilename(
            filetypes=[("Bitstream", "*.bit *.rbt")],
            title="选择 bit/rbt 码流文件"
        )
        if path:
            self.bitstream_var.set(path)

    def browse_gold_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("gold file", "*.rbt")],
            title="选择 gold 文件"
        )
        if path:
            self.gold_var.set(path)
            
    def browse_batch_config(self):
        path = filedialog.askopenfilename(
            filetypes=[("config.json file", "*.json")],
            title="选择 config.json 配置文件"
        )
        if path:
            self.batch_config_var.set(path)
            
    def browse_mask(self):
        path = filedialog.askopenfilename(
            filetypes=[("msd file", "*.msd")],
            title="选择 msd 掩码文件"
        )
        if path:
            self.mask_var.set(path)

    def browse_output(self):
        path = filedialog.askdirectory(title="选择一个输出目录")
        self.output_var.set(path)
        if path:
            self.output_var.set(path)

    def _parse_json_config(self, config_path: str):
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config_data = json.load(f)
            except json.JSONDecodeError:
                logging.error(f"The file {config_path} is not a valid JSON file.\n")
                self._after_error(f"The file {config_path} is not a valid JSON file.")
                return False
            except IOError:
                logging.error(f"Unable to read the file {config_path}.\n")
                self._after_error(f"Unable to read the file {config_path}.")
                return False
        else:
            logging.error(f"The file {config_path} does not exist.")
            self._after_error(f"The file {config_path} does not exist.")
            return False

        result_root = config_data.get("result_root_path", "")
        bit_group = config_data.get("bit_group", {})

        bitstream_file_paths = []
        readback_file_paths = []
        mask_file_paths = []
        gold_paths = []
        result_paths = []
        special_values = []

        for special_value, info in bit_group.items():
            # 拼接生成回读和结果文件路径
            result_file_path = os.path.join(result_root, f"{special_value}_result.rbt")
            readback_file_path = os.path.join(result_root, f"{special_value}.rbd")
            status_csv_path = os.path.join(result_root, f"status.csv")

            if special_value == "led_run":
                result_file_path = ""
                
            # 添加到列表
            bitstream_file_paths.append(info.get("bit_path", ""))
            mask_file_paths.append(info.get("msd_path", ""))
            gold_paths.append(info.get("gold_path", ""))
            result_paths.append(result_file_path)
            readback_file_paths.append(readback_file_path)
            special_values.append(special_value)

        return dict(
            bitstream_file_paths = bitstream_file_paths,
            readback_file_paths = readback_file_paths,
            mask_file_paths = mask_file_paths,
            gold_paths = gold_paths,
            result_paths = result_paths,
            special_values = special_values,
            status_csv_path = status_csv_path
        )

    def on_run(self):
        # 禁用按钮，防止重复点击
        self.run_btn.config(state="disabled")
        cur_mode = self.mode_var.get()
        
        if cur_mode == "single":
            vivado_bin_path = self.vivado_bin_path_var.get().strip()
            if not vivado_bin_path or not os.path.exists(vivado_bin_path):
                self._after_error("请设置正确的 Vivado bin 路径！")
                return
            if not vivado_bin_path:
                self._after_error("请设置vivado bin路径！")
                return
        elif cur_mode == "batch":
            vivado_bin_path = self.vivado_bin_path_var.get().strip()
            if not vivado_bin_path or not os.path.exists(vivado_bin_path):
                self._after_error("请设置正确的 Vivado bin 路径！")
                return
            if not vivado_bin_path:
                self._after_error("请设置vivado bin路径！")
                return
        
        special_value = self.special_var.get().strip()
        if cur_mode == "single":
            bit_file_path = self.bitstream_var.get().strip()
            mask_file_path = self.mask_var.get().strip()
            gold_file_path = self.gold_var.get().strip()
            output_file_path = self.output_var.get().strip()

            result_file_path = os.path.join(output_file_path, f"{special_value}_result.rbt")
            readback_file_path = os.path.join(output_file_path, f"{special_value}.rbd")
            status_csv_path = os.path.join(output_file_path, f"status.csv")
            
            # 特殊情况：led_run 不需要 result 文件
            if special_value == "led_run":
                result_file_path = ""
                
            try:
                # 删除已存在的 readback 文件
                if os.path.exists(readback_file_path):
                    os.remove(readback_file_path)
            except Exception as e:
                logging.warning(f"无法删除 {readback_file_path}: {e}")

            try:
                # 删除已存在的 result 文件（除非是 led_run）
                if result_file_path and os.path.exists(result_file_path):
                    os.remove(result_file_path)
            except Exception as e:
                logging.warning(f"无法删除 {result_file_path}: {e}")
                            
            if not os.path.isfile(bit_file_path):
                self._after_error("无效的码流文件路径！")
                return
            if not output_file_path:
                self._after_error("请设置输出文件目录！")
                return
            
            if not gold_file_path:
                self._after_error("请设置 GOLD 文件路径！")
                return

            kwargs = dict(
                vivado_bin_path=vivado_bin_path,
                bitstream_file_paths=[bit_file_path],
                readback_file_paths=[readback_file_path],
                mask_file_paths=[mask_file_path],
                gold_paths=[gold_file_path],
                result_paths=[result_file_path],
                special_values=[special_value],
                status_csv_path=status_csv_path
            )
            
            run_in_thread(
                self,
                self._run_vivado_process,
                lock_widget=self.run_btn,
                on_success=self._after_success,
                on_error=self._after_error,
                **kwargs
            )

        elif cur_mode == "batch":
            config_path = self.batch_config_var.get().strip()
            if not os.path.isfile(config_path):
                self._after_error("请提供有效的config json 文件路径！")
                return
            try:
                config_list = self._parse_json_config(config_path)
                config_list["vivado_bin_path"] = vivado_bin_path
            except Exception as e:
                self._after_error(f"配置文件解析失败：{e}")
                return
            if not config_list:
                self._after_error(f"配置文件解析失败：{e}")
                return
                
            kwargs = config_list
            
            run_in_thread(
                self,
                self._run_vivado_process,
                lock_widget=self.run_btn,
                on_success=self._after_success,
                on_error=self._after_error,
                **kwargs
            )
        elif cur_mode == "compare":
            readback_file_path = self.readback_var.get().strip()
            mask_file_path = self.mask_var.get().strip()
            gold_file_path = self.gold_var.get().strip()
            output_file_path = self.output_var.get().strip()
            
            result_file_path = os.path.join(output_file_path, f"{special_value}_result.rbt")
            
            # 特殊情况：led_run 不需要 result 文件
            if special_value == "led_run":
                result_file_path = ""
             
            try:
                # 删除已存在的 result 文件（除非是 led_run）
                if result_file_path and os.path.exists(result_file_path):
                    os.remove(result_file_path)
            except Exception as e:
                logging.warning(f"无法删除 {result_file_path}: {e}")
                
            if not os.path.isfile(readback_file_path):
                self._after_error("无效的回读文件路径！")
                return
            if not output_file_path:
                self._after_error("请设置输出文件目录！")
                return
            if not os.path.isfile(gold_file_path):
                self._after_error("无效的 GOLD 文件路径！")
                return
            # 打印所有参数
            logging.info("=======================================================")
            logging.info(f"[vivado 回读校验] 执行参数: \n"
                         f"readback_file_path = {readback_file_path}, \n"
                         f"mask_file_path = {mask_file_path}, \n"
                         f"gold_file_path = {gold_file_path}, \n"
                         f"result_file_path = {result_file_path}, \n"
                         f"special_value = {special_value}")
            logging.info("=======================================================")
            kwargs = {
                "mask_file_path": mask_file_path,
                "readback_file_path": readback_file_path,
                "gold_file_path": gold_file_path,
                "special_value": special_value,
                "result_file_path": result_file_path
            }
            run_in_thread(
                self,
                self._run_compare,
                lock_widget=self.run_btn,
                on_success=self._after_success,
                on_error=self._after_error,
                **kwargs
            )
            
    def _run_compare(self, mask_file_path, readback_file_path, gold_file_path, special_value, result_file_path):
        if special_value in ["00","AA","55","FF"]:
            if not self._compare_files(mask_file_path, readback_file_path, gold_file_path, special_value, result_file_path):
                logging.error(f"[vivado 回读校验] {special_value} 比对失败: {result_file_path}")
            else:
                logging.info(f"[vivado 回读校验] 比对通过 PASS")
        else:
            if not self._compare_func_files(mask_file_path, readback_file_path, gold_file_path):
                logging.error(f"[vivado 回读校验] {special_value} 比对失败: {result_file_path}")
            else:
                logging.info(f"[vivado 回读校验] 比对通过 PASS")
                
    def _run_vivado_process(self, 
                            *, 
                            vivado_bin_path, 
                            bitstream_file_paths, 
                            readback_file_paths, 
                            mask_file_paths, 
                            gold_paths, 
                            result_paths, 
                            special_values, 
                            status_csv_path
        ):
        is_all_pass = True
        logging.info(f"[vivado 回读校验] 开始处理")
        program_script  = utils.resource_path("RESOURCE/SCRIPTS/program.tcl")
        readback_script = utils.resource_path("RESOURCE/SCRIPTS/readback.tcl")
        vivado_bat_path = os.path.join(vivado_bin_path, "vivado.bat")
        
        if not os.path.exists(program_script):
            raise RuntimeError(f"program.tcl 文件未找到: {program_script}")
        if not os.path.exists(readback_script):
            raise RuntimeError(f"readback.tcl 文件未找到: {readback_script}")
        if not os.path.exists(vivado_bat_path):
            raise RuntimeError(f"Vivado.bat 文件未找到: {vivado_bat_path}")
        if len(bitstream_file_paths) != len(readback_file_paths) \
            or len(bitstream_file_paths) != len(mask_file_paths) \
            or len(bitstream_file_paths) != len(gold_paths) \
            or len(bitstream_file_paths) != len(special_values) \
            or len(bitstream_file_paths) != len(result_paths):
            raise RuntimeError("参数长度不匹配，请检查选项或config.json文件")
        
        for bitstream_file_path, readback_file_path, mask_file_path, gold_path, result_path, special_value in zip(bitstream_file_paths, readback_file_paths, mask_file_paths, gold_paths, result_paths, special_values):
            
            # 打印所有参数
            logging.info("=======================================================")
            logging.info(f"[vivado 回读校验] 执行参数: \n"
                         f"vivado_bin_path = {vivado_bin_path}, \n"
                         f"bit_file_path = {bitstream_file_path}, \n"
                         f"mask_file_path = {mask_file_path}, \n"
                         f"gold_file_path = {gold_path}, \n"
                         f"readback_file_path = {readback_file_path}, \n"
                         f"result_file_path = {result_path}, \n"
                         f"status_csv_path = {status_csv_path}, \n"
                         f"special_value = {special_value}")
            logging.info("=======================================================")
            
            cur_special_value_status = True
            cur_status = {
                "special_value": special_value,
                "status": "PASS",
                "readback_file": readback_file_path,
            }
            if not self._program_bitstream_file(vivado_bat_path, program_script, bitstream_file_path):
                logging.error(f"[vivado 回读校验] 烧写 bitstream 文件失败: {bitstream_file_path}")
                cur_special_value_status = False
                is_all_pass = False
                cur_status["status"] = "FAIL"
                cur_status["readback_file"] = "/"
                logging.error(f"[vivado 回读校验] 跳过当前case")
                self._append_status_csv(cur_status, status_csv_path)
                continue

            try:
                # 删除已存在的 readback 文件
                if os.path.exists(readback_file_path):
                    os.remove(readback_file_path)
            except Exception as e:
                logging.warning(f"无法删除 {readback_file_path}: {e}")

            try:
                # 删除已存在的 result 文件（除非是 led_run）
                if result_path and os.path.exists(result_path):
                    os.remove(result_path)
            except Exception as e:
                logging.warning(f"无法删除 {result_path}: {e}")
                
            if not self._readback_file(vivado_bat_path, readback_script, readback_file_path):
                logging.error(f"[vivado 回读校验] 回读 rbd 文件失败: {readback_file_path}")
                cur_special_value_status = False
                is_all_pass = False
                cur_status["status"] = "FAIL"
                cur_status["readback_file"] = "/"
                logging.error(f"[vivado 回读校验] 跳过当前case")
                self._append_status_csv(cur_status, status_csv_path)
                continue
                
            if special_value in ["00","AA","55","FF"]:
                if not self._compare_files(mask_file_path, readback_file_path, gold_path, special_value, result_path):
                    logging.error(f"[vivado 回读校验] {special_value} 比对失败: {result_path}")
                    cur_special_value_status = False
                else:
                    logging.info(f"[vivado 回读校验] 比对通过 PASS")
            else:
                if not self._compare_func_files(mask_file_path, readback_file_path, gold_path):
                    logging.error(f"[vivado 回读校验] {special_value} 比对失败: {result_path}")
                    cur_special_value_status = False
                else:
                    logging.info(f"[vivado 回读校验] 比对通过 PASS")

            if not cur_special_value_status:
                is_all_pass = False
                cur_status["status"] = "FAIL"
                
            self._append_status_csv(cur_status, status_csv_path)
                    
        if not is_all_pass:
            logging.info(f"[vivado 回读校验] ========= 存在 FAIL 查看 {status_csv_path} =========")
            return False
        else:
            logging.info(f"[vivado 回读校验] ========= ALL PASS =========")
            return True
        
    def _append_status_csv(self, status_dict: dict, output_path: str):
        """将每个回读校验结果追加写入到 CSV 文件中"""
        file_exists = os.path.isfile(output_path)
        with open(output_path, mode="a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["special_value", "status", "readback_file"])
            if not file_exists:
                writer.writeheader()
            writer.writerow(status_dict)
            
    def _program_bitstream_file(self, vivado_bat_path, program_script, bitstream_file):
        """烧写 bitstream 文件到 FPGA"""
        cmd = [
            vivado_bat_path, "-mode", "batch",
            "-log", "NUL", "-journal", "NUL",
            "-source", program_script,
            "-tclargs", bitstream_file
        ]
        # 设置 startupinfo 来隐藏窗口
        result = subprocess.run(
            cmd, 
            capture_output=False, 
            text=True
        )
        logging.info(f"[vivado 回读校验] 烧写 {bitstream_file} 完成")
        if result.returncode != 0:
            return False
        else:
            return True
    
    def _readback_file(self, vivado_bat_path, readback_script, readback_file):
        """回读 FPGA 中的 bitstream 文件到指定路径"""
        cmd = [
            vivado_bat_path, "-mode", "batch",
            "-log", "NUL", "-journal", "NUL",
            "-source", readback_script,
            "-tclargs", readback_file
        ]
        result = subprocess.run(
            cmd, 
            capture_output=False, 
            text=True
        )
        logging.info(f"[vivado 回读校验] 回读 {readback_file} 完成")
        if result.returncode != 0:
            return False
        else:
            return True
    
    def _compare_func_files(self, mask_file_path, readback_file_path, gold_path):
        # 打开掩码文件和读出文件
        with open(mask_file_path, 'r') as mask_file, open(readback_file_path, 'r') as readout_file, open(gold_path, 'r') as gold_file:
            # 逐行读取文件内容
            mask_lines = mask_file.readlines()
            readout_lines = readout_file.readlines()
            gold_lines = gold_file.readlines()
        
        # 逐字符比较
        for idx, (mask_line, readout_line, gold_line) in enumerate(zip(mask_lines, readout_lines, gold_lines)):
            mask = mask_line.strip()
            readout = readout_line.strip()
            gold = gold_line.strip()
            # 检查长度是否一致
            if not (len(mask) == len(readout) == len(gold)):
                return False
            for pos, (m, r, g) in enumerate(zip(mask, readout, gold)):
                if m == '1':
                    # Mask 为 '1'，跳过比较
                    continue
                if r != g:
                    return False
        return True
    
    def _compare_files(self, mask_file_path, readback_file_path, gold_path, special_value, result_path):
        sp_value = SPECIAL_VALUE.get(special_value, "11")
        # 打开掩码文件和读出文件
        with open(mask_file_path, 'r') as mask_file, open(readback_file_path, 'r') as readout_file:
            # 逐行读取文件内容
            mask_lines = mask_file.readlines()
            readout_lines = readout_file.readlines()
            count = 0

        # 创建一个新文件来保存修改后的读出文件内容
        result_content = []
        for mask_line, readout_line in zip(mask_lines, readout_lines):
            # 假设每行都是由空格分隔的二进制值
            mask_values = mask_line.strip()
            readout_values = readout_line.strip()
            count += 1

            # 检查一行中的元素数量是否相同
            if len(mask_values) != len(readout_values) or len(mask_values) != 32:
                raise ValueError("Each line in the mask file and readout file must have 32 bits.")

            modified_readout_values = []
            for i in range(0, len(mask_values)-1, 2):  # 每2位为一组
                # 检查掩码中的两个值是否都为1
                if mask_values[i:i+2] == '11':
                    modified_readout_values.extend([sp_value])
                else:
                    # 不需要替换
                    modified_readout_values.extend([readout_values[i], readout_values[i+1]])
                # print(modified_readout_values)
            result_content.append("".join(modified_readout_values))
        
        if not result_path or result_path == "":
            pass
        else:
            with open(result_path, 'w') as output_file:
                for line in result_content:
                    output_file.write(line+'\n')
        
        with open(gold_path, 'r') as gold_file:
            # 逐行读取文件内容
            gold_content = gold_file.readlines()
        gold_len = len(gold_content)
        result_content_len = len(result_content)
        if gold_content[-1] == "":
            gold_content = gold_content[:-1]
            gold_len -= 1
        if result_content[-1] == "":
            modified_readout_values = modified_readout_values[:-1]
            result_content_len -= 1
        if result_content_len != gold_len:
            return False
        # Compare
        for i in range(gold_len):
            if gold_content[i].strip() != result_content[i].strip():
                return False
        return True
    
    def _after_success(self, result=None):
        messagebox.showinfo("完成", "回读校验已完成！")
        self.run_btn.config(state="normal")

    def _after_error(self, exc: Exception):
        messagebox.showerror("错误", str(exc))
        self.run_btn.config(state="normal")

    def clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")

    def reset(self):
        self.bitstream_var.set("")
        self.output_var.set("")
        self.clear_log()

    def clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.config(state="disabled")
