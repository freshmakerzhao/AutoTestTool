import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
import os 
import time

from CORE.SERIAL.serial_core import GLOBAL_SERIAL_CORE
from CORE.SERIAL.serial_packet_parser import AckType
from GUI.COMPONENT.thread_utils import run_in_thread

class PageFClockConfig(ttk.Frame):
    """F组 时钟配置页面"""
    def __init__(self, master, app_ctx, **kw):
        super().__init__(master, **kw)
        self.app_ctx = app_ctx
        self.columnconfigure(0, weight=1)
        self.build_ui()

    def build_ui(self):
        top_frame = ttk.Frame(self)
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        top_frame.columnconfigure(1, weight=1)

        # 文件选择区
        ttk.Label(top_frame, text="配置文件:").grid(row=0, column=0, sticky=tk.W)
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(top_frame, textvariable=self.path_var)
        self.path_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.browse_btn = ttk.Button(top_frame, text="浏览", command=self.browse_file)
        self.browse_btn.grid(row=0, column=2, padx=5)

        # 设置按钮 + 计数器
        count_frame = ttk.Frame(self)
        count_frame.grid(row=1, column=0, pady=10)

        self.set_btn = ttk.Button(count_frame, text="发送配置", command=self.send_config)
        self.set_btn.pack(side="left", padx=5)

        ttk.Label(count_frame, text="已发送:").pack(side="left")
        self.count_var = tk.StringVar(value="0")
        self.count_entry = ttk.Entry(count_frame, textvariable=self.count_var, width=6, state="readonly", justify="center")
        self.count_entry.pack(side="left")

        # 日志显示
        self.log_text = tk.Text(self, height=15, state="disabled")
        self.log_text.grid(row=2, column=0, sticky="nsew", padx=10)
        self.rowconfigure(2, weight=1)

        
        # === 底部控制区 ===
        bottom_frame = ttk.Frame(self)
        bottom_frame.grid(row=3, column=0, sticky="ew", pady=6)

        self.clear_btn = ttk.Button(bottom_frame, text="清空日志", command=self.clear_log)
        self.clear_btn.pack(side="right", padx=4)


    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("Config Files", "*.txt *.cfg"), ("All Files", "*.*")])
        if path:
            self.path_var.set(path)

    def send_config(self):
        file_path = self.path_var.get().strip()
        if not file_path or not os.path.exists(file_path):
            messagebox.showwarning("提示", "请先选择一个配置文件")
            return
        
        if not GLOBAL_SERIAL_CORE.running:
            messagebox.showerror("错误", "端口未连接")
            return
        

        kwargs = dict(
            file_path=file_path
        )
        run_in_thread(
            self,
            self._config_clk,
            lock_widget=self.set_btn,
            on_success=self._after_success,
            on_error=self._after_error,
            **kwargs
        )

    def _config_clk(self, file_path):

        count = 0  # 初始化计数
        self.count_var.set(str(count))  # 重置显示

        try:
            # 一个指令最多尝试3次
            max_try_times = 3
            cur_try_times = 0
            with open(file_path, 'r') as f:
                for lineno, line in enumerate(f, 1):
                    line = line.strip()

                    if not line or line.startswith("#"):
                        continue

                    if line.startswith("0x"):
                        parts = [s.strip() for s in line.split(",")]
                        if len(parts) != 2:
                            self.append_log(f"[Line {lineno}] 格式非法: {line}")
                            continue

                        reg_addr, reg_data = parts

                        if reg_addr.upper() == "0x0540" and reg_data.upper() == "0x01":
                            time.sleep(0.3)

                        cmd_str = f"MC1PCLKCFG 0000 {reg_addr} {reg_data}"
                        real_len = len(cmd_str)
                        len_hex = f"{real_len:04X}"
                        cmd_str = cmd_str[:11] + len_hex + cmd_str[15:]

                        # 发送命令并等待ACK
                        router = GLOBAL_SERIAL_CORE.event_router
                        router.reset_ack(AckType.CLKCFG)
                        GLOBAL_SERIAL_CORE.send_text(cmd_str)
                        self.append_log(f"发送: {cmd_str}")
                        cur_try_times += 1

                        if not router.wait_for_ack(AckType.CLKCFG):
                            if cur_try_times > max_try_times:
                                messagebox.showerror("错误", f"[Line {lineno}] 等待 ACK 超时")
                        
                        # 更新计数
                        count += 1
                        self.count_var.set(str(count))
                        self.count_entry.update_idletasks()

        except Exception as e:
            logging.exception("发送配置失败")
            messagebox.showerror("错误", f"发送配置失败:\n{e}")

    def append_log(self, msg: str):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def _after_success(self, result=None):
        messagebox.showinfo("完成", "配置完成")
        self.set_btn.config(state="normal")

    def _after_error(self, exc: Exception):
        messagebox.showerror("错误", str(exc))
        self.set_btn.config(state="normal")
        
    def clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")