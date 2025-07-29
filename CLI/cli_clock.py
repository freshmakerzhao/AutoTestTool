# CLI/cli_clock.py
import time
import re
import os
import argparse
import threading
import queue
from CORE.serial_api import SerialCore
from CORE.module_clock import (
    build_clk_set_command,
    build_clk_get_command,
    build_clk_cfg_command,
    parse_clk_response
)

class ClockClient:
    def __init__(self, serial_core: SerialCore):
        self.serial = serial_core
        self._last_idx = 0
        self._response_buffer = []
        self._setup_response_handler()

    def _setup_response_handler(self):
        """设置响应处理器，监听串口数据"""
        self.serial.add_event_handler(self)

    def on_data_received(self, data_dict):
        """串口数据接收事件处理"""
        if 'ascii' in data_dict:
            lines = data_dict['ascii'].split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    self._response_buffer.append(line)
                    # 只保留最近的100条响应，避免内存溢出
                    if len(self._response_buffer) > 100:
                        self._response_buffer.pop(0)

    def on_data_sent(self, data: bytes):
        """数据发送事件处理（暂不需要）"""
        pass

    def on_connection_changed(self, connected: bool, port: str = None):
        """连接状态变化事件处理（暂不需要）"""
        pass

    def on_error(self, error: str):
        """错误事件处理（暂不需要）"""
        pass

    def set_clock(self, table_idx: int):
        """发送时钟 Table 配置命令"""
        self._last_idx = table_idx
        cmd = build_clk_set_command(table_idx)
        self.serial.send_text(cmd + "\n")

    def get_clock(self, timeout: float = 2.0) -> int:
        """发送查询命令并返回当前配置的 table 索引"""
        cmd = build_clk_get_command(self._last_idx)
        
        # 清空响应缓冲区
        self._response_buffer.clear()
        
        self.serial.send_text(cmd + "\n")
        start = time.time()
        
        while time.time() - start < timeout:
            # 检查响应缓冲区
            for i, line in enumerate(self._response_buffer):
                if line.startswith("MC1PCLKGET"):
                    try:
                        result = parse_clk_response(line)
                        # 移除已处理的响应
                        self._response_buffer = self._response_buffer[i+1:]
                        return result
                    except ValueError:
                        continue
            time.sleep(0.1)
            
        raise TimeoutError("Clock get timeout")

    def send_reg_with_ack(self, reg_offset: str, reg_value: str, timeout: float = 2.0) -> bool:
        """
        发送单个寄存器配置并等待确认
        返回 True 表示成功收到确认，False 表示超时或失败
        """
        # 构造并发送命令
        cmd = build_clk_cfg_command(reg_offset, reg_value)
        
        # 清空响应缓冲区中的旧数据
        self._response_buffer.clear()
        
        # 发送命令
        self.serial.send_text(cmd + "\n")
        
        # 等待确认响应
        start = time.time()
        expected_reg = reg_offset.lower().replace("0x", "")
        expected_val = reg_value.lower().replace("0x", "")
        
        while time.time() - start < timeout:
            # 检查响应缓冲区
            for i, line in enumerate(self._response_buffer):
                # 查找确认响应格式：MC1P recv clk reg set reg xxxx value xx
                if "recv clk reg set reg" in line.lower():
                    # 使用正则表达式提取寄存器地址和值
                    match = re.search(r'reg set reg ([0-9a-f]+) value ([0-9a-f]+)', line.lower())
                    if match:
                        recv_reg = match.group(1)
                        recv_val = match.group(2)
                        
                        # 检查是否匹配我们发送的寄存器
                        if recv_reg == expected_reg and recv_val == expected_val:
                            # 移除已处理的响应
                            self._response_buffer = self._response_buffer[i+1:]
                            return True
                            
                # 也检查可能的错误响应
                elif "error" in line.lower() or "fail" in line.lower():
                    print(f"设备响应错误: {line}")
                    return False
                    
            time.sleep(0.05)  # 50ms检查间隔
            
        print(f"等待确认超时: {reg_offset} = {reg_value}")
        return False

    def send_regs_file(self, file_path: str, progress_callback=None) -> dict:
        """
        逐行读取寄存器文件并发送 MC1PCLKCFG 命令。
        progress_callback: 进度回调函数 callback(current, total, success, failed)
        返回发送结果统计。
        """
        count = 0
        success_count = 0
        failed_count = 0
        
        # 首先统计总行数
        total_regs = 0
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = [x.strip() for x in line.split(",")]
                    if len(parts) == 2 and parts[0].startswith("0x"):
                        total_regs += 1
        except Exception as e:
            return {"error": f"文件读取失败: {e}"}
        
        # 发送寄存器配置
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                        
                    parts = [x.strip() for x in line.split(",")]
                    if len(parts) != 2 or not parts[0].startswith("0x"):
                        continue
                    
                    count += 1
                    
                    # 调用进度回调
                    if progress_callback:
                        progress_callback(count, total_regs, success_count, failed_count)
                    
                    # 发送并等待确认
                    try:
                        if self.send_reg_with_ack(parts[0], parts[1], timeout=2.0):
                            success_count += 1
                        else:
                            failed_count += 1
                            print(f"发送失败: {parts[0]} = {parts[1]}")
                    except Exception as e:
                        failed_count += 1
                        print(f"发送异常: {parts[0]} = {parts[1]}, {e}")
                    
                    # 短暂延迟
                    time.sleep(0.01)
                    
        except Exception as e:
            return {"error": f"发送过程失败: {e}"}
        
        return {
            "total": count,
            "success": success_count, 
            "failed": failed_count,
            "success_rate": success_count / count if count > 0 else 0
        }

