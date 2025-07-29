# CLI/cli_moni.py - 串口监视器CLI模块 (包含异步监听功能)

import argparse
import threading
import time
import sys
import os
import signal
from datetime import datetime
from collections import deque
from typing import Optional, Dict, List
from CORE.serial_api import create_serial_monitor, SerialEventHandler

class MessageBuffer:
    """消息缓冲器，用于拼接完整的串口消息"""
    
    def __init__(self):
        self.buffer = ""
        self.lock = threading.Lock()
        
    def add_data(self, data: str) -> List[str]:
        """
        添加接收到的数据，返回完整的消息列表
        
        Args:
            data: 新接收到的数据
            
        Returns:
            List[str]: 完整消息列表
        """
        with self.lock:
            self.buffer += data
            complete_messages = []
            
            # 按换行符分割消息
            lines = self.buffer.split('\n')
            
            # 最后一行可能不完整，保留在缓冲区
            self.buffer = lines[-1]
            
            # 处理完整的消息（除了最后一行）
            for line in lines[:-1]:
                line = line.strip()
                if line:  # 忽略空行
                    complete_messages.append(line)
                    
            return complete_messages
    
    def clear(self):
        """清空缓冲区"""
        with self.lock:
            self.buffer = ""

class CLIEventHandler(SerialEventHandler):
    """CLI模式下的串口事件处理器"""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.running = True
        self.message_buffer = MessageBuffer()
        
    def on_data_received(self, processed_data: dict) -> None:
        """处理接收到的数据"""
        if not self.verbose or not self.running:
            return
            
        # 获取接收时间戳
        receive_timestamp = processed_data['timestamp']
        ascii_data = processed_data['ascii']
        
        # 将数据添加到缓冲区，获取完整消息
        complete_messages = self.message_buffer.add_data(ascii_data)
        
        # 显示每条完整的消息
        for message in complete_messages:
            timestamp_str = receive_timestamp.strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp_str}] RX: {message}")
    
    def on_data_sent(self, data: bytes) -> None:
        """处理发送的数据"""
        if not self.verbose or not self.running:
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        try:
            text = data.decode('utf-8', errors='replace').rstrip('\r\n')
            if text:
                print(f"[{timestamp}] TX: {text}")
        except:
            print(f"[{timestamp}] TX: <binary data {len(data)} bytes>")
    
    def on_connection_changed(self, connected: bool, port: str = None) -> None:
        """处理连接状态变化"""
        if connected:
            print(f"✓ 串口连接成功: {port}")
        else:
            print(f"✗ 串口连接断开: {port or ''}")
    
    def on_error(self, error: str) -> None:
        """处理错误信息"""
        print(f"❌ 错误: {error}")
        
    def stop(self):
        """停止事件处理"""
        self.running = False

class AsyncMonitorEventHandler(SerialEventHandler):
    """异步监视器事件处理器"""
    
    def __init__(self, monitor_instance):
        self.monitor = monitor_instance
        
    def on_data_received(self, processed_data: dict) -> None:
        """数据接收事件处理"""
        self.monitor.handle_received_data(processed_data)
        
    def on_data_sent(self, data: bytes) -> None:
        """数据发送事件处理"""
        pass
        
    def on_connection_changed(self, connected: bool, port: str = None) -> None:
        """连接状态变化事件处理"""
        self.monitor.handle_connection_change(connected, port)
        
    def on_error(self, error: str) -> None:
        """错误事件处理"""
        self.monitor.handle_error(error)

