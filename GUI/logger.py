import logging, queue, tkinter as tk

class TextHandler(logging.Handler):
    """把 logging 输出写到 Tkinter.Text（使用线程安全的 queue）"""
    def __init__(self, text_widget, q):
        super().__init__()
        self.text_widget = text_widget
        self.queue = q

    def emit(self, record):
        self.queue.put(self.format(record))

def gui_logger(text_widget):
    """在 GUI 中启用 logger；返回 queue 方便其他线程放日志"""
    q = queue.Queue()
    handler = TextHandler(text_widget, q)
    handler.setFormatter(logging.Formatter('%(message)s'))
    root_logger = logging.getLogger()
    if not any(isinstance(h, TextHandler) for h in root_logger.handlers):
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)

    def poll_queue():
        while not q.empty():
            msg = q.get_nowait()
            text_widget.config(state="normal")
            text_widget.insert(tk.END, msg + '\n')
            text_widget.see(tk.END)
            text_widget.config(state="disabled")
        text_widget.after(100, poll_queue)

    poll_queue()
    return q
