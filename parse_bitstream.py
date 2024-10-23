import os 
import struct
import logging
import argparse

# logging.basicConfig(level=logging.WARNING)  # 正常模式
logging.basicConfig(level=logging.DEBUG)  # 调试模式

file_path = r"E:\CodeSpace_vscode\P_筛片脚本\xilinx_pcie_2_1_rport_7x_xilinx.bit"

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

# 读取bit文件内容，返回头部信息和4字节一个元素的list
def read_bit_or_bin_file(file_path, file_type="bit"):
    # 标识位
    # TARGET_START = b'\x00\x09'
    # TARGET_A = b'\x61'
    # TARGET_B = b'\x62'
    # TARGET_C = b'\x63'
    # TARGET_D = b'\x64'
    # TARGET_E = b'\x65'

    # 存储头部信息，FF之前
    bit_head_content = b''
    # 存储码流主体内容
    bit_body_content = []

    start_index = 0
    end_index = 0
    # 打开 bit 文件
    try:
        
        with open(file_path, 'rb') as f:
            try:
                if file_type == "bit":
                    # ========== 起始数据 ============
                    bit_head_content += f.read(2) # 标识
                    bit_head_content += f.read(11) # 内容
                    start_index += 13
                    # ========== 起始数据 ============
                    
                    # ========== 标识符A ============
                    
                    bit_head_content += f.read(1) # 标识 b'\x61'
                    cur_group_length = f.read(2)
                    bit_head_content += cur_group_length  # 内容 该组字节长度
                    group_length = struct.unpack('>H', cur_group_length)[0]
                    bit_head_content += f.read(group_length) # 文件路径、Version、UserID
                    start_index += 3
                    end_index = start_index + group_length
                    logging.debug(f"\tA content: {bit_head_content[start_index:end_index].hex()}")
                    show_ascii_content(bit_head_content[start_index:end_index])
                    start_index = end_index
                    # ========== 标识符A ============
                    
                    # ========== 标识符B ============
                    bit_head_content += f.read(1) # 标识 b'\x62'
                    cur_group_length = f.read(2)
                    bit_head_content += cur_group_length  # 内容 该组字节长度
                    group_length = struct.unpack('>H', cur_group_length)[0]
                    bit_head_content += f.read(group_length) # part name
                    start_index += 3
                    end_index = start_index + group_length
                    logging.debug(f"\tB content: {bit_head_content[start_index:end_index].hex()}")
                    show_ascii_content(bit_head_content[start_index:end_index])
                    start_index = end_index
                    # ========== 标识符B ============
                    
                    # ========== 标识符C ============
                    bit_head_content += f.read(1) # 标识 b'\x63'
                    cur_group_length = f.read(2)
                    bit_head_content += cur_group_length  # 内容 该组字节长度
                    group_length = struct.unpack('>H', cur_group_length)[0]
                    bit_head_content += f.read(group_length) # 年/月/日
                    start_index += 3
                    end_index = start_index + group_length
                    logging.debug(f"\tC content: {bit_head_content[start_index:end_index].hex()}")
                    show_ascii_content(bit_head_content[start_index:end_index])
                    start_index = end_index
                    # ========== 标识符C ============

                    # ========== 标识符D ============
                    bit_head_content += f.read(1) # 标识 b'\x64'
                    cur_group_length = f.read(2)
                    bit_head_content += cur_group_length  # 内容 该组字节长度
                    group_length = struct.unpack('>H', cur_group_length)[0]
                    bit_head_content += f.read(group_length) # 时:分:秒
                    start_index += 3
                    end_index = start_index + group_length
                    logging.debug(f"\tD content: {bit_head_content[start_index:end_index].hex()}")
                    show_ascii_content(bit_head_content[start_index:end_index])
                    start_index = end_index
                    # ========== 标识符D ============

                    # ========== 标识符E ============
                    bit_head_content += f.read(1) # 标识 b'\x65'
                    bit_head_content += f.read(4) # 位流的总长度
                    start_index += 1
                    end_index = start_index + 4
                    logging.debug(f"\tE content: {bit_head_content[start_index:end_index].hex()}")
                    show_number_content(bit_head_content[start_index:end_index])
                    start_index = end_index
                    # ========== 标识符E ============
                # ========== 读取剩余内容 ============
                while True:
                    chunk = f.read(4)
                    if not chunk:
                        break  # 到达文件末尾，停止读取
                    if len(chunk) < 4:
                        # 如果最后的 chunk 不足 4 个字节，输出提示
                        logging.warning(f"Warning: Last chunk is less than 4 bytes: {chunk.hex()}")
                    bit_body_content.append(chunk)
                # ========== 读取剩余内容 ============

            except struct.error as e:
                logging.error(f"Error during data unpacking: {e}")
            except EOFError as e:
                logging.error(f"Error reading file: {e}")
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
    except IOError as e:
        logging.error(f"I/O error: {e}")
    return bit_head_content,bit_body_content

