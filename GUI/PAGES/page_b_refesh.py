# bit_tool/gui/pages/page_b.py
import pathlib, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from GUI.COMPONENT.collapsible import CollapsibleFrame 
import COMMON.utils as utils
from GUI.COMPONENT.thread_utils import run_in_thread
from CORE.process_runner import run_base_task

class PageBRefresh(ttk.Frame):
    """B 组：定时刷新 & 回读刷新 双抽屉设置界面"""

    def __init__(self, master, app_ctx, **kw):
        super().__init__(master, **kw)
        self.columnconfigure(0, weight=1)

        # 默认值
        self._defaults = {}
        self.timer_vars  = {}
        self.rb_vars     = {}
        self.build_ui()
        # 进入界面先恢复默认
        self.reset()

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
            
        self.run_btn = ttk.Button(self, text="开始处理", command=self.on_run)
        self.run_btn.grid(row=0, column=3, padx=4)
            
        # ---- 抽屉 1：定时刷新 ----
        self.timer_cf = CollapsibleFrame(self, " 定时刷新 设置", expanded=True, group="refresh")
        self.timer_cf.grid(row=1, column=0, sticky="ew", pady=4)

        self._build_timer_options(self.timer_cf.body)

        # ---- 抽屉 2：回读刷新 ----
        self.rd_cf = CollapsibleFrame(
            self, " 回读刷新 设置", expanded=False, group="refresh")
        self.rd_cf.grid(row=2, column=0, sticky="ew", pady=4)

        # 用于回读刷新
        self._readback_suspend    = False  # 防止更新dec hex时出现左脚踩右脚
        self._build_readback_options(self.rd_cf.body)
        
    # ===== 定时刷新选项 =====
    def _build_timer_options(self, parent):
        self.timer_vars = {}

        # -------------------------------------------------
        # 1) cfg_clk (MHz) —— 只允许 1 位小数、范围 0.1 ~ 100.0
        # -------------------------------------------------
        ttk.Label(parent, text="cfg_clk (MHz)").grid(row=0, column=0, sticky="w", pady=2)
        self.timer_vars["cfg_mhz"] = tk.StringVar()
        self.timer_vars["cfg_mhz"].set("3.0")

        def cfg_validate(P):
            # 允许空串；至多 1 位小数；数值 0.1~100.0
            if P == "":
                return True
            import re
            if not re.fullmatch(r"\d{1,3}(\.\d)?", P):
                return False
            return 0.1 <= float(P) <= 100.0

        ttk.Entry(parent, width=6, textvariable=self.timer_vars["cfg_mhz"],
                validate="key",
                validatecommand=(parent.register(cfg_validate), "%P"))\
            .grid(row=0, column=1, sticky="w")
        self._defaults["cfg_mhz"] = "3.0"

        # -------------------------------------------------
        # 2) DIV (2-16, 偶数)
        # -------------------------------------------------
        ttk.Label(parent, text="分频系数 DIV").grid(row=1, column=0, sticky="w", pady=2)
        self.timer_vars["div"] = tk.StringVar()
        self.timer_vars["div"].set("2")

        def div_validate(P):
            if P == "":
                return True
            if not P.isdigit():
                return False
            v = int(P)
            return v in {2,4,6,8,10,12,14,16}

        ttk.Entry(parent, width=4, textvariable=self.timer_vars["div"],
                validate="key",
                validatecommand=(parent.register(div_validate), "%P"))\
            .grid(row=1, column=1, sticky="w")
        self._defaults["div"] = "2"

        # -------------------------------------------------
        # 3) RH_hold 计数（0 ~ 0xFFFFFFFF）
        # -------------------------------------------------
        ttk.Label(parent, text="RH_hold (计数)").grid(row=2, column=0, sticky="w", pady=2)
        self.timer_vars["rh_hold"] = tk.StringVar()
        self.timer_vars["rh_hold"].set("1")

        def hold_validate(P):
            if P == "":
                return True
            if not P.isdigit():
                return False
            v = int(P)
            return 0 <= v <= 0xFFFFFFFF

        ttk.Entry(parent, width=12, textvariable=self.timer_vars["rh_hold"],
                validate="key",
                validatecommand=(parent.register(hold_validate), "%P"))\
            .grid(row=2, column=1, sticky="w")
        self._defaults["rh_hold"] = "1"

        # -------------------------------------------------
        # 4) 两个 32 位预览
        # -------------------------------------------------
        ttk.Label(parent, text="RH_hold 预览").grid(row=3, column=0, sticky="w", pady=(6,0))
        self.rh_hold_bin = tk.StringVar()
        ttk.Entry(parent, textvariable=self.rh_hold_bin,
                font=("Courier New", 10), width=38, state="readonly")\
            .grid(row=3, column=1, sticky="w")

        ttk.Label(parent, text="RHBD 预览 (位16-14)").grid(row=4, column=0, sticky="w", pady=(2,0))
        self.rhbd_bin = tk.StringVar()
        ttk.Entry(parent, textvariable=self.rhbd_bin,
                font=("Courier New", 10), width=38, state="readonly")\
            .grid(row=4, column=1, sticky="w")

        # ---------- 公共更新 ----------
        def update_previews(*_):
            # 处理空串 → 0
            div  = int(self.timer_vars["div"].get()  or 0)
            hold = int(self.timer_vars["rh_hold"].get() or 0)

            # RH_hold 直接格式化
            self.rh_hold_bin.set(f"{hold & 0xFFFFFFFF:032b}")

            # 计算 rhbd = DIV/2 - 1，限制 0..7
            rhbd = max(0, min(7, div // 2 - 1))
            self.rhbd_bin.set(f"{rhbd << 14:032b}")

        # 监听变量
        for v in (self.timer_vars["div"], self.timer_vars["rh_hold"]):
            v.trace_add("write", update_previews)
        update_previews()            # 初始化

        
    # ===== 回读刷新选项 =====
    def _build_readback_options(self, parent):
        """ecc_err_tank —— 十进制 / 十六进制双向实时联动"""
        MIN_V, MAX_V = 0, 16383
        self._readback_suspend = False          # 防递归

        # -------- 共有的“核心值”变量（IntVar 仍保留，给 reset()、业务使用） --------
        self.ecc_val = tk.IntVar(value=0)

        # -------- 十进制输入框 --------
        ttk.Label(parent, text="ecc_err_tank (Dec, 0-16383)").grid(row=0, column=0,
                                                        sticky="w", pady=2)
        dec_var = tk.StringVar()
        dec_entry = ttk.Entry(parent, textvariable=dec_var, width=10)
        dec_entry.grid(row=0, column=1, sticky="w")
        dec_entry.configure(validate="key",validatecommand=(parent.register(utils.is_dec), "%P"))
        
        # -------- 十六进制输入框 --------
        ttk.Label(parent, text="ecc_err_tank (Hex, 0-3FFF)").grid(row=1, column=0,
                                                        sticky="w", pady=2)
        hex_var = tk.StringVar()
        hex_entry = ttk.Entry(parent, textvariable=hex_var, width=10)
        hex_entry.grid(row=1, column=1, sticky="w")
        hex_entry.configure(validate="key", validatecommand=(parent.register(utils.is_hex), "%P"))

        # -------- 工具函数 --------
        def clamp(val: int) -> int:
            return max(MIN_V, min(MAX_V, val))

        # 更新两个文本框，带闭锁
        def _update_entries(n: int):
            self._readback_suspend = True
            dec_var.set(str(n))
            hex_var.set(f"{n:X}")
            self._readback_suspend = False

        # ---- ① 监听十进制框变化 ----
        def on_dec_change(*_):
            if self._readback_suspend:
                return
            txt = dec_var.get()
            if txt.isdigit():
                n = clamp(int(txt))
                _update_entries(n)
                self.ecc_val.set(n)     # 给外部逻辑 / reset 使用

        dec_var.trace_add("write", on_dec_change)

        # ---- ② 监听十六进制框变化 ----
        def on_hex_change(*_):
            if self._readback_suspend:
                return
            txt = hex_var.get()
            if txt and all(c in "0123456789abcdefABCDEF" for c in txt):
                try:
                    n = int(txt, 16)
                except ValueError:
                    return
                n = clamp(n)
                _update_entries(n)
                self.ecc_val.set(n)

        hex_var.trace_add("write", on_hex_change)

        # ---- ③ 当 reset() 或其它代码 set ecc_val 时，同步到文本框 ----
        def sync_from_int(*_):
            if self._readback_suspend:
                return
            _update_entries(clamp(self.ecc_val.get()))

        self.ecc_val.trace_add("write", sync_from_int)
        sync_from_int()                 # 初始化

        # ---- ④ 注册到 reset()/defaults ----
        self.rb_vars = {"ecc_err_tank": self.ecc_val}
        self._defaults["ecc_err_tank"] = 0
        
        self.RHBD_DATA = tk.StringVar()

        ttk.Label(parent, text="RHBD DATA").grid(
            row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(parent, textvariable=self.RHBD_DATA,
                  font=("Courier New", 10), width=38, state="readonly")\
            .grid(row=2, column=1, sticky="w")
            
        
        # --- 更新函数：根据 ecc_val 拼 32 位字符串 ---
        def update_rb_bin(*_):
            bits = ["0"] * 32
            # ecc_err_tank 映射 30-17 共 14 位
            val = self.ecc_val.get()
            for i in range(14):
                bits[31 - (17 + i)] = "1" if (val >> i) & 1 else "0"
            self.RHBD_DATA.set("".join(bits))

        # 监听 ecc_val（十进制或十六进制任何修改最终都会写 ecc_val）
        self.ecc_val.trace_add("write", update_rb_bin)
        update_rb_bin()          # 初始化
        
    # ---------- 文件选择事件 ----------
    def browse_file(self):
        f = filedialog.askopenfilename(filetypes=[("Bitstream", "*.rbt *.bit *.bin")])
        if f: self.file_var.set(f)
        
    
    def on_run(self):
        # 禁用，防止重复点
        self.run_btn.config(state="disabled")
        
        path = self.file_var.get()
        if not pathlib.Path(path).is_file():
            self._after_err("请选择正确的输入文件！"); return
            
        if self.timer_cf.is_expanded():
            # 定时刷新参数
            pass
            
        elif self.rd_cf.is_expanded():
            # 回读刷新参数
            kwargs = dict(
                file=path,
                readback_refresh=self.RHBD_DATA.get(),
            )
        else:
            self._after_err("未选择刷新配置"); return
        
        run_in_thread(
            self,                             # root
            run_base_task,                
            lock_widget=self.run_btn,         
            on_success=self._after_ok,        # 成功回调
            on_error=self._after_err,         # 失败回调
            **kwargs
        )

    # ====== 重置接口 ======
    def reset(self):
        self.file_var.set("")
        """恢复所有选项到初始默认值"""
        for key, default in self._defaults.items():
            # 根据类型写回
            (self.timer_vars.get(key) or self.rb_vars.get(key)).set(default)
    
    # ---------- 回调 ----------
    def _after_ok(self, out_path: str):
        self.run_btn.config(state="normal")        
        messagebox.showinfo("完成", f"输出文件已保存：{out_path}")

    def _after_err(self, exc: Exception):
        self.run_btn.config(state="normal")      
        messagebox.showerror("错误", str(exc))
