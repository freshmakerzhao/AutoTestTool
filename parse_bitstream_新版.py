import os 
import struct
import logging
import argparse
import enum
# 配置日志级别和格式
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# logging.basicConfig(level=logging.WARNING,  format='%(asctime)s - %(levelname)s - %(message)s')
# logging.basicConfig(level=logging.INFO,  format='%(asctime)s - %(levelname)s - %(message)s')

file_path = r"E:\CodeSpace_vscode\P_筛片脚本\xilinx_pcie_2_1_rport_7x_xilinx.bit"

FILE_ENDWITH = "_replace"

DUMMY_STR = "11111111111111111111111111111111"
DUMMY_BIN = 0b11111111111111111111111111111111

SYNC_WORD_STR = "10101010100110010101010101100110"
SYNC_WORD_BIN = 0b10101010100110010101010101100110

BUS_WIDTH_AUTO_DETECT_01_STR = "00000000000000000000000010111011"
BUS_WIDTH_AUTO_DETECT_01_BIN = 0b00000000000000000000000010111011

BUS_WIDTH_AUTO_DETECT_02_STR = "00010001001000100000000001000100"
BUS_WIDTH_AUTO_DETECT_02_BIN = 0b00010001001000100000000001000100

NOOP_STR = "00100000000000000000000000000000"
NOOP_BIN = 0b00100000000000000000000000000000

FDRI_STR = "00110000000000000100000000000000"
FDRI_BIN = 0b00110000000000000100000000000000

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

# 配置包格式
class ConfigurationPacket:
    
    @enum.unique
    class Address(enum.Enum):
        UNKNOWN = -1
        CRC = 0
        FAR = 1
        FDRI = 2
        FDRO = 3
        CMD = 4
        CTL0 = 5
        MASK = 6
        STAT = 7
        LOUT = 8
        COR0 = 9
        MFWR = 10
        CBC = 11
        IDCODE = 12 
        AXSS = 13
        COR1 = 14
        UNKNOWN_15 = 15 #if write, csob_reg(ib) <= packet, csbo_cnt(ib) <= word count, csbo_flag(ib) < '1'
        WBSTAR = 16
        TIMER = 17
        UNKNOWN_18 = 18
        POST_CRC = 19 #Undocumented in UG470
        UNKNOWN_20 = 20
        UNKNOWN_21 = 21
        BOOTSTS = 22
        CTL1 = 24
        UNKNOWN_30 = 30 #if next packet is Type2 and bcout_cnt(ib) = 0, set bocut_flag(ib) <= '1' and bout_cnt(ib) <= word count
        BSPI = 31
        
    @enum.unique
    class OpCode(enum.Enum):
        UNKNOWN = -1
        NOOP = 0
        READ = 1
        WRITE = 2
        
    def get_packet_type(self, word):
        return word >> 29 

    # 根据传入word获取其type1格式的数据，content_type为int时，直接读，str时转换后再读
    def get_type_1_packet_content(self, word, content_type = "int"):
        if content_type != "int":
            word = int(word, 2)
        header_type = self.get_packet_type(word) # [31:29]
        opcode = self.OpCode((word >> 27) & 0x3) # [28:27]
        address = self.Address((word >> 13) & 0x1F) # [26:13]
        reserved = (word >> 11) & 0x3 # [12:11]
        word_count = word & 0x7FF # [10:0]
        return {
                "header_type":header_type,
                "opcode":opcode,
                "address":address,
                "reserved":reserved,
                "word_count":word_count
            }
        
    # 根据传入word获取其type2格式的数据，content_type为int时，直接读，str时转换后再读
    def get_type_2_packet_content(self, word, content_type = "int"):
        if content_type != "int":
            word = int(word, 2)
        header_type = self.get_packet_type(word) # [31:29]
        opcode = self.OpCode((word >> 27) & 0x3) # [28:27]
        word_count = word & 0x7FFFFFF # [26:0]
        return {
                "header_type":header_type,
                "opcode":opcode,
                "word_count":word_count
            }
        
    def __init__(self) -> None:
        pass
    
