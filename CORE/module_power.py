# CORE/power_temp_api.py

import csv
import threading
from datetime import datetime
from collections import deque
from abc import ABC, abstractmethod

class PowerTempEventHandler(ABC):
    """电流功耗温度事件处理器抽象类"""
    @abstractmethod
    def on_power_data_received(self, data: dict) -> None: ...
    @abstractmethod
    def on_temperature_data_received(self, data: dict) -> None: ...
    @abstractmethod
    def on_config_response_received(self, data: dict) -> None: ...
    @abstractmethod
    def on_error(self, error: str) -> None: ...

class PowerTempConfig:
    """电流功耗温度监控配置类"""
    def __init__(self):
        # 12路电源监控通道
        self.power_channels = [
            "VCCO_34", "VCCO_16", "VCCO_15", "VCCO_14", "VCCO_13", "VCCO_0",
            "VCCADC", "MGTAVTT", "MGTAVCC", "VCCAUX", "VCCRAM", "VCCINT"
        ]
        
        # 通道使能状态（默认全部关闭）
        self.channel_enabled = {ch: False for ch in self.power_channels}
        
    def get_config_string(self):
        """获取配置字符串用于串口发送"""
        config_bits = []
        for channel in self.power_channels:
            config_bits.append('1' if self.channel_enabled[channel] else '0')
        return ' '.join(config_bits)
    
    def set_channel_enabled(self, channel: str, enabled: bool):
        """设置通道使能状态"""
        if channel in self.channel_enabled:
            self.channel_enabled[channel] = enabled
            return True
        return False
    
    def enable_all_channels(self):
        """使能所有通道"""
        for channel in self.power_channels:
            self.channel_enabled[channel] = True
    
    def disable_all_channels(self):
        """禁用所有通道"""
        for channel in self.power_channels:
            self.channel_enabled[channel] = False

