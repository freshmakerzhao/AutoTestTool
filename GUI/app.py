import tkinter as tk
from tkinter import ttk
from GUI.PAGES.page_a_program import PageAProgram
from GUI.PAGES.page_b_refesh import PageBRefresh
from GUI.PAGES.page_c_vccm import PageCVCCM
from GUI.PAGES.page_d_vivado_rd_check import PageDVivadoRDCheck
from GUI.PAGES.page_e_serial_config import PageESerialConfig
from GUI.PAGES.page_f_clock_config import PageFClockConfig
from GUI.PAGES.page_g_ibert import PageGIbertTest
from GUI.PAGES.page_h_base import PageHBase
from GUI.PAGES.page_i_voltage import PageIVoltage

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
        self._prev_page = None  #上一个页面

    def _build_ui(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)
        self.ctx = {}

        self.page_a = PageAProgram(self.nb, self.ctx)
        self.page_b = PageBRefresh(self.nb, self.ctx)
        self.page_c = PageCVCCM(self.nb, self.ctx)
        self.page_d = PageDVivadoRDCheck(self.nb, self.ctx)
        self.page_e = PageESerialConfig(self.nb, self.ctx)
        self.page_f = PageFClockConfig(self.nb, self.ctx)
        self.page_g = PageGIbertTest(self.nb, self.ctx)
        self.page_h = PageHBase(self.nb, self.ctx)
        self.page_i = PageIVoltage(self.nb, self.ctx)

        self.nb.add(self.page_a, text="  码流烧写  ")
        self.nb.add(self.page_b, text="  自刷新  ")
        self.nb.add(self.page_c, text="  VCCM设置  ")
        self.nb.add(self.page_d, text="  Vivado回读校验  ")
        self.nb.add(self.page_e, text="  串口配置  ")
        self.nb.add(self.page_f, text="  Si5344 clk  ")
        self.nb.add(self.page_i, text="  Voltage Monitor  ")
        self.nb.add(self.page_g, text="  Ibert测试  ")
        self.nb.add(self.page_h, text="  基础功能  ")
        
        # 绑定切换事件
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # 默认先绑定第一个页面的日志区
        update_log_target(self.page_h.log_text)

    def _on_tab_changed(self, event):
        next_page = self.nb.nametowidget(self.nb.select())
        if hasattr(next_page, "reset"):
            next_page.reset()
        if hasattr(next_page, "log_text"):
            update_log_target(next_page.log_text)
            
        # if self._prev_page and hasattr(self._prev_page, "unregister_handler"):
        #     self._prev_page.unregister_handler()

        # 注册新页面的 handler
        if hasattr(next_page, "register_handler"):
            next_page.register_handler()

        # 更新当前页面为上一个  
        self._prev_page = next_page

    def _poll_logger(self):
        text_handler.poll()
        self.after(100, self._poll_logger)

def main():
    MainApp().mainloop()

if __name__ == "__main__":
    main()
