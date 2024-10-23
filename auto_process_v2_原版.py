import os
import argparse
import struct
import logging

logging.basicConfig(level=logging.WARNING)  # 正常模式
# logging.basicConfig(level=logging.DEBUG)  # 调试模式

FILE_ENDWITH = "_replace"

CRC = '00110000000000000000000000000001'
CMD_RCRC_01 = '00110000000000001000000000000001'
CMD_RCRC_02 = '00000000000000000000000000000111'
COR1 = '00110000000000011100000000000001'

CMD_MASK_01 = '00110000000000001100000000000001'
CMD_MASK_02 = '10000000000000000000000000000000'
CMD_TRIM_01 = '00110000000000110110000000000001'
CMD_TRIM_02 = '10000000000000000000000000000000'

CMD_FDRI = '00110000000000000100000000000000'
CMD_FDRI_WORD_COUNT = '01010000000011101001010111011000'

BITS_CMD = 'Bits:'

NOOP = '00100000000000000000000000000000'

RBT_HEADER_CONTENT = []
BIT_HEADER_CONTENT = []

# GTP 修改位置 ,这里放的是实际行号，在用的时候是index
GTP_LINES = {
                0:{
                    386730:[2],      
                    386752:[2],      
                    386787:[2],      
                    386809:[2]       
                }
}

# PCIE 校验位
PCIE_CHECK = {
                0:{
                    348875:[26],    
                    348976:[24,21], 
                    350997:[8],     
                    351408:[8],     
                },
                1:{
                    348877:[12],         
                    349685:[15],         
                    350998:[8],          
                    351402:[8],     
                },
                2:{
                    348978:[7],       
                    349685:[14],         
                    350998:[0],           
                    351402:[0],            
                }
}

# PCIE 修改位置
PCIE_CONFIG = {
                0:{
                    348875:[26,25], 
                    348976:[24,21], 
                    350997:[8],     
                    351401:[8],     
                    386730:[2],     
                    386752:[2],     
                    386787:[2],     
                    386809:[2]      
                },
                1:{
                    348875:[25, 22],   
                    348877:[12],    
                    349685:[15],    
                    350291:[15],    
                    350998:[8],     
                    351402:[8],      
                    386730:[2],     
                    386752:[2],     
                    386787:[2],     
                    386809:[2]      
                },
                2:{
                    348875:[25, 22],
                    348978:[7],     
                    349685:[14],    
                    350291:[15],        
                    350998:[0],      
                    351402:[0],         
                    386730:[2],         
                    386752:[2],            
                    386787:[2],         
                    386809:[2]           
                }
}

# 判断是否开启crc
def able_crc(origin_file_path):
    with open(origin_file_path, "r") as f:
        origin_lines = f.readlines()
        i = 0
        origin_lines_len = len(origin_lines)
        end_first_segment = 101
        while i < end_first_segment:
            line = origin_lines[i].strip()
            if CRC in line:
                if (i + 2) < end_first_segment and (i + 3) < end_first_segment:
                    if NOOP in origin_lines[i + 2] and NOOP in origin_lines[i + 3]:
                        return True

        end_second_segment = max(0, origin_lines_len - 600)

        # 处理后 600 行
        i = end_second_segment
        while i < origin_lines_len:
            line = origin_lines[i].strip()
            if CRC in line:
                if (i + 2) < origin_lines_len and (i + 3) < origin_lines_len:
                    if NOOP in origin_lines[i + 2] and NOOP in origin_lines[i + 3]:
                        return True
    return False

# 处理gtp
def process_gtp(origin_file_lines, configuration_lens):
    last_index = len(origin_file_lines)-1
    for group_index in GTP_LINES:
        group = GTP_LINES[group_index]
        for line_num in group:
            line_index = line_num + configuration_lens - 1
            for bit_index in group[line_num]:
                cur_line_index = line_index
                left_end_index = -bit_index-1
                right_start_index = -bit_index
                if cur_line_index > 0 and cur_line_index <= last_index:
                    origin_file_lines[cur_line_index] = origin_file_lines[cur_line_index][:left_end_index] + "1" + ( origin_file_lines[cur_line_index][right_start_index:] if right_start_index!=0 else "")