class AsyncSerialMonitor:
    """异步串口监视器 - 全局单例"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.serial_core = None
        self.is_monitoring = False
        self.data_cache = deque(maxlen=1000)  # 环形缓冲区
        self.log_enabled = False
        self.log_file = None
        self.lock = threading.Lock()
        self.port = None
        self.baudrate = None
        self.start_time = None
        self.total_received = 0
        self.message_buffer = MessageBuffer()  # 消息缓冲器
        self._initialized = True
        
    def start_monitoring(self, port: str, baudrate: int, log_file: Optional[str] = None) -> bool:
        """开始后台监听"""
        if self.is_monitoring:
            print("❌ 监听已在运行中")
            return False
            
        try:
            # 创建串口监视器
            self.serial_core = create_serial_monitor()
            self.serial_core.config.port = port
            self.serial_core.config.baudrate = baudrate
            
            # 添加事件处理器
            handler = AsyncMonitorEventHandler(self)
            self.serial_core.add_event_handler(handler)
            
            # 连接串口
            if not self.serial_core.connect():
                print(f"❌ 无法连接串口 {port}@{baudrate}")
                return False
                
            # 设置日志
            if log_file:
                self.enable_logging(log_file)
                
            # 清空消息缓冲区
            self.message_buffer.clear()
                
            # 更新状态
            self.is_monitoring = True
            self.port = port
            self.baudrate = baudrate
            self.start_time = datetime.now()
            self.total_received = 0
            
            print(f"✓ 后台串口监听已启动: {port}@{baudrate}")
            if log_file:
                print(f"📝 日志记录到: {log_file}")
            else:
                print("💾 数据缓存在内存中")
                
            return True
            
        except Exception as e:
            print(f"❌ 启动监听失败: {e}")
            return False
    
    def stop_monitoring(self) -> bool:
        """停止监听"""
        if not self.is_monitoring:
            print("⚠️  监听未运行")
            return False
            
        try:
            # 停止串口连接
            if self.serial_core:
                self.serial_core.disconnect()
                
            # 关闭日志文件
            self.disable_logging()
            
            # 清空消息缓冲区
            self.message_buffer.clear()
            
            # 更新状态
            self.is_monitoring = False
            
            # 显示统计信息
            duration = datetime.now() - self.start_time if self.start_time else None
            print(f"✓ 后台串口监听已停止")
            print(f"📊 统计: 运行时长 {duration}, 接收数据 {self.total_received} 条, 缓存 {len(self.data_cache)} 条")
            
            return True
            
        except Exception as e:
            print(f"❌ 停止监听失败: {e}")
            return False
    
    def enable_logging(self, log_file: str) -> bool:
        """动态开启文件日志"""
        try:
            if self.log_file:
                self.log_file.close()
                
            self.log_file = open(log_file, 'a', encoding='utf-8')
            self.log_enabled = True
            
            # 写入日志头
            header = f"\n=== 串口监听日志 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n"
            self.log_file.write(header)
            self.log_file.flush()
            
            print(f"✓ 文件日志已启用: {log_file}")
            return True
            
        except Exception as e:
            print(f"❌ 启用日志失败: {e}")
            return False
    
    def disable_logging(self) -> bool:
        """动态关闭文件日志"""
        try:
            if self.log_file:
                footer = f"=== 日志结束 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n"
                self.log_file.write(footer)
                self.log_file.close()
                self.log_file = None
                
            self.log_enabled = False
            print("✓ 文件日志已关闭")
            return True
            
        except Exception as e:
            print(f"❌ 关闭日志失败: {e}")
            return False
    
    def handle_received_data(self, processed_data: dict):
        """处理接收到的数据"""
        with self.lock:
            try:
                # 获取接收时间戳和数据
                receive_timestamp = processed_data['timestamp']
                raw_data = processed_data['raw_data']
                ascii_data = processed_data['ascii']
                
                # 将数据添加到消息缓冲区，获取完整消息
                complete_messages = self.message_buffer.add_data(ascii_data)
                
                # 处理每条完整的消息
                for message in complete_messages:
                    # 构建缓存数据
                    cache_data = {
                        'timestamp': receive_timestamp,
                        'raw_text': message,
                        'length': len(message.encode('utf-8')),
                        'packet_id': processed_data.get('packet_id', 0)
                    }
                    
                    # 缓存数据
                    self.data_cache.append(cache_data)
                    self.total_received += 1
                    
                    # 写入日志文件
                    if self.log_enabled and self.log_file:
                        log_line = self._format_log_line(cache_data)
                        self.log_file.write(log_line + '\n')
                        self.log_file.flush()
                    
            except Exception as e:
                print(f"❌ 数据处理错误: {e}")
    
    def handle_connection_change(self, connected: bool, port: str = None):
        """处理连接状态变化"""
        if not connected and self.is_monitoring:
            print(f"⚠️  串口连接断开: {port}")
    
    def handle_error(self, error: str):
        """处理错误"""
        print(f"❌ 串口监听错误: {error}")
    
    def _format_log_line(self, data: Dict) -> str:
        """格式化日志行"""
        timestamp = data['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return f"[{timestamp}] {data['raw_text']}"
    
    def get_status(self) -> Dict:
        """获取监听状态"""
        return {
            'is_monitoring': self.is_monitoring,
            'port': self.port,
            'baudrate': self.baudrate,
            'start_time': self.start_time,
            'log_enabled': self.log_enabled,
            'total_received': self.total_received,
            'cached_count': len(self.data_cache)
        }
    
    def get_cached_data(self, count: Optional[int] = None) -> List[Dict]:
        """获取缓存数据"""
        with self.lock:
            if count is None:
                return list(self.data_cache)
            else:
                return list(self.data_cache)[-count:] if count > 0 else list(self.data_cache)
    
    def save_cache_to_file(self, filename: str) -> bool:
        """保存缓存数据到文件"""
        try:
            with self.lock:
                data_list = list(self.data_cache)
                
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# 串口监听数据导出 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 总计 {len(data_list)} 条数据\n\n")
                
                for data in data_list:
                    f.write(self._format_log_line(data) + '\n')
                    
            print(f"✓ 缓存数据已保存到: {filename} ({len(data_list)} 条)")
            return True
            
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return False
    
    def clear_cache(self) -> bool:
        """清空数据缓存"""
        try:
            with self.lock:
                self.data_cache.clear()
                print("✓ 数据缓存已清空")
                return True
        except Exception as e:
            print(f"❌ 清空缓存失败: {e}")
            return False

# 全局异步监听器实例
_global_monitor = AsyncSerialMonitor()

# 🔧 新增：暴露串口核心接口供外部访问（如 cli_clock 使用）
serial_monitor = None

def run_moni_cli(args_list):
    """串口监视器CLI主入口函数"""
    parser = argparse.ArgumentParser(
        prog="moni", 
        description="串口监视器 CLI 工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
基础串口功能:
  moni ports                              # 列出所有可用串口
  moni test COM3 115200                   # 测试串口连接
  moni listen COM3 115200                 # 监听串口数据
  moni interactive COM3 115200            # 交互式串口终端
  moni send COM3 115200 "Hello World"     # 发送文本

异步监听功能:
  moni start_monitor COM3 115200          # 开始后台监听
  moni start_monitor COM3 115200 --log data.log  # 开始监听并记录日志
  moni stop_monitor                       # 停止后台监听
  moni monitor_status                     # 查看监听状态
  moni show_data 10                       # 显示最近10条缓存数据
  moni enable_log test.log                # 动态开启日志记录
  moni disable_log                        # 动态关闭日志记录
  moni save_log all_data.txt              # 保存缓存数据到文件
  moni clear_cache                        # 清空数据缓存
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # === 基础串口功能 ===
    subparsers.add_parser("ports", help="列出所有可用串口")

    parser_test = subparsers.add_parser("test", help="测试串口连接")
    parser_test.add_argument("port", help="串口号 (如: COM3, /dev/ttyUSB0)")
    parser_test.add_argument("baudrate", type=int, help="波特率 (如: 115200)")

    parser_listen = subparsers.add_parser("listen", help="监听串口数据")
    parser_listen.add_argument("port", help="串口号")
    parser_listen.add_argument("baudrate", type=int, help="波特率")
    parser_listen.add_argument("--timeout", type=int, default=0, help="监听超时时间(秒，0表示无限)")
    parser_listen.add_argument("--log", type=str, help="日志文件路径")
    parser_listen.add_argument("--quiet", action="store_true", help="静默模式，不显示接收数据")

    parser_interactive = subparsers.add_parser("interactive", help="交互式串口终端")
    parser_interactive.add_argument("port", help="串口号")
    parser_interactive.add_argument("baudrate", type=int, help="波特率")

    parser_send = subparsers.add_parser("send", help="发送文本数据")
    parser_send.add_argument("port", help="串口号")
    parser_send.add_argument("baudrate", type=int, help="波特率")
    parser_send.add_argument("text", help="要发送的文本")
    parser_send.add_argument("--cr", action="store_true", help="添加回车符(\\r)")
    parser_send.add_argument("--lf", action="store_true", help="添加换行符(\\n)")
    parser_send.add_argument("--crlf", action="store_true", help="添加回车换行符(\\r\\n)")

    parser_stats = subparsers.add_parser("stats", help="获取串口统计信息")
    parser_stats.add_argument("port", help="串口号")
    parser_stats.add_argument("baudrate", type=int, help="波特率")

    # === 异步监听功能 ===
    parser_start = subparsers.add_parser("start_monitor", help="开始后台监听")
    parser_start.add_argument("port", help="串口号")
    parser_start.add_argument("baudrate", type=int, help="波特率")
    parser_start.add_argument("--log", type=str, help="日志文件路径")

    subparsers.add_parser("stop_monitor", help="停止后台监听")
    subparsers.add_parser("monitor_status", help="查看监听状态")

    parser_show = subparsers.add_parser("show_data", help="显示缓存数据")
    parser_show.add_argument("count", nargs='?', type=int, help="显示条数，默认显示所有")

    parser_enable_log = subparsers.add_parser("enable_log", help="动态开启日志记录")
    parser_enable_log.add_argument("filename", help="日志文件名")

    subparsers.add_parser("disable_log", help="动态关闭日志记录")

    parser_save = subparsers.add_parser("save_log", help="保存缓存数据到文件")
    parser_save.add_argument("filename", help="保存的文件名")

    subparsers.add_parser("clear_cache", help="清空数据缓存")

    # 解析参数
    if not args_list:
        parser.print_help()
        return

    try:
        args = parser.parse_args(args_list)
    except SystemExit:
        return

    # 执行相应的命令
    try:
        if args.command == "ports":
            _cmd_list_ports()
        elif args.command == "test":
            _cmd_test_connection(args)
        elif args.command == "listen":
            _cmd_listen_mode(args)
        elif args.command == "interactive":
            _cmd_interactive_mode(args)
        elif args.command == "send":
            _cmd_send_text(args)
        elif args.command == "stats":
            _cmd_get_stats(args)
        # 异步监听命令
        elif args.command == "start_monitor":
            _cmd_start_monitor(args)
        elif args.command == "stop_monitor":
            _cmd_stop_monitor()
        elif args.command == "monitor_status":
            _cmd_monitor_status()
        elif args.command == "show_data":
            _cmd_show_data(args)
        elif args.command == "enable_log":
            _cmd_enable_log(args)
        elif args.command == "disable_log":
            _cmd_disable_log()
        elif args.command == "save_log":
            _cmd_save_log(args)
        elif args.command == "clear_cache":
            _cmd_clear_cache()
        else:
            parser.print_help()
    except KeyboardInterrupt:
        print("\n操作被用户取消")
    except Exception as e:
        print(f"❌ 执行命令时出错: {e}")

# =============================================================================
# 基础串口功能实现
# =============================================================================

def _cmd_list_ports():
    """列出所有可用串口"""
    print("正在扫描可用串口...")
    serial = create_serial_monitor()
    ports = serial.get_available_ports()
    
    if ports:
        print(f"\n找到 {len(ports)} 个可用串口:")
        print("-" * 80)
        print(f"{'端口':<12} {'描述':<30} {'制造商':<20} {'硬件ID'}")
        print("-" * 80)
        
        for port in ports:
            device = port['device']
            description = port.get('description', 'Unknown')[:28]
            manufacturer = port.get('manufacturer', 'Unknown')[:18]
            hwid = port.get('hwid', 'Unknown')[:20]
            print(f"{device:<12} {description:<30} {manufacturer:<20} {hwid}")
    else:
        print("❌ 未找到可用串口")

def _cmd_test_connection(args):
    """测试串口连接"""
    print(f"正在测试串口连接: {args.port}@{args.baudrate}...")
    
    serial = create_serial_monitor()
    result = serial.test_connection(args.port, args.baudrate)
    
    if result["success"]:
        print(f"✓ 连接测试成功!")
        details = result['details']
        print(f"  端口: {details['port']}")
        print(f"  波特率: {details['baudrate']}")
        print(f"  数据位: {details['bytesize']}")
        print(f"  停止位: {details['stopbits']}")
        print(f"  校验位: {details['parity']}")
        print(f"  超时: {details['timeout']}s")
        print(f"  输入缓冲: {details['in_waiting']} 字节")
    else:
        print(f"❌ 连接测试失败: {result.get('error')}")

def _cmd_listen_mode(args):
    """监听模式实现"""
    print(f"正在连接串口: {args.port}@{args.baudrate}...")
    
    serial = create_serial_monitor()
    handler = CLIEventHandler(verbose=not args.quiet)
    serial.add_event_handler(handler)
    
    serial.config.port = args.port
    serial.config.baudrate = args.baudrate
    
    if args.log:
        if not serial.log_manager.start_logging(args.log):
            print(f"❌ 无法创建日志文件: {args.log}")
            return
        print(f"📝 日志记录到: {args.log}")
    
    if not serial.connect():
        print(f"❌ 连接失败: {args.port}@{args.baudrate}")
        return
    
    stop_event = threading.Event()
    
    def signal_handler(signum, frame):
        print("\n正在停止监听...")
        handler.stop()
        stop_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print(f"📡 开始监听 {args.port}@{args.baudrate}")
    print("按 Ctrl+C 停止监听")
    if not args.quiet:
        print("-" * 50)
    
    try:
        start_time = time.time()
        while not stop_event.is_set():
            if args.timeout > 0 and time.time() - start_time > args.timeout:
                print(f"\n⏰ 监听超时 ({args.timeout}秒)")
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        print("\n正在断开连接...")
        serial.disconnect()
        
        stats = serial.get_statistics()
        print(f"📊 统计信息:")
        print(f"  接收字节: {stats['session_bytes']}")
        print(f"  数据包数: {stats['packet_count']}")
        if args.log:
            print(f"  日志字节: {stats['log_bytes']}")

def _cmd_interactive_mode(args):
    """交互模式实现"""
    print(f"正在启动交互式串口终端: {args.port}@{args.baudrate}...")
    
    serial = create_serial_monitor()
    handler = CLIEventHandler(verbose=True)
    serial.add_event_handler(handler)
    
    serial.config.port = args.port
    serial.config.baudrate = args.baudrate
    
    if not serial.connect():
        print(f"❌ 连接失败: {args.port}@{args.baudrate}")
        return
    
    print(f"🖥️  交互式串口终端")
    print("=" * 50)
    print("命令:")
    print("  输入文本直接发送")
    print("  /stats          - 显示统计信息")
    print("  /help           - 显示帮助")
    print("  /exit           - 退出")
    print("=" * 50)
    
    try:
        while True:
            try:
                user_input = input(">> ").strip()
                
                if not user_input:
                    continue
                    
                if user_input == '/exit':
                    break
                elif user_input == '/help':
                    _show_interactive_help()
                elif user_input == '/stats':
                    _show_interactive_stats(serial)
                else:
                    if serial.send_text(user_input + '\n'):
                        pass
                    else:
                        print(f"❌ 发送失败")
                        
            except EOFError:
                break
                
    except KeyboardInterrupt:
        pass
    finally:
        print("\n正在退出交互模式...")
        serial.disconnect()

def _show_interactive_help():
    """显示交互模式帮助"""
    print("""
