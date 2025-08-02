class GUISerialEventHandler:
    """GUI 事件处理器：桥接 SerialCore 与 GUI 页面"""

    def __init__(self, gui_page):
        self.gui_page = gui_page

    def on_data_received(self, processed_data):
        """接收数据后通知 GUI"""
        self.gui_page.after(0, self._update_received_data, processed_data)

    def on_data_sent(self, data):
        """发送数据后通知 GUI"""
        self.gui_page.after(0, self._update_sent_data, data)

    def on_connection_changed(self, connected, port):
        """连接状态变化通知 GUI"""
        self.gui_page.after(0, self._update_connection_status, connected, port)

    def on_error(self, error):
        """错误信息通知 GUI"""
        self.gui_page.after(0, self._update_error, error)

    def _update_received_data(self, processed_data):
        self.gui_page.display_received_data(processed_data)

    def _update_sent_data(self, data):
        self.gui_page.display_sent_data(data)

    def _update_connection_status(self, connected, port):
        self.gui_page.update_connection_status(connected, port)

    def _update_error(self, error):
        self.gui_page.show_error(error)
