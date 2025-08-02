import tkinter as tk
from tkinter import ttk, messagebox
import CORE.SERIAL.serial_command_builder as serial_cmd_builder
from CORE.SERIAL.serial_core import GLOBAL_SERIAL_CORE
from CORE.SERIAL.serial_handler_factory import create_handler
from GUI.COMPONENT.thread_utils import run_in_thread
from CORE.SERIAL.serial_packet_parser import AckType

# 电压参数说明 (名称, 默认值, 最大值)
VOLTAGE_SPECS = [
    ("VCCO_0", 3300, 3600),
    ("VCCBRAM", 800, 1100),
    ("VCCAUX", 1800, 2000),
    ("VCCINT", 800, 1100),
    ("VCCO_16", 3300, 3600),
    ("VCCO_15", 3300, 3600),
    ("VCCO_14", 3300, 3600),
    ("VCCO_13", 3300, 3600),
    ("VCCO_34", 1500, 1550),
    ("MGTAVTT", 1200, 1320),
    ("MGTAVCC", 1000, 1100),
]

class PageIVoltage(ttk.Frame):
    """Voltage Monitor 页面"""

    def __init__(self, master, app_ctx=None, **kwargs):
        super().__init__(master, **kwargs)
        self.app_ctx = app_ctx
        self.voltage_entries = {}  # 保存每个电压项的 StringVar
        self.build_ui()

    def build_ui(self):
        
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ===== 左侧：电压项 =====
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsw")

        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, padx=120, sticky="n")

        for i, (label, default_val, maxv) in enumerate(VOLTAGE_SPECS):
            step = "5mV" if default_val < 1600 else "10mV"
            text = f"{label} (max{maxv})"
            ttk.Label(left_frame, text=text).grid(row=i, column=0, sticky="w", pady=2)
            var = tk.StringVar(value=str(default_val))
            ent = ttk.Entry(left_frame, textvariable=var, width=10)
            ent.grid(row=i, column=1, padx=5, pady=2)
            self.voltage_entries[label] = var

        # ===== 右侧：控制项 =====

        # VCCADC
        self.vccadc_var = tk.IntVar(value=1)
        ttk.Label(right_frame, text="VCCADC").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(right_frame, variable=self.vccadc_var, value=1, text="Enable").grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(right_frame, variable=self.vccadc_var, value=0, text="Disable").grid(row=0, column=2, sticky="w")

        # VCCREF
        self.vccref_var = tk.IntVar(value=0)
        ttk.Label(right_frame, text="VCCREF").grid(row=1, column=0, sticky="w", pady=(10, 0))
        ttk.Radiobutton(right_frame, variable=self.vccref_var, value=1, text="Enable").grid(row=1, column=1, sticky="w", pady=(10, 0))
        ttk.Radiobutton(right_frame, variable=self.vccref_var, value=0, text="Disable").grid(row=1, column=2, sticky="w", pady=(10, 0))

        # 按钮
        btn_frame = ttk.Frame(right_frame)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=20)
        ttk.Button(btn_frame, text="show", command=self.on_show).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="set", command=self.on_set).pack(side="left", padx=10)

    def on_show(self):
        cmd = serial_cmd_builder.build_get_all_voltage()
        
        if not GLOBAL_SERIAL_CORE.running:
            messagebox.showerror("错误", "端口未连接")
            return
        
        kwargs = dict(
            cmd=cmd
        )
        run_in_thread(
            self,
            self._send_get_voltage,
            on_error=self.show_error,
            **kwargs
        )

    def _send_get_voltage(self, cmd: str):
        # 发送命令并等待ACK
        GLOBAL_SERIAL_CORE.event_router.reset_ack(AckType.VOLGET)
        GLOBAL_SERIAL_CORE.send_text(cmd)
        if not GLOBAL_SERIAL_CORE.event_router.wait_for_ack(AckType.VOLGET):
            messagebox.showerror("错误", "等待超时")

    def on_set(self):
        # TODO: 串口写入逻辑占位
        messagebox.showinfo("Set", "设置电压命令发送成功（待实现）")

    def register_handler(self):
        self.gui_handler = create_handler("gui", "PageIVoltage", gui_page=self)
        GLOBAL_SERIAL_CORE.event_router.register(self.gui_handler)

    def unregister_handler(self):
        GLOBAL_SERIAL_CORE.event_router.unregister(self.gui_handler)
        del self.gui_handler

    def show_error(self, exc: Exception):
        messagebox.showerror("错误", str(exc))

    def display_volget_data(self, data: dict):
        for key, var in self.voltage_entries.items():
            if key in data:
                var.set(data[key])

        if "VCCADC" in data:
            try:
                self.vccadc_var.set(int(data["VCCADC"]))
            except ValueError:
                self.vccadc_var.set(0)

        if "VCCREF" in data:
            try:
                self.vccref_var.set(int(data["VCCREF"]))
            except ValueError:
                self.vccref_var.set(0)