import tkinter as tk
from tkinter import ttk, messagebox
import CORE.SERIAL.serial_command_builder as serial_cmd_builder
from CORE.SERIAL.serial_core import GLOBAL_SERIAL_CORE
from CORE.SERIAL.serial_handler_factory import create_handler
from GUI.COMPONENT.thread_utils import run_in_thread
from CORE.SERIAL.serial_packet_parser import AckType

from CORE.SERIAL.serial_voltage import (
    VOLTAGE_ORDER,
    VOLTAGE_LIMITS,
    validate_and_align,
    get_voltage,
    set_voltage,
)

class PageIVoltage(ttk.Frame):
    """Voltage Monitor 页面"""

    page_name = "PageIVoltage"

    def __init__(self, master, app_ctx=None, **kwargs):
        super().__init__(master, **kwargs)
        self.app_ctx = app_ctx
        self.voltage_vars: dict[str, tk.StringVar] = {}   # 每路电压的 StringVar
        self.entry_widgets: dict[str, ttk.Entry] = {}     # 每路电压的 Entry（便于后续高亮）
        self.build_ui()

    # ---------------- UI ----------------
    def build_ui(self):
        # 主框架，填充整个页面
        main_frame = ttk.Frame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # 两列自适应
        main_frame.columnconfigure(0, weight=1)  # 左侧表格
        main_frame.columnconfigure(1, weight=1)  # 右侧控制区
        main_frame.rowconfigure(0, weight=1)

        # 左侧电压区域
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        left_frame.columnconfigure(0, weight=1)
        left_frame.columnconfigure(1, weight=1)
        left_frame.columnconfigure(2, weight=1)
        left_frame.columnconfigure(3, weight=1)

        # 右侧控制区域
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.columnconfigure(0, weight=1)
        right_frame.columnconfigure(1, weight=1)
        right_frame.columnconfigure(2, weight=1)

        # 表头
        ttk.Label(left_frame, text="Name").grid(row=0, column=0, sticky="nsew", pady=2)
        ttk.Label(left_frame, text="Min (mV)").grid(row=0, column=1, sticky="nsew", pady=2)
        ttk.Label(left_frame, text="Max (mV)").grid(row=0, column=2, sticky="nsew", pady=2)
        ttk.Label(left_frame, text="Value (mV)").grid(row=0, column=3, sticky="nsew", pady=2)

        # 电压行
        for i, name in enumerate(VOLTAGE_ORDER, start=1):
            vmin, vmax, vdefault = VOLTAGE_LIMITS[name]
            ttk.Label(left_frame, text=name).grid(row=i, column=0, sticky="nsew", pady=2)
            ttk.Label(left_frame, text=f"{vmin}", foreground="gray").grid(row=i, column=1, sticky="nsew", padx=5)
            ttk.Label(left_frame, text=f"{vmax}", foreground="gray").grid(row=i, column=2, sticky="nsew", padx=5)

            var = tk.StringVar(value=str(vdefault))
            ent = ttk.Entry(left_frame, textvariable=var)
            ent.grid(row=i, column=3, padx=5, pady=2, sticky="nsew")

            self.voltage_vars[name] = var
            self.entry_widgets[name] = ent

        # VCCADC
        ttk.Label(right_frame, text="VCCADC").grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.vccadc_var = tk.IntVar(value=1)
        ttk.Radiobutton(right_frame, variable=self.vccadc_var, value=1, text="Enable").grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(right_frame, variable=self.vccadc_var, value=0, text="Disable").grid(row=0, column=2, sticky="w")

        # VCCREF
        ttk.Label(right_frame, text="VCCREF").grid(row=1, column=0, sticky="w", pady=(8, 8))
        self.vccref_var = tk.IntVar(value=0)
        ttk.Radiobutton(right_frame, variable=self.vccref_var, value=1, text="Enable").grid(row=1, column=1, sticky="w")
        ttk.Radiobutton(right_frame, variable=self.vccref_var, value=0, text="Disable").grid(row=1, column=2, sticky="w")

        # 按钮
        btn_frame = ttk.Frame(right_frame)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=16)

        self.btn_show = ttk.Button(btn_frame, text="show", command=self.on_show)
        self.btn_show.pack(side="left", padx=10)
        self.btn_set = ttk.Button(btn_frame, text="set", command=self.on_set)
        self.btn_set.pack(side="left", padx=10)

        # 说明
        info = "说明：<1600mV 步进 5mV，≥1600mV 步进 10mV；设置时自动对齐步进"
        ttk.Label(right_frame, text=info, foreground="gray", wraplength=250, justify="left")\
            .grid(row=3, column=0, columnspan=3, sticky="w", pady=(6, 0))

    def on_show(self, info=None):
        if not GLOBAL_SERIAL_CORE.is_connect:
            messagebox.showerror("错误", "端口未连接")
            return

        run_in_thread(
            self,
            self._send_get_voltage,
            lock_widget=self.btn_show,
            on_error=self.show_error
        )

    def on_set(self):
        if not GLOBAL_SERIAL_CORE.is_connect:
            messagebox.showerror("错误", "端口未连接")
            return

        try:
            # 收集 UI 值
            ui_values = [int(self.voltage_vars[name].get().strip()) for name in VOLTAGE_ORDER]
            # 校验 & 对齐 & 回写 UI
            aligned_values = validate_and_align(ui_values)

            for name, val in zip(VOLTAGE_ORDER, aligned_values):
                self.voltage_vars[name].set(str(val))

            # vccadc & vccref
            vccadc_en = int(self.vccadc_var.get())
            vccref_en = int(self.vccref_var.get())

            run_in_thread(
                self,
                self._send_set_voltage,
                lock_widget=self.btn_set,
                on_success=self.on_show,
                on_error=self.show_error,
                values=aligned_values,
                vccadc_en=vccadc_en,
                vccref_en=vccref_en,
            )

        except ValueError as ve:
            messagebox.showerror("输入错误", str(ve))
        except Exception as e:
            messagebox.showerror("异常", str(e))

    # -------------- 串口发送--------------
    def _send_get_voltage(self):
        get_voltage(timeout=2.0)

    def _send_set_voltage(self, values, vccadc_en: int, vccref_en: int):
        set_voltage(values, vccadc_en, vccref_en, timeout=2.0)

    # -------------- 回调 --------------
    def register_handler(self):
        """在进入该页面时调用"""
        self.gui_handler = create_handler("gui", handler_name=self.page_name, gui_page=self)
        GLOBAL_SERIAL_CORE.event_router.register(self.gui_handler)

    def unregister_handler(self):
        """离开该页面时调用"""
        if hasattr(self, "gui_handler"):
            GLOBAL_SERIAL_CORE.event_router.unregister(self.gui_handler)
            del self.gui_handler

    def show_error(self, exc: Exception):
        messagebox.showerror("错误", str(exc))

    def display_volget_data(self, values_dict: dict):
        # 回写电压
        for name in VOLTAGE_ORDER:
            if name in values_dict:
                self.voltage_vars[name].set(str(values_dict[name]))

        if "VCCADC" in values_dict:
            adc_val = values_dict.get("VCCADC")
            try:
                self.vccadc_var.set(int(adc_val))
            except Exception:
                pass

        if "VCCREF" in values_dict:
            ref_val = values_dict.get("VCCREF")
            try:
                self.vccref_var.set(int(ref_val))
            except Exception:
                pass