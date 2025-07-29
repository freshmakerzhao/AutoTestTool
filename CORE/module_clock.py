# CORE/clock_api.py
from typing import List

def calc_length(payload: str, cmd_name: str) -> str:
    """
    按协议：长度 = 整个命令字符串的长度（不包括换行符）
    """
    # 构建完整命令： "MC1PCLKCFG 0000 payload"
    full_command = f"{cmd_name} 0000 {payload}"
    total_length = len(full_command)
    return f"{total_length:04X}"

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
    """构造 MC1PCLKCFG 命令，按TCL版本协议"""
    payload = f"{reg_offset} {reg_value}"
    
    # 按TCL方式：先构建完整命令，再计算长度
    temp_command = f"MC1PCLKCFG 0000 {payload}"
    length = f"{len(temp_command):04X}"
    
    # 构建最终命令
    final_command = f"MC1PCLKCFG {length} {payload}"
    return final_command

def parse_clk_response(resp: str) -> int:
    """
    解析 MC1PCLKGET 响应，格式：MC1PCLKGET xxxx <table_idx>
    返回 <table_idx>（int）
    """
    parts = resp.strip().split()
    if len(parts) < 3 or not parts[2].isdigit():
        raise ValueError(f"Clock response format error: {resp}")
    return int(parts[2])
