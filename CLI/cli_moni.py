#!/usr/bin/env python3
# CLI/cli_moni.py

import os
import sys

# 将项目根目录加入 sys.path，便于导入 CORE/serial_api.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from CORE.serial_api import (
    SerialCore,
    SerialEventHandler,
    SerialConfig,
    get_available_ports,
    test_serial_connection,
    create_serial_monitor
)

if __name__ == "__main__":
    print("串口监视器后端模块测试")
    ports = get_available_ports()
    print(f"可用串口: {len(ports)} 个")
    for p in ports:
        print(f"  {p['device']} - {p['description']}")

    if ports:
        test_port = ports[0]['device']
        res = test_serial_connection(test_port)
        print(f"连接测试结果: {res}")
