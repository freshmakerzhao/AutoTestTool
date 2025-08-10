class GUISerialEventHandler:
    """GUI 事件处理器：桥接 SerialCore 与 GUI 页面"""

    def __init__(self, handler_name, gui_page):
        self.handler_name = handler_name
        self.gui_page = gui_page

    def on_data_received(self, processed_data):
        """接收数据"""
        self.gui_page.after(0, self._update_received_data, processed_data)

    def on_data_sent(self, data):
        """发送数据"""
        self.gui_page.after(0, self._update_sent_data, data)

    def on_connection_changed(self, connected, port):
        """连接状态变化"""
        self.gui_page.after(0, self._update_connection_status, connected, port)

    def on_error(self, error):
        """错误信息"""
        self.gui_page.after(0, self._update_error, error)

    def on_data_volget(self, content: dict):
        """展示volget数据"""
        self._safe_call("display_volget_data", content)

    def _update_received_data(self, processed_data):
        self._safe_call("display_received_data", processed_data)

    def _update_sent_data(self, data):
        self._safe_call("display_sent_data", data)

    def _update_connection_status(self, connected, port):
        self._safe_call("update_connection_status", connected, port)

    def _update_error(self, error):
        self._safe_call("show_error", error)

    # 安全回调，有对应回调再调
    def _safe_call(self, method_name: str, *args, **kwargs):
        method = getattr(self.gui_page, method_name, None)
        if callable(method):
            method(*args, **kwargs)