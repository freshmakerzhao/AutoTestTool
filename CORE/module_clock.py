# CORE/clock_api.py
from typing import List

def calc_length(payload: str, cmd_name: str) -> str:
    """
    按协议：长度 = len(cmd_name) + 1(空格) + len(payload) + 5(协议额外字节)
    返回 4 位大写十六进制字符串
    """
    base = len(cmd_name) + 1 + len(payload)
    total = base + 5
    return f"{total:04X}"

def build_clk_set_command(table_idx: int) -> str:
    """构造 MC1PCLKSET 命令，table_idx: 0~10"""
    if not (0 <= table_idx <= 10):
        raise ValueError("Table 索引必须在 0~10 之间")
    payload = f"{table_idx}"
    length = calc_length(payload, "MC1PCLKSET")
    return f"MC1PCLKSET {length} {payload}"

def build_clk_get_command(table_idx: int) -> str:
    """构造 MC1PCLKGET 命令，带同样的 table_idx 占位"""
    if not (0 <= table_idx <= 10):
        raise ValueError("Table 索引必须在 0~10 之间")
    payload = f"{table_idx}"
    length = calc_length(payload, "MC1PCLKGET")
    return f"MC1PCLKGET {length} {payload}"

def build_clk_cfg_command(reg_offset: str, reg_value: str) -> str:
    """构造 MC1PCLKCFG 命令，用于逐寄存器发送"""
    payload = f"{reg_offset} {reg_value}"
    length = calc_length(payload, "MC1PCLKCFG")
    return f"MC1PCLKCFG {length} {payload}"

def parse_clk_response(resp: str) -> int:
    """
    解析 MC1PCLKGET 响应，格式：MC1PCLKGET xxxx <table_idx>
    返回 <table_idx>（int）
    """
    parts = resp.strip().split()
    if len(parts) < 3 or not parts[2].isdigit():
        raise ValueError(f"Clock response format error: {resp}")
    return int(parts[2])