class BitstreamReader:
    def __init__(self, input_file_path: str):
        """
        初始化 BitstreamReader

        参数:
            input_file_path (str): 文件路径
        """
        self.input_file_path = input_file_path # 输入文件路径
        self.file_type = "" # 文件类型
        self.file_path_except_type = "" # 不带文件类型的路径，方便存储新文件
        
        # ======================= bit =====================      
        # bit文件全部内容
        self.bit_byte_content = []
        # 字节长度
        self.bit_byte_content_len = 0
        # 读取位置
        self.bit_byte_content_cur_loc = 0
        # 数据内容的字节长度
        self.bit_data_content_byte_count = 0
        # 存储头部信息，FF之前
        self.bit_head_byte_content = b''
         # 存储头部配置信息
        self.bit_cfg_content_pre = []
        # 存储码流主体内容
        self.bit_data_content = []
        # 存储后续配置信息
        self.bit_cfg_content_after = []
        # ======================= bit =====================     
        
        
        # ======================= rbt =====================      
        # rbt文件全部内容
        self.rbt_content = []
        # 存储rbt文件注释信息
        self.rbt_annotation_content = []
        # rbt内容长度
        self.rbt_content_len = 0
        # 读取位置
        self.rbt_content_cur_loc = 0
        # 存储头部信息，FF之前
        self.rbt_head_content = b''
         # 存储头部配置信息
        self.rbt_cfg_content_pre = []
        # 存储码流主体内容
        self.rbt_data_content = []
        # 存储后续配置信息
        self.rbt_cfg_content_after = []
        # ======================= rbt =====================     
        
        self.cfg_obj = ConfigurationPacket()
        
        self.load_file()
    
    def load_file(self) -> None:
        # 根据类型读取文件内容
        self.file_path_except_type, self.file_type = get_file_type(self.input_file_path)
        if self.file_type == ".rbt":
            with open(self.input_file_path, "r") as f:
                self.rbt_content = f.readlines()
                self.rbt_content = [line.strip() for line in self.rbt_content] 
                self.rbt_content_len = len(self.rbt_content)
            self.parse_rbt()
        elif self.file_type == ".bit" or self.file_type == ".bin":
            with open(self.input_file_path, 'rb') as file:
                self.bit_byte_content = file.read()
            self.bit_byte_content_len = len(self.bit_byte_content)
            self.parse_bit_or_bin(self.file_type)
        else:
            raise ValueError("文件格式错误")
        
    def parse_rbt_head_content(self):
        # Xilinx ASCII Bitstream
        # Created by Bitstream 2020.2 SW Build 3064766 on Wed Nov 18 09:12:45 MST 2020
        # Design name: 	xilinx_pcie_2_1_rport_7x;UserID=0XFFFFFFFF;Version=2020.2
        # Architecture:	artix7
        # Part:        	7a100tfgg484
        # Date:        	Mon Sep 02 11:44:48 2024
        # Bits:        	30606304
        for line_index, line in enumerate(self.rbt_content):
            # 不是空行，并且仅有0、1构成
            if bool(line) and set(line).issubset({'0', '1'}):
                self.rbt_content_cur_loc = line_index # 找到开头
                return
            self.rbt_annotation_content.append(line) # 仅存储注释信息
        raise ValueError("文件格式错误")
        
    # 解析位流，读取头部信息    
    def parse_bit_head_content(self) -> None:
        # 标识位
        # TARGET_START = b'\x00\x09'
        # TARGET_A = b'\x61'
        # TARGET_B = b'\x62'
        # TARGET_C = b'\x63'
        # TARGET_D = b'\x64'
        # TARGET_E = b'\x65'
        start_index = 0
        end_index = 0
        
        # ========== 起始数据 ============
        self.bit_head_byte_content += self.read_bit_bytes(2) # 标识
        self.bit_head_byte_content += self.read_bit_bytes(11) # 内容
        start_index += 13
        # ========== 起始数据 ============
        
        # ========== 标识符A ============
        self.bit_head_byte_content += self.read_bit_bytes(1) # 标识 b'\x61'
        cur_group_length = self.read_bit_bytes(2)
        self.bit_head_byte_content += cur_group_length  # 内容 该组字节长度
        group_length = struct.unpack('>H', cur_group_length)[0]
        self.bit_head_byte_content += self.read_bit_bytes(group_length) # 文件路径、Version、UserID
        start_index += 3
        end_index = start_index + group_length
        logging.debug(f"\tA content: {self.bit_head_byte_content[start_index:end_index].hex()}")
        show_ascii_content(self.bit_head_byte_content[start_index:end_index])
        start_index = end_index
        # ========== 标识符A ============
        
        # ========== 标识符B ============
        self.bit_head_byte_content += self.read_bit_bytes(1) # 标识 b'\x62'
        cur_group_length = self.read_bit_bytes(2)
        self.bit_head_byte_content += cur_group_length  # 内容 该组字节长度
        group_length = struct.unpack('>H', cur_group_length)[0]
        self.bit_head_byte_content += self.read_bit_bytes(group_length) # part name
        start_index += 3
        end_index = start_index + group_length
        logging.debug(f"\tB content: {self.bit_head_byte_content[start_index:end_index].hex()}")
        show_ascii_content(self.bit_head_byte_content[start_index:end_index])
        start_index = end_index
        # ========== 标识符B ============
        
        # ========== 标识符C ============
        self.bit_head_byte_content += self.read_bit_bytes(1) # 标识 b'\x63'
        cur_group_length = self.read_bit_bytes(2)
        self.bit_head_byte_content += cur_group_length  # 内容 该组字节长度
        group_length = struct.unpack('>H', cur_group_length)[0]
        self.bit_head_byte_content += self.read_bit_bytes(group_length) # 年/月/日
        start_index += 3
        end_index = start_index + group_length
        logging.debug(f"\tC content: {self.bit_head_byte_content[start_index:end_index].hex()}")
        show_ascii_content(self.bit_head_byte_content[start_index:end_index])
        start_index = end_index
        # ========== 标识符C ============

        # ========== 标识符D ============
        self.bit_head_byte_content += self.read_bit_bytes(1) # 标识 b'\x64'
        cur_group_length = self.read_bit_bytes(2)
        self.bit_head_byte_content += cur_group_length  # 内容 该组字节长度
        group_length = struct.unpack('>H', cur_group_length)[0]
        self.bit_head_byte_content += self.read_bit_bytes(group_length) # 时:分:秒
        start_index += 3
        end_index = start_index + group_length
        logging.debug(f"\tD content: {self.bit_head_byte_content[start_index:end_index].hex()}")
        show_ascii_content(self.bit_head_byte_content[start_index:end_index])
        start_index = end_index
        # ========== 标识符D ============

        # ========== 标识符E ============
        self.bit_head_byte_content += self.read_bit_bytes(1) # 标识 b'\x65'
        self.bit_head_byte_content += self.read_bit_bytes(4) # 位流的总长度
        start_index += 1
        end_index = start_index + 4
        logging.debug(f"\tE content: {self.bit_head_byte_content[start_index:end_index].hex()}")
        show_number_content(self.bit_head_byte_content[start_index:end_index])
        start_index = end_index
        # ========== 标识符E ============
            
    # 解析位流，读取cfg内容
    def parse_bit_cfg_content_pre(self) -> None: 
        while True:
            word = self.read_bit_bytes(4)
            log_debug_with_description(bytes_to_binary(word))
            if not word:
                break  # 到达文件末尾，停止读取
            if len(word) < 4:
                # 如果最后的 chunk 不足 4 个字节，输出提示
                logging.warning(f"Warning: Last chunk is less than 4 bytes: {word.hex()}")
            
            # 存入cfg中
            self.bit_cfg_content_pre.append(word)
            word_content = struct.unpack('>I', word)[0] # 转无符号整型
            
            if word_content == DUMMY_BIN:
                # DUMMY
                continue
            elif word_content == SYNC_WORD_BIN:
                # SYNC WORD
                continue
            elif word_content == BUS_WIDTH_AUTO_DETECT_01_BIN or word_content == BUS_WIDTH_AUTO_DETECT_02_BIN:
                # BUS WIDTH AUTO DETECT
                continue
            elif word_content == NOOP_BIN:
                # NOP
                continue
            
            content = self.cfg_obj.get_type_1_packet_content(word_content, "int")
            # 读取到 FDRI 后，读取结束 30004000
            if content.get("header_type", -1) == 1 \
                and content.get("opcode", self.cfg_obj.OpCode.UNKNOWN) == self.cfg_obj.OpCode.WRITE \
                and content.get("address", self.cfg_obj.Address.UNKNOWN) == self.cfg_obj.Address.FDRI:
                    word = self.read_bit_bytes(4)
                    self.bit_cfg_content_pre.append(word)
                    word_content = struct.unpack('>I', word)[0] # 转无符号整型
                    # 拿到 word_count，其单位是word，换成字节*4
                    self.word_count = self.cfg_obj.get_type_2_packet_content(word_content, "int").get("word_count",0)
                    self.bit_data_content_byte_count = self.word_count * 4
                    break
                       
    # 解析rbt，读取cfg内容
    def parse_rbt_cfg_content_pre(self) -> None: 
        for index in range(self.rbt_content_cur_loc, self.rbt_content_len):
            # 存入cfg中
            self.rbt_cfg_content_pre.append(self.rbt_content[index])
                        
            if self.rbt_content[index] == DUMMY_STR:
                # DUMMY
                continue
            elif self.rbt_content[index] == SYNC_WORD_STR:
                # SYNC WORD
                continue
            elif self.rbt_content[index] == BUS_WIDTH_AUTO_DETECT_01_STR or  self.rbt_content[index] == BUS_WIDTH_AUTO_DETECT_02_STR:
                # BUS WIDTH AUTO DETECT
                continue
            elif self.rbt_content[index] == NOOP_STR:
                # NOP
                continue
            if self.rbt_content[index] == FDRI_STR:
                word_content = self.rbt_content[index+1]
                self.rbt_cfg_content_pre.append(word_content)
                self.word_count = self.cfg_obj.get_type_2_packet_content(word_content,"str").get("word_count",0)
                self.rbt_content_cur_loc = index+2
                break
        else:
            raise ValueError("文件格式错误")
        
    # 解析位流，数据帧后面的cfg
    def parse_rbt_cfg_content_aft(self) -> None:
        self.rbt_cfg_content_after.extend(self.rbt_content[self.rbt_content_cur_loc:])
        self.rbt_content_cur_loc = self.rbt_content_len - 1
        
    # 解析位流，读取cfg内容
    def parse_bit_cfg_content_aft(self) -> None: 
        while True:
            word = self.read_bit_bytes(4)
            if not word:
                break  # 到达文件末尾，停止读取
            if len(word) < 4:
                # 如果最后的 chunk 不足 4 个字节，输出提示
                logging.warning(f"Warning: Last chunk is less than 4 bytes: {word.hex()}")
            
            # 存入cfg中
            self.bit_cfg_content_after.append(word)
        
    def parse_bit_data_content(self) -> None: 
        data_content = self.read_bit_bytes(self.bit_data_content_byte_count)
        for i in range(0,self.bit_data_content_byte_count,4):
            self.bit_data_content.append(data_content[i:i+4])
    
    # 解析cfg，读取数据帧
    def parse_rbt_data_content(self) -> None: 
        self.rbt_data_content.extend(self.rbt_content[self.rbt_content_cur_loc:self.rbt_content_cur_loc+self.word_count+1])
        self.rbt_content_cur_loc = self.rbt_content_cur_loc + self.word_count + 1
            
    def parse_rbt(self) -> None:
        # ============================================ rbt header ============================================
        self.parse_rbt_head_content()
        # ============================================ rbt header ============================================

        # ============================================ cfg content pre ============================================
        # 从 11111111111111111111111111111111 开始
        self.parse_rbt_cfg_content_pre()
        # 到 30004000 XXXXXXXX 结束，其中 XXXXXXXX 的低27位标识接下来 data frame 的长度
        # self.word_count 为 接下来有多少个 word
        # 1个word为4字节，1字节为8位
        # ============================================ cfg content pre ============================================
          
        # ============================================ data frame ============================================
        # 从 FDRI data word 1 开始
        self.parse_rbt_data_content()
        # 到 FDRI data word XXXX 结束，其中 XXXX 指的是 parse_rbt_cfg_content_pre 解析出来的 self.word_count
        # ============================================ data frame ============================================
        
        # ============================================ cfg content after ============================================
        # 对于没有关闭CRC的位流，此处从 30000001 开始
        self.parse_rbt_cfg_content_aft()
        # 到 码流末尾 结束
        # ============================================ cfg content after ============================================
        
        log_debug_with_description(len(self.rbt_annotation_content), description="头部注释信息行数")
        log_debug_with_description(len(self.rbt_cfg_content_pre), description="数据帧之前的寄存器行数")
        log_debug_with_description(len(self.rbt_data_content), description="数据行数")
        log_debug_with_description(len(self.rbt_cfg_content_after), description="数据帧之后的寄存器行数")
        log_debug_with_description(len(self.rbt_annotation_content) + len(self.rbt_cfg_content_pre) + len(self.rbt_data_content) + len(self.rbt_cfg_content_after), description="总行数")
        
    def parse_bit_or_bin(self, file_type: str) -> None:
        # ============================================ bit header ============================================
        if file_type == ".bit":
            self.parse_bit_head_content()
        # ============================================ bit header ============================================
        
        # ============================================ cfg content pre ============================================
        # 从 FFFFFFFF 开始
        self.parse_bit_cfg_content_pre()
        # 到 30004000 XXXXXXXX 结束，其中 XXXXXXXX 的低27位标识接下来 data frame 的长度
        # self.word_count 为 接下来有多少个 word
        # self.bit_data_content_byte_count 为 接下来有多少个字节
        # 1个word为4字节，1字节为8位
        # ============================================ cfg content pre ============================================
                
        # ============================================ data frame ============================================
        # 从 FDRI data word 1 开始
        self.parse_bit_data_content()
        # 到 FDRI data word XXXX 结束，其中 XXXX 指的是 parse_bit_cfg_content_pre 解析出来的 self.word_count
        # ============================================ data frame ============================================
        
        # ============================================ cfg content after ============================================
        # 对于没有关闭CRC的位流，此处从 30000001 开始
        self.parse_bit_cfg_content_aft()
        # 到 码流末尾 结束
        # ============================================ cfg content after ============================================
        
        # len(self.bit_head_byte_content)) 头部信息字节数
        # len(self.bit_cfg_content_pre)) 数据帧之前的寄存器所占word数，*4为字节数
        # len(self.bit_data_content)) 数据帧所占word数，*4为字节数
        # len(self.bit_cfg_content_after)) 数据帧之后的寄存器所占word数，*4为字节数
        
        # 四个字节数相加为整段位流长度
        log_debug_with_description(len(self.bit_head_byte_content), 'X', '头部信息字节数')
        log_debug_with_description(len(self.bit_cfg_content_pre)*4, 'X', '数据帧之前的寄存器字节数')
        log_debug_with_description(len(self.bit_data_content)*4, 'X', '数据帧字节数')
        log_debug_with_description(len(self.bit_cfg_content_after)*4, 'X', '数据帧之后的寄存器字节数')
        log_debug_with_description(len(self.bit_cfg_content_after)*4 + len(self.bit_data_content)*4 + len(self.bit_cfg_content_pre)*4 + len(self.bit_head_byte_content), 'X', '总字节数')
        
        with open(r"E:\workspace\parse_bitstream\parse_bitstream\data\system_wrapper_1_原版_2.bin", 'wb') as file:
            file.write(self.bit_head_byte_content)
            for byte_elem in self.bit_cfg_content_pre:
                file.write(byte_elem)
            for byte_elem in self.bit_data_content:
                file.write(byte_elem)
            for byte_elem in self.bit_cfg_content_after:
                file.write(byte_elem)
    
    def get_data_frame(self, region, row, col, frame):
        pass
    
    def get_data_word(self, region, row, col, frame, word):
        pass
    
    def get_data_bit(self, region, row, col, frame, word, bit):
        pass
    
    def read_bit_bytes(self, read_length: int) -> bytes:
        """
        从当前位置读取指定长度的字节。

        参数:
            read_length (int): 要读取的字节长度。

        返回:
            bytes: 读取的字节数据。

        异常:
            ValueError: 如果读取操作超出内容范围。
        """
        # if self.bit_byte_content_cur_loc + read_length > self.bit_byte_content_len:
        #     error_msg = f"Attempted to read {read_length} bytes from position {self.bit_byte_content_cur_loc}, " \
        #                 f"which exceeds the content length {self.bit_byte_content_len}."
        #     logging.error(error_msg)
        #     raise ValueError(error_msg)
        
        if self.bit_byte_content_cur_loc + read_length > self.bit_byte_content_len:
            return b''
        data = self.bit_byte_content[self.bit_byte_content_cur_loc : self.bit_byte_content_cur_loc + read_length]
        self.bit_byte_content_cur_loc += read_length
        return data
    
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
    
    reader = BitstreamReader(args.rbt_file)

if __name__ == "__main__":
    main()
    
# INPUT_FILE_PATH = r"E:\workspace\parse_bitstream\parse_bitstream\data\system_wrapper_1_原版.bit"
# # 打开文件，以二进制模式('rb')读取
# with open(INPUT_FILE_PATH, 'rb') as file:
#     # 读取整个文件内容
#     bit_byte_content = file.read()
# reader = BitstreamReader(bit_byte_content)
# reader.read_bit_or_bin_file_and_parse("bit")
# print(123)