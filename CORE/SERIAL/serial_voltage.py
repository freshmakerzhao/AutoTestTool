from typing import List, Tuple, Dict
import time

from CORE.SERIAL.serial_core import GLOBAL_SERIAL_CORE
from CORE.SERIAL.serial_packet_parser import AckType
import CORE.SERIAL.serial_command_builder as serial_cmd_builder

# ------------------- 协议顺序-------------------
VOLTAGE_ORDER: List[str] = [
    "VCCO_0", "VCCBRAM", "VCCAUX", "VCCINT",
    "VCCO_16", "VCCO_15", "VCCO_14", "VCCO_13",
    "VCCO_34", "MGTAVTT", "MGTAVCC",
]

# name -> (min, max, default)
VOLTAGE_LIMITS: Dict[str, Tuple[int, int, int]] = {
    "VCCO_0":  (800, 3350, 3300),
    "VCCBRAM": (400, 1100, 800),
    "VCCAUX":  (800, 2000, 1800),
    "VCCINT":  (400, 1100, 800),
    "VCCO_16": (800, 3350, 3300),
    "VCCO_15": (800, 3350, 3300),
    "VCCO_14": (800, 3350, 3300),
    "VCCO_13": (800, 3350, 3300),
    "VCCO_34": (400, 1550, 1500),
    "MGTAVTT": (400, 1320, 1200),
    "MGTAVCC": (400, 1100, 1000),
}


def _align_step(val: int) -> int:
    """按规则对齐步进：<1600 -> 5mV，>=1600 -> 10mV"""
    if val < 1600:
        return round(val / 5) * 5
    else:
        return round(val / 10) * 10

def validate_and_align(values: List[int]) -> List[int]:
    """
    校验 11 路电压并按步进对齐。
    :param values: 与 VOLTAGE_ORDER 对应的 11 个 mV 值
    :return: 对齐后（可能被修改）的列表
    :raises ValueError: 非法长度或越界
    """
    if len(values) != len(VOLTAGE_ORDER):
        raise ValueError(f"电压数量必须为 {len(VOLTAGE_ORDER)}，实际为 {len(values)}")

    aligned = [] # 合法化后的值
    for idx, name in enumerate(VOLTAGE_ORDER):
        v = int(values[idx])
        vmin, vmax, _ = VOLTAGE_LIMITS[name]
        if v < vmin or v > vmax:
            raise ValueError(f"{name} 超出范围：{v}（允许 {vmin}~{vmax} mV）")
        aligned.append(_align_step(v))

    return aligned

def split_cli_voltage_args(args13: List[int]) -> Tuple[List[int], int, int]:
    """
    将 CLI 的 13 个参数拆成 11 路电压 + VCCADC + VCCREF
    :param args13: [11 路电压, VCCADC, VCCREF]
    """
    if len(args13) != 13:
        raise ValueError("voltage_set 需要 13 个参数：11 路电压 + VCCADC + VCCREF")
    values = list(map(int, args13[:11]))
    vccadc = int(args13[11])
    vccref = int(args13[12])
    if vccadc not in (0, 1) or vccref not in (0, 1):
        raise ValueError("VCCADC/VCCREF 必须是 0 或 1")
    return values, vccadc, vccref

# ------------------- 串口动作：GET / SET -------------------

def get_voltage(timeout: float = 2.0) -> None:
    """
    发送 VOLGET 并等待 ACK
    """
    if not GLOBAL_SERIAL_CORE.is_connect:
        raise RuntimeError("串口未连接")

    cmd = serial_cmd_builder.build_get_all_voltage()
    print("get_voltage")
    print(cmd)
    router = GLOBAL_SERIAL_CORE.event_router

    router.reset_ack(AckType.VOLGET)
    if not GLOBAL_SERIAL_CORE.send_text(cmd):
        raise RuntimeError("获取 voltage 失败")

    if not router.wait_for_ack(AckType.VOLGET, timeout=timeout):
        raise TimeoutError("等待 VOLGET 超时")

def set_voltage(
    values: List[int],
    vccadc_en: int,
    vccref_en: int,
    timeout: float = 2.0,
) -> List[int]:
    """
    设置 11 路电压 + ADC/REF 使能。
    :param values: 11 路 mV 值
    :param vccadc_en: 0/1 或 bool
    :param vccref_en: 0/1 或 bool
    :return: 返回对齐后的电压列表
    """
    if not GLOBAL_SERIAL_CORE.is_connect:
        raise RuntimeError("串口未连接")

    vals = validate_and_align(values)
    adc = int(bool(vccadc_en))
    ref = int(bool(vccref_en))

    cmd = serial_cmd_builder.build_set_voltage(vals, adc, ref)
    print("set_voltage")
    print(cmd)
    router = GLOBAL_SERIAL_CORE.event_router

    router.reset_ack(AckType.VOLGET)
    if not GLOBAL_SERIAL_CORE.send_text(cmd):
        raise RuntimeError("设置 voltage 失败")
    if not router.wait_for_ack(AckType.VOLGET, timeout=timeout):
        raise TimeoutError("等待 VOLSET 超时")

    return vals
