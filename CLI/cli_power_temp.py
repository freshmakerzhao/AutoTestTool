# CLI/cli_power_temp.py

import os
import sys
import time

# 将项目根目录加入 sys.path，便于导入 CORE/power_temp_api.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from CORE.power_temp_api import (
    PowerTempMonitor,
    PowerTempConfig,
    PowerTempEventHandler,
    create_power_temp_monitor
)
from CORE.serial_api import create_serial_monitor

class CLIPowerTempHandler(PowerTempEventHandler):
    """命令行电流功耗温度事件处理器"""
    
    def __init__(self):
        self.power_data_count = 0
        self.temp_data_count = 0
        
    def on_power_data_received(self, data: dict) -> None:
        """电流功耗数据接收处理"""
        self.power_data_count += 1
        print(f"\n=== 电流功耗数据 #{self.power_data_count} ===")
        print(f"时间戳: {data['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        print(f"帧头: {data['frame_header']}, 长度: {data['frame_length']}")
        
        # 只显示有效数据（非零）的通道
        active_channels = 0
        for channel, values in data['channels'].items():
            if values['voltage'] > 0 or values['current'] > 0 or values['power'] > 0:
                print(f"  {channel:10}: {values['voltage']:8} μV, {values['current']:8} μA, {values['power']:8} μW")
                active_channels += 1
        
        if active_channels == 0:
            print("  (所有通道均为0)")
        else:
            print(f"  活跃通道: {active_channels}/12")
    
    def on_temperature_data_received(self, data: dict) -> None:
        """温度数据接收处理"""
        self.temp_data_count += 1
        print(f"\n=== 温度数据 #{self.temp_data_count} ===")
        print(f"时间戳: {data['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        print(f"传感器温度: {data['temp_sensor']:6.3f} °C")
        print(f"FPGA温度:   {data['temp_fpga']:6.3f} °C")
    
    def on_config_response_received(self, data: dict) -> None:
        """配置响应处理"""
        print(f"\n=== 配置响应 ===")
        print(f"响应数据: {data}")
    
    def on_error(self, error: str) -> None:
        """错误处理"""
        print(f"\n❌ 错误: {error}")

class SerialDataHandler:
    """串口数据处理器"""
    def __init__(self, pt_monitor):
        self.pt_monitor = pt_monitor
        
    def on_data_received(self, processed_data):
        if 'ascii' in processed_data:
            self.pt_monitor.process_received_data(processed_data['ascii'])
    
    def on_data_sent(self, data): pass
    def on_connection_changed(self, connected, port=None): pass
    def on_error(self, error): pass

def print_help():
    """打印帮助信息"""
    print("""
电流功耗温度监控 CLI 工具

命令列表:
  help          - 显示此帮助信息
  status        - 显示当前状态
  list_ports    - 列出可用串口
  connect [port] [baud] - 连接串口 (默认: COM1, 115200)
  disconnect    - 断开串口连接
  
  enable [channels] - 启用指定通道 (用逗号分隔，或 'all')
  disable [channels] - 禁用指定通道 (用逗号分隔，或 'all')
  show_config   - 显示当前通道配置
  send_set      - 发送配置SET命令
  send_get      - 发送配置GET命令
  
  monitor [duration] - 开始监控 (可选时长，秒)
  stop_monitor  - 停止监控
  clear_data    - 清空数据
  stats         - 显示统计信息
  export [file] - 导出数据到CSV文件
  
  exit/quit     - 退出程序

电源通道:
  VCCO_34, VCCO_16, VCCO_15, VCCO_14, VCCO_13, VCCO_0,
  VCCADC, MGTAVTT, MGTAVCC, VCCAUX, VCCRAM, VCCINT

示例:
  enable VCCO_16,VCCO_14,VCCINT
  enable all
  connect COM3 115200
  monitor 60
""")

def main():
    """主函数"""
    print("=== 电流功耗温度监控 CLI 工具 ===")
    print("输入 'help' 查看命令帮助")
    
    # 创建串口监视器和电流功耗温度监控器
    serial_monitor = create_serial_monitor()
    power_temp_monitor = create_power_temp_monitor(serial_monitor)
    
    # 添加事件处理器
    cli_handler = CLIPowerTempHandler()
    power_temp_monitor.add_event_handler(cli_handler)
    
    serial_handler = SerialDataHandler(power_temp_monitor)
    serial_monitor.add_event_handler(serial_handler)
    
    monitoring_active = False
    
    try:
        while True:
            try:
                command = input("\n> ").strip().lower()
                parts = command.split()
                
                if not parts:
                    continue
                    
                cmd = parts[0]
                
                if cmd in ['exit', 'quit']:
                    break
                    
                elif cmd == 'help':
                    print_help()
                    
                elif cmd == 'status':
                    is_connected = serial_monitor.is_connected
                    stats = power_temp_monitor.get_statistics()
                    print(f"\n=== 状态信息 ===")
                    print(f"串口连接: {'已连接' if is_connected else '未连接'}")
                    if is_connected:
                        print(f"串口: {serial_monitor.config.port}@{serial_monitor.config.baudrate}")
                    print(f"监控状态: {'运行中' if monitoring_active else '已停止'}")
                    print(f"电流功耗包数: {stats['total_power_packets']}")
                    print(f"温度包数: {stats['total_temp_packets']}")
                    print(f"数据点数: 电流功耗={stats['power_data_points']}, 温度={stats['temp_data_points']}")
                    enabled_ch = stats['enabled_channels']
                    print(f"已启用通道: {len(enabled_ch)} ({', '.join(enabled_ch) if enabled_ch else '无'})")
                    
                elif cmd == 'list_ports':
                    ports = serial_monitor.get_available_ports()
                    print(f"\n=== 可用串口 ({len(ports)}个) ===")
                    for i, port in enumerate(ports, 1):
                        print(f"  {i}. {port['device']} - {port['description']}")
                        print(f"     制造商: {port['manufacturer']}")
                    
                elif cmd == 'connect':
                    if len(parts) >= 2:
                        serial_monitor.config.port = parts[1]
                    if len(parts) >= 3:
                        try:
                            serial_monitor.config.baudrate = int(parts[2])
                        except ValueError:
                            print("❌ 波特率格式错误")
                            continue
                    
                    if serial_monitor.connect():
                        print(f"✅ 连接成功: {serial_monitor.config.port}@{serial_monitor.config.baudrate}")
                    else:
                        print("❌ 连接失败")
                        
                elif cmd == 'disconnect':
                    serial_monitor.disconnect()
                    monitoring_active = False
                    print("✅ 串口已断开")
                    
                elif cmd == 'enable':
                    if len(parts) < 2:
                        print("❌ 请指定要启用的通道")
                        continue
                        
                    if parts[1] == 'all':
                        power_temp_monitor.config.enable_all_channels()
                        print("✅ 已启用所有通道")
                    else:
                        channels = parts[1].split(',')
                        enabled_count = 0
                        for ch in channels:
                            ch = ch.strip().upper()
                            if power_temp_monitor.config.set_channel_enabled(ch, True):
                                enabled_count += 1
                            else:
                                print(f"❌ 未知通道: {ch}")
                        print(f"✅ 已启用 {enabled_count} 个通道")
                        
                elif cmd == 'disable':
                    if len(parts) < 2:
                        print("❌ 请指定要禁用的通道")
                        continue
                        
                    if parts[1] == 'all':
                        power_temp_monitor.config.disable_all_channels()
                        print("✅ 已禁用所有通道")
                    else:
                        channels = parts[1].split(',')
                        disabled_count = 0
                        for ch in channels:
                            ch = ch.strip().upper()
                            if power_temp_monitor.config.set_channel_enabled(ch, False):
                                disabled_count += 1
                            else:
                                print(f"❌ 未知通道: {ch}")
                        print(f"✅ 已禁用 {disabled_count} 个通道")
                        
                elif cmd == 'show_config':
                    print(f"\n=== 通道配置 ===")
                    for i, channel in enumerate(power_temp_monitor.config.power_channels):
                        enabled = power_temp_monitor.config.channel_enabled[channel]
                        status = "✅" if enabled else "❌"
                        print(f"  {i+1:2}. {channel:10} {status}")
                    
                    config_str = power_temp_monitor.config.get_config_string()
                    print(f"\n配置字符串: {config_str}")
                    
                elif cmd == 'send_set':
                    if power_temp_monitor.send_power_config_set():
                        print("✅ 配置SET命令已发送")
                    else:
                        print("❌ 发送失败")
                        
                elif cmd == 'send_get':
                    if power_temp_monitor.send_power_config_get():
                        print("✅ 配置GET命令已发送")
                    else:
                        print("❌ 发送失败")
                        
                elif cmd == 'monitor':
                    if not serial_monitor.is_connected:
                        print("❌ 请先连接串口")
                        continue
                        
                    duration = None
                    if len(parts) >= 2:
                        try:
                            duration = float(parts[1])
                        except ValueError:
                            print("❌ 时长格式错误")
                            continue
                    
                    monitoring_active = True
                    power_temp_monitor.monitoring_enabled = True
                    print(f"✅ 开始监控{'(' + str(duration) + '秒)' if duration else ' (按Ctrl+C停止)'}")
                    
                    if duration:
                        start_time = time.time()
                        try:
                            while time.time() - start_time < duration:
                                time.sleep(0.1)
                        except KeyboardInterrupt:
                            pass
                        monitoring_active = False
                        power_temp_monitor.monitoring_enabled = False
                        print("\n⏹️ 监控已停止")
                    else:
                        print("提示: 输入 'stop_monitor' 停止监控")
                        
                elif cmd == 'stop_monitor':
                    monitoring_active = False
                    power_temp_monitor.monitoring_enabled = False
                    print("⏹️ 监控已停止")
                    
                elif cmd == 'clear_data':
                    power_temp_monitor.data_processor.clear_all_data()
                    cli_handler.power_data_count = 0
                    cli_handler.temp_data_count = 0
                    print("✅ 数据已清空")
                    
                elif cmd == 'stats':
                    stats = power_temp_monitor.get_statistics()
                    print(f"\n=== 详细统计 ===")
                    print(f"总电流功耗包数: {stats['total_power_packets']}")
                    print(f"总温度包数: {stats['total_temp_packets']}")
                    print(f"电流功耗数据点: {stats['power_data_points']}")
                    print(f"温度数据点: {stats['temp_data_points']}")
                    print(f"内存使用: 电流功耗={stats['memory_usage_power']}, 温度={stats['memory_usage_temp']}")
                    if stats['last_update_time']:
                        print(f"最后更新: {stats['last_update_time'].strftime('%Y-%m-%d %H:%M:%S')}")
                    
                elif cmd == 'export':
                    filename = "power_temp_export.csv"
                    if len(parts) >= 2:
                        filename = parts[1]
                        if not filename.endswith('.csv'):
                            filename += '.csv'
                    
                    if power_temp_monitor.csv_exporter.export_current_data(filename):
                        print(f"✅ 数据已导出到: {filename}")
                    else:
                        print("❌ 导出失败")
                        
                else:
                    print(f"❌ 未知命令: {cmd}")
                    print("输入 'help' 查看可用命令")
                    
            except KeyboardInterrupt:
                if monitoring_active:
                    monitoring_active = False
                    power_temp_monitor.monitoring_enabled = False
                    print("\n⏹️ 监控已中断")
                else:
                    break
            except Exception as e:
                print(f"❌ 命令执行错误: {e}")
                
    except KeyboardInterrupt:
        pass
    
    finally:
        # 清理资源
        if serial_monitor.is_connected:
            serial_monitor.disconnect()
        print("\n👋 程序已退出")

if __name__ == "__main__":
    main()