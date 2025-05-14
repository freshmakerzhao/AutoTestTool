# gui/parse_bitstream_gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, queue, logging, pathlib

from CORE.parse_bitstream import run_bit_process, FILE_ENDWITH

# ---------- 日志输出到 Tkinter Text ----------
class TextHandler(logging.Handler):
    def __init__(self, text_widget, q):
        super().__init__()
        self.text_widget = text_widget
        self.queue = q

    def emit(self, record):
        self.queue.put(self.format(record))

def gui_logger(text_widget):
    q = queue.Queue()
    handler = TextHandler(text_widget, q)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)

    def poll_queue():
        while not q.empty():
            msg = q.get_nowait()
            text_widget.configure(state="normal")
            text_widget.insert(tk.END, msg + '\n')
            text_widget.see(tk.END)
            text_widget.configure(state="disabled")
        text_widget.after(100, poll_queue)

    poll_queue()

# ---------- 主窗口 ----------
class BitGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bitstream Parser GUI")
        self.geometry("720x480")
        self.create_widgets()

    def create_widgets(self):
        # ---------- 0) 最外层 ----------
        root_frame = ttk.Frame(self, padding=10)
        root_frame.pack(fill="both", expand=True)

        # ---------- 1) Notebook ----------
        nb = ttk.Notebook(root_frame)
        nb.pack(fill="both", expand=True)

        # === A 组标签页 ===
        page_a = ttk.Frame(nb)
        nb.add(page_a, text="A组")

        # === B 组标签页 ===
        page_b = ttk.Frame(nb)
        nb.add(page_b, text="B组")

        # === C 组标签页 ===
        page_c = ttk.Frame(nb)
        nb.add(page_c, text="C组")
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        # ---------- A 组控件 ----------
        self.build_group_a(page_a)

        # ---------- 3) B、C 组示例 ----------
        ttk.Label(page_b, text="这里放 B 组功能 🚧").pack(pady=40)
        ttk.Label(page_c, text="这里放 C 组功能 🚧").pack(pady=40)

    # ——— 把原 A 组布局封装成函数方便维护 ———
    def build_group_a(self, parent_frame: ttk.Frame):
        # --- 文件选择 ---
        file_row = ttk.Frame(parent_frame)
        file_row.grid(row=0, column=0, columnspan=3, sticky="ew", pady=6)   # 行距 = 6
        file_row.columnconfigure(1, weight=1)      # 让 Entry 随窗口拉伸

        ttk.Label(file_row, text="输入文件:").grid(row=0, column=0, sticky=tk.W)
        self.file_var = tk.StringVar()
        ttk.Entry(file_row, textvariable=self.file_var).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(file_row, text="浏览...", command=self.browse_file)\
                .grid(row=0, column=2, padx=4)

        # --- 设备下拉 ---
        dev_row = ttk.Frame(parent_frame)
        dev_row.grid(row=1, column=0, columnspan=3, sticky="ew", pady=6)

        ttk.Label(dev_row, text="Device:").grid(row=0, column=0, sticky=tk.W)
        self.dev_var = tk.StringVar(value="MC1P110")
        ttk.Combobox(dev_row, textvariable=self.dev_var,
                    values=["MC1P110", "MC1P170", "MC1P210"], width=10)\
                .grid(row=0, column=1, sticky=tk.W, padx=4)

        # --- 文件后缀 ---
        suffix_row = ttk.Frame(parent_frame)
        suffix_row.grid(row=2, column=0, columnspan=3, sticky="ew", pady=6)

        ttk.Label(suffix_row, text="文件后缀:").grid(row=0, column=0, sticky=tk.W)
        self.suffix_var = tk.StringVar(value=FILE_ENDWITH)
        ttk.Entry(suffix_row, textvariable=self.suffix_var, width=12)\
                .grid(row=0, column=1, sticky=tk.W, padx=4)

        # ---------- 选项区 ----------
        opts = [
            ("PCIE",         "pcie"),
            ("GTP",          "gtp"),
            ("CRC",          "crc"),
            ("COMPRESS",     "compress"),
            ("TRIM",         "trim"),
            ("DELETE_GHIGH", "delete_ghigh"),
            ("回读刷新",      "readback_refresh"),
        ]
        self.check_vars = {}
        row_frame = None
        for idx, (text, key) in enumerate(opts):
            # 每 4 项新建一行 Frame
            if idx % 4 == 0:
                row_frame = ttk.Frame(parent_frame)
                row_frame.grid(row=3 + idx // 4, column=0, columnspan=3, sticky="ew", pady=3)
                # 让 4 列平均拉伸
                for col in range(4):
                    row_frame.columnconfigure(col, weight=1)

            var = tk.BooleanVar()
            self.check_vars[key] = var
            col = idx % 4
            ttk.Checkbutton(row_frame, text=text, variable=var)\
                .grid(row=0, column=col, sticky="w", padx=4)

        # ---------- 运行按钮 ----------
        ttk.Button(parent_frame, text="开始处理", command=self.on_run)\
            .grid(row=10, column=0, columnspan=3, pady=10)

        # ---------- 日志输出 ----------
        self.log_text = tk.Text(parent_frame, height=10, state="disabled")
        self.log_text.grid(row=11, column=0, columnspan=3, sticky="nsew")
        parent_frame.rowconfigure(11, weight=1)
        parent_frame.columnconfigure(1, weight=1)

        # logger
        gui_logger(self.log_text)

    # ---------- 事件 ----------
    def browse_file(self):
        f = filedialog.askopenfilename(filetypes=[("Bitstream", "*.rbt *.bit")])
        if f:
            self.file_var.set(f)

    def on_run(self):
        path = self.file_var.get()
        if not pathlib.Path(path).is_file():
            messagebox.showerror("错误", "请选择正确的输入文件！")
            return

        kwargs = dict(
            file=path,
            device=self.dev_var.get(),
            file_suffix=self.suffix_var.get(),
            pcie=self.check_vars["pcie"].get(),
            gtp=self.check_vars["gtp"].get(),
            crc=self.check_vars["crc"].get(),
            compress=self.check_vars["compress"].get(),
            trim=self.check_vars["trim"].get(),
            delete_ghigh=self.check_vars["delete_ghigh"].get(),
            readback_refresh=self.check_vars["readback_refresh"].get(),
        )

        threading.Thread(target=self.run_in_thread, args=(kwargs,), daemon=True).start()

    def run_in_thread(self, kwargs):
        try:
            out_file = run_bit_process(**kwargs)
            messagebox.showinfo("完成", f"输出文件已保存：\n{out_file}")
        except Exception as exc:
            logging.error("❌ %s", exc)
            messagebox.showerror("出错", str(exc))

# ---------- 启动 ----------
if __name__ == "__main__":
    BitGUI().mainloop()