def send_regs_file_direct(self, file_path: str, progress_callback=None) -> dict:
    """改进的直发模式，修正协议格式"""
    count = 0
    success_count = 0
    failed_count = 0
    
    # 首先统计总行数
    total_regs = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:  # 改用UTF-8编码
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [x.strip() for x in line.split(",")]
                if len(parts) == 2 and parts[0].startswith("0x"):
                    total_regs += 1
    except Exception as e:
        return {"error": f"文件读取失败: {e}"}
    
    print(f"📋 检测到 {total_regs} 个寄存器配置")
    print(f"🚀 开始发送时钟配置命令...")
    
    # 发送寄存器配置
    start_time = time.time()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                    
                parts = [x.strip() for x in line.split(",")]
                if len(parts) != 2 or not parts[0].startswith("0x"):
                    print(f"⚠️  第{line_no}行格式错误，跳过: {line}")
                    continue
                
                count += 1
                
                # 调用进度回调
                if progress_callback:
                    progress_callback(count, total_regs, success_count, failed_count)
                
                # 确保数据部分有0x前缀
                addr_part = parts[0].strip()
                data_part = parts[1].strip()
                if not data_part.startswith("0x"):
                    data_part = "0x" + data_part
                
                # 发送寄存器配置
                try:
                    cmd = build_clk_cfg_command(addr_part, data_part)
                    if self.serial.send_text(cmd + "\n"):
                        success_count += 1
                        if count % 20 == 0:  # 每20个显示一次进度
                            print(f"✓ [{count}/{total_regs}] {addr_part} = {data_part}")
                    else:
                        failed_count += 1
                        print(f"❌ [{count}/{total_regs}] 发送失败: {addr_part} = {data_part}")
                        
                except Exception as e:
                    failed_count += 1
                    print(f"❌ [{count}/{total_regs}] 异常: {addr_part} = {data_part}, {e}")
                
                # 特殊延迟处理（按TCL代码）
                if addr_part == "0x0540" and data_part == "0x01":
                    print("⏸️  检测到0x0540=0x01，等待300ms...")
                    time.sleep(0.3)
                else:
                    time.sleep(0.05)  # 增加到50ms
                    
    except Exception as e:
        return {"error": f"发送过程失败: {e}"}
    
    elapsed_time = time.time() - start_time
    speed = count / elapsed_time if elapsed_time > 0 else 0
    
    print(f"📊 发送完成统计:")
    print(f"  总耗时: {elapsed_time:.2f}秒")
    
    return {
        "total": count,
        "success": success_count, 
        "failed": failed_count,
        "success_rate": success_count / count if count > 0 else 0,
        "elapsed_time": elapsed_time,
        "speed": speed
    }

