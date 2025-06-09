# bit_tool/gui/pages/page_e.py
from tkinter import ttk
import os, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from GUI.COMPONENT.thread_utils import run_in_thread
import logging
import subprocess
import COMMON.utils as utils
import csv

class PageFIbertTest(ttk.Frame):
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

        # --- 码流文件 bitstream_var ---
        bitstream_row = ttk.Frame(self)
        bitstream_row.grid(row=1, column=0, sticky="ew", pady=6)
        bitstream_row.columnconfigure(1, weight=1)
        ttk.Label(bitstream_row, text="码流文件:").grid(row=0, column=0, sticky=tk.W)
        self.bitstream_var = tk.StringVar()
        ttk.Entry(bitstream_row, textvariable=self.bitstream_var).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(bitstream_row, text="浏览...", command=self.browse_bitstream).grid(row=0, column=2, padx=4)

        # --- 输出文件路径 output_var ---
        output_row = ttk.Frame(self)
        output_row.grid(row=2, column=0, sticky="ew", pady=6)
        output_row.columnconfigure(1, weight=1)
        ttk.Label(output_row, text="输出文件目录:").grid(row=0, column=0, sticky=tk.W)
        self.output_var = tk.StringVar()
        ttk.Entry(output_row, textvariable=self.output_var).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(output_row, text="浏览...", command=self.browse_output).grid(row=0, column=2, padx=4)

        # === 执行按钮 ===
        btn_row = ttk.Frame(self)
        btn_row.grid(row=5, column=0, pady=10)
        self.run_btn = ttk.Button(btn_row, text="执行Ibert测试", command=self.on_run)
        self.run_btn.pack(side="left", padx=6)
        self.clear_btn = ttk.Button(btn_row, text="清空日志", command=self.clear_log)
        self.clear_btn.pack(side="left", padx=6)

        # === 日志输出 ===
        self.log_text = tk.Text(self, height=10, state="disabled")
        self.log_text.grid(row=6, column=0, sticky="nsew")
        self.rowconfigure(6, weight=1)

        

    def browse_vivado_path(self):
        path = filedialog.askdirectory(title="选择 Vivado 安装目录")
        if path:
            self.vivado_bin_path_var.set(path)

    def browse_bitstream(self):
        path = filedialog.askopenfilename(
            filetypes=[("Bitstream", "*.bit *.rbt")],
            title="选择 bit/rbt 码流文件"
        )
        if path:
            self.bitstream_var.set(path)
            
    def browse_output(self):
        path = filedialog.askdirectory(title="选择一个输出目录")
        self.output_var.set(path)
        if path:
            self.output_var.set(path)

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

        bit_file_path = self.bitstream_var.get().strip()
        if not bit_file_path or not os.path.exists(bit_file_path):
            self._after_error("请设置正确的码流文件路径！")
            return
        if not bit_file_path:
            self._after_error("请设置码流文件路径！")
            return
        if not os.path.isfile(bit_file_path):
            self._after_error("无效的码流文件路径！")
            return

        output_file_path = self.output_var.get().strip() 
        if not output_file_path:
            self._after_error("请设置输出文件目录！")
            return
        

        kwargs = dict(
            vivado_bin_path=vivado_bin_path,
            bitstream_file_path=bit_file_path,
            output_path=output_file_path
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
                            bitstream_file_path, 
                            output_path
        ):
        is_all_pass = True
        logging.info(f"[vivado 回读校验] 开始处理")
        program_script  = utils.resource_path("RESOURCE/SCRIPTS/program.tcl")
        ibert_script  = utils.resource_path("RESOURCE/SCRIPTS/ibert.tcl")
        vivado_bat_path = os.path.join(vivado_bin_path, "vivado.bat")
        
        if not os.path.exists(program_script):
            raise RuntimeError(f"program.tcl 文件未找到: {program_script}")
        if not os.path.exists(vivado_bat_path):
            raise RuntimeError(f"Vivado.bat 文件未找到: {vivado_bat_path}")
        
        # 打印所有参数
        logging.info("=======================================================")
        logging.info(f"[vivado 回读校验] 执行参数: \n"
                        f"vivado_bin_path = {vivado_bin_path}, \n"
                        f"bit_file_path = {bitstream_file_path}, \n"
                        f"output_path = {output_path}")
        logging.info("=======================================================")

        if not self._ibert_test(vivado_bat_path, ibert_script, bitstream_file_path, output_path):
            logging.error(f"[vivado 回读校验] ibert 测试失败")
                    
        logging.info(f"[vivado 回读校验] ========= ALL PASS =========")
        return True
        
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

    def _ibert_test(self, vivado_bat_path, ibert_script, bitstream_file, output_path):
        """执行iber测试脚本"""
        cmd = [
            vivado_bat_path, "-mode", "batch",
            "-log", "NUL", "-journal", "NUL",
            "-source", ibert_script,
            "-tclargs", bitstream_file, output_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=False,
            text=True
        )
        logging.info(f"[vivado 回读校验] ibert测试完成")
        if result.returncode != 0:
            return False
        else:
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

