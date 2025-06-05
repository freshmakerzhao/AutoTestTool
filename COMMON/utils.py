
import logging
import os 
import struct
import hashlib
import sys

def log_debug_with_description(value: int, format_spec: str = '', description: str = ''):
    if format_spec:
        formatted_value = f"{value:{format_spec}}"
    else:
        formatted_value = f"{value}"
    logging.debug(f"{description}: {formatted_value}")

def bytes_to_binary(byte_data):
    if len(byte_data) < 4:
        # 不足 4 个字节
        logging.warning(f"Warning: Received less than 4 bytes. Padding with zeros to right.")
        byte_data = byte_data.rjust(4, b'\x00')  # 用 0 补齐到 4 字节
    return ''.join(f'{byte:08b}' for byte in byte_data)

def binary_to_bytes(binary_str):
    try:
        # 转换为十六进制
        return f"{int(binary_str, 2):X}"
    except ValueError as e:
        logging.error(f"Error: {e}")
        return None

def show_ascii_content(content):
    print_content = ""
    for byte in content:
        try:
            # 尝试将字节转换为 ASCII 字符
            print_content += chr(byte)
        except ValueError as e:
            # 输出错误信息
            logging.error(f"Error converting byte {byte} to ASCII: {e}")
            print_content += '?'  # 使用占位符替代无法转换的字符
    logging.debug(f"\t{print_content}")

def show_number_content(content):
    try:
        # 高位在前,转换为十进制整数
        number = int.from_bytes(content, byteorder='big')
    except ValueError as e:
        # 输出错误信息
        logging.error(f"Error converting bytes to number: {e}")
    logging.debug(f"\t{str(number)}")

def get_file_type(file_path): 
    # 获取传入path文件的类型
    if file_path:
        return os.path.splitext(file_path)
    return ("","")

def parse_bin_str_to_dec(bin_str):
    # 将二进制字符串转为十进制
    return int(bin_str, 2)

def reverse_bits(data, num_bits):
    reflected = 0
    for i in range(num_bits):
        if data & (1 << i):
            reflected |= 1 << (num_bits - 1 - i)
    reflected = bin(reflected)[2:]
    while len(reflected) != num_bits:
        reflected = '0' + reflected	
    return reflected

# 二进制字符串转字节
def binary_str_to_bytes(binary_str):
    # 将32位二进制字符串转换为整数
    num = int(binary_str, 2)
    # 使用struct将整数转换为4字节的字节对象
    return struct.pack('>I', num)  # '>I'表示大端4字节无符号整数

# 整数转字节
def decimal_to_bytes(decimal_value):
    # 将十进制整数转换为 4 字节的字节序列（32 位）
    byte_value = decimal_value.to_bytes(4, byteorder='big')
    return byte_value

# 获取特征值
# 这里传入content为list， 每个元素的数据类型为 content_type
def get_feature(content:list, content_type = "int"):
    if content_type == "str":
        # 此时是二进制字符串作为一个元素
        combined_string = ''.join(content)
        # 使用 hashlib 计算特征值（SHA256）
        feature_hash = hashlib.sha256(combined_string.encode()).hexdigest()
        return feature_hash
    elif content_type == "int":
        combined_bytes = b''.join(content)
        # 使用 hashlib 计算特征值（SHA256）
        feature_hash = hashlib.sha256(combined_bytes).hexdigest()
        return feature_hash
    else:
        raise ValueError("Unsupported content_type. Use 'str' or 'int'.")
    
# 修改指定位置
def update_data_by_index(
    data_content,
    index = [0],
    data = ["0"]
):
    if len(index) != len(data):
        raise ValueError("index 和 data 长度必须一致")
    if not all(d in {"0", "1"} for d in data):
        raise ValueError("data 中只能包含字符 '0' 或 '1'")
    bits = list(data_content)
    for idx, bit_val in zip(index, data):
        if not (0 <= idx < 32):
            raise IndexError("bit 索引超出 [0, 31] 范围")
        bits[31 - idx] = bit_val
    return "".join(bits)

# 根据value转换字符串，默认32位
def int_to_bin_str(value: int, length: int = 32) -> str:
    if length <= 0:
        raise ValueError("length 必须是正整数")

    # ---------- 范围检查 ----------
    max_val = (1 << length) - 1
    if not (0 <= value <= max_val):
        raise ValueError(f"value={value} 超出 {length} 位可表示范围 0~{max_val}")
    # ---------- 转二进制并前导补零 ----------
    return format(value, f'0{length}b')

# 判断输入内容是否符合十进制或十六进制格式
def is_dec(P: str) -> bool:
    """允许空串或纯 0-9"""
    return P == "" or P.isdigit()
HEX_CHARS = set("0123456789abcdefABCDEF")
def is_hex(P: str) -> bool:
    """允许空串或 0-9a-fA-F"""
    return P == "" or all(ch in HEX_CHARS for ch in P)

def resource_path(relative_path):
    """返回资源文件在打包状态或开发状态下的绝对路径"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
        # 开发模式：获取当前文件所在目录
        # base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
