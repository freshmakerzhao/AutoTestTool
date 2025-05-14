import tkinter as tk
from tkinter import ttk
from pathlib import Path

# 项目根目录 = “resource/image/” 的上两级
ROOT_DIR   = Path(__file__).resolve().parents[2]
IMAGE_DIR  = ROOT_DIR / "RESOURCE" / "IMAGE"

class CollapsibleFrame(ttk.Frame):
    _groups = {}
    _icons  = {}               # ← 缓存 PhotoImage，键: 'right'/'down'

    def __init__(self, master, title="Section", expanded=False, group=None, **kw):
        super().__init__(master, **kw)
        self.group = group
        self._title = title
        self._ensure_icons(master)
        self._build_header()
        self._build_body()
        self.set_state(expanded)

    # ---------- 懒加载图标 ----------
    @classmethod
    def _ensure_icons(cls, widget):
        if cls._icons: 
            return
        root = widget.winfo_toplevel()      # 拿到已有 Tk
        cls._icons["right"] = tk.PhotoImage(master=root,
                                            file=IMAGE_DIR / "arrow_right.png")
        cls._icons["down"]  = tk.PhotoImage(master=root,
                                            file=IMAGE_DIR / "arrow_down.png")


    # ---------- UI ----------
    def _build_header(self):
        """header = Arrow + Title + 横线"""
        hdr = ttk.Frame(self)
        hdr.pack(fill="x", pady=4)

        self._arrow = ttk.Label(hdr, image=self._icons["right"])
        self._arrow.pack(side="left", padx=(0, 2))

        # 标题（左对齐）
        self._title_lbl = ttk.Label(hdr, text=self._title, anchor="w")
        self._title_lbl.pack(side="left")

        # 横线填充到最右
        sep = ttk.Separator(hdr, orient="horizontal")
        sep.pack(side="left", fill="x", expand=True, padx=4)

        # 整个 header 都可点击
        for w in (hdr, self._arrow, self._title_lbl):
            w.bind("<Button-1>", lambda e: self._toggle())

    def _build_body(self):
        self._container = ttk.Frame(self)
        self._container.columnconfigure(0, weight=1)

    @property
    def body(self):
        """外部在 body 内添加控件"""
        return self._container

    # ---------- 折叠 / 展开 ----------
    def set_state(self, expanded: bool):
        if expanded:
            if self.group:
                prev = CollapsibleFrame._groups.get(self.group)
                if prev and prev is not self:
                    prev.set_state(False)
                CollapsibleFrame._groups[self.group] = self
            self._container.pack(fill="both", expand=True, padx=4, pady=(0, 6))
            self._arrow.config(image=self._icons["down"])
        else:
            if self.group and CollapsibleFrame._groups.get(self.group) is self:
                CollapsibleFrame._groups[self.group] = None
            self._container.forget()
            self._arrow.config(image=self._icons["right"])

    def _toggle(self):
        self.set_state(not self._container.winfo_ismapped())
