# CORE/voltage_api.py
from typing import List

def calc_length(payload: str, cmd_name: str) -> str:
    """
    根据协议：长度 = len(cmd_name) + 1空格 + len(payload) + 5额外字节
    返回 4位16进制字符串
    """
    base = len(cmd_name) + 1 + len(payload)
    total = base + 5
    return f"{total:04X}"

def build_vol_set_command(values: List[int], enable_vccadc: bool, enable_vccref: bool) -> str:
    if len(values) != 11:
        raise ValueError("电压值必须为11个（不含ADC/REF控制）")
    payload = " ".join(f"{v:04d}" for v in values)
    control = f"{int(enable_vccadc)} {int(enable_vccref)}"
    all_payload = f"{payload} {control}"
    length_str = calc_length(all_payload, "MC1PVOLSET")
    return f"MC1PVOLSET {length_str} {all_payload}"

def build_vol_get_command(values: List[int], enable_vccadc: bool, enable_vccref: bool) -> str:
    """
    构造带载荷的查询帧，与 SET 一致：11路值 + 两使能位
    """
    payload = " ".join(f"{v:04d}" for v in values)
    control = f"{int(enable_vccadc)} {int(enable_vccref)}"
    all_payload = f"{payload} {control}"
    length_str = calc_length(all_payload, "MC1PVOLGET")
    return f"MC1PVOLGET {length_str} {all_payload}"

def parse_vol_response(resp: str) -> dict:
    tokens = resp.strip().split()
    if len(tokens) < 15:
        raise ValueError("响应数据格式错误")
    voltages = [int(t) for t in tokens[2:13]]
    enable_adc = bool(int(tokens[13]))
    enable_ref = bool(int(tokens[14]))
    return {
        "VCCO_0":   voltages[0],
        "VCCBRAM":  voltages[1],
        "VCCAUX":   voltages[2],
        "VCCINT":   voltages[3],
        "VCCO_16":  voltages[4],
        "VCCO_15":  voltages[5],
        "VCCO_14":  voltages[6],
        "VCCO_13":  voltages[7],
        "VCCO_34":  voltages[8],
        "MGTAVTT":  voltages[9],
        "MGTAVCC":  voltages[10],
        "VCCADC":   enable_adc,
        "VCCREF":   enable_ref
    }
