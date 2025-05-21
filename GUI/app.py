# bit_tool/gui/app.py
import tkinter as tk
from tkinter import ttk
from GUI.PAGES.page_a import PageA
from GUI.PAGES.page_b import PageB
from GUI.PAGES.page_c import PageC
import logging
from GUI.logger import setup_logger, text_handler, update_log_target

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bitstream Tool GUI")
        self.geometry("720x480")
        setup_logger(logging.INFO)
        self._build_ui()
        self.after(100, self._poll_logger)

    def _build_ui(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)
        self.ctx = {}

        self.page_a = PageA(self.nb, self.ctx)
        self.page_b = PageB(self.nb, self.ctx)
        self.page_c = PageC(self.nb, self.ctx)

        self.nb.add(self.page_a, text="  基础功能  ")
        self.nb.add(self.page_b, text="  自刷新  ")
        self.nb.add(self.page_c, text="  C组  ")

        # 绑定切换事件
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # 默认先绑定第一个页面的日志区
        update_log_target(self.page_a.log_text)

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