# 处理pcie
def process_pcie(origin_file_lines, configuration_lens):
    last_index = len(origin_file_lines)-1
    for group_index in PCIE_CHECK:
        # 拿到一组规则
        cur_group_have_value = False
        group = PCIE_CHECK[group_index]
        group_config_done = False
        # 逐组进行判断，当一组中的所有位置都为0时，再做修改
        for line_num in group:
            line_index = line_num + configuration_lens - 1
            for bit_index in group[line_num]:
                cur_line_index = line_index
                edit_index = -bit_index-1 # 需要修改的位置
                if edit_index+len(origin_file_lines[cur_line_index]) < 0:
                    return {"data":"", "msg":"pcie校验规则存在问题", "code": 0} # 0 失败
                if origin_file_lines[cur_line_index][edit_index] == "1":
                    # 有任意一个为1，这组就无法修改
                    cur_group_have_value = True
                    break
            if cur_group_have_value:
                # 跳出这组规则
                break
        else:
            # 都为0时，可进行修改
            group = PCIE_CONFIG[group_index]
            for line_num in group:
                line_index = line_num + configuration_lens - 1
                for bit_index in group[line_num]:
                    cur_line_index = line_index
                    left_end_index = -bit_index-1
                    right_start_index = -bit_index
                    if cur_line_index > 0 and cur_line_index <= last_index:
                        origin_file_lines[cur_line_index] = origin_file_lines[cur_line_index][:left_end_index] + "1" + ( origin_file_lines[cur_line_index][right_start_index:] if right_start_index!=0 else "")
            # 修改后，直接退出循环，不再进行后续判断
            group_config_done = True
            break
    if not group_config_done:
        # 如果没有修改成功
            return {"data":"", "msg":"无法处理", "code": 0} # 0 失败
    return {"data":"", "msg":"成功", "code": 1} # 1 成功

def process_rbt_file_header_return_start_index(origin_file_lines):
    # Xilinx ASCII Bitstream
    # Created by Bitstream 2020.2 SW Build 3064766 on Wed Nov 18 09:12:45 MST 2020
    # Design name: 	xilinx_pcie_2_1_rport_7x;UserID=0XFFFFFFFF;Version=2020.2
    # Architecture:	artix7
    # Part:        	7a100tfgg484
    # Date:        	Mon Sep 02 11:44:48 2024
    # Bits:        	30606304
    global RBT_HEADER_CONTENT
    RBT_HEADER_CONTENT = []
    for line_number, line in enumerate(origin_file_lines, start=1):
        # 不是空行，并且仅有0、1构成
        if bool(line) and set(line).issubset({'0', '1'}):
            return line_number-1
        RBT_HEADER_CONTENT.append(line)
    raise ValueError("文件格式错误")

# 获取数据帧的起始索引
def get_configuration_lens(rbt_file_lines):
    for line_number, line in enumerate(rbt_file_lines, start=0):
        if line_number > 0 and CMD_FDRI_WORD_COUNT in line and CMD_FDRI in rbt_file_lines[line_number-1]:
            return line_number+1
    raise ValueError("文件格式错误")

# 处理trim和crc
def process_trim_crc(origin_file_lines, enable_trim=False, enable_crc=False):
    # 处理后结果
    new_lines = []
    flag_COR1 = False
    flag_status = False # False is not modify / True is modify
    i = 0
    origin_lines_len = len(origin_file_lines)
    end_first_segment = 101
    while i < end_first_segment:
        line = origin_file_lines[i].strip()
        if CRC in line:
            if (i + 2) < end_first_segment and (i + 3) < end_first_segment:
                if NOOP in origin_file_lines[i + 2] and NOOP in origin_file_lines[i + 3]:
                    new_lines.extend([CMD_RCRC_01, CMD_RCRC_02])
                    i += 2
                    continue
            new_lines.append(line)
            i += 1
            continue
        
        if enable_trim and COR1 in line and (i+1) < end_first_segment:
            flag_COR1 = True
            new_lines.append(line)
            i += 1
            continue

        if flag_COR1:
            flag_COR1 = False
            if line[-13] != "1":
                flag_status = True
                new_line = line[:-13] + "1" + line[-12:]
                new_lines.extend([new_line, CMD_MASK_01, CMD_MASK_02, CMD_TRIM_01, CMD_TRIM_02])
                i += 1
            else:
                new_lines.append(line)
                i += 1
        else:
            new_lines.append(line)
            i += 1

    # 处理中间部分
    start_second_segment = min(101, origin_lines_len)
    end_second_segment = max(0, origin_lines_len - 600)
    for i in range(start_second_segment, end_second_segment):
        line = origin_file_lines[i].strip()
        new_lines.append(line)

    # 处理后 600 行
    i = end_second_segment
    while i < origin_lines_len:
        line = origin_file_lines[i].strip()
        if CRC in line:
            if (i + 2) < origin_lines_len and (i + 3) < origin_lines_len:
                if NOOP in origin_file_lines[i + 2] and NOOP in origin_file_lines[i + 3]:
                    new_lines.extend([CMD_RCRC_01, CMD_RCRC_02])
                    i += 2
                    continue
            new_lines.append(line)
            i += 1
            continue
        
        if enable_trim and COR1 in line and (i+1) < origin_lines_len:
            flag_COR1 = True
            new_lines.append(line)
            i += 1
            continue

        if flag_COR1:
            flag_COR1 = False
            if line[-13] != "1":
                flag_status = True
                new_line = line[:-13] + "1" + line[-12:]
                new_lines.extend([new_line, CMD_MASK_01, CMD_MASK_02, CMD_TRIM_01, CMD_TRIM_02])
                i += 1
            else:
                new_lines.append(line)
                i += 1
        else:
            new_lines.append(line)
            i += 1
            
    return new_lines

