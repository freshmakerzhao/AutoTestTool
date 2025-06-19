# CORE/serial_api.py

import serial
import serial.tools.list_ports
import threading
import queue
import time
import configparser
import logging
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class SerialEventHandler(ABC):
    """串口事件处理器抽象类"""
    @abstractmethod
    def on_data_received(self, data: bytes) -> None: ...
    @abstractmethod
    def on_data_sent(self, data: bytes) -> None: ...
    @abstractmethod
    def on_connection_changed(self, connected: bool, port: str = None) -> None: ...
    @abstractmethod
    def on_error(self, error: str) -> None: ...

class SerialConfig:
    """串口配置类"""
    def __init__(self):
        self.port = "COM1"
        self.baudrate = 115200
        self.databits = 8
        self.stopbits = 1
        self.parity = 'N'
        self.timeout = 1.0

    def to_dict(self):
        return {
            'port': self.port,
            'baudrate': self.baudrate,
            'databits': self.databits,
            'stopbits': self.stopbits,
            'parity': self.parity,
            'timeout': self.timeout
        }

    def from_dict(self, d):
        self.port     = d.get('port', self.port)
        self.baudrate = int(d.get('baudrate', self.baudrate))
        self.databits = int(d.get('databits', self.databits))
        self.stopbits = float(d.get('stopbits', self.stopbits))
        self.parity   = d.get('parity', self.parity)
        self.timeout  = float(d.get('timeout', self.timeout))

class SerialDataProcessor:
    """串口数据处理器"""
    def __init__(self):
        self.total_bytes   = 0
        self.session_bytes = 0
        self.packet_count  = 0

    def process_received_data(self, data: bytes) -> dict:
        self.total_bytes   += len(data)
        self.session_bytes += len(data)
        self.packet_count  += 1

        result = {
            'raw_data': data,
            'length':   len(data),
            'timestamp': datetime.now(),
            'packet_id': self.packet_count,
            'total_bytes':   self.total_bytes,
            'session_bytes': self.session_bytes,
        }
        # ASCII
        try:
            result['ascii'] = data.decode('utf-8', errors='replace')
        except:
            result['ascii'] = data.decode('latin-1', errors='replace')
        # HEX
        result['hex'] = data.hex().upper()
        # printable
        try:
            text = data.decode('utf-8')
            result['printable_text'] = ''.join(c if 32<=ord(c)<=126 else '.' for c in text)
        except:
            result['printable_text'] = ''.join(chr(b) if 32<=b<=126 else '.' for b in data)

        return result

    def reset_session_stats(self):
        self.session_bytes = 0
        self.packet_count  = 0

class SerialLogManager:
    """串口日志管理器"""
    def __init__(self):
        self.log_file = None
        self.log_path = None
        self.is_logging = False
        self.log_bytes  = 0

    def start_logging(self, file_path: str, append_mode: bool = False) -> bool:
        try:
            mode = 'ab' if append_mode else 'wb'
            self.log_file = open(file_path, mode)
            self.log_path = file_path
            self.is_logging = True
            self.log_bytes  = 0
            logger.info(f"开始日志记录: {file_path}")
            return True
        except Exception as e:
            logger.error(f"日志文件创建失败: {e}")
            return False

    def stop_logging(self):
        if self.log_file:
            try:
                self.log_file.close()
                logger.info(f"日志已停止，共写入 {self.log_bytes} 字节")
            except:
                pass
            finally:
                self.log_file = None
                self.is_logging = False
                self.log_path = None

    def write_data(self, data: bytes):
        if self.is_logging and self.log_file:
            try:
                self.log_file.write(data)
                self.log_file.flush()
                self.log_bytes += len(data)
            except Exception as e:
                logger.error(f"日志写入失败: {e}")