交互模式命令:
  普通文本              - 直接发送文本 (自动添加换行符)
  /stats                - 显示连接统计信息
  /help                 - 显示此帮助信息
  /exit                 - 退出交互模式
    """)

def _show_interactive_stats(serial):
    """显示交互模式统计信息"""
    stats = serial.get_statistics()
    print(f"""
📊 连接统计:
  状态: {'已连接' if stats['is_connected'] else '未连接'}
  端口: {stats.get('current_port', 'N/A')}
  会话接收: {stats['session_bytes']} 字节
  总接收: {stats['total_bytes']} 字节
  数据包数: {stats['packet_count']}
  日志状态: {'启用' if stats['log_enabled'] else '禁用'}
    """)

def _cmd_send_text(args):
    """发送文本命令"""
    serial = create_serial_monitor()
    serial.config.port = args.port
    serial.config.baudrate = args.baudrate
    
    print(f"正在连接 {args.port}@{args.baudrate}...")
    if not serial.connect():
        print(f"❌ 连接失败")
        return
    
    try:
        text = args.text
        if args.crlf:
            text += '\r\n'
        elif args.cr:
            text += '\r'
        elif args.lf:
            text += '\n'
        
        print(f"发送文本: {repr(text)}")
        if serial.send_text(text):
            print("✓ 发送成功")
        else:
            print("❌ 发送失败")
    finally:
        serial.disconnect()

def _cmd_get_stats(args):
    """获取统计信息命令"""
    serial = create_serial_monitor()
    serial.config.port = args.port
    serial.config.baudrate = args.baudrate
    
    print(f"正在连接 {args.port}@{args.baudrate}...")
    if not serial.connect():
        print(f"❌ 连接失败")
        return
    
    try:
        stats = serial.get_statistics()
        print("📊 串口统计信息:")
        print(f"  连接状态: {'已连接' if stats['is_connected'] else '未连接'}")
        print(f"  当前端口: {stats.get('current_port', 'N/A')}")
        print(f"  会话接收: {stats['session_bytes']} 字节") 
        print(f"  总接收: {stats['total_bytes']} 字节") 
        print(f"  数据包数: {stats['packet_count']}")
        print(f"  日志状态: {'启用' if stats['log_enabled'] else '禁用'}")
        if stats['log_enabled']:
            print(f"  日志文件: {stats['log_file']}")
            print(f"  日志大小: {stats['log_bytes']} 字节")
        
        if stats['is_connected']:
            print(f"  输入缓冲: {stats.get('in_waiting', 0)} 字节")
            print(f"  输出缓冲: {stats.get('out_waiting', 0)} 字节")
    finally:
        serial.disconnect()

# =============================================================================
# 异步监听功能实现
# =============================================================================

def _cmd_start_monitor(args):
    """开始后台监听"""
    _global_monitor.start_monitoring(args.port, args.baudrate, args.log)

def _cmd_stop_monitor():
    """停止后台监听"""
    _global_monitor.stop_monitoring()

def _cmd_monitor_status():
    """查看监听状态"""
    status = _global_monitor.get_status()
    
    if status['is_monitoring']:
        duration = datetime.now() - status['start_time'] if status['start_time'] else None
        print("📊 监听状态:")
        print(f"  状态: 运行中")
        print(f"  端口: {status['port']}@{status['baudrate']}")
        print(f"  运行时长: {duration}")
        print(f"  接收数据: {status['total_received']} 条")
        print(f"  缓存数据: {status['cached_count']}/1000 条")
        print(f"  文件日志: {'启用' if status['log_enabled'] else '禁用'}")
    else:
        print("📊 监听状态: 未运行")

def _cmd_show_data(args):
    """显示缓存数据"""
    try:
        count = args.count if hasattr(args, 'count') else None
        data_list = _global_monitor.get_cached_data(count)
        
        if not data_list:
            print("暂无缓存数据")
            return
        
        print(f"📋 缓存数据 (显示 {len(data_list)} 条):")
        print("-" * 80)
        
        for data in data_list:
            timestamp = data['timestamp'].strftime('%H:%M:%S.%f')[:-3]
            print(f"[{timestamp}] {data['raw_text']}")
                
    except Exception as e:
        print(f"❌ 显示数据失败: {e}")

def _cmd_enable_log(args):
    """开启文件日志"""
    _global_monitor.enable_logging(args.filename)

def _cmd_disable_log():
    """关闭文件日志"""
    _global_monitor.disable_logging()

def _cmd_save_log(args):
    """保存缓存数据到文件"""
    _global_monitor.save_cache_to_file(args.filename)

def _cmd_clear_cache():
    """清空数据缓存"""
    _global_monitor.clear_cache()

# =============================================================================
# 对外提供的接口函数 (供main_shell.py调用)
# =============================================================================

def start_monitor(port: str, baudrate: int, log_file: Optional[str] = None) -> bool:
    """
    开始后台串口监听
    
    Args:
        port: 串口号 (如: COM3)
        baudrate: 波特率 (如: 115200)
        log_file: 可选的日志文件路径
        
    Returns:
        bool: 成功返回True，失败返回False
        
    作用:
        - 在后台启动串口监听线程
        - 默认不在终端显示数据，只缓存在内存中
        - 如果指定log_file，则同时写入文件日志
        - 支持异步操作，不阻塞主shell线程
    """
    # return _global_monitor.start_monitoring(port, baudrate, log_file)
    global serial_monitor  # ✅ 声明我们要用全局变量
    result = _global_monitor.start_monitoring(port, baudrate, log_file)
    if result:
        serial_monitor = _global_monitor.serial_core  # ✅ 将当前串口对象赋给 serial_monitor
    else:
        serial_monitor = None
    return result

def stop_monitor() -> bool:
    """
    停止后台串口监听
    
    Returns:
        bool: 成功返回True，失败返回False
        
    作用:
        - 停止后台监听线程
        - 断开串口连接
        - 关闭日志文件（如果已开启）
        - 显示统计信息
    """
    return _global_monitor.stop_monitoring()

def get_monitor_status() -> Dict:
    """
    获取监听状态信息
    
    Returns:
        Dict: 包含监听状态的字典
        
    作用:
        - 返回当前监听状态（运行中/已停止）
        - 返回连接信息（端口、波特率）
        - 返回统计信息（运行时长、接收数据量、缓存数量）
        - 返回日志状态
    """
    return _global_monitor.get_status()

def show_cached_data(count: Optional[int] = None) -> List[Dict]:
    """
    获取缓存的监听数据
    
    Args:
        count: 可选，指定返回的数据条数，None表示返回全部
        
    Returns:
        List[Dict]: 缓存数据列表
        
    作用:
        - 返回内存中缓存的串口数据
        - 每条数据包含时间戳、原始文本、长度等信息
        - 支持指定返回条数（用于查看最近N条数据）
    """
    return _global_monitor.get_cached_data(count)

def enable_logging(log_file: str) -> bool:
    """
    动态开启文件日志记录
    
    Args:
        log_file: 日志文件路径
        
    Returns:
        bool: 成功返回True，失败返回False
        
    作用:
        - 在监听运行过程中动态开启文件日志
        - 从开启时刻开始将接收到的数据写入文件
        - 支持在测试的关键阶段开启日志记录
    """
    return _global_monitor.enable_logging(log_file)

def disable_logging() -> bool:
    """
    动态关闭文件日志记录
    
    Returns:
        bool: 成功返回True，失败返回False
        
    作用:
        - 停止向文件写入日志
        - 关闭日志文件
        - 监听继续进行，只是不再记录到文件
    """
    return _global_monitor.disable_logging()

def save_cache_to_file(filename: str) -> bool:
    """
    保存缓存数据到文件
    
    Args:
        filename: 保存的文件名
        
    Returns:
        bool: 成功返回True，失败返回False
        
    作用:
        - 将内存中的所有缓存数据保存到指定文件
        - 用于在测试结束后导出完整的数据记录
        - 包含时间戳和原始数据内容
    """
    return _global_monitor.save_cache_to_file(filename)

def clear_cache() -> bool:
    """
    清空数据缓存
    
    Returns:
        bool: 成功返回True，失败返回False
        
    作用:
        - 清空内存中的数据缓存
        - 用于在新的测试阶段开始前清理旧数据
        - 不影响正在进行的监听和日志记录
    """
    return _global_monitor.clear_cache()

def is_monitoring() -> bool:
    """
    检查是否正在监听
    
    Returns:
        bool: 正在监听返回True，否则返回False
        
    作用:
        - 简单的状态检查函数
        - 用于其他模块判断串口监听状态
    """
    return _global_monitor.is_monitoring

# 用于测试的主函数
if __name__ == "__main__":
    import sys
    run_moni_cli(sys.argv[1:])