class PowerTempDataProcessor:
    """电流功耗温度数据处理器"""
    def __init__(self, max_points=1000):
        self.max_points = max_points
        
        # 电流功耗数据存储
        self.power_channels = [
            "VCCO_34", "VCCO_16", "VCCO_15", "VCCO_14", "VCCO_13", "VCCO_0",
            "VCCADC", "MGTAVTT", "MGTAVCC", "VCCAUX", "VCCRAM", "VCCINT"
        ]
        
        # 使用deque实现固定大小的数据缓存
        self.timestamps = deque(maxlen=max_points)
        self.voltage_data = {ch: deque(maxlen=max_points) for ch in self.power_channels}
        self.current_data = {ch: deque(maxlen=max_points) for ch in self.power_channels}
        self.power_data = {ch: deque(maxlen=max_points) for ch in self.power_channels}
        
        # 温度数据存储
        self.temp_timestamps = deque(maxlen=max_points)
        self.temp_sensor_data = deque(maxlen=max_points)
        self.temp_fpga_data = deque(maxlen=max_points)
        
        # 统计信息
        self.total_power_packets = 0
        self.total_temp_packets = 0
        self.last_update_time = None
        
    def process_power_data(self, raw_line: str) -> dict:
        """处理电流功耗数据"""
        try:
            # 解析 MC1PCURSHW 格式
            # MC1PCURSHW 00D8 VCCO_16 3317500 0 0 VCCO_14 3338750 5658 18887 ...
            
            parts = raw_line.strip().split()
            if len(parts) < 3 or parts[0] != "MC1PCURSHW":
                return None
                
            timestamp = datetime.now()
            self.timestamps.append(timestamp)
            self.total_power_packets += 1
            self.last_update_time = timestamp
            
            processed_data = {
                'timestamp': timestamp,
                'frame_header': parts[0],
                'frame_length': parts[1],
                'channels': {}
            }
            
            # 解析各通道数据
            i = 2  # 跳过帧头和长度
            while i + 3 < len(parts):
                channel = parts[i]
                voltage = int(parts[i+1])  # μV
                current = int(parts[i+2])  # μA  
                power = int(parts[i+3])    # μW
                
                if channel in self.voltage_data:
                    self.voltage_data[channel].append(voltage)
                    self.current_data[channel].append(current)
                    self.power_data[channel].append(power)
                    
                    processed_data['channels'][channel] = {
                        'voltage': voltage,
                        'current': current,
                        'power': power
                    }
                
                i += 4
            
            # 确保所有通道都有数据点（未启用的通道补0）
            for channel in self.power_channels:
                if channel not in processed_data['channels']:
                    self.voltage_data[channel].append(0)
                    self.current_data[channel].append(0)
                    self.power_data[channel].append(0)
                    
                    processed_data['channels'][channel] = {
                        'voltage': 0,
                        'current': 0,
                        'power': 0
                    }
            
            return processed_data
            
        except Exception as e:
            return None
    
    def process_temperature_data(self, raw_line: str) -> dict:
        """处理温度数据"""
        try:
            # 解析 MC1PTMPGET 格式
            # MC1PTMPGET 001D 46.625 46.125
            
            parts = raw_line.strip().split()
            if len(parts) < 4 or parts[0] != "MC1PTMPGET":
                return None
                
            timestamp = datetime.now()
            self.temp_timestamps.append(timestamp)
            self.total_temp_packets += 1
            self.last_update_time = timestamp
            
            temp_sensor = float(parts[2])  # EVB传感器温度
            temp_fpga = float(parts[3])    # FPGA芯片温度
            
            self.temp_sensor_data.append(temp_sensor)
            self.temp_fpga_data.append(temp_fpga)
            
            processed_data = {
                'timestamp': timestamp,
                'frame_header': parts[0],
                'frame_length': parts[1],
                'temp_sensor': temp_sensor,
                'temp_fpga': temp_fpga
            }
            
            return processed_data
            
        except Exception as e:
            return None
    
    def get_latest_power_data(self):
        """获取最新的电流功耗数据"""
        if not self.timestamps:
            return None
            
        latest_data = {}
        for channel in self.power_channels:
            if self.voltage_data[channel]:
                latest_data[channel] = {
                    'voltage': self.voltage_data[channel][-1],
                    'current': self.current_data[channel][-1],
                    'power': self.power_data[channel][-1]
                }
        
        return {
            'timestamp': self.timestamps[-1],
            'channels': latest_data
        }
    
    def get_latest_temperature_data(self):
        """获取最新的温度数据"""
        if not self.temp_timestamps:
            return None
            
        return {
            'timestamp': self.temp_timestamps[-1],
            'temp_sensor': self.temp_sensor_data[-1],
            'temp_fpga': self.temp_fpga_data[-1]
        }
    
    def get_statistics(self):
        """获取统计信息"""
        return {
            'total_power_packets': self.total_power_packets,
            'total_temp_packets': self.total_temp_packets,
            'power_data_points': len(self.timestamps),
            'temp_data_points': len(self.temp_timestamps),
            'last_update_time': self.last_update_time,
            'memory_usage_power': len(self.timestamps),
            'memory_usage_temp': len(self.temp_timestamps)
        }
    
    def clear_all_data(self):
        """清空所有数据"""
        self.timestamps.clear()
        self.temp_timestamps.clear()
        
        for channel in self.power_channels:
            self.voltage_data[channel].clear()
            self.current_data[channel].clear()
            self.power_data[channel].clear()
            
        self.temp_sensor_data.clear()
        self.temp_fpga_data.clear()
        
        self.total_power_packets = 0
        self.total_temp_packets = 0

