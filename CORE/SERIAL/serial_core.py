
import serial
import threading
import serial.tools.list_ports
from datetime import datetime
from CORE.SERIAL.serial_event_router import SerialEventRouter
from collections import deque

class SerialConfig:
    def __init__(self):
        self.port = ""
        self.baudrate = 115200
        self.databits = 8
        self.stopbits = 1
        self.parity = 'N'

class SerialCore:
    """
    核心串口操作类 - 提供串口连接、发送、接收、事件分发功能
    """
    def __init__(self):
        self.SERIAL_INSTANCE = None
        self.config = SerialConfig()
        self.rx_count = 0
        self.tx_count = 0
        self.lock = threading.Lock()
        self.recv_thread = None
        self.is_connect = False
        self.event_router = SerialEventRouter()

    def register_handler(self, handler):
        if handler:
            self.event_router.register(handler)

    def get_available_ports(self):
        """枚举系统所有串口设备"""
        return [p.__dict__ for p in serial.tools.list_ports.comports()]

    def connect(self):
        """连接串口并启动后台接收线程"""
        try:
            self.SERIAL_INSTANCE = serial.Serial(
                port=self.config.port,
                baudrate=self.config.baudrate,
                bytesize=int(self.config.databits),
                stopbits=float(self.config.stopbits),
                parity=self._get_parity(self.config.parity),
                timeout=0.1
            )
            self.is_connect = True
            self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
            self.recv_thread.start()
            self.event_router.on_connection_changed(True, self.config.port)
            return True
        except Exception as e:
            self.event_router.on_error(f"连接失败: {e}")
            return False

    def disconnect(self):
        """断开串口连接"""
        self.is_connect = False
        if self.SERIAL_INSTANCE:
            self.SERIAL_INSTANCE.close()
            self.SERIAL_INSTANCE = None
        self.event_router.on_connection_changed(False)

    def test_connection(self):
        """尝试连接串口，用于预检测端口配置是否正确"""
        try:
            test_ser = serial.Serial(
                port=self.config.port,
                baudrate=self.config.baudrate,
                bytesize=int(self.config.databits),
                stopbits=float(self.config.stopbits),
                parity=self._get_parity(self.config.parity),
                timeout=0.5
            )
            result = {
                "success": True,
                "details": {
                    "port": test_ser.port,
                    "baudrate": test_ser.baudrate,
                    "bytesize": test_ser.bytesize,
                    "stopbits": test_ser.stopbits,
                    "parity": test_ser.parity,
                    "in_waiting": test_ser.in_waiting
                }
            }
            test_ser.close()
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    def send_bytes(self, data: bytes) -> bool:
        """发送原始字节数据"""
        try:
            with self.lock:
                self.SERIAL_INSTANCE.write(data)
                self.tx_count += len(data)
            self.event_router.on_data_sent(data)
            return True
        except Exception as e:
            self.event_router.on_error(f"BYTES 发送失败: {e}")
            return False

    def send_text(self, text: str) -> bool:
        if not self.is_connect:
            self.event_router.on_error(f"串口未连接")
            return False
        
        """发送 UTF-8 编码的字符串"""
        try:
            data = text.encode("utf-8")
            print(f"[SerialCore Info] send_text: {data}")
            with self.lock:
                self.SERIAL_INSTANCE.write(data)
                self.tx_count += len(data)
            self.event_router.on_data_sent(data)
            return True
        except Exception as e:
            self.event_router.on_error(f"TEXT 发送失败: {e}")
            return False

    def send_hex(self, hex_str: str) -> bool:
        """发送十六进制字符串"""
        try:
            data = bytes.fromhex(hex_str.replace(" ", "").strip())
            with self.lock:
                self.SERIAL_INSTANCE.write(data)
                self.tx_count += len(data)
            self.event_router.on_data_sent(data)
            return True
        except Exception as e:
            self.event_router.on_error(f"HEX 发送失败: {e}")
            return False

    def _recv_loop(self):
        """后台接收线程，不断读取数据并派发给事件处理器"""
        rec_buffer = b""  # 当前拼接缓冲区
        while self.is_connect and self.SERIAL_INSTANCE and self.SERIAL_INSTANCE.is_open:
            try:
                data = self.SERIAL_INSTANCE.read(self.SERIAL_INSTANCE.in_waiting or 1)
                if data:
                    rec_buffer += data

                    # 如果包含完整一行
                    while b'\r\n' in rec_buffer:
                        line, rec_buffer = rec_buffer.split(b'\r\n', 1) # 防止切一半扔一半
                        line_str = line.decode(errors="ignore").strip()
                        # 构建数据包
                        processed = {
                            "timestamp": datetime.now(),
                            "origin_content": line,
                            "decode_content": line_str
                        }
                        # 广播给各个 handler
                        self.event_router.on_data_received(processed)
            except Exception as e:
                self.event_router.on_error(f"接收线程异常: {e}")

    def _get_parity(self, val: str):
        """将字符串转换为 pyserial 的校验枚举值"""
        return {
            'N': serial.PARITY_NONE,
            'E': serial.PARITY_EVEN,
            'O': serial.PARITY_ODD,
            'M': serial.PARITY_MARK,
            'S': serial.PARITY_SPACE
        }.get(val.upper(), serial.PARITY_NONE)

class SerialDataProcessor:
    def __init__(self):
        pass

    def process(self, data: bytes):
        pass

    def decode(self, data: bytes) -> dict:
        pass

# 全局单例实例
GLOBAL_SERIAL_CORE = SerialCore()
