import threading, logging, traceback
from tkinter import messagebox
from typing import Callable, Any
import contextlib

_is_running = False

def run_in_thread(
    root,
    func,
    *args,
    lock_widget=None,           # 执行按钮，防止二次点击
    on_success=None,            # 成功回调
    on_error=None,              # 失败回调
    log_path=None,          # 新增参数
    **kwargs,
):
    
    global _is_running
    if _is_running:
        logging.warning("任务已在运行中，请稍后再试")
        messagebox.showwarning("任务运行中", "已有任务正在执行，请等待其完成。")
        return

    _is_running = True
    
    if lock_widget:
        lock_widget.config(state="disabled")

    # 禁用跳转
    if hasattr(root, "disable_tabs"):
        root.disable_tabs()
        
    def _worker():
        try:
            if log_path:
                with open(log_path, "a", encoding="utf-8") as f, \
                        contextlib.redirect_stdout(f), \
                        contextlib.redirect_stderr(f):
                    result = func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            root.after(0, lambda: (
                lock_widget and lock_widget.config(state="normal"),
                on_success and on_success(result)
            ))
        except Exception as e:
            logging.error("❌ %s", e, exc_info=True)
            err = e  # 解决 lambda 引用问题
            root.after(0, lambda: (
                lock_widget and lock_widget.config(state="normal"),
                on_error and on_error(err)
            ))
        finally:
            global _is_running
            _is_running = False

    threading.Thread(target=_worker, daemon=True).start()
