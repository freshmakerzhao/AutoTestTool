import pathlib, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from CORE.process_runner import run_base_task,FILE_ENDWITH
import logging

class PageGBase(ttk.Frame):
    """A 组：Bitstream 解析功能"""

    def __init__(self, master, app_ctx, **kw):
        super().__init__(master, **kw)
        self.app_ctx = app_ctx
        self.columnconfigure(0, weight=1)
        self.build_ui()

    # ---------- UI ----------
    def build_ui(self):
        # --- 文件选择 ---
        file_row = ttk.Frame(self); file_row.grid(row=0, column=0, sticky="ew", pady=6)
        file_row.columnconfigure(1, weight=1)
        ttk.Label(file_row, text="输入文件:").grid(row=0, column=0, sticky=tk.W)
        self.file_var = tk.StringVar()
        ttk.Entry(file_row, textvariable=self.file_var)\
            .grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(file_row, text="浏览...", command=self.browse_file)\
            .grid(row=0, column=2, padx=4)

        # --- 设备下拉 ---
        dev_row = ttk.Frame(self); dev_row.grid(row=1, column=0, sticky="ew", pady=6)
        ttk.Label(dev_row, text="Device:").grid(row=0, column=0, sticky=tk.W)
        self.dev_var = tk.StringVar(value="MC1P110")
        ttk.Combobox(
            dev_row,
            textvariable=self.dev_var,
            values=["MC1P110", "MC1P170", "MC1P210"],
            width=10,
            state="readonly"
        ).grid(row=0, column=1, sticky=tk.W, padx=4)


        # --- 文件后缀 ---
        suffix_row = ttk.Frame(self); suffix_row.grid(row=2, column=0, sticky="ew", pady=6)
        ttk.Label(suffix_row, text="文件后缀:").grid(row=0, column=0, sticky=tk.W)
        self.suffix_var = tk.StringVar(value=FILE_ENDWITH)
        ttk.Entry(suffix_row, textvariable=self.suffix_var, width=12)\
            .grid(row=0, column=1, sticky=tk.W, padx=4)

        # --- 选项区：4 列均分 ---
        opts = [("PCIE","pcie"),("GTP","gtp"),("CRC","crc"),("COMPRESS","compress"),
                ("TRIM","trim"),("DELETE_GHIGH","delete_ghigh")]
        self.check_vars = {}
        for idx, (txt,key) in enumerate(opts):
            if idx % 4 == 0:
                row_frame = ttk.Frame(self); row_frame.grid(
                    row=3+idx//4, column=0, sticky="ew", pady=3)
                for c in range(4): row_frame.columnconfigure(c, weight=1)
            var = tk.BooleanVar()
            self.check_vars[key]=var
            ttk.Checkbutton(row_frame, text=txt, variable=var)\
                .grid(row=0, column=idx%4, sticky="w", padx=4)

        # --- 运行按钮 ---
        ttk.Button(self, text="开始处理", command=self.on_run)\
            .grid(row=10, column=0, pady=8)

        # --- 日志输出 ---
        self.log_text = tk.Text(self, height=10, state="disabled")
        self.log_text.grid(row=11, column=0, sticky="nsew")
        self.rowconfigure(11, weight=1)
    # ---------- 事件 ----------
    def browse_file(self):
        f = filedialog.askopenfilename(filetypes=[("Bitstream", "*.rbt *.bit *.bin")])
        if f: self.file_var.set(f)

    def on_run(self):
        path = self.file_var.get()
        if not pathlib.Path(path).is_file():
            logging.error("[错误] 请选择正确的输入文件！")
            messagebox.showerror("错误", "请选择正确的输入文件！"); return
        kwargs = dict(
            file=path, device=self.dev_var.get(), file_suffix=self.suffix_var.get(),
            pcie=self.check_vars["pcie"].get(), gtp=self.check_vars["gtp"].get(),
            crc=self.check_vars["crc"].get(), compress=self.check_vars["compress"].get(),
            trim=self.check_vars["trim"].get(), delete_ghigh=self.check_vars["delete_ghigh"].get(),
        )
        threading.Thread(target=self._run_thread, args=(kwargs,), daemon=True).start()

    def _run_thread(self, kwargs):
        try:
            out = run_base_task(**kwargs)
            logging.info("[提示] 输出文件保存至: %s", out)
            messagebox.showinfo("完成", f"输出文件已保存：\n{out}")
        except Exception as e:
            logging.error("[错误] %s", e)
            messagebox.showerror("出错", str(e))
            
    def reset(self):
        # 清空日志
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.config(state="disabled")

        # 清空输入文件路径
        self.file_var.set("")

        # 重置设备下拉选项
        self.dev_var.set("MC1P110")

        # 重置文件后缀
        self.suffix_var.set(FILE_ENDWITH)

        # 重置所有选项
        for var in self.check_vars.values():
            var.set(False)