class PowerTempCSVExporter:
    """CSV导出管理器"""
    def __init__(self, data_processor):
        self.data_processor = data_processor
        self.csv_lock = threading.Lock()
        
    def export_current_data(self, file_path: str) -> bool:
        """导出当前所有数据到CSV"""
        try:
            with self.csv_lock:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    # 写入表头
                    fieldnames = ['timestamp']
                    
                    # 电流功耗字段
                    for channel in self.data_processor.power_channels:
                        fieldnames.extend([
                            f'{channel}_voltage_uV',
                            f'{channel}_current_uA', 
                            f'{channel}_power_uW'
                        ])
                    
                    # 温度字段
                    fieldnames.extend(['temp_sensor_C', 'temp_fpga_C'])
                    
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    # 写入数据 - 以电流功耗时间戳为主
                    power_timestamps = list(self.data_processor.timestamps)
                    temp_timestamps = list(self.data_processor.temp_timestamps)
                    
                    for i, timestamp in enumerate(power_timestamps):
                        row = {'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}
                        
                        # 电流功耗数据
                        for channel in self.data_processor.power_channels:
                            if i < len(self.data_processor.voltage_data[channel]):
                                row[f'{channel}_voltage_uV'] = self.data_processor.voltage_data[channel][i]
                                row[f'{channel}_current_uA'] = self.data_processor.current_data[channel][i]
                                row[f'{channel}_power_uW'] = self.data_processor.power_data[channel][i]
                            else:
                                row[f'{channel}_voltage_uV'] = 0
                                row[f'{channel}_current_uA'] = 0
                                row[f'{channel}_power_uW'] = 0
                        
                        # 查找最接近的温度数据
                        if temp_timestamps:
                            # 简单的时间匹配 - 找最接近的温度数据点
                            closest_temp_idx = min(range(len(temp_timestamps)), 
                                                 key=lambda x: abs((temp_timestamps[x] - timestamp).total_seconds()))
                            
                            if closest_temp_idx < len(self.data_processor.temp_sensor_data):
                                row['temp_sensor_C'] = self.data_processor.temp_sensor_data[closest_temp_idx]
                                row['temp_fpga_C'] = self.data_processor.temp_fpga_data[closest_temp_idx]
                            else:
                                row['temp_sensor_C'] = 0
                                row['temp_fpga_C'] = 0
                        else:
                            row['temp_sensor_C'] = 0
                            row['temp_fpga_C'] = 0
                        
                        writer.writerow(row)
                
                return True
                
        except Exception as e:
            return False

class PowerTempMonitor:
    """电流功耗温度监控核心类"""
    def __init__(self, serial_core=None):
        self.serial_core = serial_core
        self.config = PowerTempConfig()
        self.data_processor = PowerTempDataProcessor()
        self.csv_exporter = PowerTempCSVExporter(self.data_processor)
        self.event_handlers = []
        
        # 数据解析线程控制
        self.monitoring_enabled = True
        
    def add_event_handler(self, handler: PowerTempEventHandler):
        """添加事件处理器"""
        if handler not in self.event_handlers:
            self.event_handlers.append(handler)
    
    def remove_event_handler(self, handler: PowerTempEventHandler):
        """移除事件处理器"""
        if handler in self.event_handlers:
            self.event_handlers.remove(handler)
    
    def _notify_handlers(self, event_type: str, *args):
        """通知事件处理器"""
        for handler in self.event_handlers:
            try:
                method = getattr(handler, event_type)
                method(*args)
            except Exception as e:
                pass
    
    def send_power_config_set(self) -> bool:
        """发送电流功耗配置SET命令"""
        if not self.serial_core or not self.serial_core.is_connected:
            self._notify_handlers('on_error', "串口未连接")
            return False
        
        config_str = self.config.get_config_string()
        command = f"MC1PCURSET 0027 {config_str}"
        
        if self.serial_core.send_text(command + '\n'):
            return True
        else:
            self._notify_handlers('on_error', "发送配置SET命令失败")
            return False
    
    def send_power_config_get(self) -> bool:
        """发送电流功耗配置GET命令"""
        if not self.serial_core or not self.serial_core.is_connected:
            self._notify_handlers('on_error', "串口未连接")
            return False
        
        config_str = ' '.join(['0'] * 12)  # GET命令使用全0
        command = f"MC1PCURGET 0027 {config_str}"
        
        if self.serial_core.send_text(command + '\n'):
            return True
        else:
            self._notify_handlers('on_error', "发送配置GET命令失败")
            return False
    
    def process_received_data(self, data_line: str):
        """处理接收到的数据"""
        if not self.monitoring_enabled:
            return
        
        data_line = data_line.strip()
        if not data_line:
            return
        
        # 处理电流功耗数据
        if data_line.startswith("MC1PCURSHW"):
            processed_data = self.data_processor.process_power_data(data_line)
            if processed_data:
                self._notify_handlers('on_power_data_received', processed_data)
                
        # 处理温度数据  
        elif data_line.startswith("MC1PTMPGET"):
            processed_data = self.data_processor.process_temperature_data(data_line)
            if processed_data:
                self._notify_handlers('on_temperature_data_received', processed_data)
    
    def get_statistics(self):
        """获取监控统计信息"""
        stats = self.data_processor.get_statistics()
        stats.update({
            'monitoring_enabled': self.monitoring_enabled,
            'serial_connected': self.serial_core.is_connected if self.serial_core else False,
            'enabled_channels': [ch for ch, enabled in self.config.channel_enabled.items() if enabled]
        })
        return stats

def create_power_temp_monitor(serial_core=None) -> PowerTempMonitor:
    """创建电流功耗温度监控实例"""
    return PowerTempMonitor(serial_core)