class SerialCore:
    """串口核心类"""
    def __init__(self):
        self.config       = SerialConfig()
        self.serial_conn  = None
        self.is_connected = False
        self.data_processor = SerialDataProcessor()
        self.log_manager    = SerialLogManager()
        self.event_handlers = []
        self.receive_thread = None
        self.send_history   = []
        self.max_history    = 50

    def add_event_handler(self, h: SerialEventHandler):
        if h not in self.event_handlers:
            self.event_handlers.append(h)

    def remove_event_handler(self, h: SerialEventHandler):
        if h in self.event_handlers:
            self.event_handlers.remove(h)

    def _notify(self, typ: str, *args):
        for h in self.event_handlers:
            try:
                getattr(h, typ)(*args)
            except Exception as e:
                logger.error(f"事件处理异常: {e}")

    def get_available_ports(self) -> list:
        try:
            return [
                {'device': p.device,
                 'description': p.description,
                 'manufacturer': getattr(p,'manufacturer','Unknown'),
                 'hwid': getattr(p,'hwid','Unknown')}
                for p in serial.tools.list_ports.comports()
            ]
        except Exception as e:
            logger.error(f"获取端口失败: {e}")
            return []

    def test_connection(self, port: str = None, baudrate: int = None) -> dict:
        p = port or self.config.port
        b = baudrate or self.config.baudrate
        res = {'success':False, 'port':p, 'baudrate':b, 'error':None,'details':{}}
        try:
            s = serial.Serial(port=p, baudrate=b,
                              bytesize=self.config.databits,
                              stopbits=self.config.stopbits,
                              parity=self.config.parity,
                              timeout=self.config.timeout)
            res['details'] = {
                'port': s.port, 'baudrate': s.baudrate,
                'bytesize': s.bytesize, 'stopbits': s.stopbits,
                'parity': s.parity, 'timeout': s.timeout,
                'is_open': s.is_open, 'in_waiting': s.in_waiting
            }
            s.close()
            res['success'] = True
            logger.info(f"测试成功: {p}@{b}")
        except Exception as e:
            res['error'] = str(e)
            logger.error(f"测试失败: {e}")
        return res

    def connect(self) -> bool:
        if self.is_connected:
            logger.warning("已连接")
            return True
        try:
            self.serial_conn = serial.Serial(
                port=self.config.port,
                baudrate=self.config.baudrate,
                bytesize=self.config.databits,
                stopbits=self.config.stopbits,
                parity=self.config.parity,
                timeout=0.1
            )
            
            self.is_connected = True
            self.receive_thread = threading.Thread(
                target=self._recv_worker, daemon=True)
            self.receive_thread.start()
            self.data_processor.reset_session_stats()
            logger.info(f"连接成功: {self.config.port}")
            self._notify('on_connection_changed', True, self.config.port)
            return True
        except Exception as e:
            msg = f"连接失败: {e}"
            logger.error(msg)
            self._notify('on_error', msg)
            return False
    def readline(self, timeout: float = 1.0) -> str:
        """
        同步读取一行，直到遇到换行或超时，返回已解码的字符串。
        """
        if not self.is_connected or not self.serial_conn:
            raise RuntimeError("尚未连接串口")
        # 暂时修改超时以支持 readline
        old_to = self.serial_conn.timeout
        self.serial_conn.timeout = timeout
        try:
            raw = self.serial_conn.readline()  # 等待 '\n' 或超时
            return raw.decode('utf-8', errors='ignore')
        finally:
            # 恢复原来的非阻塞小超时
            self.serial_conn.timeout = old_to
    def disconnect(self):
        if not self.is_connected:
            return
        self.is_connected = False
        try:
            if self.serial_conn.is_open:
                self.serial_conn.close()
        except: pass
        self.log_manager.stop_logging()
        self._notify('on_connection_changed', False)
    def flush_input(self):
        """清空串口接收缓冲区"""
        if self.is_connected and self.serial_conn:
            self.serial_conn.reset_input_buffer()  
    def _recv_worker(self):
        while self.is_connected and self.serial_conn and self.serial_conn.is_open:
            try:
                n = self.serial_conn.in_waiting
                if n > 0:
                    data = self.serial_conn.read(n)
                    pd = self.data_processor.process_received_data(data)
                    self.log_manager.write_data(data)
                    self._notify('on_data_received', pd)
                time.sleep(0.01)
            except Exception as e:
                if self.is_connected:
                    msg = f"接收异常: {e}"
                    logger.error(msg)
                    self._notify('on_error', msg)
                break

    def send_data(self, data: bytes) -> bool:
        if not self.is_connected:
            msg = "未连接"
            logger.warning(msg)
            self._notify('on_error', msg)
            return False
        try:
            self.serial_conn.write(data)
            self.serial_conn.flush()
            self._notify('on_data_sent', data)
            return True
        except Exception as e:
            msg = f"发送失败: {e}"
            logger.error(msg)
            self._notify('on_error', msg)
            return False

    def send_text(self, text: str, encoding: str='utf-8') -> bool:
        try:
            b = text.encode(encoding)
            ok = self.send_data(b)
            if ok:
                self._add_history(text)
            return ok
        except Exception as e:
            msg = f"编码失败: {e}"
            logger.error(msg)
            self._notify('on_error', msg)
            return False

    def send_hex(self, hex_str: str) -> bool:
        try:
            clean = hex_str.replace(' ','').replace(',','').replace('-','')
            b = bytes.fromhex(clean)
            ok = self.send_data(b)
            if ok:
                self._add_history(f"HEX:{clean}")
            return ok
        except ValueError as e:
            msg = f"HEX格式错: {e}"
            logger.error(msg)
            self._notify('on_error', msg)
            return False

    def send_file(self, file_path: str, chunk_size: int=1024, delay_ms: int=0) -> bool:
        try:
            with open(file_path,'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    if not self.send_data(chunk):
                        return False
                    if delay_ms>0:
                        time.sleep(delay_ms/1000)
            logger.info(f"文件发送完: {file_path}")
            return True
        except Exception as e:
            msg = f"文件发送失败: {e}"
            logger.error(msg)
            self._notify('on_error', msg)
            return False

    def _add_history(self, txt: str):
        if txt in self.send_history:
            self.send_history.remove(txt)
        self.send_history.insert(0, txt)
        if len(self.send_history)>self.max_history:
            self.send_history = self.send_history[:self.max_history]

    def get_send_history(self) -> list:
        return list(self.send_history)

    def clear_send_history(self):
        self.send_history.clear()

    def get_statistics(self) -> dict:
        stats = {
            'total_bytes':   self.data_processor.total_bytes,
            'session_bytes': self.data_processor.session_bytes,
            'packet_count':  self.data_processor.packet_count,
            'is_connected':  self.is_connected,
            'current_port':  self.config.port if self.is_connected else None,
            'log_enabled':   self.log_manager.is_logging,
            'log_bytes':     self.log_manager.log_bytes,
            'log_file':      self.log_manager.log_path,
        }
        if self.is_connected:
            stats['in_waiting']  = self.serial_conn.in_waiting
            stats['out_waiting'] = getattr(self.serial_conn,'out_waiting',0)
        return stats

    def save_config(self, file_path: str) -> bool:
        try:
            cfg = configparser.ConfigParser()
            cfg['Serial'] = self.config.to_dict()
            for k,v in cfg['Serial'].items():
                cfg['Serial'][k] = str(v)
            with open(file_path,'w') as f:
                cfg.write(f)
            logger.info(f"配置保存: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存失败: {e}")
            return False

    def load_config(self, file_path: str) -> bool:
        try:
            cfg = configparser.ConfigParser()
            cfg.read(file_path)
            if 'Serial' in cfg:
                self.config.from_dict(dict(cfg['Serial']))
                logger.info(f"配置加载: {file_path}")
                return True
            else:
                logger.error("配置文件格式错")
                return False
        except Exception as e:
            logger.error(f"加载失败: {e}")
            return False

def create_serial_monitor() -> SerialCore:
    return SerialCore()

def get_available_ports() -> list:
    return create_serial_monitor().get_available_ports()

def test_serial_connection(port: str, baudrate: int = 115200) -> dict:
    mon = create_serial_monitor()
    mon.config.port     = port
    mon.config.baudrate = baudrate
    return mon.test_connection()
