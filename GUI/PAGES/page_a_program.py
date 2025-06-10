# bit_tool/gui/pages/page_a.py
from tkinter import ttk
import os, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from GUI.COMPONENT.thread_utils import run_in_thread
import logging
import subprocess
import COMMON.utils as utils
import json
import csv

class PageAProgram(ttk.Frame):
    """A 组：烧写码流"""

    def __init__(self, master, app_ctx, **kw):
        super().__init__(master, **kw)
        self.app_ctx = app_ctx
        self.columnconfigure(0, weight=1)
        self.build_ui()
    
    def build_ui(self):

        # --- vivado bin目录选择 -----
        vivado_row = ttk.Frame(self)
        vivado_row.grid(row=0, column=0, sticky="ew", pady=6)
        vivado_row.columnconfigure(1, weight=1)
        ttk.Label(vivado_row, text="Vivado bin路径:").grid(row=0, column=0, sticky=tk.W)
        self.vivado_bin_path_var = tk.StringVar()
        ttk.Entry(vivado_row, textvariable=self.vivado_bin_path_var)\
            .grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(vivado_row, text="浏览...", command=self.browse_vivado_path)\
            .grid(row=0, column=2, padx=4)

        # --- 码流选择 ---
        program_flash_row = ttk.Frame(self)
        program_flash_row.grid(row=1, column=0, sticky="ew", pady=6)
        program_flash_row.columnconfigure(1, weight=1)
        ttk.Label(program_flash_row, text="码流文件(.bin .bit .rbt)").grid(row=0, column=0, sticky=tk.W)
        self.bitstream_var = tk.StringVar()
        ttk.Entry(program_flash_row, textvariable=self.bitstream_var) .grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(program_flash_row, text="浏览...", command=self.browse_bitstream).grid(row=0, column=2, padx=4)
        
        # === 模式选择 ===
        mode_row = ttk.Frame(self); mode_row.grid(row=2, column=0, sticky="w", pady=6)
        ttk.Label(mode_row, text="执行模式：").grid(row=1, column=0, sticky=tk.W)
        self.mode_var = tk.StringVar(value="program")
        for idx, (txt, val) in enumerate([("直接烧写", "program"), ("烧写到flash", "program_flash")]):
            ttk.Radiobutton(mode_row, text=txt, variable=self.mode_var, value=val, command=self.update_mode)\
                .grid(row=1, column=idx+1, padx=6, sticky="w")

        # --- flash码流烧写 ----
        self.program_flash_frame = ttk.Frame(self)
        self.program_flash_frame.grid(row=3, column=0, sticky="ew", pady=6)
        self.program_flash_frame.columnconfigure(0, weight=1)
        self._build_program_flash_mode()

        # === 执行按钮 ===
        btn_row = ttk.Frame(self); btn_row.grid(row=4, column=0, pady=10)
        self.run_btn = ttk.Button(btn_row, text="执行烧写", command=self.on_run)
        self.run_btn.pack(side="left", padx=6)
        self.clear_btn = ttk.Button(btn_row, text="清空日志", command=self.clear_log)
        self.clear_btn.pack(side="left", padx=6)

        # === 日志输出 ===
        self.log_text = tk.Text(self, height=10, state="disabled")
        self.log_text.grid(row=6, column=0, sticky="nsew")
        self.rowconfigure(6, weight=1)

        self.update_mode()

    def _build_program_flash_mode(self):
        # --- flash 选择 ----
        part_row = ttk.Frame(self.program_flash_frame); part_row.grid(row=0, column=0, sticky="ew", pady=6)
        ttk.Label(part_row, text="flash型号：").grid(row=0, column=0, sticky=tk.W)
        self.flash_part_var = tk.StringVar(value="mt25ql128-spi-x1_x2_x4")
        ttk.Combobox(
            part_row,
            textvariable=self.flash_part_var,
            values=[
                "28f00ap30t-bpi-x16",
                "28f512p30t-bpi-x16",
                "28f256p30t-bpi-x16",
                "28f512p30e-bpi-x16",
                "mt28gu256aax1e-bpi-x16",
                "mt28fw02gb-bpi-x16",
                "mt25ql128-spi-x1_x2_x4"
            ],
            width=20,
            state="readonly"
        ).grid(row=0, column=1, sticky=tk.W, padx=4)

    def browse_vivado_path(self):
        path = filedialog.askdirectory(title="选择 Vivado 安装目录")
        if path:
            self.vivado_bin_path_var.set(path)

    def browse_bitstream(self):
        path = filedialog.askopenfilename(
            filetypes=[("Bitstream", "*.bin *.bit *.rbt")],
            title="选择 bit/rbt/bin 码流文件"
        )
        if path:
            self.bitstream_var.set(path)

    def on_run(self):
        # 禁用按钮，防止重复点击
        self.run_btn.config(state="disabled")
        cur_mode = self.mode_var.get()

        vivado_bin_path = self.vivado_bin_path_var.get().strip()
        if not vivado_bin_path or not os.path.exists(vivado_bin_path):
            self._after_error("请设置正确的 Vivado bin 路径！")
            return
        if not vivado_bin_path:
            self._after_error("请设置vivado bin路径！")
            return

        bit_file_path = self.bitstream_var.get().strip()
        if not os.path.isfile(bit_file_path):
            self._after_error("无效的码流文件路径！")
            return
        
        if cur_mode == "program":
            kwargs = dict(
                vivado_bin_path=vivado_bin_path,
                bitstream_file=bit_file_path,
            )

            run_in_thread(
                self,
                self._program_bitstream_file,
                lock_widget=self.run_btn,
                on_success=self._after_success,
                on_error=self._after_error,
                **kwargs
            )
        elif cur_mode == "program_flash":
            kwargs = dict(
                vivado_bin_path=vivado_bin_path,
                bitstream_file=bit_file_path,
                flash_part=self.flash_part_var.get()
            )

            run_in_thread(
                self,
                self._program_flash_file,
                lock_widget=self.run_btn,
                on_success=self._after_success,
                on_error=self._after_error,
                **kwargs
            )

    def _program_bitstream_file(self, *, vivado_bin_path,  bitstream_file):
        """烧写 bitstream 文件到 FPGA"""
        logging.info("[Program] 开始处理")
        program_script  = utils.resource_path("RESOURCE/SCRIPTS/program.tcl")
        vivado_bat_path = os.path.join(vivado_bin_path, "vivado.bat")

        if not os.path.exists(program_script):
            raise RuntimeError(f"program.tcl 文件未找到: {program_script}")
        if not os.path.exists(vivado_bat_path):
            raise RuntimeError(f"Vivado.bat 文件未找到: {vivado_bat_path}")

        logging.info("=======================================================")
        logging.info(f"[Program] 执行参数: \n"
                        f"vivado_bin_path = {vivado_bin_path}, \n"
                        f"bit_file_path = {bitstream_file}")
        logging.info("=======================================================")
        

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

        if result.returncode != 0:
            logging.error(f"[Program] 烧写 bitstream 文件失败: {bitstream_file}")
        else:
            logging.info(f"[Program] 烧写 {bitstream_file} 完成")

        logging.info(f"[Program] ========= ALL PASS =========")

    def _program_flash_file(self, *, vivado_bin_path,  bitstream_file, flash_part):
        """烧写 bitstream 文件到 flash"""
        logging.info("[Program] 开始处理")
        program_script  = utils.resource_path("RESOURCE/SCRIPTS/program_flash.tcl")
        vivado_bat_path = os.path.join(vivado_bin_path, "vivado.bat")

        if not os.path.exists(program_script):
            raise RuntimeError(f"program.tcl 文件未找到: {program_script}")
        if not os.path.exists(vivado_bat_path):
            raise RuntimeError(f"Vivado.bat 文件未找到: {vivado_bat_path}")

        logging.info("=======================================================")
        logging.info(f"[Program] 执行参数: \n"
                        f"vivado_bin_path = {vivado_bin_path}, \n"
                        f"bit_file_path = {bitstream_file}\n"
                        f"flash = {flash_part}"
        )
        logging.info("=======================================================")
        

        cmd = [
            vivado_bat_path, "-mode", "batch",
            "-log", "NUL", "-journal", "NUL",
            "-source", program_script,
            "-tclargs", bitstream_file, flash_part
        ]
        # 设置 startupinfo 来隐藏窗口
        result = subprocess.run(
            cmd, 
            capture_output=False, 
            text=True
        )

        if result.returncode != 0:
            logging.error(f"[Program] 烧写 bitstream 文件失败: {bitstream_file}")
        else:
            logging.info(f"[Program] 烧写 {bitstream_file} 完成")

        logging.info(f"[Program] ========= ALL PASS =========")


    def clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")

    def update_mode(self):
        mode = self.mode_var.get()
        self.program_flash_frame.grid_remove()
        if mode == "program_flash":
            self.program_flash_frame .grid()

    def _after_success(self, result=None):
        messagebox.showinfo("完成", "码流烧写完成")
        self.run_btn.config(state="normal")

    def _after_error(self, exc: Exception):
        messagebox.showerror("错误", str(exc))
        self.run_btn.config(state="normal")