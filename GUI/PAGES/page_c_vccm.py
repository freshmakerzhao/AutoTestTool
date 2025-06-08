# bit_tool/gui/pages/page_c.py
from tkinter import ttk
import os, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from CORE.process_runner import run_vccm_task, run_vccm_project
from GUI.COMPONENT.thread_utils import run_in_thread
import logging

class PageCVCCM(ttk.Frame):
    """VCCM 批处理功能"""

    def __init__(self, master, app_ctx, **kw):
        super().__init__(master, **kw)
        self.app_ctx = app_ctx
        self.columnconfigure(0, weight=1)
        self.build_ui()

    def build_ui(self):
        # --------------------- 模式选择 开始 ---------------------
        # 文件/文件夹 执行 process_vccm_file
        # 项目目录 执行 process_vccm_project
        mode_row = ttk.Frame(self); mode_row.grid(row=0, column=0, sticky="ew", pady=6)
        mode_row.columnconfigure(1, weight=1)

        ttk.Label(mode_row, text="处理模式：").grid(row=0, column=0, sticky=tk.W)
        self.mode_var = tk.StringVar(value="process_vccm_file")

        mode_opts = ttk.Frame(mode_row)
        mode_opts.grid(row=0, column=1, sticky="w")

        # 单选按钮
        for idx, (txt, val) in enumerate([
            ("码流文件", "process_vccm_file")]):
            ttk.Radiobutton(mode_opts, text=txt, variable=self.mode_var, value=val)\
                .grid(row=0, column=idx, sticky="w", padx=6)

        # 问号
        # ttk.Button(mode_opts, text="?", width=2, command=self.show_mode_help)\
        #     .grid(row=0, column=3, padx=6)
        # --------------------- 模式选择 结束 ---------------------

        # --------------------- 路径选择 开始 ---------------------
        # --- 路径选择 根据模式不同这里路径代表的含义也不同---
        path_row = ttk.Frame(self)
        path_row.grid(row=1, column=0, sticky="ew", pady=6)
        path_row.columnconfigure(1, weight=1)
        ttk.Label(path_row, text="选择路径:").grid(row=0, column=0, sticky=tk.W)
        self.path_var = tk.StringVar()
        ttk.Entry(path_row, textvariable=self.path_var).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(path_row, text="浏览...", command=self.browse_path).grid(row=0, column=2, padx=4)
        # --------------------- 路径选择 结束 ---------------------

        # --------------------- 电压选择 开始 ---------------------
        # volt_frame = ttk.LabelFrame(self, text="选择电压 (VCCM)")
        # volt_frame.grid(row=2, column=0, sticky="ew", padx=4, pady=4)
        # self.vccm_vars = {}
        # for idx, v in enumerate(list(range(105, 113)) + [115]):
        #     row, col = divmod(idx, 6)
        #     label = f"1.{str(v)[-2:]}"
        #     var = tk.BooleanVar()
        #     self.vccm_vars[v] = var
        #     ttk.Checkbutton(volt_frame, text=label, variable=var)\
        #         .grid(row=row, column=col, sticky="w", padx=6, pady=2)
        # --------------------- 电压选择 结束 ---------------------

        # --------------------- VS_WL选择（单选） 开始 ---------------------
        # vswl_frame = ttk.LabelFrame(self, text="选择电压 (VS_WL)")
        # vswl_frame.grid(row=3, column=0, sticky="ew", padx=4, pady=4)

        # self.vswl_var = tk.IntVar(value=0)  # 默认值为0，表示未选择
        
        # vswl_values = [110, 115, 120, 125, 130, 135, 140, 145, 150]
        # for idx, v in enumerate(vswl_values):
        #     row, col = divmod(idx, 6)
        #     label = f"1.{str(v)[-2:]}"
        #     ttk.Radiobutton(vswl_frame, text=label, value=v, variable=self.vswl_var)\
        #         .grid(row=row, column=col, sticky="w", padx=6, pady=2)
        # --------------------- VS_WL选择（单选） 结束 ---------------------

        # --- 执行按钮 ---
        button_row = ttk.Frame(self)
        button_row.grid(row=4, column=0, pady=10)

        self.run_btn = ttk.Button(button_row, text="开始处理", command=self.on_run)
        self.run_btn.pack(side="left", padx=6)

        self.clear_btn = ttk.Button(button_row, text="清空日志", command=self.clear_log)
        self.clear_btn.pack(side="left", padx=6)

        # --- 日志输出区 ---
        self.log_text = tk.Text(self, height=10, state="disabled")
        self.log_text.grid(row=5, column=0, sticky="nsew")
        self.rowconfigure(5, weight=1)

    def browse_path(self):
        # 获得用户选择的模式
        cur_mode = self.mode_var.get()
        cur_path = None
        # process_vccm_file 选择一个位流文件
        # process_vccm_folder 选择一个文件夹
        # process_vccm_project 选择一个项目目录
        if cur_mode == "process_vccm_file":
            cur_path = filedialog.askopenfilename(
                filetypes=[("Bitstream", "*.bit *.bin *.rbt")],
                title="选择一个位流文件"
            )
        elif cur_mode == "process_vccm_folder":
            cur_path = filedialog.askdirectory(title="选择一个模块目录")
        else:
            cur_path = filedialog.askdirectory(title="选择一个项目目录")
        if cur_path:
            # 更新UI
            self.path_var.set(cur_path)

    def on_run(self):
        
        # 禁用按钮，防止重复点击
        self.run_btn.config(state="disabled")
        
        file_path = self.path_var.get()
        cur_mode = self.mode_var.get()
        vccm_values = [115]

        vswl_selected = 125
        if vswl_selected == 0:
            pass

        if not os.path.exists(file_path):
            messagebox.showerror("错误", "路径无效！")
            self.run_btn.config(state="normal")
            return
        if not vccm_values:
            messagebox.showerror("错误", "请至少选择一个 VCCM 电压值！")
            self.run_btn.config(state="normal")
            return

        kwargs = dict(file_path=file_path, vccm_values=vccm_values, vswl_selected=vswl_selected, process_mode=cur_mode)
        
        run_in_thread(
            self,
            self._run_thread,         
            lock_widget=self.run_btn, 
            on_success=self._show_project_summary,
            on_error=self._after_err,
            **kwargs
        )

    def _run_thread(self, *, file_path, vccm_values, vswl_selected, process_mode):
        stats = None
        try:
            if process_mode == "process_vccm_project":
                stats = run_vccm_project(file_path, vccm_values=vccm_values, vswl_selected=vswl_selected)
            else:
                stats = run_vccm_task(file_path, vccm_values=vccm_values, vswl_selected=vswl_selected)
        except Exception as e:
            logging.error("[ERROR] %s", e)
            messagebox.showerror("处理失败", str(e))
        return stats
    
    def reset(self):
        self.path_var.set("")
        # for var in self.vccm_vars.values():
        #     var.set(False)
        # # 清空 VS_WL 单选
        # self.vswl_var.set(0)
        
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.config(state="disabled")

    def clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.config(state="disabled")

    def show_mode_help(self):
        messagebox.showinfo(
            "处理模式说明",
            "码流文件：\n"
            "   - 在码流文件同级目录生成对应不同vccm_1pxx的码流\n\n"
            "模块目录：\n"
            "   - 选择文件夹，递归处理该文件夹下所有 bitstream（.rbt、.bit、.bin） 文件，输出到选择文件夹下的各 vccm_1pxx 文件夹中\n\n"
            "项目目录：\n"
            "   - 选择文件夹，对当前目录下的每个一级子目录分别执行 VCCM 批处理，分别创建对应的 vccm_1pxx 文件夹\n\n"
        )
            
    def _after_err(self, exc: Exception):
        self.run_btn.config(state="normal")      
        messagebox.showerror("错误", str(exc))
        
    def _show_project_summary(self, stats: dict):
        summary = (
            f"项目处理完成\n\n"
            f"模块数量:    {stats.get('project_subdirs', '1')}\n"
            f"总文件数:    {stats.get('total_files', '-')}\n"
            f"成功处理数:  {stats.get('success_count', '-')}\n"
            f"失败跳过数:  {stats.get('fail_count', '-')}"
        )
        messagebox.showinfo("批处理完成", summary)
