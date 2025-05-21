import threading, logging, traceback
from tkinter import messagebox
from typing import Callable, Any

def run_in_thread(
    root,
    func,
    *args,
    lock_widget=None,           # 执行按钮，防止二次点击
    on_success=None,            # 成功回调
    on_error=None,              # 失败回调
    **kwargs,
):
    if lock_widget:
        lock_widget.config(state="disabled")

    def _worker():
        try:
            result = func(*args, **kwargs)
            root.after(0, lambda: (
                lock_widget and lock_widget.config(state="normal"),
                on_success and on_success(result)
            ))
        except Exception as e:
            logging.error("❌ %s", e, exc_info=True)
            root.after(0, lambda: (
                lock_widget and lock_widget.config(state="normal"),
                on_error and on_error(e)
            ))

    threading.Thread(target=_worker, daemon=True).start()
