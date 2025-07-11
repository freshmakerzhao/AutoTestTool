# CLI/cli_voltage.py - 基于MC1P110规格的电压控制
from CORE.serial_api import SerialCore
from CORE.voltage_api import (
    build_vol_set_command, 
    build_vol_get_command, 
    parse_vol_response
)
from typing import Union, List, Optional, Dict
import time
import argparse
import re
from datetime import datetime, timedelta

# MC1P110电压规格定义 (名称, 默认值mV, 最大值mV, 最小值mV, 步进值mV)
VOLTAGE_SPECS = [
    ("VCCO_0", 3300, 3350, 800, 10),
    ("VCCBRAM", 1000, 1100, 400, 5),
    ("VCCAUX", 1800, 2000, 800, 10),
    ("VCCINT", 1000, 1100, 400, 5),
    ("VCCO_16", 3300, 3350, 800, 10),
    ("VCCO_15", 3300, 3350, 800, 10),
    ("VCCO_14", 3300, 3350, 800, 10),
    ("VCCO_13", 3300, 3350, 800, 10),
    ("VCCO_34", 1500, 1550, 400, 5),
    ("MGTAVTT", 1200, 1320, 400, 5),
    ("MGTAVCC", 1000, 1100, 400, 5),
]

# 设备中的电压名称映射（设备返回的名称可能略有不同）
DEVICE_VOLTAGE_MAPPING = {
    "VCCO_0": "VCCO_0",
    "VCCBRAM": "VCCRAM",      # 设备中显示为VCCRAM
    "VCCAUX": "VCCAUX", 
    "VCCINT": "VCCINT",
    "VCCO_16": "VCCO_16",
    "VCCO_15": "VCCO_15", 
    "VCCO_14": "VCCO_14",
    "VCCO_13": "VCCO_13",
    "VCCO_34": "VCCO_34",
    "MGTAVTT": "MGTAVTT",
    "MGTAVCC": "MGTAVCC",
}

class VoltageDataParser:
    """电压数据解析器 - 基于MC1PCURSHW格式"""
    
    @staticmethod
    def parse_voltage_hardware_data(data_line: str) -> Dict:
        """
        解析MC1PCURSHW数据行，只关注电压值
        
        格式: MC1PCURSHW 012B VCCO_34 1501250 1932 2900 VCCO_16 3301250 0 0 ...
        其中: VCCO_34 1501250 1932 2900
             ↑      ↑       ↑    ↑
           名称   电压(μV)  电流  功耗
        
        Returns:
            Dict: 解析后的电压数据 {电压名称: 电压值(mV)}
        """
        if not data_line.startswith("MC1PCURSHW"):
            return {}
        
        # 移除MC1PCURSHW和长度字段
        parts = data_line.split()[2:]  # 跳过 "MC1PCURSHW" 和 "012B"
        
        voltage_data = {}
        i = 0
        
        # 已知的电压名称列表
        voltage_names = ["VCCO_34", "VCCO_16", "VCCO_15", "VCCO_14", "VCCO_13", 
                        "VCCO_0", "VCCADC", "MGTAVTT", "MGTAVCC", "VCCAUX", 
                        "VCCRAM", "VCCINT"]
        
        while i < len(parts):
            if parts[i] in voltage_names:
                voltage_name = parts[i]
                try:
                    # 电压名称后第一个数值是电压值(微伏)
                    if i + 1 < len(parts):
                        voltage_uv = int(parts[i + 1])  # 微伏
                        voltage_mv = voltage_uv / 1000.0  # 转换为毫伏
                        voltage_data[voltage_name] = voltage_mv
                        i += 4  # 跳过: 名称 + 电压 + 电流 + 功耗
                    else:
                        i += 1
                except (ValueError, IndexError):
                    i += 1
            else:
                i += 1
        
        return voltage_data

