import logging
from CORE.module_serial import GLOBAL_SERIAL_CORE
import time

def run_serial_cli(args):
    # 配置串口参数
    GLOBAL_SERIAL_CORE.config.port = args.port
    GLOBAL_SERIAL_CORE.config.baudrate = 115200
    GLOBAL_SERIAL_CORE.config.databits = 8
    GLOBAL_SERIAL_CORE.config.stopbits = 1
    GLOBAL_SERIAL_CORE.config.parity = 'N'
 
    # 尝试连接
    if not GLOBAL_SERIAL_CORE.SERIAL_INSTANCE or not GLOBAL_SERIAL_CORE.SERIAL_INSTANCE.is_open:
        # 当连接不存在时，尝试连接
        success = GLOBAL_SERIAL_CORE.connect()
        if success:
            print(f"[INFO] 串口已连接: {GLOBAL_SERIAL_CORE.config.port}")
        else:
            print(f"[ERROR] 串口连接失败")
            return

    # 仅连接
    if args.connect_only:
        return

    # 发送配置文件
    if args.clock_config_path:
        send_clock_config_file(args.config_file)

    # 发送数据
    if args.send_text:
        success = GLOBAL_SERIAL_CORE.send_text(args.send_text)
        time.sleep(args.wait or 1.0)
        if success:
            logging.info(f"[Serial INFO] 已发送 TEXT: {args.send_text}")
        else:
            logging.error(f"[Serial ERROR] 发送失败 TEXT: {args.send_text}")

    if args.send_hex:
        success = GLOBAL_SERIAL_CORE.send_hex(args.send_hex)
        time.sleep(args.wait or 1.0)
        if success:
            logging.info(f"[Serial INFO] 已发送 HEX: {args.send_hex}")
        else:
            logging.error(f"[Serial ERROR] 发送失败 HEX: {args.send_hex}")

def send_clock_config_file(file_path: str):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()

                # 跳过注释
                if not line or line.startswith("#"):
                    continue

                if line.startswith("0x"):
                    parts = [s.strip() for s in line.split(",")]
                    if len(parts) != 2:
                        logging.warning(f"[Line {lineno}] 格式非法: {line}")
                        continue
                    # 寄存器地址、寄存器值
                    reg_addr, reg_data = parts

                    # 检查是否需要延时
                    if reg_addr.upper() == "0x0540" and reg_data.upper() == "0x01":
                        logging.info(f"[Line {lineno}] 延时 300ms")
                        time.sleep(0.3)

                    # 构造字符串：MC1PCLKCFG 0000 0xADDR 0xVALUE
                    cmd_str = f"MC1PCLKCFG 0000 {reg_addr} {reg_data}"

                    # 计算长度（字符数），填入原 cmd_str 的 0000 位置
                    real_len = len(cmd_str)
                    len_hex = f"{real_len:04X}"  # 长度为4位HEX大写
                    cmd_str = cmd_str[:12] + len_hex + cmd_str[16:]

                    logging.info(f"[Line {lineno}] 发送命令: {cmd_str}")

                    # 发送数据（编码为 utf-8）
                    GLOBAL_SERIAL_CORE.send_text(cmd_str)

                    time.sleep(0.05)
    except Exception as e:
        logging.error(f"发送配置文件失败: {e}")