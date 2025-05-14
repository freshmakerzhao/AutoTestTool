# bit_tool/gui/app.py
import tkinter as tk
from tkinter import ttk
from GUI.PAGES.page_a import PageA
from GUI.PAGES.page_b import PageB
from GUI.PAGES.page_c import PageC

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bitstream Tool GUI")
        self.geometry("720x480")
        self._build_ui()

    def _build_ui(self):
        nb = ttk.Notebook(self); nb.pack(fill="both", expand=True)
        ctx = {}                              # 日后可以放 logger / 配置等共享对象
        nb.add(PageA(nb, ctx), text="  基础功能  ")
        nb.add(PageB(nb, ctx), text="  自刷新  ")
        nb.add(PageC(nb, ctx), text="  C组  ")
        
        # 绑定切换事件
        nb.bind("<<NotebookTabChanged>>",
                lambda e: self._on_tab_changed(e, nb))
    
    def _on_tab_changed(self, event, nb):
        page = nb.nametowidget(nb.select())
        if hasattr(page, "reset"):
            page.reset()      # 自动清空

if __name__ == "__main__":
    MainApp().mainloop()
