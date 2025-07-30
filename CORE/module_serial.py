import serial
import threading
import serial.tools.list_ports
from datetime import datetime

class SerialConfig:
    """串口配置参数结构体"""
    def __init__(self):
        self.port = ""                              # 端口号
        self.baudrate = 115200                      # 波特率
        self.databits = 8                           # 每个传输字节中实际用于传输数据的位数
        self.stopbits = 1
        self.parity = 'N'  # 可选: N, E, O, M, S
        self.ack_event = threading.Event()
        self.last_ack_result = None
        self._ack_buffer = []

class SerialCore:
    """
    核心串口操作类
    """
    def __init__(self):
        self.SERIAL_INSTANCE = None
        self.config = SerialConfig()
        self.rx_count = 0
        self.tx_count = 0
        self.lock = threading.Lock()
        self.recv_thread = None
        self.running = False
        self.event_handlers = []
        self.log_manager = SerialLogManager()
        self.data_processor = SerialDataProcessor()

    def add_event_handler(self, handler):
        """添加事件处理器对象，需包含 on_data_received/on_data_sent/on_error 等方法"""
        self.event_handlers.append(handler)

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
            self.running = True
            self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
            self.recv_thread.start()
            return True
        except Exception as e:
            self._log_error(f"连接失败: {e}")
            return False

    def disconnect(self):
        """断开串口连接"""
        self.running = False
        if self.SERIAL_INSTANCE:
            self.SERIAL_INSTANCE.close()
            self.SERIAL_INSTANCE = None

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
            self._notify_send(data)
            self.log_manager.log_data(data, tx=True)
            return True
        except Exception as e:
            self._log_error(f"发送失败: {e}")
            return False

    def send_text(self, text: str) -> bool:
        """发送 UTF-8 编码的字符串"""
        try:
            data = text.encode("utf-8")
            with self.lock:
                self.SERIAL_INSTANCE.write(data)
                self.tx_count += len(data)
            self._notify_send(data)
            self.log_manager.log_data(data, tx=True)
            return True
        except Exception as e:
            self._log_error(f"发送失败: {e}")
            return False

    def send_hex(self, hex_str: str) -> bool:
        """发送十六进制字符串（空格可选）"""
        try:
            data = bytes.fromhex(hex_str.replace(" ", "").strip())
            with self.lock:
                self.SERIAL_INSTANCE.write(data)
                self.tx_count += len(data)
            self._notify_send(data)
            self.log_manager.log_data(data, tx=True)
            return True
        except Exception as e:
            self._log_error(f"HEX发送失败: {e}")
            return False

    def _recv_loop(self):
        """后台接收线程，不断读取数据并派发给事件处理器"""
        while self.running and self.SERIAL_INSTANCE and self.SERIAL_INSTANCE.is_open:
            try:
                data = self.SERIAL_INSTANCE.read(self.SERIAL_INSTANCE.in_waiting or 1)
                if data:
                    self.rx_count += len(data)
                    self.data_processor.process(data)
                    self._notify_recv(data)
                    self.log_manager.log_data(data, tx=False)
            except Exception as e:
                self._log_error(f"接收线程异常: {e}")

    def _notify_recv(self, data: bytes):
        """通知外部接收到数据"""
        processed = self.data_processor.decode(data)
        for h in self.event_handlers:
            if hasattr(h, "on_data_received"):
                h.on_data_received(processed)

    def _notify_send(self, data: bytes):
        """通知外部已发送数据"""
        for h in self.event_handlers:
            if hasattr(h, "on_data_sent"):
                h.on_data_sent(data)

    def _log_error(self, msg: str):
        """通知外部发生错误"""
        for h in self.event_handlers:
            if hasattr(h, "on_error"):
                h.on_error(msg)

    def _get_parity(self, val: str):
        """将字符串转换为 pyserial 的校验枚举值"""
        return {
            'N': serial.PARITY_NONE,
            'E': serial.PARITY_EVEN,
            'O': serial.PARITY_ODD,
            'M': serial.PARITY_MARK,
            'S': serial.PARITY_SPACE
        }.get(val.upper(), serial.PARITY_NONE)

    def get_statistics(self):
        """返回当前会话的统计信息"""
        return self.data_processor.get_stats()


class SerialLogManager:
    """串口日志文件管理器：支持启动、停止、写入"""
    def __init__(self):
        self.log_file = None
        self.log_path = ""
        self.is_logging = False

    def start_logging(self, path, append_mode=False):
        """开始记录日志"""
        try:
            mode = 'a' if append_mode else 'w'
            self.log_file = open(path, mode, encoding='utf-8')
            self.log_path = path
            self.is_logging = True
            return True
        except Exception as e:
            print(f"日志启动失败: {e}")
            return False

    def stop_logging(self):
        """停止日志记录"""
        if self.log_file:
            self.log_file.close()
        self.log_file = None
        self.log_path = ""
        self.is_logging = False

    def log_data(self, data: bytes, tx: bool):
        """写入日志记录"""
        if not self.is_logging or not self.log_file:
            return
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        direction = "TX" if tx else "RX"
        hex_data = data.hex().upper()
        log_line = f"[{timestamp}] {direction}: {hex_data}\n"
        self.log_file.write(log_line)
        self.log_file.flush()


class SerialDataProcessor:
    """会话数据统计与编码处理模块"""
    def __init__(self):
        self.session_bytes = 0
        self.packet_count = 0
        self.log_bytes = 0

    def process(self, data: bytes):
        """处理接收到的数据用于统计"""
        self.session_bytes += len(data)
        self.packet_count += 1
        self.log_bytes += len(data)

    def decode(self, data: bytes) -> dict:
        """将原始字节转换为多种表示形式"""
        ts = datetime.now()
        return {
            "timestamp": ts,
            "raw_data": data,
            "ascii": data.decode('utf-8', errors='replace'),
            "hex": data.hex().upper(),
            "printable_text": ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data)
        }

    def get_stats(self):
        """返回统计信息"""
        return {
            "session_bytes": self.session_bytes,
            "packet_count": self.packet_count,
            "log_bytes": self.log_bytes
        }

    def reset_session_stats(self):
        """重置会话统计"""
        self.session_bytes = 0
        self.packet_count = 0
        self.log_bytes = 0

GLOBAL_SERIAL_CORE = SerialCore()