# 将4字节数据转换为32位二进制字符串
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

# 将4字节十六进制一个元素的bit list转为32位二进制一个元素的list
def hex_content_to_binary(hex_content):
    bit_body_binary_content = []
    for i, chunk in enumerate(hex_content):
        # 将4字节数据转为32位二进制字符串
        bit_body_binary_content.append(bytes_to_binary(chunk))
    return bit_body_binary_content

# 将32位二进制一个元素的list转为4字节十六进制一个元素的bit list
def rbt_content_to_hex(binary_content):
    hex_list = []
    for line in binary_content:
        binary_data = line.strip()
        cur_len = len(binary_data)
        try:
            # 使用列表推导式将每 4 位二进制转换为十六进制
            hex_list.append(''.join(binary_to_bytes(binary_data[i:i+4]) for i in range(0, cur_len, 4)))
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
    return hex_list

def write_hex_content_to_file(hex_str, file_path, length_bytes_struct = None):
    if length_bytes_struct:
        pre_header = (
            b'\x00\x09\x0F\xF0\x0F\xF0\x0F\xF0\x0F\xF0\x00\x00\x01\x61\x00\x2D'
            b'\x65\x78\x61\x6D\x70\x6C\x65\x5F\x74\x6F\x70\x3B\x55\x73\x65\x72'
            b'\x49\x44\x3D\x30\x58\x46\x46\x46\x46\x46\x46\x46\x46\x3B\x56\x65'
            b'\x72\x73\x69\x6F\x6E\x3D\x32\x30\x32\x30\x2E\x32\x00\x62\x00\x0D'
            b'\x37\x61\x31\x30\x30\x74\x66\x67\x67\x34\x38\x34\x00\x63\x00\x0B'
            b'\x32\x30\x32\x34\x2F\x30\x37\x2F\x30\x39\x00\x64\x00\x09\x31\x31'
            b'\x3A\x31\x36\x3A\x32\x31\x00\x65'
        ) + length_bytes_struct
    else:
        pre_header = None
    with open(file_path, 'wb') as file:
        if pre_header:
            file.write(pre_header)
        # 将十六进制字符串转换为字节
        bytes_to_write = bytes.fromhex(hex_str)
        file.write(bytes_to_write)

def write_binary_content_to_file(binary_content, file_path, head_content = None):
    with open(file_path, 'w') as file:
        for line in binary_content:
            file.write(line + '\n')

def process_rbt_file_header_return_start_index(origin_file_lines):
    # Xilinx ASCII Bitstream
    # Created by Bitstream 2020.2 SW Build 3064766 on Wed Nov 18 09:12:45 MST 2020
    # Design name: 	xilinx_pcie_2_1_rport_7x;UserID=0XFFFFFFFF;Version=2020.2
    # Architecture:	artix7
    # Part:        	7a100tfgg484
    # Date:        	Mon Sep 02 11:44:48 2024
    # Bits:        	30606304
    rbt_header_content = []
    for line_number, line in enumerate(origin_file_lines, start=1):
        stripped_line = line.strip()
        # 不是空行，并且仅有0、1构成
        if bool(stripped_line) and set(stripped_line).issubset({'0', '1'}):
            return line_number-1
        rbt_header_content.append(stripped_line)
    logging.error(f"Error converting rbt file")