class ReliableClockClient:
    """真正可靠的时钟客户端（GUI使用）"""
    def __init__(self, serial_core):
        self.serial = serial_core
        self._response_queue = queue.Queue()
        self._raw_buffer = ""  # 添加原始数据缓冲区
        self._ack_patterns = [
            r'MC1P recv clk reg set reg ([0-9a-f]+) value ([0-9a-f]+)',
            r'CLKCFG.*reg\s+([0-9a-f]{4}).*value\s+([0-9a-f]+)',
            r'reg.*set.*reg\s+([0-9a-f]{4}).*value\s+([0-9a-f]+)',
        ]
        self._setup_response_handler()

    def _setup_response_handler(self):
        """设置响应处理器"""
        self.serial.add_event_handler(self)

    def on_data_received(self, data_dict):
        """接收串口数据并放入队列 - 改进版本"""
        if 'ascii' in data_dict:
            # 将数据添加到原始缓冲区
            self._raw_buffer += data_dict['ascii']
            
            # 按行分割并处理完整行
            lines = self._raw_buffer.split('\n')
            # 保留最后一个可能不完整的行
            self._raw_buffer = lines[-1]
            
            # 处理完整的行
            for line in lines[:-1]:
                line = line.strip()
                if line:
                    self._response_queue.put(line)

    def on_data_sent(self, data: bytes):
        pass

    def on_connection_changed(self, connected: bool, port: str = None):
        pass

    def on_error(self, error: str):
        pass

    def is_connected(self) -> bool:
        """检查串口连接状态"""
        return self.serial.is_connected

    def send_reg_direct(self, reg_offset: str, reg_value: str) -> bool:
        """直发模式：发送单个寄存器配置（修正版）"""
        try:
            cmd = build_clk_cfg_command(reg_offset, reg_value)
            return self.send_command_to_serial(cmd)
        except Exception as e:
            print(f"❌ 构造命令失败: {reg_offset} = {reg_value}, 错误: {e}")
            return False

    def send_reg_with_guaranteed_ack(self, reg_offset: str, reg_value: str, timeout: float = 5.0, max_retries: int = 3) -> dict:
        """
        发送寄存器并确保收到设备确认
        返回详细的结果信息
        """
        result = {
            "success": False,
            "attempts": 0,
            "ack_received": False,
            "actual_response": "",
            "parsed_reg": "",
            "parsed_value": "",
            "error": None
        }
        
        expected_reg = reg_offset.lower().replace("0x", "").zfill(4)  # 确保4位格式
        expected_val = reg_value.lower().replace("0x", "").zfill(2)   # 确保2位格式
        
        for attempt in range(max_retries):
            result["attempts"] = attempt + 1
            
            # 清空响应队列中的旧数据
            old_responses = []
            while not self._response_queue.empty():
                try:
                    old_responses.append(self._response_queue.get_nowait())
                except queue.Empty:
                    break
            
            # 清空原始缓冲区
            self._raw_buffer = ""
            
            # 发送命令
            cmd = build_clk_cfg_command(reg_offset, reg_value)
            self.serial.send_text(cmd + "\n")
            
            # 等待确认
            start = time.time()
            responses_collected = []
            
            while time.time() - start < timeout:
                try:
                    line = self._response_queue.get(timeout=0.1)
                    responses_collected.append(line)
                    result["actual_response"] = line  # 保存最后一个响应
                    
                    # 检查是否是我们期待的确认
                    line_lower = line.lower()
                    
                    # 主要模式：MC1P recv clk reg set reg xxxx value xx
                    main_match = re.search(r'MC1P recv clk reg set reg ([0-9a-f]+) value ([0-9a-f]+)', line_lower)
                    if main_match:
                        recv_reg = main_match.group(1).zfill(4)
                        recv_val = main_match.group(2).zfill(2)
                        
                        result["parsed_reg"] = recv_reg
                        result["parsed_value"] = recv_val
                        
                        if recv_reg == expected_reg and recv_val == expected_val:
                            result["success"] = True
                            result["ack_received"] = True
                            return result
                    
                    # 备用模式：检查其他可能的确认格式
                    for pattern in self._ack_patterns[1:]:
                        match = re.search(pattern, line_lower)
                        if match and len(match.groups()) >= 2:
                            recv_reg = match.group(1).zfill(4)
                            recv_val = match.group(2).zfill(2)
                            
                            result["parsed_reg"] = recv_reg
                            result["parsed_value"] = recv_val
                            
                            if recv_reg == expected_reg and recv_val == expected_val:
                                result["success"] = True
                                result["ack_received"] = True
                                return result
                    
                    # 检查错误响应
                    if any(err in line_lower for err in ["error", "fail", "nack", "invalid"]):
                        result["error"] = f"Device error: {line}"
                        break
                        
                except queue.Empty:
                    continue
            
            # 如果没有找到匹配，记录所有收集到的响应
            if not result["success"] and responses_collected:
                result["actual_response"] = " | ".join(responses_collected)
            
            # 本次尝试失败，等待一下再重试
            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))  # 递增延迟
        
        if not result["success"]:
            result["error"] = result["error"] or f"No valid ACK received after {max_retries} attempts. Expected: reg={expected_reg}, value={expected_val}"
        
        return result

