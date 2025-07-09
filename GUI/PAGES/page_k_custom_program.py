# bit_tool/gui/pages/page_a.py
from tkinter import ttk
import os, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from GUI.COMPONENT.thread_utils import run_in_thread
import logging
import subprocess
import sys
import os

class PageKCustomProgram(ttk.Frame):
    """K 组：使用openfpgaloader烧写flash"""

    def __init__(self, master, app_ctx, **kw):
        super().__init__(master, **kw)
        self.app_ctx = app_ctx
        self.columnconfigure(0, weight=1)
        self.prog_mode = "fpga"  # 当前烧写类型：fpga or flash
        self.build_ui()

    def build_ui(self):
        # --- 操作按钮 -----
        mode_row = ttk.Frame(self)
        mode_row.grid(row=0, column=0, sticky="ew", pady=12)
        ttk.Label(mode_row, text="请选择烧写操作:").pack(side="left", padx=(0, 8))
        self.fpga_btn = ttk.Button(mode_row, text="配置FPGA", command=lambda: self.set_mode("fpga"))
        self.fpga_btn.pack(side="left")
        self.flash_btn = ttk.Button(mode_row, text="配置Flash", command=lambda: self.set_mode("flash"))
        self.flash_btn.pack(side="left", padx=(8,0))

        # --- bit文件选择 -----
        file_row = ttk.Frame(self)
        file_row.grid(row=1, column=0, sticky="ew")
        file_row.columnconfigure(1, weight=1)
        ttk.Label(file_row, text="选择文件:").grid(row=0, column=0, sticky=tk.W)
        self.bit_path_var = tk.StringVar()
        ttk.Entry(file_row, textvariable=self.bit_path_var).grid(row=0, column=1, sticky="ew", padx=4)
        self.browse_btn = ttk.Button(file_row, text="浏览...", command=self.browse_bitfile)
        self.browse_btn.grid(row=0, column=2, padx=4)

        # --- 烧写按钮 -----
        btn_row = ttk.Frame(self)
        btn_row.grid(row=2, column=0, pady=14)
        self.run_btn = ttk.Button(btn_row, text="配置", command=self.on_run)
        self.run_btn.pack(side="left", padx=10)

        # --- 日志框 -----
        self.log_text = tk.Text(self, height=8, state="disabled")
        self.log_text.grid(row=3, column=0, sticky="nsew")
        self.rowconfigure(3, weight=1)

        self.set_mode("fpga")  # 默认模式

    def set_mode(self, mode):
        self.prog_mode = mode
        if mode == "fpga":
            self.fpga_btn.state(["disabled"])
            self.flash_btn.state(["!disabled"])
        else:
            self.flash_btn.state(["disabled"])
            self.fpga_btn.state(["!disabled"])
        self.bit_path_var.set("")

    def browse_bitfile(self):
        if self.prog_mode == "fpga":
            types = [("FPGA位流文件", "*.bit *.bin")]
        else:
            types = [("所有支持的文件", "*.bit *.bin *.mcs")]
        path = filedialog.askopenfilename(
            filetypes=types,
            title="选择烧写文件"
        )
        if path:
            self.bit_path_var.set(path)

    def on_run(self):
        bit_file = self.bit_path_var.get().strip()
        if not os.path.isfile(bit_file):
            messagebox.showerror("错误", "请选择有效的烧写文件！")
            return

        kwargs = dict(bit_file=bit_file, prog_mode=self.prog_mode)
        self.run_btn.config(state="disabled")
        base_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
        cur_log_path = os.path.join(base_dir, "log.txt")
        run_in_thread(
            self,
            self.program_bit_file,
            lock_widget=self.run_btn,
            on_success=self._after_success,
            on_error=self._after_error,
            log_path=cur_log_path,
            **kwargs
        )

    def program_bit_file(self, bit_file, prog_mode):
        base_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
        exe_path = os.path.join(base_dir, "bin", "BitstreamLoader.exe")
        indirect_path = os.path.join(base_dir, "resource", "spiOverJtag_MC1P110.bit.gz")
        param_cable = "digilent_hs3"
        param_chip = "arty_a7_100t"
        param_license = "emhhb3NodWFpZGFvY2l5aXlvdQ=="

        # 构建不同命令
        if prog_mode == "fpga":
            cmd = [exe_path, "-c", param_cable, bit_file, "--license", param_license]
        else:
            cmd = [exe_path, "-c", param_cable, "-b", param_chip, "-B", indirect_path, "-f", bit_file, "--license", param_license]

        logging.info(f"[Program] {bit_file} 烧写中...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logging.info("[Program] 烧写完成！")
            return "烧写成功！"
        else:
            logging.error("[Program] 烧写失败！" + result.stderr)
            return result.stdout + "\n" + result.stderr

    def clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")

    def _after_success(self, result=None):
        messagebox.showinfo("完成", str(result))
        self.run_btn.config(state="normal")

    def _after_error(self, exc: Exception):
        messagebox.showerror("错误", str(exc))
        self.run_btn.config(state="normal")