# 读入bit文件，转成rbt
def bit_or_bin_file_to_rbt_file(bit_file_path, rbt_file_path, file_type="bit"):
    # 读取文件信息
    bit_head_content,bit_body_content = read_bit_or_bin_file(bit_file_path, file_type)
    # 转成32位二进制字符串为单位的list
    bit_body_binary_content = hex_content_to_binary(bit_body_content)
    write_binary_content_to_file(bit_body_binary_content, rbt_file_path)

# 读入rbt文件，转成bit或bin
def rbt_file_to_bit_or_bin_file(rbt_file_path, output_file_path, file_type="bin"):
    with open(rbt_file_path, "r") as f:
        rbt_content = f.readlines()
    rbt_content = [line.strip() for line in rbt_content] 
    # rbt,将rbt中头部信息记录下来,并获取起始index
    start_index = process_rbt_file_header_return_start_index(rbt_content)
    rbt_content = rbt_content[start_index:]
    body_hex_content = rbt_content_to_hex(rbt_content)
    hex_str = "".join(body_hex_content)
    if file_type == "bin":
        write_hex_content_to_file(hex_str, output_file_path)
    elif file_type == "bit":
        bit_len = len(rbt_content) * 4
        length_bytes_struct = struct.pack('>I', bit_len)
        write_hex_content_to_file(hex_str, output_file_path, length_bytes_struct)

def main():
    parser = argparse.ArgumentParser(description="Parse Bitstream")
    # 创建一个互斥组，确保用户在一次运行中只能选择其中一个选项。
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--bit2rbt',
        nargs=2,
        metavar=('INPUT_FILE_PATH', 'OUTPUT_FILE_PATH'),
        help='Convert Bitstream to RBT. Usage: --bit2rbt <input.bit> <output.rbt>'
    )

    group.add_argument(
        '--rbt2bin',
        nargs=2,
        metavar=('INPUT_FILE_PATH', 'OUTPUT_FILE_PATH'),
        help='Convert RBT to Binary. Usage: --rbt2bin <input.rbt> <output.bin>'
    )

    group.add_argument(
        '--rbt2bit',
        nargs=2,
        metavar=('INPUT_FILE_PATH', 'OUTPUT_FILE_PATH'),
        help='Convert RBT to Bitstream. Usage: --rbt2bit <input.rbt> <output.bit>'
    )

    group.add_argument(
        '--bin2rbt',
        nargs=2,
        metavar=('INPUT_FILE_PATH', 'OUTPUT_FILE_PATH'),
        help='Convert BIN to RBT. Usage: --bin2rbt <input.rbt> <output.bit>'
    )

    # 解析命令行参数
    args = parser.parse_args()
    
    # 根据子命令调用相应的函数
    if args.bit2rbt:
        INPUT_FILE_PATH, OUTPUT_FILE_PATH = args.bit2rbt
        bit_or_bin_file_to_rbt_file(INPUT_FILE_PATH, OUTPUT_FILE_PATH, "bit")
    elif args.rbt2bin:
        INPUT_FILE_PATH, OUTPUT_FILE_PATH = args.rbt2bin
        rbt_file_to_bit_or_bin_file(INPUT_FILE_PATH, OUTPUT_FILE_PATH, "bin")
    elif args.rbt2bit:
        INPUT_FILE_PATH, OUTPUT_FILE_PATH = args.rbt2bit
        rbt_file_to_bit_or_bin_file(INPUT_FILE_PATH, OUTPUT_FILE_PATH, "bit")
    elif args.bin2rbt:
        INPUT_FILE_PATH, OUTPUT_FILE_PATH = args.bin2rbt
        bit_or_bin_file_to_rbt_file(INPUT_FILE_PATH, OUTPUT_FILE_PATH, "bin")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
