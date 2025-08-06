import logging
from CORE.SERIAL.serial_core import GLOBAL_SERIAL_CORE
from CORE.SERIAL.serial_handler_factory import create_handler
from CORE.SERIAL.serial_packet_parser import AckType
import CORE.SERIAL.serial_command_builder as serial_cmd_builder
import time

from CORE.SERIAL.serial_voltage import (
    validate_and_align,
    split_cli_voltage_args,
    get_voltage,
    set_voltage,
)



def run_serial_cli(args):
    # 配置串口参数
    GLOBAL_SERIAL_CORE.config.port = args.port
    GLOBAL_SERIAL_CORE.config.baudrate = 115200
    GLOBAL_SERIAL_CORE.config.databits = 8
    GLOBAL_SERIAL_CORE.config.stopbits = 1
    GLOBAL_SERIAL_CORE.config.parity = 'N'
 
    # 注册 CLI 事件处理器
    cli_handler = create_handler("cli", "run_serial_cli")
    GLOBAL_SERIAL_CORE.event_router.register(cli_handler)

    # 尝试连接
    if not GLOBAL_SERIAL_CORE.SERIAL_INSTANCE or not GLOBAL_SERIAL_CORE.SERIAL_INSTANCE.is_open:
        # 当连接不存在时，尝试连接
        success = GLOBAL_SERIAL_CORE.connect()
        if success:
            print(f"[INFO] 串口已连接: {GLOBAL_SERIAL_CORE.config.port}")
        else:
            print(f"[ERROR] 串口连接失败")
            return
    time.sleep(1)

    try:
        if not GLOBAL_SERIAL_CORE.is_connect:
            raise RuntimeError("串口未连接")
        # 1) Si5344 时钟配置
        if getattr(args, "clock_config_path", None):
            _send_clock_config_file(args.clock_config_path)
            return

        # 2) 读取电压
        if getattr(args, "voltage_show", False):
            _voltage_show()
            return

        # 3) 设置电压（11 路 + VCCADC + VCCREF）
        if getattr(args, "voltage_set", None):
            raw = args.voltage_set
            if len(raw) != 13:
                print("[Serial ERROR] --voltage_set 需要 13 个参数：11 路电压 + VCCADC + VCCREF")
                return
            _voltage_set(raw, 2.0)
            return

        print("[Serial WARN] 未指定操作。可用参数：--clock_config_path / --voltage_show / --voltage_set")

    except Exception as e:
        # 统一错误处理
        logging.error("run_serial_cli failed: %s", e, exc_info=True)

def _send_clock_config_file(file_path: str):
    event_router = GLOBAL_SERIAL_CORE.event_router
    try:
        with open(file_path, 'r') as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()

                # 跳过注释或空行
                if not line or line.startswith("#"):
                    continue

                if line.startswith("0x"):
                    parts = [s.strip() for s in line.split(",")]
                    if len(parts) != 2:
                        logging.warning(f"[Line {lineno}] 格式非法: {line}")
                        continue

                    # 寄存器地址、寄存器值
                    reg_addr, reg_data = parts

                    # 特殊延时
                    if reg_addr.upper() == "0x0540" and reg_data.upper() == "0x01":
                        time.sleep(0.3) # delay 300ms

                    # 构造字符串：MC1PCLKCFG 0000 0xADDR 0xVALUE
                    cmd_str = f"MC1PCLKCFG 0000 {reg_addr} {reg_data}"

                    # 计算长度（字符数）
                    real_len = len(cmd_str)
                    len_hex = f"{real_len:04X}"  # 长度为4位HEX大写
                    cmd_str = cmd_str[:11] + len_hex + cmd_str[15:]

                    # 发送前清除 ACK 状态
                    event_router.reset_ack(AckType.CLKCFG)
                    GLOBAL_SERIAL_CORE.send_text(cmd_str)
                    event_router.wait_for_ack(AckType.CLKCFG)

    except Exception as e:
        logging.error(f"发送配置文件失败: {e}")


def _voltage_show(timeout: float = 2.0):
    """
    显示电压
    """
    get_voltage(timeout)

def _voltage_set(args13, timeout=2.0):
    """
    设置电压
    """
    values, vccadc, vccref = split_cli_voltage_args(args13)
    set_voltage(values, vccadc, vccref, timeout=timeout)