# =============================================================================
# 新增的命令行功能类
# =============================================================================

class CommandLineClock:
    """
    命令行时钟配置客户端
    通过现有的异步监听服务发送命令
    """
    
    def __init__(self):
        self._sent_count = 0
    
    def _get_serial_interface(self):
        """
        尝试获取串口接口
        """
        try:
            # 尝试从cli_moni模块获取串口接口
            import CLI.cli_moni as moni
            
            # 检查是否有全局的串口监听器实例
            if hasattr(moni, 'serial_monitor') and moni.serial_monitor:
                if hasattr(moni.serial_monitor, 'send_text'):
                    return moni.serial_monitor
            
            # 检查其他可能的属性
            for attr_name in ['_serial_core', '_monitor', 'monitor_instance']:
                if hasattr(moni, attr_name):
                    attr = getattr(moni, attr_name)
                    if attr and hasattr(attr, 'send_text'):
                        return attr
            
            return None
            
        except Exception as e:
            print(f"获取串口接口失败: {e}")
            return None
    
    def send_command_to_serial(self, command: str) -> bool:
        """发送命令到串口"""
        try:
            serial_interface = self._get_serial_interface()
            
            if not serial_interface:
                print(f"⚠️  无法获取串口接口，命令: {command}")
                print("💡 提示：请在串口监视器中手动发送此命令")
                return True  # 返回True以继续处理
            
            # 发送命令
            result = serial_interface.send_text(command + "\n")
            if result:
                self._sent_count += 1
                print(f"✅ 已发送: {command}")
            else:
                print(f"❌ 发送失败: {command}")
            return result
                
        except Exception as e:
            print(f"❌ 发送命令失败: {command}, 错误: {e}")
            return False
    
    def send_reg_direct(self, reg_offset: str, reg_value: str) -> bool:
        """直发模式：发送单个寄存器配置"""
        try:
            cmd = build_clk_cfg_command(reg_offset, reg_value)
            return self.send_command_to_serial(cmd)
        except Exception as e:
            print(f"❌ 构造命令失败: {reg_offset} = {reg_value}, 错误: {e}")
            return False
    
    def send_regs_file_direct(self, file_path: str, progress_callback=None) -> dict:
        """直发模式：逐行读取寄存器文件并发送"""
        count = 0
        success_count = 0
        failed_count = 0
        
        # 首先统计总行数
        total_regs = 0
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = [x.strip() for x in line.split(",")]
                    if len(parts) == 2 and parts[0].startswith("0x"):
                        total_regs += 1
        except Exception as e:
            return {"error": f"文件读取失败: {e}"}
        
        print(f"📋 检测到 {total_regs} 个寄存器配置")
        print(f"🚀 开始发送时钟配置命令...")
        
        # 发送寄存器配置
        start_time = time.time()
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                        
                    parts = [x.strip() for x in line.split(",")]
                    if len(parts) != 2 or not parts[0].startswith("0x"):
                        continue
                    
                    count += 1
                    
                    # 调用进度回调
                    if progress_callback:
                        progress_callback(count, total_regs, success_count, failed_count)
                    
                    # 确保数据部分有0x前缀
                    addr_part = parts[0].strip()
                    data_part = parts[1].strip()
                    if not data_part.startswith("0x"):
                        data_part = "0x" + data_part
                    
                    # 发送寄存器配置
                    try:
                        if self.send_reg_direct(addr_part, data_part):
                            success_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        failed_count += 1
                        print(f"❌ 发送异常: {addr_part} = {data_part}, {e}")
                    
                    # 短暂延迟，避免发送过快
                    time.sleep(0.01)
                    
        except Exception as e:
            return {"error": f"发送过程失败: {e}"}
        
        elapsed_time = time.time() - start_time
        speed = count / elapsed_time if elapsed_time > 0 else 0
        
        print(f"📊 发送完成 - 耗时: {elapsed_time:.2f}秒, 速度: {speed:.1f} reg/s")
        
        return {
            "total": count,
            "success": success_count, 
            "failed": failed_count,
            "success_rate": success_count / count if count > 0 else 0,
            "elapsed_time": elapsed_time,
            "speed": speed
        }
    
    def set_clock(self, table_idx: int) -> bool:
        """发送时钟 Table 配置命令"""
        try:
            cmd = build_clk_set_command(table_idx)
            return self.send_command_to_serial(cmd)
        except Exception as e:
            print(f"❌ 构造时钟表命令失败: {e}")
            return False
    
    def get_sent_count(self):
        """获取已发送命令数量"""
        return self._sent_count