def find_rbt_files(root_path): 
    if not os.path.exists(root_path):
        print(f"Error: The specified path '{root_path}' does not exist.")
        return []
    # rsplit(".rbt", 1) right and only one
    rbt_files = [
        os.path.join(dirpath, filename).rsplit(".rbt", 1)[0]
        for dirpath, _, filenames in os.walk(root_path)
        for filename in filenames if filename.lower().endswith('.rbt')
    ]
    return rbt_files

def get_file_type(file_path): 
    # 获取传入path文件的类型
    if file_path:
        return os.path.splitext(file_path)
    return ("","")

def save_file(file_path, file_type, file_content):
    if file_type == ".rbt":
        global RBT_HEADER_CONTENT
        with open(file_path, 'w') as f:
            bits_flag = True
            # 计算长度
            byte_nums = len(file_content)*32
            file_content = RBT_HEADER_CONTENT+file_content
            for line in file_content:
                if bits_flag and BITS_CMD in line:
                    bits_flag = False
                    line = f"Bits:\t{byte_nums}"
                f.write(line + '\n')
        print(f"writing rbt file : {file_path}")
    elif file_type == ".bit":
        global BIT_HEADER_CONTENT
        bit_len = len(file_content) * 4
        length_bytes_struct = struct.pack('>I', bit_len)
        # 重新计算长度
        BIT_HEADER_CONTENT = BIT_HEADER_CONTENT[:-4] + length_bytes_struct
        bit_body_hex_content = rbt_content_to_hex(file_content)
        hex_str = "".join(bit_body_hex_content)
        with open(file_path, 'wb') as file:
            if BIT_HEADER_CONTENT:
                file.write(BIT_HEADER_CONTENT)
            # 将十六进制字符串转换为字节
            bytes_to_write = bytes.fromhex(hex_str)
            file.write(bytes_to_write)
        print(f"writing bit file : {file_path}")
    else:
        raise ValueError("文件格式错误")

# 读取bit文件内容，返回头部信息和4字节一个元素的list
def read_bit_file(file_path):
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
                start_index = end_index
                # ========== 标识符D ============

                # ========== 标识符E ============
                bit_head_content += f.read(1) # 标识 b'\x65'
                bit_head_content += f.read(4) # 位流的总长度
                start_index += 1
                end_index = start_index + 4
                logging.debug(f"\tE content: {bit_head_content[start_index:end_index].hex()}")
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

