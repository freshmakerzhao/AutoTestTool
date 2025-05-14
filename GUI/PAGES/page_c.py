# bit_tool/gui/pages/page_c.py
from tkinter import ttk
class PageC(ttk.Frame):
    def __init__(self, master, app_ctx, **kw):
        super().__init__(master, **kw)
        ttk.Label(self, text="这里放 C 组功能 🚧").pack(pady=40)