# 全局命令行时钟客户端实例
_cmdline_clock = CommandLineClock()

def _get_cmdline_clock():
    """获取命令行时钟客户端实例"""
    return _cmdline_clock

# =============================================================================
# 命令行接口函数
# =============================================================================

def run_clock_cli(args_list):
    """时钟配置命令行接口"""
    from CLI.cli_moni import is_monitoring
    
    if not args_list:
        print_clock_help()
        return
    
    # 检查串口监听状态
    if not is_monitoring():
        print("❌ 串口监听未启动，请先执行: start_monitor <port> <baudrate>")
        return
    
    command = args_list[0].lower()
    
    try:
        if command == "status":
            _handle_clock_status(args_list[1:])
        elif command == "set":
            _handle_clock_set(args_list[1:])
        elif command == "table":
            _handle_clock_table(args_list[1:])
        elif command == "test":
            _handle_clock_test(args_list[1:])
        elif command == "help":
            print_clock_help()
        else:
            print(f"❌ 未知的时钟命令: {command}")
            print("使用 'clock help' 查看帮助")
    except Exception as e:
        print(f"❌ 执行时钟命令失败: {e}")

def _handle_clock_status(args):
    """处理时钟状态查询"""
    from CLI.cli_moni import get_monitor_status
    
    monitor_status = get_monitor_status()
    cmdline_clock = _get_cmdline_clock()
    
    print("📊 时钟配置状态:")
    print(f"  串口监听: ✓ 运行中")
    print(f"  连接端口: {monitor_status['port']}@{monitor_status['baudrate']}")
    print(f"  缓存数据: {monitor_status['cached_count']}/1000 条")
    print(f"  已发送命令: {cmdline_clock.get_sent_count()} 条")
    print(f"  时钟模块: Si5344配置就绪")