def main():
    parser = argparse.ArgumentParser(description="Auto Process")

    # Add optional arguments
    parser.add_argument('--rbt_folder', type=str, help="Input .rbt folder path")
    parser.add_argument('--rbt_file', type=str, help="Only process this specific rbt file")
    parser.add_argument('--bit_file', type=str, help="Only process this specific bit file")
    parser.add_argument('--file_suffix', type=str, default=FILE_ENDWITH, help="Suffix to add to the new .rbt file (default: _HybrdChip)")
    parser.add_argument('--PCIE', action='store_true', help="Enable PCIE processing (Default: False)")
    parser.add_argument('--GTP', action='store_true', help="Enable GTP processing (Default: False)")
    parser.add_argument('--TRIM', action='store_true', help="Enable TRIM processing (Default: False)")

    # 解析参数
    args = parser.parse_args()

    # Display help if no arguments are provided
    if not any(vars(args).values()):
        parser.print_help()
        return

    logging.info(f"Parameters:")
    logging.info(f"\trbt_folder: {args.rbt_folder}")
    logging.info(f"\trbt_file: {args.rbt_file}")
    logging.info(f"\tbit_file: {args.bit_file}")
    logging.info(f"\tfile_suffix: {args.file_suffix}")
    logging.info(f"\tPCIE: {args.PCIE}")
    logging.info(f"\tGTP: {args.GTP}")
    logging.info(f"\tTRIM: {args.TRIM}\n")

    if args.rbt_file:
        origin_file_path = args.rbt_file
        
        # 判断其文件类型
        file_path,file_type = get_file_type(origin_file_path)

        # 读取内容
        if file_type == ".rbt":
            with open(origin_file_path, "r") as f:
                rbt_content = f.readlines()
            rbt_content = [line.strip() for line in rbt_content] 
            # rbt,将rbt中头部信息记录下来,并获取起始index
            start_index = process_rbt_file_header_return_start_index(rbt_content)
            rbt_content = rbt_content[start_index:]
            configuration_lens = get_configuration_lens(rbt_content)
        else:
            raise ValueError("文件格式错误")
        
        # 获取新文件路径
        new_file_path = file_path + args.file_suffix + file_type
        
        if args.GTP:
            # 处理GTP
            process_gtp(rbt_content, configuration_lens)
        if args.PCIE:
            # 处理PCIE
            pcie_result = process_pcie(rbt_content, configuration_lens)
            if pcie_result["code"] == 1:
                # 成功
                pass
            else:
                # 失败
                logging.error(pcie_result["msg"])
                return
        
        # 处理trim和crc
        rbt_content = process_trim_crc(rbt_content, args.TRIM)
        save_file(new_file_path, file_type, rbt_content)
    elif args.bit_file:
        origin_file_path = args.bit_file
        
        # 判断其文件类型
        file_path,file_type = get_file_type(origin_file_path)

        # 读取内容
        if file_type == ".bit":
            global BIT_HEADER_CONTENT
            BIT_HEADER_CONTENT,bit_body_content = read_bit_file(origin_file_path)
            rbt_content = hex_content_to_binary(bit_body_content)
            rbt_content = [line.strip() for line in rbt_content] 
            configuration_lens = get_configuration_lens(rbt_content)
        else:
            raise ValueError("文件格式错误")
        
        # 获取新文件路径
        new_file_path = file_path + args.file_suffix + file_type
        
        if args.GTP:
            # 处理GTP
            process_gtp(rbt_content, configuration_lens)
        if args.PCIE:
            # 处理PCIE
            pcie_result = process_pcie(rbt_content, configuration_lens)
            if pcie_result["code"] == 1:
                # 成功
                pass
            else:
                # 失败
                logging.error(pcie_result["msg"])
                return
        
        # 处理trim和crc
        rbt_content = process_trim_crc(rbt_content, args.TRIM)
        save_file(new_file_path, file_type, rbt_content)
    elif args.rbt_folder:
        # 搜寻 args.rbt_folder 下的rbt文件路径
        rbt_files = find_rbt_files(args.rbt_folder)
        for one_path in rbt_files:
            # 取到一个文件
            one_rbt_file_path = one_path + ".rbt"
            # 判断其文件类型
            file_path,file_type = get_file_type(one_rbt_file_path)
            # 读取内容
            with open(one_rbt_file_path, "r") as f:
                rbt_content = f.readlines()
            rbt_content = [line.strip() for line in rbt_content] 
            if file_type == ".rbt":
                # rbt,将rbt中头部信息记录下来,并获取起始index
                start_index = process_rbt_file_header_return_start_index(rbt_content)
                rbt_content = rbt_content[start_index:]
                configuration_lens = get_configuration_lens(rbt_content)
            else:
                raise ValueError("文件格式错误")
        
            # 获取新文件路径
            new_file_path = file_path + args.file_suffix + file_type
            
            if args.GTP:
                # 处理GTP
                process_gtp(rbt_content, configuration_lens)
            if args.PCIE:
                # 处理PCIE
                pcie_result = process_pcie(rbt_content, configuration_lens)
                if pcie_result["code"] == 1:
                    # 成功
                    pass
                else:
                    # 失败
                    logging.error(pcie_result["msg"])
                    return
                
            # 处理trim和crc
            rbt_content = process_trim_crc(rbt_content, args.TRIM)
            save_file(new_file_path, file_type, rbt_content)
    else:
        logging.error("No input folder or file specified. Use -h or --help for usage information.")

if __name__ == "__main__":
    main()