# bit_tool/gui/pages/page_e.py
from tkinter import ttk
import os, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from GUI.COMPONENT.thread_utils import run_in_thread
import logging
import subprocess
import COMMON.utils as utils

class PageGIbertTest(ttk.Frame):
    """ibert 测试"""
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

        # --- tcl 文件---
        tcl_row = ttk.Frame(self)
        tcl_row.grid(row=1, column=0, sticky="ew", pady=6)
        tcl_row.columnconfigure(1, weight=1)
        ttk.Label(tcl_row, text="运行脚本(.tcl):").grid(row=0, column=0, sticky=tk.W)
        self.tcl_var = tk.StringVar()
        ttk.Entry(tcl_row, textvariable=self.tcl_var).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(tcl_row, text="浏览...", command=self.browse_tcl).grid(row=0, column=2, padx=4)

        # === 执行按钮 ===
        btn_row = ttk.Frame(self)
        btn_row.grid(row=2, column=0, pady=10)
        self.run_btn = ttk.Button(btn_row, text="运行", command=self.on_run)
        self.run_btn.pack(side="left", padx=6)
        self.clear_btn = ttk.Button(btn_row, text="清空日志", command=self.clear_log)
        self.clear_btn.pack(side="left", padx=6)

        # === 日志输出 ===
        self.log_text = tk.Text(self, height=10, state="disabled")
        self.log_text.grid(row=6, column=0, sticky="nsew")
        self.rowconfigure(6, weight=1)

    def browse_tcl(self):
        path = filedialog.askopenfilename(
            filetypes=[("tcl文件", "*.tcl")],
            title="选择tcl文件"
        )
        if path:
            self.tcl_var.set(path)

    def browse_vivado_path(self):
        path = filedialog.askdirectory(title="选择 Vivado 安装目录")
        if path:
            self.vivado_bin_path_var.set(path)
            
    def on_run(self):
        # 禁用按钮，防止重复点击
        self.run_btn.config(state="disabled")
        
        vivado_bin_path = self.vivado_bin_path_var.get().strip()
        if not vivado_bin_path or not os.path.exists(vivado_bin_path):
            self._after_error("请设置正确的 Vivado bin 路径！")
            return
        if not vivado_bin_path:
            self._after_error("请设置vivado bin路径！")
            return

        tcl_file_path = self.tcl_var.get().strip()
        if not tcl_file_path or not os.path.exists(tcl_file_path):
            self._after_error("请设置正确的tcl文件路径！")
            return
        if not tcl_file_path:
            self._after_error("请设置tcl文件路径！")
            return
        if not os.path.isfile(tcl_file_path):
            self._after_error("无效的tcl文件路径！")
            return

        kwargs = dict(
            vivado_bin_path=vivado_bin_path,
            tcl_file_path=tcl_file_path,
        )
        
        run_in_thread(
            self,
            self._run_vivado_process,
            lock_widget=self.run_btn,
            on_success=self._after_success,
            on_error=self._after_error,
            **kwargs
        )

    def _run_vivado_process(self, 
        *, 
        vivado_bin_path, 
        tcl_file_path
    ):
        logging.info(f"[ibert] 开始执行")
        tcl_script  = utils.resource_path(tcl_file_path)
        vivado_bat_path = os.path.join(vivado_bin_path, "vivado.bat")
        # 打印所有参数
        logging.info("=======================================================")
        logging.info(
            f"[ibert测试] 执行参数: \n"
            f"vivado_bin_path = {vivado_bin_path}, \n"
            f"tcl_file_path = {tcl_file_path}, \n"
        )
        logging.info("=======================================================")

        cmd = [
            vivado_bat_path, "-mode", "batch",
            "-log", "NUL", "-journal", "NUL",
            "-source", tcl_script
        ]

        result = subprocess.run(
            cmd,
            capture_output=False,
            text=True
        )

        logging.info(f"[ibert测试] ========= ALL PASS =========")
        return True
        
    def _after_success(self, result=None):
        messagebox.showinfo("完成", "tcl文件运行完成！")
        self.run_btn.config(state="normal")

    def _after_error(self, exc: Exception):
        messagebox.showerror("错误", str(exc))
        self.run_btn.config(state="normal")

    def clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")

    def reset(self):
        self.tcl_var.set("")
        self.clear_log()

    def clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.config(state="disabled")
