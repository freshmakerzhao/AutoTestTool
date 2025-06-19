# CLI/cli_voltage.py
from CORE.serial_api import SerialCore
from CORE.voltage_api import (
    build_vol_set_command, 
    build_vol_get_command, 
    parse_vol_response
)
from typing import Union, List
import time

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