class VoltageController:
    """电压控制器 - 基于串口监听服务"""
    
    def __init__(self, serial_monitor):
        self.serial_monitor = serial_monitor
        self.parser = VoltageDataParser()
        # 初始化为默认值
        self._last_vals = [spec[1] for spec in VOLTAGE_SPECS]  # 使用默认值
        self._last_adc = True
        self._last_ref = True

    def is_connected(self) -> bool:
        """检查串口是否已连接"""
        if not self.serial_monitor:
            return False
        stats = self.serial_monitor.get_statistics()
        return stats.get('is_connected', False)

    def validate_voltage_value(self, index: int, value: int) -> tuple:
        """
        验证并校正电压值
        
        Args:
            index: 电压索引 (0-10)
            value: 电压值 (mV)
            
        Returns:
            tuple: (是否有效, 校正后的值, 错误信息)
        """
        if index < 0 or index >= len(VOLTAGE_SPECS):
            return False, value, f"电压索引超出范围: {index}"
        
        name, default, max_val, min_val, step = VOLTAGE_SPECS[index]
        
        # 检查范围
        if value > max_val:
            return False, value, f"{name} 电压值 {value}mV 超出最大限制 {max_val}mV"
        if value < min_val:
            return False, value, f"{name} 电压值 {value}mV 低于最小限制 {min_val}mV"
        
        # 步进校正
        corrected_value = round(value / step) * step
        
        return True, corrected_value, ""

    def set_voltage(self, volt_list: List[Union[str,int]], enable_adc: bool, enable_ref: bool) -> bool:
        """设置电压值"""
        if not self.is_connected():
            raise ConnectionError("串口未连接，请先启动串口监听")
        
        # 清洗电压值
        vals = []
        try:
            vals = [int(str(v).strip()) for v in volt_list]
        except ValueError as e:
            raise ValueError(f"电压值格式错误: {e}")
        
        if len(vals) != 11:
            raise ValueError(f"电压列表长度必须为11，实际为{len(vals)}")
        
        # 验证并校正每个电压值
        corrected_vals = []
        for i, val in enumerate(vals):
            is_valid, corrected_val, error_msg = self.validate_voltage_value(i, val)
            if not is_valid:
                raise ValueError(error_msg)
            corrected_vals.append(corrected_val)
        
        # 保存设置值
        self._last_vals = corrected_vals
        self._last_adc = enable_adc
        self._last_ref = enable_ref

        # 构建并发送命令
        cmd = build_vol_set_command(corrected_vals, enable_adc, enable_ref)
        return self.serial_monitor.send_text(cmd + '\n')

    def get_latest_voltage_from_cache(self, max_age_seconds: int = 10) -> Optional[Dict]:
        """
        从串口监听缓存中获取最新的电压数据
        
        Args:
            max_age_seconds: 数据最大年龄(秒)
            
        Returns:
            Dict: 最新的电压数据，包含设备上报的实际电压值
        """
        if not self.is_connected():
            return None
        
        try:
            from CLI.cli_moni import show_cached_data
            cached_data = show_cached_data(50)  # 获取最近50条数据
            
            cutoff_time = datetime.now() - timedelta(seconds=max_age_seconds)
            
            # 从最新的数据开始查找MC1PCURSHW
            for data in reversed(cached_data):
                if data['timestamp'] < cutoff_time:
                    break
                    
                if 'MC1PCURSHW' in data['raw_text']:
                    voltage_data = self.parser.parse_voltage_hardware_data(data['raw_text'])
                    if voltage_data:
                        # 添加元数据
                        result = {
                            'voltages': voltage_data,
                            'timestamp': data['timestamp'],
                            'raw_data': data['raw_text'],
                            'data_source': 'device_report'
                        }
                        return result
            
            return None
            
        except Exception as e:
            print(f"获取缓存数据失败: {e}")
            return None

    def query_voltage_status(self, timeout: float = 3.0) -> Optional[Dict]:
        """
        主动查询电压状态
        
        Args:
            timeout: 查询超时时间
            
        Returns:
            Dict: 查询结果
        """
        if not self.is_connected():
            return None
        
        try:
            # 发送查询命令
            cmd = build_vol_get_command(self._last_vals, self._last_adc, self._last_ref)
            self.serial_monitor.send_text(cmd + '\n')
            
            # 等待响应并从缓存中获取
            time.sleep(min(timeout, 2.0))
            
            # 从缓存中查找最新响应
            voltage_data = self.get_latest_voltage_from_cache(timeout)
            if voltage_data:
                voltage_data['data_source'] = 'query_response'
                return voltage_data
            
            return None
            
        except Exception as e:
            print(f"查询电压失败: {e}")
            return None

    def get_voltage_status(self, use_cache: bool = True, cache_max_age: int = 10, timeout: float = 3.0) -> Dict:
        """
        获取电压状态
        
        Args:
            use_cache: 是否优先使用缓存数据
            cache_max_age: 缓存数据最大年龄(秒)
            timeout: 查询超时时间
            
        Returns:
            Dict: 电压状态结果
        """
        result = {
            'success': False,
            'data_source': 'none',
            'voltages': {},
            'timestamp': None,
            'error': None
        }
        
        if use_cache:
            # 尝试从缓存获取数据
            voltage_data = self.get_latest_voltage_from_cache(cache_max_age)
            if voltage_data:
                result['success'] = True
                result['data_source'] = voltage_data['data_source']
                result['voltages'] = voltage_data['voltages']
                result['timestamp'] = voltage_data['timestamp']
                return result
        
        # 缓存中没有数据，主动查询
        try:
            voltage_data = self.query_voltage_status(timeout)
            if voltage_data:
                result['success'] = True
                result['data_source'] = voltage_data['data_source']
                result['voltages'] = voltage_data['voltages']
                result['timestamp'] = voltage_data['timestamp']
            else:
                result['error'] = "查询超时或无响应"
                
        except Exception as e:
            result['error'] = str(e)
        
        return result

