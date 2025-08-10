import threading
from collections import defaultdict
from CORE.SERIAL.serial_packet_parser import AckType,SerialPacketParser
from CORE.SERIAL.gui_serial_handler import GUISerialEventHandler
from CORE.SERIAL.cli_serial_handler import CLISerialHandler
class SerialEventRouter:
    def __init__(self):
        self.handlers = []
        self.ack_events = defaultdict(threading.Event)
        self.packet_parser = SerialPacketParser(event_router=self)
# ===============================================================================================================================================================
# ===============================================================================================================================================================
# ===========================================================================ACK 机制相关=========================================================================   
# ===============================================================================================================================================================     
# ===============================================================================================================================================================  

    def reset_ack(self, ack_type: AckType):
        """重置 ACK 等待事件"""
        self.ack_events[ack_type].clear()

    def wait_for_ack(self, ack_type: AckType, timeout=1.0) -> bool:
        """等待指定 ACK 类型的回应"""
        return self.ack_events[ack_type].wait(timeout)

    def trigger_ack(self, ack_type: AckType):
        """手动触发 ACK 到达"""
        self.ack_events[ack_type].set()

    def ack_exists(self, ack_type: AckType) -> bool:
        """是否存在该 ACK 类型"""
        return ack_type in self.ack_events

# ===============================================================================================================================================================
# ===============================================================================================================================================================
# ===========================================================================ACK 机制相关=========================================================================   
# ===============================================================================================================================================================     
# ===============================================================================================================================================================  

# ===============================================================================================================================================================
# ===============================================================================================================================================================
# ===========================================================================事件分发机制=========================================================================   
# ===============================================================================================================================================================     
# ===============================================================================================================================================================  

    def register(self, handler):
        """注册事件"""
        handler_name = getattr(handler, "handler_name", None)
        if handler_name:
            self.handlers = [
                h for h in self.handlers
                if getattr(h, "handler_name", None) != handler_name
            ]
        self.handlers.append(handler)

    def unregister(self, handler):
        """取消注册"""
        handler_name = getattr(handler, "handler_name", None)
        if handler_name:
            self.handlers = [
                h for h in self.handlers
                if getattr(h, "handler_name", None) != handler_name
            ]

    def on_data_received(self, processed_data):
        """接收数据触发"""

        text = processed_data.get("decode_content", "")
        parsed_result = None
        
        # 解析
        if text:
            parsed_result = self.packet_parser.parse(text)
        
        # 原始数据广播
        for h in self.handlers:
            if hasattr(h, "on_data_received"):
                h.on_data_received(processed_data)
                
        # 结构化结果广播
        if parsed_result:
            data_type = parsed_result.get("data_type")
            content = parsed_result.get("data_content")
            for h in self.handlers:
                # 动态分发, 按命名约定查找
                method_name = f"on_data_{data_type.name.lower()}"
                if hasattr(h, method_name):
                    getattr(h, method_name)(content)

    def on_data_sent(self, data):
        """发送数据"""
        for h in self.handlers:
            if hasattr(h, "on_data_sent"):
                h.on_data_sent(data)

    def on_error(self, error):
        """出现错误"""
        for h in self.handlers:
            if isinstance(h, GUISerialEventHandler) and hasattr(h, "on_error"):
                h.on_error(error)
                break
            elif isinstance(h, CLISerialHandler) and hasattr(h, "on_error"):
                h.on_error(error)
                break

    def on_connection_changed(self, connected, port=None):
        """连接更新"""
        for h in self.handlers:
            if hasattr(h, "on_connection_changed"):
                h.on_connection_changed(connected, port)

# ===============================================================================================================================================================
# ===============================================================================================================================================================
# ===========================================================================事件分发机制=========================================================================   
# ===============================================================================================================================================================     
# ===============================================================================================================================================================  
