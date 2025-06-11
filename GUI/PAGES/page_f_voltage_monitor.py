# GUI/PAGES/page_f_voltage_monitor.py
import tkinter as tk
from tkinter import ttk, messagebox
from CLI.cli_voltage import VoltageClient

# (名称, 默认值, 最大值)
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

class PageFVoltageMonitor(ttk.Frame):
    def __init__(self, parent, serial_core):
        super().__init__(parent)
        self.client = VoltageClient(serial_core)
        self.entries = {}
        self._build_ui()

    def _build_ui(self):
        frm = ttk.LabelFrame(self, text="Voltage Monitor")
        frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for i, (label, default_val, maxv) in enumerate(VOLTAGE_SPECS):
            step = "5mV" if default_val < 1600 else "10mV"
            ttk.Label(frm, text=f"{label} (default:{default_val}mV, max:{maxv}mV, step:{step})").grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            var = tk.StringVar(value=str(default_val))
            ent = ttk.Entry(frm, textvariable=var, width=10)
            ent.grid(row=i, column=1, padx=5, pady=2)
            self.entries[label] = var

        self.vccadc_var = tk.BooleanVar(value=True)
        self.vccref_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm, text="VCCADC Enable", variable=self.vccadc_var).grid(row=12, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(frm, text="VCCREF Enable", variable=self.vccref_var).grid(row=12, column=1, sticky=tk.W, pady=2)

        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=13, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Show", command=self._on_show).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Set", command=self._on_set).pack(side=tk.LEFT, padx=5)

        # 显示说明信息
        info = "说明：电压单位为 mV，<1600mV 步进为 5mV，>=1600mV 步进为 10mV"
        ttk.Label(frm, text=info, foreground="gray").grid(row=14, column=0, columnspan=2, pady=5)

    def _on_show(self):
        try:
            data = self.client.get_voltage()
            for key, _, _ in VOLTAGE_SPECS:
                self.entries[key].set(str(data[key]))
            self.vccadc_var.set(data["VCCADC"])
            self.vccref_var.set(data["VCCREF"])
        except Exception as e:
            messagebox.showerror("Voltage Show Failed", str(e))

    def _on_set(self):
        try:
            values = []
            for key, _, maxv in VOLTAGE_SPECS:
                raw = self.entries[key].get().strip()
                if not raw.isdigit():
                    raise ValueError(f"{key} 电压必须为整数: '{raw}'")
                val = int(raw)
                if val > maxv:
                    raise ValueError(f"{key} 超出最大限制: {val} > {maxv}")

                # 步进校正：小于1.6v的 -> 5mV，大于等于1.6v -> 10mV
                if val < 1600:
                    val = round(val / 5) * 5
                else:
                    val = round(val / 10) * 10

                values.append(val)

            adc_en = self.vccadc_var.get()
            ref_en = self.vccref_var.get()
            self.client.set_voltage(values, adc_en, ref_en)
            self._on_show()
        except Exception as e:
            messagebox.showerror("Voltage Set Failed", str(e))