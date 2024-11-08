
import logging
import os 
import struct
import hashlib

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