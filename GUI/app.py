import tkinter as tk
from tkinter import ttk
from GUI.PAGES.page_a_program import PageAProgram
from GUI.PAGES.page_a_base import PageABase
from GUI.PAGES.page_b_refesh import PageBRefresh
from GUI.PAGES.page_c_vccm import PageCVCCM
from GUI.PAGES.page_d_vivado_rd_check import PageDVivadoRDCheck
# 添加串口监视器页面导入
from GUI.PAGES.page_e_serial_monitor import PageESerialMonitor
from GUI.PAGES.page_f_voltage_monitor import PageFVoltageMonitor

import logging
from GUI.logger import setup_logger, text_handler, update_log_target

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bitstream Tool GUI")
        self.geometry("800x700")
        setup_logger(logging.INFO)
        self._build_ui()
        self.after(100, self._poll_logger)

    def _build_ui(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)
        self.ctx = {}

        self.page_a = PageAProgram(self.nb, self.ctx)
        self.page_b = PageBRefresh(self.nb, self.ctx)
        self.page_c = PageCVCCM(self.nb, self.ctx)
        self.page_d = PageDVivadoRDCheck(self.nb, self.ctx)
        self.page_e = PageESerialMonitor(self.nb, self.ctx)
        self.page_h = PageABase(self.nb, self.ctx)
        
        # —— 这里修改 —— 
        # 直接取串口监视器页面的 serial_core
        serial_core = self.page_e.serial_core
        self.page_f = PageFVoltageMonitor(self.nb, serial_core)

        self.nb.add(self.page_a, text="  码流烧写  ")
        self.nb.add(self.page_b, text="  自刷新  ")
        self.nb.add(self.page_c, text="  VCCM设置  ")
        self.nb.add(self.page_d, text="  Vivado回读校验  ")
        self.nb.add(self.page_e, text="  串口监视器  ")
        self.nb.add(self.page_f, text="  电压设置查询  ")
        self.nb.add(self.page_h, text="  基础功能  ")

        # 绑定切换事件
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # 默认先绑定第一个页面的日志区
        update_log_target(self.page_h.log_text)

    def _on_tab_changed(self, event):
        page = self.nb.nametowidget(self.nb.select())
        if hasattr(page, "reset"):
            page.reset() # 自动清空
        if hasattr(page, "log_text"):
            update_log_target(page.log_text)

    def _poll_logger(self):
        text_handler.poll()
        self.after(100, self._poll_logger)

if __name__ == "__main__":
    MainApp().mainloop()