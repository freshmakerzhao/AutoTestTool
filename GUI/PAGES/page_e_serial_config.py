from tkinter import ttk
import tkinter as tk
from CORE.SERIAL.serial_core import GLOBAL_SERIAL_CORE
from tkinter import ttk, messagebox
from CORE.SERIAL.serial_handler_factory import get_handler

class PageESerialConfig(ttk.Frame):
    """E 组：串口配置"""
    def __init__(self, master, app_ctx, **kw):
        super().__init__(master, **kw)
        self.app_ctx = app_ctx
        self.columnconfigure(0, weight=1)
        self.port_map = {}  # 用于从显示值 -> 实际端口名
        self.build_ui()
        self.bind_events()
        self.refresh_ports()

    def build_ui(self):
        # === 串口选择区 ===
        top_frame = ttk.Frame(self)
        top_frame.grid(row=0, column=0, sticky="ew", pady=6)
        top_frame.columnconfigure(1, weight=1)

        # =========== 下拉选择 =============
        ttk.Label(top_frame, text="串口号:").grid(row=0, column=0, sticky=tk.W)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(top_frame, textvariable=self.port_var, width=30, state="readonly")
        self.port_combo.grid(row=0, column=1, sticky="w", padx=4)
        # =========== 下拉选择 =============

        # =========== 按钮们 =============
        self.refresh_btn = ttk.Button(top_frame, text="刷新")
        self.refresh_btn.grid(row=0, column=2, padx=4)

        self.connect_btn = ttk.Button(top_frame, text="连接")
        self.connect_btn.grid(row=0, column=3, padx=4)

        self.disconnect_btn = ttk.Button(top_frame, text="断开")
        self.disconnect_btn.grid(row=0, column=4, padx=4)
        
        self.status_label = ttk.Label(top_frame, text="未连接")
        self.status_label.grid(row=0, column=5, padx=10)
        # =========== 按钮们 =============

        # === 日志显示区 ===
        self.log_text = tk.Text(self, height=15, state="disabled")
        self.log_text.grid(row=1, column=0, sticky="nsew")
        self.rowconfigure(1, weight=1)

        # === 底部控制区 ===
        bottom_frame = ttk.Frame(self)
        bottom_frame.grid(row=2, column=0, sticky="ew", pady=6)
        
        self.pause_var = tk.BooleanVar(value=False)
        self.pause_btn = ttk.Checkbutton(bottom_frame, text="暂停日志显示", variable=self.pause_var)
        self.pause_btn.pack(side="left", padx=4)

        self.clear_btn = ttk.Button(bottom_frame, text="清空日志", command=self.clear_log)
        self.clear_btn.pack(side="right", padx=4)

    def bind_events(self):
        self.refresh_btn.config(command=self.refresh_ports)
        self.connect_btn.config(command=self.connect_serial)
        self.disconnect_btn.config(command=self.disconnect_serial)

        self.gui_handler = get_handler("gui", gui_page=self)
        GLOBAL_SERIAL_CORE.event_router.register(self.gui_handler)

    def refresh_ports(self):
        ports = GLOBAL_SERIAL_CORE.get_available_ports()
        display_list = []
        self.port_map.clear()

        for p in ports:
            display = f"{p['name']} - {p['description']}"
            display_list.append(display)
            self.port_map[display] = p['name']

        self.port_combo["values"] = display_list
        if display_list:
            self.port_var.set(display_list[0])

    # 供 Handler 回调, 更新连接状态
    def update_connection_status(self, connected: bool, port: str):
        self.connect_btn.config(state="disabled" if connected else "normal")
        self.disconnect_btn.config(state="normal" if connected else "disabled")
        self.port_combo.config(state="disabled" if connected else "readonly")
        self.status_label.config(text=f"已连接: {port}" if connected else "未连接")

    def connect_serial(self):
        display_str = self.port_var.get()
        port = self.port_map.get(display_str)
        if not port:
            self.show_warning("提示", "请选择串口号")
            return

        GLOBAL_SERIAL_CORE.config.port = port
        try:
            if GLOBAL_SERIAL_CORE.connect():
                messagebox.showinfo("成功", f"串口已连接: {port}")
            else:
                messagebox.showerror("失败", "串口连接失败")
        except Exception as e:
            self.show_error(e)

    def disconnect_serial(self):
        GLOBAL_SERIAL_CORE.disconnect()
        messagebox.showinfo("提示", "串口已断开")

    # 供 Handler 回调, 显示接收到的数据
    def display_received_data(self, data: dict):
        if self.pause_var.get():
            return  # 暂停显示时不处理
        text = data.get("decode_content", "")
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")

    def show_info(self, title_text: str, show_content: str):
        messagebox.showinfo(title_text, show_content)

    def show_warning(self, title_text: str, show_content: str):
        messagebox.showwarning(title_text, show_content)

    def show_error(self, exc: Exception):
        messagebox.showerror("错误", str(exc))