def _handle_clock_set(args):
    """处理时钟寄存器文件配置"""
    parser = argparse.ArgumentParser(prog="clock set", add_help=False)
    parser.add_argument("-f", "--file", required=True, help="时钟配置文件路径")
    parser.add_argument("-m", "--mode", choices=["direct"], default="direct", 
                       help="发送模式: direct(直发)")
    
    try:
        parsed_args = parser.parse_args(args)
        
        file_path = parsed_args.file
        mode = parsed_args.mode
        
        if not os.path.isfile(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return
        
        cmdline_clock = _get_cmdline_clock()
        
        print(f"🔒 开始时钟配置 - 文件: {os.path.basename(file_path)} | 模式: {mode}")
        
        def progress_callback(current, total, success, failed):
            if current % 50 == 0 or current == total:  # 每50个或最后显示进度
                rate = success / current * 100 if current > 0 else 0
                print(f"📊 进度: {current}/{total} | 成功: {success} | 失败: {failed} | 成功率: {rate:.1f}%")
        
        # 使用直发模式
        result = cmdline_clock.send_regs_file_direct(file_path, progress_callback)
        
        if "error" in result:
            print(f"❌ 配置失败: {result['error']}")
        else:
            success_rate = result['success_rate'] * 100
            print(f"\n✅ 时钟配置完成:")
            print(f"  总寄存器: {result['total']}")
            print(f"  成功发送: {result['success']}")
            print(f"  失败: {result['failed']}")
            print(f"  成功率: {success_rate:.1f}%")
            print(f"  发送速度: {result.get('speed', 0):.1f} reg/s")
            print(f"  总耗时: {result.get('elapsed_time', 0):.2f} 秒")
            
            if result['failed'] == 0:
                print("🎉 所有寄存器配置命令发送成功！")
                print("💡 设备应该已经接收到配置，请检查时钟输出")
            elif success_rate >= 95:
                print("⚠️ 大部分寄存器配置成功发送")
            else:
                print("⚠️ 发送失败较多，请检查串口连接")
                
    except (SystemExit, ValueError):
        print("用法: clock set -f <file> [-m direct]")
    except Exception as e:
        print(f"❌ 配置失败: {e}")

def _handle_clock_table(args):
    """处理时钟表设置"""
    parser = argparse.ArgumentParser(prog="clock table", add_help=False)
    parser.add_argument("-i", "--index", type=int, required=True, 
                       help="时钟表索引 (0-10)")
    
    try:
        parsed_args = parser.parse_args(args)
        
        table_idx = parsed_args.index
        
        if not (0 <= table_idx <= 10):
            print("❌ 时钟表索引必须在 0-10 之间")
            return
        
        cmdline_clock = _get_cmdline_clock()
        
        print(f"🔧 设置时钟表索引: {table_idx}")
        success = cmdline_clock.set_clock(table_idx)
        
        if success:
            print(f"✅ 时钟表设置命令已发送: {table_idx}")
        else:
            print(f"❌ 时钟表设置失败: {table_idx}")
                
    except (SystemExit, ValueError):
        print("用法: clock table -i <index>")
    except Exception as e:
        print(f"❌ 设置失败: {e}")

def _handle_clock_test(args):
    """处理时钟功能测试"""
    print("🧪 开始时钟功能测试")
    
    cmdline_clock = _get_cmdline_clock()
    
    # 测试: 发送测试寄存器
    print("\n📝 测试: 寄存器发送")
    try:
        test_reg = "0x0001"
        test_val = "0x00"
        success = cmdline_clock.send_reg_direct(test_reg, test_val)
        if success:
            print(f"✅ 寄存器发送成功: {test_reg} = {test_val}")
        else:
            print(f"❌ 寄存器发送失败: {test_reg} = {test_val}")
    except Exception as e:
        print(f"❌ 寄存器测试失败: {e}")
    
    # 测试: 时钟表设置
    print("\n📝 测试: 时钟表设置")
    try:
        success = cmdline_clock.set_clock(0)
        if success:
            print("✅ 时钟表设置成功")
        else:
            print("❌ 时钟表设置失败")
    except Exception as e:
        print(f"❌ 时钟表测试失败: {e}")
    
    print(f"\n📊 测试统计: 已发送命令 {cmdline_clock.get_sent_count()} 条")
    print("✅ 时钟功能测试完成")

def print_clock_help():
    """显示时钟功能帮助信息"""
    help_text = """
🔒 Si5344时钟配置功能帮助

📋 基本命令:
  clock status                     显示时钟配置状态
  clock set -f <file>              配置时钟寄存器文件 (直发模式)
  clock test                       测试时钟功能
  clock help                       显示此帮助信息

📁 文件格式:
  时钟配置文件应包含格式如下的行:
  0x1234,0x56
  0x1235,56
  # 注释行会被跳过

🔧 发送模式:
  direct  : 直发模式，快速发送不等待确认

⚠️  使用前提:
  必须先启动串口监听: start_monitor <port> <baudrate>

💡 使用示例:
  start_monitor COM4 115200        # 先启动串口监听
  clock status                     # 查看状态
  clock set -f si5344_config.txt   # 配置寄存器文件
  clock table -i 5                 # 设置时钟表索引5
  clock test                       # 测试功能

🎯 实际应用:
  clk_set -f config.txt            # 快速配置命令
  clk_table -i 3                  # 快速表切换
  clk_status                       # 快速状态查看
"""
    print(help_text)

# =============================================================================
# 对外接口函数（供main_shell调用）
# =============================================================================

def clk_set_regs_file(file_path: str, mode: str = "direct") -> dict:
    """快速配置时钟寄存器文件 (供其他脚本调用)"""
    from CLI.cli_moni import is_monitoring
    
    if not is_monitoring():
        return {"error": "串口监听未启动"}
    
    if not os.path.isfile(file_path):
        return {"error": f"文件不存在: {file_path}"}
    
    cmdline_clock = _get_cmdline_clock()
    
    try:
        result = cmdline_clock.send_regs_file_direct(file_path)
        return result
    except Exception as e:
        return {"error": str(e)}

def clk_get_status() -> dict:
    """获取时钟配置状态 (供其他脚本调用)"""
    from CLI.cli_moni import is_monitoring, get_monitor_status
    
    result = {
        "available": False,
        "monitor_running": False,
        "error": None,
        "details": {}
    }
    
    try:
        result["monitor_running"] = is_monitoring()
        
        if result["monitor_running"]:
            monitor_status = get_monitor_status()
            result["details"]["monitor"] = monitor_status
            result["available"] = True
        else:
            result["error"] = "串口监听未启动"
            
    except Exception as e:
        result["error"] = str(e)
    
    return result

def clk_test() -> bool:
    """测试时钟功能 (供其他脚本调用)"""
    try:
        from CLI.cli_moni import is_monitoring
        
        if not is_monitoring():
            return False
            
        cmdline_clock = _get_cmdline_clock()
        
        # 简单测试: 发送一个寄存器
        success = cmdline_clock.send_reg_direct("0x0001", "0x00")
        return success
    except Exception:
        return False

def is_clock_available() -> bool:
    """检查时钟功能是否可用 (供其他脚本调用)"""
    from CLI.cli_moni import is_monitoring
    return is_monitoring()

def get_cmdline_clock_sender():
    """获取命令行时钟发送器 (供main_shell调用)"""
    return _get_cmdline_clock()

def send_reg_with_proper_protocol(self, reg_offset: str, reg_value: str) -> bool:
    """按照TCL版本的协议发送寄存器配置"""
    try:
        # 构建命令
        payload = f"{reg_offset} {reg_value}"
        temp_command = f"MC1PCLKCFG 0000 {payload}"
        length = f"{len(temp_command):04X}"
        final_command = f"MC1PCLKCFG {length} {payload}"
        
        print(f"发送: {final_command}")
        
        # 发送命令
        success = self.serial.send_text(final_command + "\n")
        if success:
            # 短暂等待确保发送完成
            time.sleep(0.05)
        
        return success
        
    except Exception as e:
        print(f"❌ 发送失败: {reg_offset} = {reg_value}, 错误: {e}")
        return False