def run_voltage_cli(args_list):
    """电压控制CLI主入口函数"""
    parser = argparse.ArgumentParser(
        prog="voltage", 
        description="MC1P110电压控制 CLI 工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用前提：必须先启动串口监听服务
  start_monitor COM3 115200        # 启动串口监听

电压控制功能:
  voltage status                   # 显示当前电压状态(优先缓存)
  voltage status --live            # 主动查询电压状态  
  voltage set --defaults           # 设置默认电压值
  voltage set --values 3300 1000 1800 ...  # 设置指定电压值
  voltage specs                    # 显示电压规格
  voltage test                     # 测试电压功能
  voltage interactive              # 交互式电压设置
  
电压参数说明:
  - 11路电压固定顺序: VCCO_0、VCCBRAM、VCCAUX、VCCINT、VCCO_16、VCCO_15、VCCO_14、VCCO_13、VCCO_34、MGTAVTT、MGTAVCC
  - 电压单位: mV (毫伏)
  - 步进值: 根据电压类型自动校正
  - 支持VCCADC和VCCREF使能控制
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # === 状态查看 ===
    parser_status = subparsers.add_parser("status", help="显示当前电压状态")
    parser_status.add_argument("--live", action="store_true", help="主动查询而非使用缓存")
    parser_status.add_argument("--max-age", type=int, default=10, help="缓存数据最大年龄(秒)")
    parser_status.add_argument("--format", choices=["table", "json"], default="table", help="输出格式")

    # === 设置电压 ===
    parser_set = subparsers.add_parser("set", help="设置电压值")
    parser_set.add_argument("--values", type=int, nargs=11, help="11路电压值(mV)", metavar="mV")
    parser_set.add_argument("--defaults", action="store_true", help="使用默认电压值")
    parser_set.add_argument("--vccadc", type=bool, default=True, help="VCCADC使能")
    parser_set.add_argument("--vccref", type=bool, default=True, help="VCCREF使能")
    parser_set.add_argument("--verify", action="store_true", help="设置后验证")

    # === 显示规格 ===
    subparsers.add_parser("specs", help="显示MC1P110电压规格")

    # === 测试功能 ===
    subparsers.add_parser("test", help="测试电压设置和读取")

    # === 交互模式 ===
    subparsers.add_parser("interactive", help="交互式电压设置")

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
        if args.command == "status":
            _cmd_show_status(args)
        elif args.command == "set":
            _cmd_set_voltage(args)
        elif args.command == "specs":
            _cmd_show_specs()
        elif args.command == "test":
            _cmd_test_voltage()
        elif args.command == "interactive":
            _cmd_interactive_voltage()
        else:
            parser.print_help()
    except KeyboardInterrupt:
        print("\n操作被用户取消")
    except Exception as e:
        print(f"❌ 执行命令时出错: {e}")

# =============================================================================
# 命令实现函数
# =============================================================================

def _get_voltage_controller():
    """获取电压控制器实例"""
    from CLI.cli_moni import _global_monitor
    
    if not _global_monitor.is_monitoring:
        raise ConnectionError("串口监听未运行，请先执行: start_monitor <port> <baudrate>")
    
    return VoltageController(_global_monitor.serial_core)

def _cmd_show_status(args):
    """显示电压状态命令"""
    try:
        controller = _get_voltage_controller()
        
        if args.live:
            print("📖 主动查询电压状态...")
        else:
            print(f"📖 获取电压状态(缓存最大年龄: {args.max_age}秒)...")
        
        status = controller.get_voltage_status(
            use_cache=not args.live, 
            cache_max_age=args.max_age
        )
        
        if status['success']:
            if args.format == "json":
                import json
                print(json.dumps(status, indent=2, ensure_ascii=False, default=str))
            else:
                _print_voltage_status_table(status)
        else:
            print(f"❌ 获取电压状态失败: {status.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 显示状态失败: {e}")

def _cmd_set_voltage(args):
    """设置电压值命令"""
    try:
        controller = _get_voltage_controller()
        
        # 确定电压值
        if args.defaults:
            values = [spec[1] for spec in VOLTAGE_SPECS]  # 使用默认值
            print("📝 使用默认电压值")
        elif args.values:
            values = args.values
            print(f"📝 使用指定电压值: {values}")
        else:
            print("❌ 必须指定 --values 或 --defaults")
            return
        
        print("⚡ 正在设置电压...")
        success = controller.set_voltage(values, args.vccadc, args.vccref)
        
        if success:
            print("✓ 电压设置命令已发送")
            
            if args.verify:
                print("🔍 验证设置结果...")
                time.sleep(2)  # 等待设备响应
                status = controller.get_voltage_status(use_cache=True, cache_max_age=5)
                if status['success']:
                    _print_voltage_status_table(status)
                else:
                    print(f"⚠️  验证失败: {status.get('error')}")
        else:
            print("❌ 电压设置失败")
            
    except Exception as e:
        print(f"❌ 设置电压失败: {e}")

def _cmd_show_specs():
    """显示MC1P110电压规格"""
    print("📋 MC1P110电压规格:")
    print("=" * 90)
    print(f"{'Bank名称':<12} {'默认值(mV)':<12} {'最大值(mV)':<12} {'最小值(mV)':<12} {'步进值(mV)':<12}")
    print("-" * 90)
    
    for name, default, max_val, min_val, step in VOLTAGE_SPECS:
        print(f"{name:<12} {default:<12} {max_val:<12} {min_val:<12} {step:<12}")
    
    print("-" * 90)
    print("使能控制:")
    print("  • VCCADC: 模拟电源使能控制 (1=enable, 0=disable)")
    print("  • VCCREF: 参考电源使能控制 (1=enable, 0=disable)")
    print("")
    print("说明:")
    print("  • 电压值单位为 mV (毫伏)")
    print("  • 超出范围的参数将保持原值不变")
    print("  • 非步进值将自动校正为最近的有效值")
    print("  • 11路电压顺序固定，不可调整")

def _cmd_test_voltage():
    """测试电压功能"""
    try:
        controller = _get_voltage_controller()
        print("🧪 开始MC1P110电压功能测试")
        
        # 测试1: 读取当前状态
        print("\n📖 测试1: 读取当前电压状态")
        status = controller.get_voltage_status()
        if status['success']:
            print("✓ 读取成功")
            _print_voltage_status_table(status)
        else:
            print(f"❌ 读取失败: {status.get('error')}")
            return
        
        # 测试2: 设置默认电压
        print("\n📝 测试2: 设置默认电压")
        default_values = [spec[1] for spec in VOLTAGE_SPECS]
        print(f"默认值: {default_values}")
        
        success = controller.set_voltage(default_values, True, True)
        if success:
            print("✓ 设置命令已发送")
            time.sleep(2)
            
            # 验证设置结果
            status = controller.get_voltage_status(use_cache=True, cache_max_age=5)
            if status['success']:
                print("🔍 验证结果:")
                _print_voltage_status_table(status)
            else:
                print(f"⚠️  验证失败: {status.get('error')}")
        else:
            print("❌ 设置失败")
        
        print("\n✓ 电压功能测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def _cmd_interactive_voltage():
    """交互式电压设置"""
    try:
        controller = _get_voltage_controller()
        
        print("🖥️  MC1P110交互式电压控制")
        print("=" * 60)
        print("命令:")
        print("  status                 - 显示当前电压状态")
        print("  status --live          - 主动查询电压状态")
        print("  set                    - 设置11路电压值")
        print("  defaults               - 设置为默认值")
        print("  specs                  - 显示电压规格")
        print("  help                   - 显示帮助")
        print("  exit                   - 退出")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\nvoltage> ").strip()
                
                if not user_input:
                    continue
                    
                parts = user_input.split()
                cmd = parts[0].lower()
                
                if cmd == 'exit':
                    break
                elif cmd == 'status':
                    live_mode = '--live' in parts
                    status = controller.get_voltage_status(use_cache=not live_mode)
                    if status['success']:
                        _print_voltage_status_table(status)
                    else:
                        print(f"❌ 获取状态失败: {status.get('error')}")
                elif cmd == 'set':
                    _interactive_set_voltage(controller)
                elif cmd == 'defaults':
                    _interactive_set_defaults(controller)
                elif cmd == 'specs':
                    _cmd_show_specs()
                elif cmd == 'help':
                    _show_voltage_help()
                else:
                    print(f"❌ 未知命令: {cmd}")
                    print("输入 'help' 查看可用命令")
                    
            except EOFError:
                break
            except KeyboardInterrupt:
                print("\n已停止当前操作")
                
    except Exception as e:
        print(f"❌ 交互模式失败: {e}")

# =============================================================================
# 辅助函数
# =============================================================================

def _print_voltage_status_table(status: Dict):
    """打印电压状态表格"""
    voltages = status.get('voltages', {})
    
    print(f"\n📊 MC1P110电压状态 (数据来源: {status['data_source']})")
    if status.get('timestamp'):
        print(f"⏰ 数据时间: {status['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("-" * 80)
    print(f"{'Bank名称':<12} {'设定值(mV)':<12} {'实际值(mV)':<12} {'差值(mV)':<12} {'状态'}")
    print("-" * 80)
    
    # 显示各路电压
    for i, (name, default, max_val, min_val, step) in enumerate(VOLTAGE_SPECS):
        device_name = DEVICE_VOLTAGE_MAPPING.get(name, name)
        
        if device_name in voltages:
            actual_mv = voltages[device_name]
            diff_mv = actual_mv - default
            
            # 判断状态
            if actual_mv > max_val:
                status_str = "⚠️超限"
            elif actual_mv < min_val:
                status_str = "⚠️低限"
            elif abs(diff_mv) <= step:  # 在步进误差范围内
                status_str = "✓正常"
            else:
                status_str = "⚡变更"
                
            print(f"{name:<12} {default:<12} {actual_mv:<12.1f} {diff_mv:<12.1f} {status_str}")
        else:
            print(f"{name:<12} {default:<12} {'--':<12} {'--':<12} ❌无数据")
    
    # 显示使能状态
    print("-" * 80)
    if 'VCCADC' in voltages:
        adc_voltage = voltages['VCCADC']
        adc_status = "✓使能" if adc_voltage > 0 else "✗禁用"
        print(f"{'VCCADC':<12} {'--':<12} {adc_voltage:<12.1f} {'--':<12} {adc_status}")
    else:
        print(f"{'VCCADC':<12} {'--':<12} {'--':<12} {'--':<12} ❌无数据")

def _interactive_set_voltage(controller: VoltageController):
    """交互模式设置电压"""
    try:
        print("📝 设置MC1P110电压值")
        print("请按顺序输入11路电压值 (用空格分隔):")
        print("顺序: VCCO_0 VCCBRAM VCCAUX VCCINT VCCO_16 VCCO_15 VCCO_14 VCCO_13 VCCO_34 MGTAVTT MGTAVCC")
        
        # 显示当前默认值作为参考
        defaults = [spec[1] for spec in VOLTAGE_SPECS]
        print(f"默认值: {' '.join(map(str, defaults))}")
        
        values_input = input("电压值(mV)> ").strip()
        if not values_input:
            print("❌ 输入为空")
            return
        
        values = [int(x) for x in values_input.split()]
        if len(values) != 11:
            print(f"❌ 需要11个电压值，输入了{len(values)}个")
            return
        
        adc_input = input("VCCADC使能(y/n)> ").strip().lower()
        enable_adc = adc_input in ['y', 'yes', '1', 'true']
        
        ref_input = input("VCCREF使能(y/n)> ").strip().lower()
        enable_ref = ref_input in ['y', 'yes', '1', 'true']
        
        print("⚡ 正在设置电压...")
        success = controller.set_voltage(values, enable_adc, enable_ref)
        
        if success:
            print("✓ 设置成功")
            time.sleep(2)
            print("🔍 验证结果:")
            status = controller.get_voltage_status(use_cache=True, cache_max_age=5)
            if status['success']:
                _print_voltage_status_table(status)
            else:
                print(f"⚠️  验证失败: {status.get('error')}")
        else:
            print("❌ 设置失败")
            
    except ValueError as e:
        print(f"❌ 输入格式错误: {e}")
    except Exception as e:
        print(f"❌ 设置失败: {e}")

def _interactive_set_defaults(controller: VoltageController):
    """交互模式设置默认值"""
    try:
        default_values = [spec[1] for spec in VOLTAGE_SPECS]
        print(f"📝 设置默认电压值: {default_values}")
        
        success = controller.set_voltage(default_values, True, True)
        if success:
            print("✓ 设置成功")
            time.sleep(2)
            print("🔍 验证结果:")
            status = controller.get_voltage_status(use_cache=True, cache_max_age=5)
            if status['success']:
                _print_voltage_status_table(status)
            else:
                print(f"⚠️  验证失败: {status.get('error')}")
        else:
            print("❌ 设置失败")
    except Exception as e:
        print(f"❌ 设置失败: {e}")

def _show_voltage_help():
    """显示交互模式帮助"""
    print("""
交互模式命令:
  status                  - 显示当前电压状态(从缓存)
  status --live           - 主动查询电压状态
  set                     - 手动设置11路电压值
  defaults                - 设置为默认电压值
  specs                   - 显示MC1P110电压规格
  help                    - 显示此帮助信息
  exit                    - 退出交互模式
    """)

# =============================================================================
# 对外提供的接口函数 (供main_shell.py调用)
# =============================================================================

def get_voltage_status_from_monitor(use_cache: bool = True, max_age: int = 10) -> Optional[Dict]:
    """从串口监听服务获取电压状态"""
    try:
        controller = _get_voltage_controller()
        return controller.get_voltage_status(use_cache, max_age)
    except Exception:
        return None

def set_voltage_to_monitor(values: List[int], enable_adc: bool = True, enable_ref: bool = True) -> bool:
    """通过串口监听服务设置电压值"""
    try:
        controller = _get_voltage_controller()
        return controller.set_voltage(values, enable_adc, enable_ref)
    except Exception:
        return False

def get_voltage_specs() -> List[tuple]:
    """获取MC1P110电压规格信息"""
    return VOLTAGE_SPECS.copy()

def is_voltage_available() -> bool:
    """检查电压功能是否可用"""
    try:
        from CLI.cli_moni import _global_monitor
        return _global_monitor.is_monitoring
    except Exception:
        return False

def validate_voltage_values(values: List[int]) -> tuple:
    """
    验证电压值列表
    
    Returns:
        tuple: (是否全部有效, 校正后的值列表, 错误信息列表)
    """
    if len(values) != 11:
        return False, values, [f"电压列表长度必须为11，实际为{len(values)}"]
    
    corrected_values = []
    errors = []
    
    for i, val in enumerate(values):
        name, default, max_val, min_val, step = VOLTAGE_SPECS[i]
        
        # 检查范围
        if val > max_val:
            errors.append(f"{name} 电压值 {val}mV 超出最大限制 {max_val}mV")
            corrected_values.append(val)
        elif val < min_val:
            errors.append(f"{name} 电压值 {val}mV 低于最小限制 {min_val}mV")
            corrected_values.append(val)
        else:
            # 步进校正
            corrected_val = round(val / step) * step
            corrected_values.append(corrected_val)
    
    return len(errors) == 0, corrected_values, errors

class VoltageClient:
    def __init__(self, serial_core: SerialCore):
        self.serial      = serial_core
        # 初始化一套默认值，以后 GET 会带入
        self._last_vals  = [0]*11
        self._last_adc   = False
        self._last_ref   = False

    def set_voltage(self, volt_list: List[Union[str,int]], enable_adc: bool, enable_ref: bool):
        # 清洗并保存
        vals = [int(str(v).strip()) for v in volt_list]
        if len(vals) != 11:
            raise ValueError("电压列表长度必须为11")
        self._last_vals = vals
        self._last_adc  = enable_adc
        self._last_ref  = enable_ref

        cmd = build_vol_set_command(vals, enable_adc, enable_ref)
        return self.serial.send_text(cmd + '\n')

    def get_voltage(self, timeout: float = 2.0) -> dict:
        self.serial.flush_input()  # 清理可能的粘包数据
        time.sleep(0.05)           # 稍等 MCU 回应准备好    
        
        # 构造带载荷的 GET 命令
        cmd = build_vol_get_command(self._last_vals, self._last_adc, self._last_ref)
        self.serial.send_text(cmd + '\n')

        start = time.time()
        while time.time() - start < timeout:
            line = self.serial.readline(timeout=0.5)
            if not line:
                continue
            line = line.strip()
            # 只处理 VOL 返回行
            if line.startswith("MC1PVOL"):
                return parse_vol_response(line)
        raise TimeoutError("Voltage get timeout")

    def get_raw_voltage_response(self, timeout: float = 2.0) -> str:
        cmd = build_vol_get_command(self._last_vals, self._last_adc, self._last_ref)
        self.serial.send_text(cmd + '\n')
        return self.serial.readline(timeout=timeout)
# 用于测试的主函数
if __name__ == "__main__":
    import sys
    run_voltage_cli(sys.argv[1:])