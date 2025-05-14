# bit_tool/gui/pages/page_b.py
import tkinter as tk
from tkinter import ttk
from GUI.COMPONENT.collapsible import CollapsibleFrame 

class PageB(ttk.Frame):
    """B 组：定时刷新 & 回读刷新 双抽屉设置界面"""

    def __init__(self, master, app_ctx, **kw):
        super().__init__(master, **kw)
        self.columnconfigure(0, weight=1)

        # 默认值
        self._defaults = {}



        # ---- 抽屉 1：定时刷新 ----
        self.timer_cf = CollapsibleFrame(self, " 定时刷新 设置", expanded=True, group="refresh")
        self.timer_cf.grid(row=0, column=0, sticky="ew", pady=4)

        self._build_timer_options(self.timer_cf.body)

        # ---- 抽屉 2：回读刷新 ----
        self.rd_cf = CollapsibleFrame(
            self, " 回读刷新 设置", expanded=False, group="refresh")
        self.rd_cf.grid(row=1, column=0, sticky="ew", pady=4)

        self._build_readback_options(self.rd_cf.body)
        
        # 进入界面先恢复默认
        self.reset()

    # ===== 定时刷新选项 =====
    def _build_timer_options(self, parent):
        opts = [
            ("启用定时刷新", "enable_timer",  False),
            ("定时周期(秒)", "period",        60),
            ("刷新超时(秒)", "timeout",        5),
            ("是否记录日志", "log_timer",     False),
        ]
        self.timer_vars = {}

        for idx, (label, key, *default) in enumerate(opts):
            ttk.Label(parent, text=label).grid(row=idx, column=0, sticky="w", pady=2)
            if isinstance(default, list) and default:
                var = tk.IntVar(value=default[0])
                ttk.Spinbox(parent, from_=1, to=3600, textvariable=var, width=8)\
                    .grid(row=idx, column=1, sticky="w")
            else:
                var = tk.BooleanVar(value=False)
                ttk.Checkbutton(parent, variable=var).grid(row=idx, column=1, sticky="w")
            self.timer_vars[key] = var
            self._defaults[key] = default         # 记录默认值

    # ===== 回读刷新选项 =====
    def _build_readback_options(self, parent):
        opts = [
            ("启用回读刷新",  "enable_rb",  False),
            ("回读间隔(ms)", "interval",   500),
            ("最大错误计数",  "max_err",    3),
            ("出错自动重载",  "auto_reload",False),
            ("详细日志",      "log_rb",     False),
        ]
        self.rb_vars = {}
        for idx, (label, key, *default) in enumerate(opts):
            ttk.Label(parent, text=label).grid(row=idx, column=0, sticky="w", pady=2)
            if isinstance(default, list) and default:
                var = tk.IntVar(value=default[0])
                ttk.Spinbox(parent, from_=1, to=10000, textvariable=var, width=8)\
                    .grid(row=idx, column=1, sticky="w")
            else:
                var = tk.BooleanVar(value=False)
                ttk.Checkbutton(parent, variable=var).grid(row=idx, column=1, sticky="w")
            self.rb_vars[key] = var
            self._defaults[key] = default
        
    # ====== 重置接口 ======
    def reset(self):
        """恢复所有选项到初始默认值"""
        for key, default in self._defaults.items():
            # 根据类型写回
            (self.timer_vars.get(key) or self.rb_vars.get(key)).set(default)
