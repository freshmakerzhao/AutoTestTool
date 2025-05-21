# common/logger.py
import logging
import tkinter as tk
import queue

class SwitchingTextHandler(logging.Handler):
    """
    支持动态绑定 Text 控件的日志 Handler（线程安全）
    """
    def __init__(self):
        super().__init__()
        self.text_widget = None
        self.queue = queue.Queue()
        self.setFormatter(logging.Formatter('%(message)s'))

    def attach(self, text_widget: tk.Text):
        """绑定新的 Text 控件"""
        self.text_widget = text_widget

    def emit(self, record):
        try:
            msg = self.format(record)
            self.queue.put_nowait(msg)
        except Exception:
            self.handleError(record)

    def poll(self):
        """轮询队列，将日志写入绑定的 Text 控件"""
        if self.text_widget:
            while not self.queue.empty():
                msg = self.queue.get_nowait()
                self.text_widget.config(state="normal")
                self.text_widget.insert(tk.END, msg + '\n')
                self.text_widget.see(tk.END)
                self.text_widget.config(state="disabled")


# 全局唯一 Handler 实例
text_handler = SwitchingTextHandler()


def setup_logger(level=logging.INFO):
    """
    初始化全局 logger，仅调用一次
    """
    root_logger = logging.getLogger()
    if not any(isinstance(h, SwitchingTextHandler) for h in root_logger.handlers):
        root_logger.addHandler(text_handler)
        root_logger.setLevel(level)


def update_log_target(text_widget: tk.Text):
    """
    绑定新的日志输出控件（切换页面时调用）
    """
    text_handler.attach(text_widget)


def poll_log_to_ui(root: tk.Widget, interval_ms=100):
    """
    在主窗口中周期性刷新日志到 UI（需在主线程调用一次）
    """
    def _poll():
        text_handler.poll()
        root.after(interval_ms, _poll)
    _poll()