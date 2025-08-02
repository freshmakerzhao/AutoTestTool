from typing import List

def build_get_voltage():
    return "MC1PVOLGET 004A 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0 0"

def build_get_all_voltage():
    return "MC1PVOLGET 004A 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0 0"

def build_set_voltage(values: List[int], vccadc_en: bool, vccref_en: bool):
    # 将每个数值格式化为4位大写 hex（补0）
    hex_vals = [f"{val:04X}" for val in values]
    adc_bit = "1" if vccadc_en else "0"
    ref_bit = "1" if vccref_en else "0"
    return f"MC1PSETVOLT {','.join(hex_vals)},{adc_bit},{ref_bit}"

def build_read_register(addr: int):
    return f"MC1PRDREG 0000 0x{addr:04X}"

def build_write_register(addr: int, value: int):
    return f"MC1PWRREG 0000 0x{addr:04X} 0x{value:04X}"
