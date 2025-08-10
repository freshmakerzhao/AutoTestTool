from pathlib import Path
from typing import Tuple, Optional, List
from dataclasses import dataclass

SPECIAL_MAP = {
    "00":"00", 
    "AA":"10", 
    "55":"01", 
    "FF":"11"
}

def _read_lines(path: str) -> List[str]:
    """读取文本文件，去掉行尾换行。"""
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        lines = [ln.rstrip("\r\n") for ln in f.readlines()]
    # 去掉可能的最后一行空串
    if lines and lines[-1] == "":
        lines.pop()
    return lines

def compare_dispatch(
    mask_file: str,
    readback_file: str,
    gold_file: str,
    special_value: str,
    result_path: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    统一入口
    """
    if special_value in SPECIAL_MAP:
        return compare_with_special(
            mask_file=mask_file,
            readback_file=readback_file,
            gold_file=gold_file,
            special_value=special_value,
            result_path=result_path,
        )
    else:
        return compare_functional(
            mask_file=mask_file,
            readback_file=readback_file,
            gold_file=gold_file,
        )


def compare_functional(
        mask_file: str,
        readback_file: str,
        gold_file: str
) -> Tuple[bool, str]:
    """
    mask 位为 '1' 的位置跳过比较，其余位要求 readback == gold
    """
    mask_lines = _read_lines(mask_file)
    rb_lines   = _read_lines(readback_file)
    gold_lines = _read_lines(gold_file)

    n = min(len(mask_lines), len(rb_lines), len(gold_lines))
    if not (len(mask_lines) == len(rb_lines) == len(gold_lines)):
        return False, f"行数不一致：mask={len(mask_lines)}, readback={len(rb_lines)}, gold={len(gold_lines)}"

    for idx in range(n):
        mask = mask_lines[idx]
        rb   = rb_lines[idx]
        gold = gold_lines[idx]

        if not (len(mask) == len(rb) == len(gold)):
            return False, f"第 {idx+1} 行长度不一致：mask={len(mask)}, rb={len(rb)}, gold={len(gold)}"
        if len(mask) != 32:
            return False, f"第 {idx+1} 行位宽应为 32，目前为 {len(mask)}"

        for pos, (m, r, g) in enumerate(zip(mask, rb, gold)):
            if m == '1':
                continue
            if r != g:
                return False, f"第 {idx+1} 行第 {pos} 位不匹配：rb={r}, gold={g}"
    return True, "PASS"

def compare_with_special(
        mask_file: str,
        readback_file: str,
        gold_file: str,
        special_value: str,
        result_path: Optional[str] = None
) -> Tuple[bool, str]:
    """
    2 位一组，若 mask 的该组为 '11'，则把 readback 的该组替换为 SPECIAL_VALUE 映射得到的值；
    否则保留 readback 原值。最终生成 result 内容，并和 gold 逐行比对。
    可选写入 result_path。
    返回 (ok, detail)。
    """
    mask_lines = _read_lines(mask_file)
    rb_lines   = _read_lines(readback_file)

    if not (len(mask_lines) == len(rb_lines)):
        return False, f"行数不一致：mask={len(mask_lines)}, readback={len(rb_lines)}"

    # 创建一个新文件来保存修改后的读出文件内容
    result_lines: List[str] = []
    sp = SPECIAL_MAP.get(special_value, "11")
    for idx, (mask, rb) in enumerate(zip(mask_lines, rb_lines)):
        if len(mask) != len(rb):
            return False, f"第 {idx+1} 行长度不一致：mask={len(mask)}, rb={len(rb)}"
        if len(mask) != 32:
            return False, f"第 {idx+1} 行位宽应为 32，目前为 {len(mask)}"

        out_bits = []
        for i in range(0, len(mask), 2):
            m2 = mask[i:i+2]
            r2 = rb[i:i+2]
            if m2 == "11":
                out_bits.append(sp)
            else:
                out_bits.append(r2)
        result_lines.append("".join(out_bits))

    # 写文件
    if result_path:
        p = Path(result_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8", newline="\n") as f:
            for ln in result_lines:
                f.write(ln + "\n")

    # 对比 gold
    gold_lines = _read_lines(gold_file)
    if len(result_lines) != len(gold_lines):
        return False, f"result 与 gold 行数不一致：result={len(result_lines)}, gold={len(gold_lines)}"

    for idx, (res, gold) in enumerate(zip(result_lines, gold_lines)):
        if res.strip() != gold.strip():
            return False, f"第 {idx+1} 行不匹配"
    return True, "PASS"