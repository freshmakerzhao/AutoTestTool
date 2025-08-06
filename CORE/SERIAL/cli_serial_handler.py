from datetime import datetime

class CLISerialHandler:
    """
    CLI 模式下的串口事件处理器：接收、发送、错误信息输出到控制台，
    并支持在发送配置指令时阻塞等待 ACK。
    """

    def __init__(self, handler_name):
        self.handler_name = handler_name

    def on_data_received(self, processed_data):
        pass

    def on_data_sent(self, data: bytes):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        hex_str = data.hex().upper()
        # print(f"[{timestamp}] TX: {hex_str}")

    def on_error(self, error: str):
        print(f"[ERROR] {error}")

    def on_connection_changed(self, connected: bool, port: str = None):
        if connected:
            print(f"[INFO] 串口已连接: {port}")
        else:
            print("[INFO] 串口已断开")
            
    def on_data_volget(self, content: dict):
        """展示volget数据"""
        print(f"[CLISerialHandler Info] voltage is {content}")
            