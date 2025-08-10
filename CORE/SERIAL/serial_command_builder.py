from typing import List

def build_get_voltage():
    return "MC1PVOLGET 004A 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0 0"

def build_get_all_voltage():
    return "MC1PVOLGET 004A 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0 0"

def build_set_voltage(values: List[int], vccadc_en: bool, vccref_en: bool) -> str:
    """
    MC1PVOLSET <长度> <11个电压值> <ADC> <REF>
    """
    if len(values) != 11:
        raise ValueError("电压值数量必须是 11")
    
    parts = ["MC1PVOLSET", "0000"]  # 长度暂时填充0000
    parts += [f"{v:04d}" for v in values]
    parts.append("1" if vccadc_en else "0")
    parts.append("1" if vccref_en else "0")

    # 计算命令长度（单位：字符数），补充进第二项
    cmd_str = " ".join(parts)
    length = len(cmd_str)
    parts[1] = f"{length:04X}"

    return " ".join(parts)


def build_read_register(addr: int):
    return f"MC1PRDREG 0000 0x{addr:04X}"

def build_write_register(addr: int, value: int):
    return f"MC1PWRREG 0000 0x{addr:04X} 0x{value:04X}"
