# CLI/cli_clock.py
import time
import re
from CORE.serial_api import SerialCore
from CORE.clock_api import (
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