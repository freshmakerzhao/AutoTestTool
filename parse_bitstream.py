import os 
import struct
import logging
import argparse
import enum
# 配置日志级别和格式
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# logging.basicConfig(level=logging.WARNING,  format='%(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.INFO,  format='%(asctime)s - %(levelname)s - %(message)s')

FILE_ENDWITH = "_replace"

DUMMY_STR = "11111111111111111111111111111111"
DUMMY_BIN = 0b11111111111111111111111111111111
DUMMY_BIT = b'\xFF\xFF\xFF\xFF'

SYNC_WORD_STR = "10101010100110010101010101100110"
SYNC_WORD_BIN = 0b10101010100110010101010101100110
SYNC_WORD_BIT = b'\xAA\x99\x55\x66'

BUS_WIDTH_AUTO_DETECT_01_STR = "00000000000000000000000010111011"
BUS_WIDTH_AUTO_DETECT_01_BIN = 0b00000000000000000000000010111011
BUS_WIDTH_AUTO_DETECT_01_BIT = b'\x00\x00\x00\xBB'

BUS_WIDTH_AUTO_DETECT_02_STR = "00010001001000100000000001000100"
BUS_WIDTH_AUTO_DETECT_02_BIN = 0b00010001001000100000000001000100
BUS_WIDTH_AUTO_DETECT_02_BIT = b'\x11\x22\x00\x44'

NOOP_STR = "00100000000000000000000000000000"
NOOP_BIN = 0b00100000000000000000000000000000
NOOP_BIT = b'\x20\x00\x00\x00'

FDRI_STR = "00110000000000000100000000000000"
FDRI_BIN = 0b00110000000000000100000000000000
FDRI_BIT = b'\x30\x00\x40\x00'

BITS_CMD = 'Bits:'


CRC_RBT = '00110000000000000000000000000001'
CRC_BIT = b'\x30\x00\x00\x01'

CMD_RCRC_01_RBT = '00110000000000001000000000000001'
CMD_RCRC_02_RBT = '00000000000000000000000000000111'

CMD_RCRC_01_BIT = b'\x30\x00\x80\x01'
CMD_RCRC_02_BIT = b'\x00\x00\x00\x07'


COR1_RBT = '00110000000000011100000000000001'
COR1_BIT = b'\x30\x01\xC0\x01'


CMD_MASK_01_RBT = '00110000000000001100000000000001'
CMD_MASK_02_RBT = '10000000000000000000000000000000'
CMD_TRIM_01_RBT = '00110000000000110110000000000001'
CMD_TRIM_02_RBT = '10000000000000000000000000000000'

CMD_MASK_01_BIT = b'\x30\x00\xC0\x01'
CMD_MASK_02_BIT = b'\x80\x00\x00\x00'
CMD_TRIM_01_BIT = b'\x30\x03\x60\x01'
CMD_TRIM_02_BIT = b'\x80\x00\x00\x00'

PRE_CMD_GROUP_RBT = {
    "00110000000000011100000000000001": "COR1"
}
PRE_CMD_GROUP_BIT = {
    b'\x30\x01\xC0\x01': "COR1"
}

AFTER_CMD_GROUP_RBT = {
    "00110000000000000000000000000001": "CRC"
}
AFTER_CMD_GROUP_BIT = {
    b'\x30\x00\x00\x01': "CRC"
}
# GTP 修改位置和数据

GTP_CONFIG = [
    {"frame": 3829, "word":  0, "bit": 2, "data": "1"},
    {"frame": 3829, "word": 22, "bit": 2, "data": "1"},
    {"frame": 3829, "word": 57, "bit": 2, "data": "1"},
    {"frame": 3829, "word": 79, "bit": 2, "data": "1"}
]

# PCIE 校验位
PCIE_CHECK = {
    0:[
        {"frame": 3454, "word":  20, "bit": 26, "data": "1"},
        {"frame": 3455, "word":  20, "bit": 24, "data": "1"},
        {"frame": 3455, "word":  20, "bit": 21, "data": "1"},
        {"frame": 3475, "word":  21, "bit":  8, "data": "1"},
        {"frame": 3479, "word":  21, "bit":  8, "data": "1"},
        
    ],
    1:[ 
        {"frame": 3454, "word":  22, "bit": 12, "data": "1"},   
        {"frame": 3462, "word":  22, "bit": 15, "data": "1"},    
        {"frame": 3475, "word":  22, "bit":  8, "data": "1"},   
        {"frame": 3479, "word":  22, "bit":  8, "data": "1"}
    ],
    2:[
        {"frame": 3455, "word":  22, "bit":  7, "data": "1"},
        {"frame": 3462, "word":  22, "bit": 14, "data": "1"},    
        {"frame": 3475, "word":  22, "bit":  0, "data": "1"},
        {"frame": 3479, "word":  22, "bit":  0, "data": "1"}
    ]
}

# PCIE 修改位置
PCIE_CONFIG = {
    0:[
        {"frame": 3454, "word":  20, "bit": 26, "data": "1"},
        {"frame": 3454, "word":  20, "bit": 25, "data": "1"},
        {"frame": 3455, "word":  20, "bit": 24, "data": "1"},
        {"frame": 3455, "word":  20, "bit": 21, "data": "1"},
        {"frame": 3475, "word":  21, "bit":  8, "data": "1"},
        {"frame": 3479, "word":  21, "bit":  8, "data": "1"},
        {"frame": 3829, "word":   0, "bit":  2, "data": "1"},
        {"frame": 3829, "word":  22, "bit":  2, "data": "1"},
        {"frame": 3829, "word":  57, "bit":  2, "data": "1"},
        {"frame": 3829, "word":  79, "bit":  2, "data": "1"}
    ],
    1:[
        {"frame": 3454, "word":  20, "bit": 25, "data": "1"},   
        {"frame": 3454, "word":  20, "bit": 22, "data": "1"},   
        {"frame": 3454, "word":  22, "bit": 12, "data": "1"},   
        {"frame": 3462, "word":  22, "bit": 15, "data": "1"},   
        {"frame": 3468, "word":  22, "bit": 15, "data": "1"},   
        {"frame": 3475, "word":  22, "bit":  8, "data": "1"},   
        {"frame": 3479, "word":  22, "bit":  8, "data": "1"},
        {"frame": 3829, "word":   0, "bit":  2, "data": "1"},
        {"frame": 3829, "word":  22, "bit":  2, "data": "1"},
        {"frame": 3829, "word":  57, "bit":  2, "data": "1"},
        {"frame": 3829, "word":  79, "bit":  2, "data": "1"}  
    ],
    2:[
        {"frame": 3454, "word":  20, "bit": 25, "data": "1"},
        {"frame": 3454, "word":  20, "bit": 22, "data": "1"},
        {"frame": 3455, "word":  22, "bit":  7, "data": "1"},
        {"frame": 3462, "word":  22, "bit": 14, "data": "1"},
        {"frame": 3468, "word":  22, "bit": 15, "data": "1"},
        {"frame": 3475, "word":  22, "bit":  0, "data": "1"},
        {"frame": 3479, "word":  22, "bit":  0, "data": "1"}, 
        {"frame": 3829, "word":   0, "bit":  2, "data": "1"},
        {"frame": 3829, "word":  22, "bit":  2, "data": "1"},
        {"frame": 3829, "word":  57, "bit":  2, "data": "1"},
        {"frame": 3829, "word":  79, "bit":  2, "data": "1"}  
    ]
}

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

def binary_str_to_bytes(binary_str):
    # 将32位二进制字符串转换为整数
    num = int(binary_str, 2)
    # 使用struct将整数转换为4字节的字节对象
    return struct.pack('>I', num)  # '>I'表示大端4字节无符号整数

class PacketItem:
    def __init__(self, cmd_name) -> None:
        self.cmd_name = cmd_name
        self.data = []
        self.data_len = 0
        self.opcode = 0
    def append_data(self, data):
        self.data.append(data)
        self.data_len += 1
    def get_data_from_index(self, index):
        return self.data[index]
    def get_all_data(self):
        return self.data
    def get_data_len(self):
        return self.data_len
    def set_data_to_index(self, index, data):
        self.data[index] = data
    def set_opcode(self, data):
        self.opcode = data

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
    
    def get_cmd_name(self, key):
        return self.cmd_name_map.get(key, self.Address.UNKNOWN)
    
    # 传入整型，返回其type
    def get_packet_type(self, word, content_type = "int"):
        if content_type != "int":
            word = int(word, 2)
        return word >> 29 
    
    # 传入整型，返回其opcode
    def get_opcode(self, word, content_type = "int"):
        if content_type != "int":
            word = int(word, 2)
        return self.OpCode((word >> 27) & 0x3) 

    # 根据传入word获取其type1格式的数据，content_type为int时，直接读，str时转换后再读
    def get_type_1_packet_content(self, word, content_type = "int"):
        if content_type != "int":
            word = int(word, 2)
        header_type = self.get_packet_type(word) # [31:29]
        opcode = self.OpCode((word >> 27) & 0x3) # [28:27]
        address = self.Address((word >> 13) & 0x1F) # [26:13] 取低5位
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
        
    def make_len_37_crc_data_in(self, word, cmd_word, content_type = "byte"):
        if content_type == "byte":
            word = bytes_to_binary(word)
            cmd_word = bytes_to_binary(cmd_word)
        address = cmd_word[14:19]
        crc_data_in = address + word
        return ([int(i) for i in crc_data_in[::-1]])
    
    def __init__(self) -> None:
        self.cmd_name_map = {    
            self.Address.UNKNOWN : "UNKNOWN",
            self.Address.CRC : "CRC",
            self.Address.FAR : "FAR",
            self.Address.FDRI : "FDRI",
            self.Address.FDRO : "FDRO",
            self.Address.CMD : "CMD",
            self.Address.CTL0 : "CTL0",
            self.Address.MASK : "MASK",
            self.Address.STAT : "STAT",
            self.Address.LOUT : "LOUT",
            self.Address.COR0 : "COR0",
            self.Address.MFWR : "MFWR",
            self.Address.CBC : "CBC",
            self.Address.IDCODE : "IDCODE",
            self.Address.AXSS : "AXSS",
            self.Address.COR1 : "COR1",
            self.Address.UNKNOWN_15 : "UNKNOWN_15",
            self.Address.WBSTAR : "WBSTAR",
            self.Address.TIMER : "TIMER",
            self.Address.UNKNOWN_18 : "UNKNOWN_18",
            self.Address.POST_CRC : "POST_CRC",
            self.Address.UNKNOWN_20 : "UNKNOWN_20",
            self.Address.UNKNOWN_21 : "UNKNOWN_21",
            self.Address.BOOTSTS : "BOOTSTS",
            self.Address.CTL1 : "CTL1",
            self.Address.UNKNOWN_30 : "UNKNOWN_30",
            self.Address.BSPI : "BSPI"
        }
    
class BitstreamParser:
    def __init__(self, input_file_path: str, enable_crc: bool):
        """
        初始化 BitstreamParser

        参数:
            input_file_path (str): 文件路径
        """
        self.input_file_path = input_file_path # 输入文件路径
        self.file_type = "" # 文件类型
        self.file_path_except_type = "" # 不带文件类型的路径，方便存储新文件
        
        self.enable_crc = enable_crc
        self.crc_01 = "00000000000000000000000000000000"
        self.crc_02 = "00000000000000000000000000000000"
        
        # 位流中的CRC内容
        self.crc_own_01 = "-1"
        self.crc_own_02 = "-1"
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
        # 这里构造完成后，以如下形式存在：
        # [
        #     "CRC":{
        #         "data":[
        #             "00110000000000000000000000000001",
        #             "..",
        #             "..",
        #         ]
        #     },
        #     "UNKNOWN":{
        #         "data":[
        #             "..",
        #         ]
        #     },
        #     "..",
        # ]
        # ============================================ cfg content after ============================================
        
        # ============================================ debug ============================================
        log_debug_with_description(len(self.rbt_annotation_content), description="头部注释信息行数")
        log_debug_with_description(len(self.rbt_cfg_content_pre), description="数据帧之前的寄存器行数")
        log_debug_with_description(len(self.rbt_data_content), description="数据行数")
        cur_group_len = 0
        for item in self.rbt_cfg_content_after:
            cur_group_len += item.get_data_len()
        log_debug_with_description(cur_group_len, description="数据帧之后的寄存器行数")
        log_debug_with_description(len(self.rbt_annotation_content) + len(self.rbt_cfg_content_pre) + len(self.rbt_data_content) + cur_group_len, description="总行数")
        # ============================================ debug ============================================
          
    # 解析cfg，读取数据帧
    def parse_rbt_data_content(self) -> None: 
        self.rbt_data_content.extend(self.rbt_content[self.rbt_content_cur_loc:self.rbt_content_cur_loc+self.word_count])
        self.rbt_content_cur_loc = self.rbt_content_cur_loc + self.word_count
        
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
             
    # 解析rbt，读取cfg内容
    def parse_rbt_cfg_content_pre(self) -> None: 
        index = self.rbt_content_cur_loc
        while index < self.rbt_content_len:
            line = self.rbt_content[index]
            word_type = self.cfg_obj.get_packet_type(line, "str")
            
            packet_content = {}
            if word_type == 1:
                packet_content = self.cfg_obj.get_type_1_packet_content(line, "str")
            elif word_type == 2:
                packet_content = self.cfg_obj.get_type_2_packet_content(line, "str")
            
            # 拿到word count
            word_count = packet_content.get('word_count', 0)
            
            if line == NOOP_STR:
                item = PacketItem("NOOP")
                item.set_opcode(-1)
                word_count = 0
            elif line == DUMMY_STR:
                item = PacketItem("DUMMY")
                item.set_opcode(-1)
                word_count = 0
            elif line == SYNC_WORD_STR:
                item = PacketItem("SYNC_WORD")
                item.set_opcode(-1)
                word_count = 0
            elif line == BUS_WIDTH_AUTO_DETECT_01_STR or line == BUS_WIDTH_AUTO_DETECT_02_STR:
                item = PacketItem("BUS_WIDTH")
                item.set_opcode(-1)
                word_count = 0
            else:
                item = PacketItem(self.cfg_obj.get_cmd_name(packet_content.get("address")))
                item.set_opcode(packet_content.get("opcode", -1))
            
            item.append_data(self.rbt_content[index]) # 插入cmd
            
            for i in range(word_count):
                index += 1
                item.append_data(self.rbt_content[index])
                
            index += 1
            self.rbt_cfg_content_pre.append(item)
            
            if line == FDRI_STR:
                word_content = self.rbt_content[index]
                item = PacketItem("WORD_COUNT")
                item.set_opcode(-1)
                item.append_data(word_content)
                self.rbt_cfg_content_pre.append(item)
                self.word_count = self.cfg_obj.get_type_2_packet_content(word_content,"str").get("word_count",0)
                self.rbt_content_cur_loc = index+1
                break
        else:
            raise ValueError("文件格式错误")
        
    # 解析位流，数据帧后面的cfg
    def parse_rbt_cfg_content_aft(self) -> None:
        while self.rbt_content_cur_loc < self.rbt_content_len:
            line = self.rbt_content[self.rbt_content_cur_loc]
            
            word_type = self.cfg_obj.get_packet_type(line, "str")
            
            packet_content = {}
            if word_type == 1:
                packet_content = self.cfg_obj.get_type_1_packet_content(line, "str")
            elif word_type == 2:
                packet_content = self.cfg_obj.get_type_2_packet_content(line, "str")
            
            # 拿到word count
            word_count = packet_content.get('word_count', 0)
            
            if line == NOOP_STR:
                item = PacketItem("NOOP")
                item.set_opcode(-1)
                word_count = 0
            elif line == DUMMY_STR:
                item = PacketItem("DUMMY")
                item.set_opcode(-1)
                word_count = 0
            elif line == SYNC_WORD_STR:
                item = PacketItem("SYNC_WORD")
                item.set_opcode(-1)
                word_count = 0
            elif line == BUS_WIDTH_AUTO_DETECT_01_STR or line == BUS_WIDTH_AUTO_DETECT_02_STR:
                item = PacketItem("BUS_WIDTH")
                item.set_opcode(-1)
                word_count = 0
            else:
                item = PacketItem(self.cfg_obj.get_cmd_name(packet_content.get("address")))
                item.set_opcode(packet_content.get("opcode", -1))
            
                
            item.append_data(self.rbt_content[self.rbt_content_cur_loc]) # 插入cmd
            
            for i in range(word_count):
                self.rbt_content_cur_loc += 1
                item.append_data(self.rbt_content[self.rbt_content_cur_loc])
            
            # 记录crc
            if item.cmd_name == "CRC":
                if self.crc_own_01 == '-1':
                    self.crc_own_01 = self.rbt_content[self.rbt_content_cur_loc]
                else:
                    self.crc_own_02 = self.rbt_content[self.rbt_content_cur_loc]
                    
            self.rbt_content_cur_loc += 1
            self.rbt_cfg_content_after.append(item)
             
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
            
            word_content = struct.unpack('>I', word)[0] # 转无符号整型
            word_type = self.cfg_obj.get_packet_type(word_content, "int")
            
            packet_content = {}
            if word_type == 1:
                packet_content = self.cfg_obj.get_type_1_packet_content(word_content, "int")
            elif word_type == 2:
                packet_content = self.cfg_obj.get_type_2_packet_content(word_content, "int")
            
            # 拿到word count
            word_count = packet_content.get('word_count', 0)
            
            if word == NOOP_BIT:
                item = PacketItem("NOOP")
                item.set_opcode(-1)
                word_count = 0
            elif word == DUMMY_BIT:
                item = PacketItem("DUMMY")
                item.set_opcode(-1)
                word_count = 0
            elif word == SYNC_WORD_BIT:
                item = PacketItem("SYNC_WORD")
                item.set_opcode(-1)
                word_count = 0
            elif word == BUS_WIDTH_AUTO_DETECT_01_BIT or word == BUS_WIDTH_AUTO_DETECT_02_BIT:
                item = PacketItem("BUS_WIDTH")
                item.set_opcode(-1)
                word_count = 0
            else:
                item = PacketItem(self.cfg_obj.get_cmd_name(packet_content.get("address")))
                item.set_opcode(packet_content.get("opcode", -1))
            
            item.append_data(word) # 插入cmd
            
            for i in range(word_count):
                item.append_data(self.read_bit_bytes(4))
                
            self.bit_cfg_content_pre.append(item)            
            
            # 读取到 FDRI 后，读取结束 30004000
            if packet_content.get("header_type", -1) == 1 \
                and packet_content.get("opcode", self.cfg_obj.OpCode.UNKNOWN) == self.cfg_obj.OpCode.WRITE \
                and packet_content.get("address", self.cfg_obj.Address.UNKNOWN) == self.cfg_obj.Address.FDRI:
                    word = self.read_bit_bytes(4)
                    item = PacketItem("WORD_COUNT")
                    item.set_opcode(-1)
                    item.append_data(word)
                    self.bit_cfg_content_pre.append(item)
                    word_content = struct.unpack('>I', word)[0] # 转无符号整型
                    # 拿到 word_count，其单位是word，换成字节*4
                    self.word_count = self.cfg_obj.get_type_2_packet_content(word_content, "int").get("word_count",0)
                    self.bit_data_content_byte_count = self.word_count * 4
                    break
        
    # 解析位流，读取cfg内容
    def parse_bit_cfg_content_aft(self) -> None: 
        while True:
            word = self.read_bit_bytes(4)
            if not word:
                break  # 到达文件末尾，停止读取
            if len(word) < 4:
                # 如果最后的 chunk 不足 4 个字节，输出提示
                logging.warning(f"Warning: Last chunk is less than 4 bytes: {word.hex()}")
            
            word_content = struct.unpack('>I', word)[0] # 转无符号整型
            word_type = self.cfg_obj.get_packet_type(word_content, "int")
            
            packet_content = {}
            if word_type == 1:
                packet_content = self.cfg_obj.get_type_1_packet_content(word_content, "int")
            elif word_type == 2:
                packet_content = self.cfg_obj.get_type_2_packet_content(word_content, "int")
            
            # 拿到word count
            word_count = packet_content.get('word_count', 0)
            
            if word == NOOP_BIT:
                item = PacketItem("NOOP")
                item.set_opcode(-1)
                word_count = 0
            elif word == DUMMY_BIT:
                item = PacketItem("DUMMY")
                item.set_opcode(-1)
                word_count = 0
            elif word == SYNC_WORD_BIT:
                item = PacketItem("SYNC_WORD")
                item.set_opcode(-1)
                word_count = 0
            elif word == BUS_WIDTH_AUTO_DETECT_01_BIT or word == BUS_WIDTH_AUTO_DETECT_02_BIT:
                item = PacketItem("BUS_WIDTH")
                item.set_opcode(-1)
                word_count = 0
            else:
                item = PacketItem(self.cfg_obj.get_cmd_name(packet_content.get("address")))
                item.set_opcode(packet_content.get("opcode", -1))
                
            item.append_data(word) # 插入cmd

            for i in range(word_count):
                item.append_data(self.read_bit_bytes(4))
                
            # 记录crc
            if item.cmd_name == "CRC":
                if self.crc_own_01 == '-1':
                    self.crc_own_01 = item.get_data_from_index(1)
                else:
                    self.crc_own_02 = item.get_data_from_index(1)
            self.bit_cfg_content_after.append(item)            
        
    # 解析位流，读取数据帧    
    def parse_bit_data_content(self) -> None: 
        data_content = self.read_bit_bytes(self.bit_data_content_byte_count)
        for i in range(0,self.bit_data_content_byte_count,4):
            self.bit_data_content.append(data_content[i:i+4])

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
        
        # ============================================ debug ============================================
        # len(self.bit_head_byte_content)) 头部信息字节数
        # len(self.bit_cfg_content_pre)) 数据帧之前的寄存器所占word数，*4为字节数
        # len(self.bit_data_content)) 数据帧所占word数，*4为字节数
        # len(self.bit_cfg_content_after)) 数据帧之后的寄存器所占word数，*4为字节数
        
        # 四个字节数相加为整段位流长度
        log_debug_with_description(len(self.bit_head_byte_content), 'X', '头部信息字节数')
        
        bit_cfg_content_pre_len = 0
        for item in self.bit_cfg_content_pre:
            bit_cfg_content_pre_len += item.get_data_len()
        log_debug_with_description(bit_cfg_content_pre_len*4, 'X', '数据帧之前的寄存器字节数')
        log_debug_with_description(len(self.bit_data_content)*4, 'X', '数据帧字节数')
        
        bit_cfg_content_after_len = 0
        for item in self.bit_cfg_content_after:
            bit_cfg_content_after_len += item.get_data_len()
        log_debug_with_description(bit_cfg_content_after_len*4, 'X', '数据帧之后的寄存器字节数')
        log_debug_with_description(bit_cfg_content_after_len*4 + len(self.bit_data_content)*4 + bit_cfg_content_pre_len*4 + len(self.bit_head_byte_content), 'X', '总字节数')
        # ============================================ debug ============================================
    
    def set_data_with_frame_word_bit(self, data, frame, word, bit):
        line_index = frame*101 + word
        bit_index = 31 - bit # 这里是因为bit从右往左算，而index从左往右算
        if self.file_type == ".bit" or self.file_type == ".bin":
            word = bytes_to_binary(self.bit_data_content[line_index])
            word = word[:bit_index] + data + ( word[bit_index+1:] if bit_index<31 else "")
            self.bit_data_content[line_index] = binary_str_to_bytes(word)
        elif self.file_type == ".rbt":
            # rbt_data_content中的内容是左高右低的
            self.rbt_data_content[line_index] = self.rbt_data_content[line_index][:bit_index] + data + ( self.rbt_data_content[line_index][bit_index+1:] if bit_index<31 else "")
        else:
            raise ValueError("文件格式错误")
          
    def get_data_with_frame_word_bit(self, frame, word, bit):
        line_index = frame*101 + word
        bit_index = 31 - bit # 这里是因为bit从右往左算，而index从左往右算
        if self.file_type == ".bit" or self.file_type == ".bin":
            word = bytes_to_binary(self.bit_data_content[line_index])
            return word[bit_index]
        elif self.file_type == ".rbt":
            return self.rbt_data_content[line_index][bit_index]
        else:
            raise ValueError("文件格式错误")      

    def get_data_frame(self, frame):
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
    
    def save_file(self, file_suffix = ""):
        new_file_path = self.file_path_except_type + file_suffix + self.file_type
        if self.file_type == ".rbt":
            # 计算长度
            byte_nums = len(self.rbt_data_content)
            for item in self.rbt_cfg_content_pre:
                byte_nums += item.get_data_len()
            for item in self.rbt_cfg_content_after:
                byte_nums += item.get_data_len()
            byte_nums = byte_nums * 32
            
            with open(new_file_path, 'w') as f:
                bits_flag = True
                for line in self.rbt_annotation_content:
                    if bits_flag and BITS_CMD in line:
                        bits_flag = False
                        line = f"Bits:        	{byte_nums}"
                    f.write(line + '\n')
                for item in self.rbt_cfg_content_pre:
                    values = item.get_all_data()
                    for line in values:
                        f.write(line + '\n')
                for line in self.rbt_data_content:
                    f.write(line + '\n')
                for item in self.rbt_cfg_content_after:
                    values = item.get_all_data()
                    for line in values:
                        f.write(line + '\n')
        elif self.file_type == ".bit" or self.file_type == ".bin":
            with open(new_file_path, 'wb') as file:
                # 重新计算长度
                bit_len = len(self.bit_data_content)
                for item in self.bit_cfg_content_pre:
                    bit_len += item.get_data_len()
                for item in self.bit_cfg_content_after:
                    bit_len += item.get_data_len()
                bit_len = bit_len * 4
                length_bytes_struct = struct.pack('>I', bit_len)
                self.bit_head_byte_content = self.bit_head_byte_content[:-4] + length_bytes_struct
                file.write(self.bit_head_byte_content)
                for item in self.bit_cfg_content_pre:
                    values = item.get_all_data()
                    for word in values:
                        file.write(word)
                for byte_elem in self.bit_data_content:
                    file.write(byte_elem)
                for item in self.bit_cfg_content_after:
                    values = item.get_all_data()
                    for word in values:
                        file.write(word)
        else:
            raise ValueError("文件格式错误")
        print(f"writing file : {new_file_path}")

    # 关闭CRC    
    def disable_crc(self):
        # 拿到数据帧之后的寄存器
        if self.file_type == ".rbt":
            for i in range(len(self.rbt_cfg_content_after)):
                if self.rbt_cfg_content_after[i].cmd_name == "CRC":
                    self.rbt_cfg_content_after[i].set_data_to_index(0, CMD_RCRC_01_RBT)
                    self.rbt_cfg_content_after[i].set_data_to_index(1, CMD_RCRC_02_RBT)
        elif self.file_type == ".bit" or self.file_type == ".bin":
            for i in range(len(self.bit_cfg_content_after)):
                if self.bit_cfg_content_after[i].cmd_name == "CRC":
                    self.bit_cfg_content_after[i].set_data_to_index(0, CMD_RCRC_01_BIT)
                    self.bit_cfg_content_after[i].set_data_to_index(1, CMD_RCRC_02_BIT)
        
    # 修改trim0寄存器，从0置1  
    def set_trim(self):
        # 拿到数据帧之前的寄存器
        if self.file_type == ".rbt":
            for i in range(len(self.rbt_cfg_content_pre)):
                if self.rbt_cfg_content_pre[i].cmd_name == "COR1":
                    new_line = self.rbt_cfg_content_pre[i].get_data_from_index(1)[:-13] + "1" + self.rbt_cfg_content_pre[i].get_data_from_index(1)[-12:]
                    self.rbt_cfg_content_pre[i].set_data_to_index(1, new_line)
                    self.rbt_cfg_content_pre[i].append_data(CMD_MASK_01_RBT)
                    self.rbt_cfg_content_pre[i].append_data(CMD_MASK_02_RBT)
                    self.rbt_cfg_content_pre[i].append_data(CMD_TRIM_01_RBT)
                    self.rbt_cfg_content_pre[i].append_data(CMD_TRIM_02_RBT)
        elif self.file_type == ".bit" or self.file_type == ".bin":
            for i in range(len(self.bit_cfg_content_pre)):
                if self.bit_cfg_content_pre[i].cmd_name == "COR1":
                    word = bytes_to_binary(self.bit_cfg_content_pre[i].get_data_from_index(1))
                    word = word[:-13] + "1" + word[-12:]
                    self.bit_cfg_content_pre[i].set_data_to_index(1, binary_str_to_bytes(word))
                    self.bit_cfg_content_pre[i].append_data(CMD_MASK_01_BIT)
                    self.bit_cfg_content_pre[i].append_data(CMD_MASK_02_BIT)
                    self.bit_cfg_content_pre[i].append_data(CMD_TRIM_01_BIT)
                    self.bit_cfg_content_pre[i].append_data(CMD_TRIM_02_BIT)
        
    # 计算crc
    def calculate_crc(self):
        # 拿到数据帧之前的寄存器
        if self.file_type == ".rbt":
            # ============== 第一段 =====================
            crc_start_flag = False
            # 1. 拿到数据帧前的寄存器，确定RCRC位置
            for item in self.rbt_cfg_content_pre:
                if item.opcode == -1 or item.opcode.value != 2:
                    # 不参与运算
                    continue
                else:
                    # 参与运算
                    words_len = item.get_data_len()
                    for index in range(1, words_len):
                        if item.get_data_from_index(0) == CMD_RCRC_01_RBT and item.get_data_from_index(1) == CMD_RCRC_02_RBT:
                            # 从这里开始，后面的寄存器参与运算
                            crc_start_flag = True
                            continue
                        if crc_start_flag:
                            # 计算crc
                            # 拿到cmd本身
                            cmd_word = item.get_data_from_index(0) # rbt
                            # 拿到当前cmd下的word
                            cur_word = item.get_data_from_index(index) # rbt
                            
                            crc_data_in = self.cfg_obj.make_len_37_crc_data_in(cur_word, cmd_word, "str")
                            self.crc_01 = self.icap_crc(crc_data_in, self.crc_01)
            # 00010010000111000110100110000001                
            for word in self.rbt_data_content:
                # 计算crc
                crc_data_in = self.cfg_obj.make_len_37_crc_data_in(word, FDRI_STR, "str")
                self.crc_01 = self.icap_crc(crc_data_in, self.crc_01)
            
            print(self.crc_01) # 01111100100101011110011001111001 7C95E679
            # ============== 第一段 =====================
            
            # ============== 第二段 =====================
            crc_end_flag = False
            rbt_cfg_content_after_len = len(self.rbt_cfg_content_after)
            # 这里从索引2开始，因为数据帧后的寄存器0,1位置为CRC write
            for index in range(2, rbt_cfg_content_after_len):
                item = self.rbt_cfg_content_after[index]
                if item.opcode == -1 or item.opcode.value != 2:
                    # 不参与运算
                    continue
                else:
                    # 参与运算
                    words_len = item.get_data_len()
                    for index in range(1, words_len):
                        if item.get_data_from_index(0) == CRC_RBT:
                            crc_end_flag = True
                            break
                        # 计算crc
                        # 拿到cmd本身
                        cmd_word = item.get_data_from_index(0) # RBT
                        # 拿到当前cmd下的word
                        cur_word = item.get_data_from_index(index) # RBT
                        
                        crc_data_in = self.cfg_obj.make_len_37_crc_data_in(cur_word, cmd_word, "str")
                        print(crc_data_in)
                        self.crc_02 = self.icap_crc(crc_data_in, self.crc_02)
                if crc_end_flag:
                    break
            print(self.crc_02) # 11100011101011010111111010100101 E3AD7EA5
            # ============== 第二段 =====================
            
            # 设置crc
            first_flag = True
            for i in range(rbt_cfg_content_after_len):
                if self.rbt_cfg_content_after[i].cmd_name == "CRC":
                    if first_flag:
                        # 第一个
                        self.rbt_cfg_content_after[i].set_data_to_index(1, self.crc_01)
                        first_flag = False
                    else:
                        # 第二个
                        self.rbt_cfg_content_after[i].set_data_to_index(1, self.crc_02)
            
        elif self.file_type == ".bit" or self.file_type == ".bin":
            # ============== 第一段 =====================
            crc_start_flag = False
            # 1. 拿到数据帧前的寄存器，确定RCRC位置
            for item in self.bit_cfg_content_pre:
                if item.opcode == -1 or item.opcode.value != 2:
                    # 不参与运算
                    continue
                else:
                    # 参与运算
                    words_len = item.get_data_len()
                    for index in range(1, words_len):
                        if item.get_data_from_index(0) == CMD_RCRC_01_BIT and item.get_data_from_index(1) == CMD_RCRC_02_BIT:
                            # 从这里开始，后面的寄存器参与运算
                            crc_start_flag = True
                            continue
                        if crc_start_flag:
                            # 计算crc
                            # 拿到cmd本身
                            cmd_word = item.get_data_from_index(0) # 字节
                            # 拿到当前cmd下的word
                            cur_word = item.get_data_from_index(index) # 字节
                            
                            crc_data_in = self.cfg_obj.make_len_37_crc_data_in(cur_word, cmd_word, "byte")
                            self.crc_01 = self.icap_crc(crc_data_in, self.crc_01)
            # 00010010000111000110100110000001                
            for word in self.bit_data_content:
                # 计算crc
                crc_data_in = self.cfg_obj.make_len_37_crc_data_in(word, FDRI_BIT, "byte")
                self.crc_01 = self.icap_crc(crc_data_in, self.crc_01)
                            
            print(self.crc_01) # 01111100100101011110011001111001 7C95E679
                       
            # ============== 第一段 =====================
            
            
            # ============== 第二段 =====================
            crc_end_flag = False
            bit_cfg_content_after_len = len(self.bit_cfg_content_after)
            # 这里从索引2开始，因为数据帧后的寄存器0,1位置为CRC write
            for index in range(2, bit_cfg_content_after_len):
                item = self.bit_cfg_content_after[index]
                if item.opcode == -1 or item.opcode.value != 2:
                    # 不参与运算
                    continue
                else:
                    # 参与运算
                    words_len = item.get_data_len()
                    for index in range(1, words_len):
                        if item.get_data_from_index(0) == CRC_BIT:
                            crc_end_flag = True
                            break
                        # 计算crc
                        # 拿到cmd本身
                        cmd_word = item.get_data_from_index(0) # 字节
                        # 拿到当前cmd下的word
                        cur_word = item.get_data_from_index(index) # 字节
                        
                        crc_data_in = self.cfg_obj.make_len_37_crc_data_in(cur_word, cmd_word, "byte")
                        print(crc_data_in)
                        self.crc_02 = self.icap_crc(crc_data_in, self.crc_02)
                if crc_end_flag:
                    break
            print(self.crc_02) # 11100011101011010111111010100101 E3AD7EA5
            # ============== 第二段 =====================
            
            # 设置crc
            first_flag = True
            for i in range(bit_cfg_content_after_len):
                if self.bit_cfg_content_after[i].cmd_name == "CRC":
                    if first_flag:
                        # 第一个
                        self.bit_cfg_content_after[i].set_data_to_index(1, self.crc_01)
                        first_flag = False
                    else:
                        # 第二个
                        self.bit_cfg_content_after[i].set_data_to_index(1, self.crc_02)
        # 更新crc
                    
    # 迭代crc
    def icap_crc(self, crc_data_in, crc):
        # addr 寄存器地址，整型
        # data 32位数据，整型
        # crc  32位字符串
        crc_data_new = [0] * 32  # 初始化长度为 32 的列表
        # 初始化长度为 32 的列表，用来存储crc的当前值
        # 将整数 crc 转换为 32 位的二进制字符串
        crc_int = int(crc, 2)  # 将二进制字符串转换为整数
        crc_bin_string = f'{crc_int:032b}'  # 将整数转换为 32 位二进制字符串
        crc_data_now = [int(bit) for bit in crc_bin_string]  
        crc_data_new[0] =   (crc_data_in[0]^crc_data_in[10]^crc_data_in[11]^crc_data_in[13]^crc_data_in[15]^crc_data_in[18]^crc_data_in[19]^crc_data_in[1]^crc_data_in[20]^crc_data_in[24]^crc_data_in[27]^crc_data_in[28]^crc_data_in[29]^crc_data_in[30]^crc_data_in[31]^crc_data_in[32]^crc_data_in[36]^crc_data_in[5]^crc_data_in[6]^crc_data_in[8]^crc_data_in[9]^crc_data_now[0]^crc_data_now[11]^crc_data_now[12]^crc_data_now[13]^crc_data_now[16]^crc_data_now[18]^crc_data_now[1]^crc_data_now[20]^crc_data_now[21]^crc_data_now[22]^crc_data_now[23]^crc_data_now[25]^crc_data_now[26]^crc_data_now[2]^crc_data_now[30]^crc_data_now[31]^crc_data_now[3]^crc_data_now[4]^crc_data_now[7]);
        crc_data_new[1] =   (crc_data_in[0]^crc_data_in[10]^crc_data_in[12]^crc_data_in[14]^crc_data_in[17]^crc_data_in[18]^crc_data_in[19]^crc_data_in[23]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[29]^crc_data_in[30]^crc_data_in[31]^crc_data_in[35]^crc_data_in[4]^crc_data_in[5]^crc_data_in[7]^crc_data_in[8]^crc_data_in[9]^crc_data_now[0]^crc_data_now[12]^crc_data_now[13]^crc_data_now[14]^crc_data_now[17]^crc_data_now[19]^crc_data_now[1]^crc_data_now[21]^crc_data_now[22]^crc_data_now[23]^crc_data_now[24]^crc_data_now[26]^crc_data_now[27]^crc_data_now[2]^crc_data_now[31]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[8]);
        crc_data_new[2] =   (crc_data_in[11]^crc_data_in[13]^crc_data_in[16]^crc_data_in[17]^crc_data_in[18]^crc_data_in[22]^crc_data_in[25]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[29]^crc_data_in[30]^crc_data_in[34]^crc_data_in[3]^crc_data_in[4]^crc_data_in[6]^crc_data_in[7]^crc_data_in[8]^crc_data_in[9]^crc_data_now[13]^crc_data_now[14]^crc_data_now[15]^crc_data_now[18]^crc_data_now[1]^crc_data_now[20]^crc_data_now[22]^crc_data_now[23]^crc_data_now[24]^crc_data_now[25]^crc_data_now[27]^crc_data_now[28]^crc_data_now[2]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[6]^crc_data_now[9]);
        crc_data_new[3] =   (crc_data_in[10]^crc_data_in[12]^crc_data_in[15]^crc_data_in[16]^crc_data_in[17]^crc_data_in[21]^crc_data_in[24]^crc_data_in[25]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[29]^crc_data_in[2]^crc_data_in[33]^crc_data_in[3]^crc_data_in[5]^crc_data_in[6]^crc_data_in[7]^crc_data_in[8]^crc_data_now[10]^crc_data_now[14]^crc_data_now[15]^crc_data_now[16]^crc_data_now[19]^crc_data_now[21]^crc_data_now[23]^crc_data_now[24]^crc_data_now[25]^crc_data_now[26]^crc_data_now[28]^crc_data_now[29]^crc_data_now[2]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[6]^crc_data_now[7]);
        crc_data_new[4] =   (crc_data_in[11]^crc_data_in[14]^crc_data_in[15]^crc_data_in[16]^crc_data_in[1]^crc_data_in[20]^crc_data_in[23]^crc_data_in[24]^crc_data_in[25]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[2]^crc_data_in[32]^crc_data_in[4]^crc_data_in[5]^crc_data_in[6]^crc_data_in[7]^crc_data_in[9]^crc_data_now[11]^crc_data_now[15]^crc_data_now[16]^crc_data_now[17]^crc_data_now[20]^crc_data_now[22]^crc_data_now[24]^crc_data_now[25]^crc_data_now[26]^crc_data_now[27]^crc_data_now[29]^crc_data_now[30]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[6]^crc_data_now[7]^crc_data_now[8]);
        crc_data_new[5] =   (crc_data_in[0]^crc_data_in[10]^crc_data_in[13]^crc_data_in[14]^crc_data_in[15]^crc_data_in[19]^crc_data_in[1]^crc_data_in[22]^crc_data_in[23]^crc_data_in[24]^crc_data_in[25]^crc_data_in[26]^crc_data_in[27]^crc_data_in[31]^crc_data_in[3]^crc_data_in[4]^crc_data_in[5]^crc_data_in[6]^crc_data_in[8]^crc_data_now[0]^crc_data_now[12]^crc_data_now[16]^crc_data_now[17]^crc_data_now[18]^crc_data_now[21]^crc_data_now[23]^crc_data_now[25]^crc_data_now[26]^crc_data_now[27]^crc_data_now[28]^crc_data_now[30]^crc_data_now[31]^crc_data_now[4]^crc_data_now[5]^crc_data_now[6]^crc_data_now[7]^crc_data_now[8]^crc_data_now[9]);
        crc_data_new[6] =   (crc_data_in[10]^crc_data_in[11]^crc_data_in[12]^crc_data_in[14]^crc_data_in[15]^crc_data_in[19]^crc_data_in[1]^crc_data_in[20]^crc_data_in[21]^crc_data_in[22]^crc_data_in[23]^crc_data_in[25]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[29]^crc_data_in[2]^crc_data_in[31]^crc_data_in[32]^crc_data_in[36]^crc_data_in[3]^crc_data_in[4]^crc_data_in[6]^crc_data_in[7]^crc_data_in[8]^crc_data_now[0]^crc_data_now[10]^crc_data_now[11]^crc_data_now[12]^crc_data_now[16]^crc_data_now[17]^crc_data_now[19]^crc_data_now[20]^crc_data_now[21]^crc_data_now[23]^crc_data_now[24]^crc_data_now[25]^crc_data_now[27]^crc_data_now[28]^crc_data_now[29]^crc_data_now[2]^crc_data_now[30]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[6]^crc_data_now[8]^crc_data_now[9]);
        crc_data_new[7] =   (crc_data_in[0]^crc_data_in[10]^crc_data_in[11]^crc_data_in[13]^crc_data_in[14]^crc_data_in[18]^crc_data_in[19]^crc_data_in[1]^crc_data_in[20]^crc_data_in[21]^crc_data_in[22]^crc_data_in[24]^crc_data_in[25]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[2]^crc_data_in[30]^crc_data_in[31]^crc_data_in[35]^crc_data_in[3]^crc_data_in[5]^crc_data_in[6]^crc_data_in[7]^crc_data_in[9]^crc_data_now[0]^crc_data_now[10]^crc_data_now[11]^crc_data_now[12]^crc_data_now[13]^crc_data_now[17]^crc_data_now[18]^crc_data_now[1]^crc_data_now[20]^crc_data_now[21]^crc_data_now[22]^crc_data_now[24]^crc_data_now[25]^crc_data_now[26]^crc_data_now[28]^crc_data_now[29]^crc_data_now[30]^crc_data_now[31]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[6]^crc_data_now[7]^crc_data_now[9]);
        crc_data_new[8] =   (crc_data_in[11]^crc_data_in[12]^crc_data_in[15]^crc_data_in[17]^crc_data_in[21]^crc_data_in[23]^crc_data_in[25]^crc_data_in[26]^crc_data_in[28]^crc_data_in[2]^crc_data_in[31]^crc_data_in[32]^crc_data_in[34]^crc_data_in[36]^crc_data_in[4]^crc_data_now[0]^crc_data_now[10]^crc_data_now[14]^crc_data_now[16]^crc_data_now[19]^crc_data_now[20]^crc_data_now[27]^crc_data_now[29]^crc_data_now[3]^crc_data_now[5]^crc_data_now[6]^crc_data_now[8]);
        crc_data_new[9] =   (crc_data_in[0]^crc_data_in[13]^crc_data_in[14]^crc_data_in[15]^crc_data_in[16]^crc_data_in[18]^crc_data_in[19]^crc_data_in[22]^crc_data_in[25]^crc_data_in[28]^crc_data_in[29]^crc_data_in[32]^crc_data_in[33]^crc_data_in[35]^crc_data_in[36]^crc_data_in[3]^crc_data_in[5]^crc_data_in[6]^crc_data_in[8]^crc_data_in[9]^crc_data_now[12]^crc_data_now[13]^crc_data_now[15]^crc_data_now[16]^crc_data_now[17]^crc_data_now[18]^crc_data_now[22]^crc_data_now[23]^crc_data_now[25]^crc_data_now[26]^crc_data_now[28]^crc_data_now[2]^crc_data_now[31]^crc_data_now[3]^crc_data_now[6]^crc_data_now[9]);
        crc_data_new[10] =  (crc_data_in[0]^crc_data_in[10]^crc_data_in[11]^crc_data_in[12]^crc_data_in[14]^crc_data_in[17]^crc_data_in[19]^crc_data_in[1]^crc_data_in[20]^crc_data_in[21]^crc_data_in[29]^crc_data_in[2]^crc_data_in[30]^crc_data_in[34]^crc_data_in[35]^crc_data_in[36]^crc_data_in[4]^crc_data_in[6]^crc_data_in[7]^crc_data_in[9]^crc_data_now[10]^crc_data_now[11]^crc_data_now[12]^crc_data_now[14]^crc_data_now[17]^crc_data_now[19]^crc_data_now[1]^crc_data_now[20]^crc_data_now[21]^crc_data_now[22]^crc_data_now[24]^crc_data_now[25]^crc_data_now[27]^crc_data_now[29]^crc_data_now[2]^crc_data_now[30]^crc_data_now[31]);
        crc_data_new[11] =  (crc_data_in[15]^crc_data_in[16]^crc_data_in[24]^crc_data_in[27]^crc_data_in[30]^crc_data_in[31]^crc_data_in[32]^crc_data_in[33]^crc_data_in[34]^crc_data_in[35]^crc_data_in[36]^crc_data_in[3]^crc_data_now[0]^crc_data_now[15]^crc_data_now[16]^crc_data_now[1]^crc_data_now[28]^crc_data_now[4]^crc_data_now[7]);
        crc_data_new[12] =  (crc_data_in[14]^crc_data_in[15]^crc_data_in[23]^crc_data_in[26]^crc_data_in[29]^crc_data_in[2]^crc_data_in[30]^crc_data_in[31]^crc_data_in[32]^crc_data_in[33]^crc_data_in[34]^crc_data_in[35]^crc_data_now[0]^crc_data_now[16]^crc_data_now[17]^crc_data_now[1]^crc_data_now[29]^crc_data_now[2]^crc_data_now[5]^crc_data_now[8]);
        crc_data_new[13] =  (crc_data_in[0]^crc_data_in[10]^crc_data_in[11]^crc_data_in[14]^crc_data_in[15]^crc_data_in[18]^crc_data_in[19]^crc_data_in[20]^crc_data_in[22]^crc_data_in[24]^crc_data_in[25]^crc_data_in[27]^crc_data_in[33]^crc_data_in[34]^crc_data_in[36]^crc_data_in[5]^crc_data_in[6]^crc_data_in[8]^crc_data_in[9]^crc_data_now[11]^crc_data_now[12]^crc_data_now[13]^crc_data_now[16]^crc_data_now[17]^crc_data_now[20]^crc_data_now[21]^crc_data_now[22]^crc_data_now[23]^crc_data_now[25]^crc_data_now[26]^crc_data_now[31]^crc_data_now[4]^crc_data_now[6]^crc_data_now[7]^crc_data_now[9]);
        crc_data_new[14] =  (crc_data_in[0]^crc_data_in[11]^crc_data_in[14]^crc_data_in[15]^crc_data_in[17]^crc_data_in[1]^crc_data_in[20]^crc_data_in[21]^crc_data_in[23]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[29]^crc_data_in[30]^crc_data_in[31]^crc_data_in[33]^crc_data_in[35]^crc_data_in[36]^crc_data_in[4]^crc_data_in[6]^crc_data_in[7]^crc_data_now[0]^crc_data_now[10]^crc_data_now[11]^crc_data_now[14]^crc_data_now[16]^crc_data_now[17]^crc_data_now[1]^crc_data_now[20]^crc_data_now[24]^crc_data_now[25]^crc_data_now[27]^crc_data_now[2]^crc_data_now[30]^crc_data_now[31]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[8]);
        crc_data_new[15] =  (crc_data_in[0]^crc_data_in[10]^crc_data_in[13]^crc_data_in[14]^crc_data_in[16]^crc_data_in[19]^crc_data_in[20]^crc_data_in[22]^crc_data_in[25]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[29]^crc_data_in[30]^crc_data_in[32]^crc_data_in[34]^crc_data_in[35]^crc_data_in[3]^crc_data_in[5]^crc_data_in[6]^crc_data_now[11]^crc_data_now[12]^crc_data_now[15]^crc_data_now[17]^crc_data_now[18]^crc_data_now[1]^crc_data_now[21]^crc_data_now[25]^crc_data_now[26]^crc_data_now[28]^crc_data_now[2]^crc_data_now[31]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[6]^crc_data_now[9]);
        crc_data_new[16] =  (crc_data_in[12]^crc_data_in[13]^crc_data_in[15]^crc_data_in[18]^crc_data_in[19]^crc_data_in[21]^crc_data_in[24]^crc_data_in[25]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[29]^crc_data_in[2]^crc_data_in[31]^crc_data_in[33]^crc_data_in[34]^crc_data_in[4]^crc_data_in[5]^crc_data_in[9]^crc_data_now[0]^crc_data_now[10]^crc_data_now[12]^crc_data_now[13]^crc_data_now[16]^crc_data_now[18]^crc_data_now[19]^crc_data_now[22]^crc_data_now[26]^crc_data_now[27]^crc_data_now[29]^crc_data_now[2]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[6]^crc_data_now[7]);
        crc_data_new[17] =  (crc_data_in[11]^crc_data_in[12]^crc_data_in[14]^crc_data_in[17]^crc_data_in[18]^crc_data_in[1]^crc_data_in[20]^crc_data_in[23]^crc_data_in[24]^crc_data_in[25]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[30]^crc_data_in[32]^crc_data_in[33]^crc_data_in[3]^crc_data_in[4]^crc_data_in[8]^crc_data_now[11]^crc_data_now[13]^crc_data_now[14]^crc_data_now[17]^crc_data_now[19]^crc_data_now[1]^crc_data_now[20]^crc_data_now[23]^crc_data_now[27]^crc_data_now[28]^crc_data_now[30]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[6]^crc_data_now[7]^crc_data_now[8]);
        crc_data_new[18] =  (crc_data_in[15]^crc_data_in[16]^crc_data_in[17]^crc_data_in[18]^crc_data_in[1]^crc_data_in[20]^crc_data_in[22]^crc_data_in[23]^crc_data_in[25]^crc_data_in[26]^crc_data_in[28]^crc_data_in[2]^crc_data_in[30]^crc_data_in[36]^crc_data_in[3]^crc_data_in[5]^crc_data_in[6]^crc_data_in[7]^crc_data_in[8]^crc_data_in[9]^crc_data_now[11]^crc_data_now[13]^crc_data_now[14]^crc_data_now[15]^crc_data_now[16]^crc_data_now[1]^crc_data_now[22]^crc_data_now[23]^crc_data_now[24]^crc_data_now[25]^crc_data_now[26]^crc_data_now[28]^crc_data_now[29]^crc_data_now[30]^crc_data_now[3]^crc_data_now[5]^crc_data_now[6]^crc_data_now[8]^crc_data_now[9]);
        crc_data_new[19] =  (crc_data_in[10]^crc_data_in[11]^crc_data_in[13]^crc_data_in[14]^crc_data_in[16]^crc_data_in[17]^crc_data_in[18]^crc_data_in[20]^crc_data_in[21]^crc_data_in[22]^crc_data_in[25]^crc_data_in[28]^crc_data_in[2]^crc_data_in[30]^crc_data_in[31]^crc_data_in[32]^crc_data_in[35]^crc_data_in[36]^crc_data_in[4]^crc_data_in[7]^crc_data_in[9]^crc_data_now[0]^crc_data_now[10]^crc_data_now[11]^crc_data_now[13]^crc_data_now[14]^crc_data_now[15]^crc_data_now[17]^crc_data_now[18]^crc_data_now[1]^crc_data_now[20]^crc_data_now[21]^crc_data_now[22]^crc_data_now[24]^crc_data_now[27]^crc_data_now[29]^crc_data_now[3]^crc_data_now[6]^crc_data_now[9]);
        crc_data_new[20] =  (crc_data_in[0]^crc_data_in[11]^crc_data_in[12]^crc_data_in[16]^crc_data_in[17]^crc_data_in[18]^crc_data_in[21]^crc_data_in[28]^crc_data_in[32]^crc_data_in[34]^crc_data_in[35]^crc_data_in[36]^crc_data_in[3]^crc_data_in[5]^crc_data_now[10]^crc_data_now[13]^crc_data_now[14]^crc_data_now[15]^crc_data_now[19]^crc_data_now[20]^crc_data_now[26]^crc_data_now[28]^crc_data_now[31]^crc_data_now[3]);
        crc_data_new[21] =  (crc_data_in[10]^crc_data_in[11]^crc_data_in[15]^crc_data_in[16]^crc_data_in[17]^crc_data_in[20]^crc_data_in[27]^crc_data_in[2]^crc_data_in[31]^crc_data_in[33]^crc_data_in[34]^crc_data_in[35]^crc_data_in[4]^crc_data_now[0]^crc_data_now[11]^crc_data_now[14]^crc_data_now[15]^crc_data_now[16]^crc_data_now[20]^crc_data_now[21]^crc_data_now[27]^crc_data_now[29]^crc_data_now[4]);
        crc_data_new[22] =  (crc_data_in[0]^crc_data_in[11]^crc_data_in[13]^crc_data_in[14]^crc_data_in[16]^crc_data_in[18]^crc_data_in[20]^crc_data_in[24]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[29]^crc_data_in[31]^crc_data_in[33]^crc_data_in[34]^crc_data_in[36]^crc_data_in[3]^crc_data_in[5]^crc_data_in[6]^crc_data_in[8]^crc_data_now[0]^crc_data_now[11]^crc_data_now[13]^crc_data_now[15]^crc_data_now[17]^crc_data_now[18]^crc_data_now[20]^crc_data_now[23]^crc_data_now[25]^crc_data_now[26]^crc_data_now[28]^crc_data_now[2]^crc_data_now[31]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[7]);
        crc_data_new[23] =  (crc_data_in[0]^crc_data_in[11]^crc_data_in[12]^crc_data_in[17]^crc_data_in[18]^crc_data_in[1]^crc_data_in[20]^crc_data_in[23]^crc_data_in[24]^crc_data_in[25]^crc_data_in[26]^crc_data_in[29]^crc_data_in[2]^crc_data_in[31]^crc_data_in[33]^crc_data_in[35]^crc_data_in[36]^crc_data_in[4]^crc_data_in[6]^crc_data_in[7]^crc_data_in[8]^crc_data_in[9]^crc_data_now[0]^crc_data_now[11]^crc_data_now[13]^crc_data_now[14]^crc_data_now[19]^crc_data_now[20]^crc_data_now[22]^crc_data_now[23]^crc_data_now[24]^crc_data_now[25]^crc_data_now[27]^crc_data_now[29]^crc_data_now[2]^crc_data_now[30]^crc_data_now[31]^crc_data_now[5]^crc_data_now[6]^crc_data_now[7]^crc_data_now[8]);
        crc_data_new[24] =  (crc_data_in[0]^crc_data_in[10]^crc_data_in[11]^crc_data_in[16]^crc_data_in[17]^crc_data_in[19]^crc_data_in[1]^crc_data_in[22]^crc_data_in[23]^crc_data_in[24]^crc_data_in[25]^crc_data_in[28]^crc_data_in[30]^crc_data_in[32]^crc_data_in[34]^crc_data_in[35]^crc_data_in[3]^crc_data_in[5]^crc_data_in[6]^crc_data_in[7]^crc_data_in[8]^crc_data_now[12]^crc_data_now[14]^crc_data_now[15]^crc_data_now[1]^crc_data_now[20]^crc_data_now[21]^crc_data_now[23]^crc_data_now[24]^crc_data_now[25]^crc_data_now[26]^crc_data_now[28]^crc_data_now[30]^crc_data_now[31]^crc_data_now[3]^crc_data_now[6]^crc_data_now[7]^crc_data_now[8]^crc_data_now[9]);
        crc_data_new[25] =  (crc_data_in[11]^crc_data_in[13]^crc_data_in[16]^crc_data_in[19]^crc_data_in[1]^crc_data_in[20]^crc_data_in[21]^crc_data_in[22]^crc_data_in[23]^crc_data_in[28]^crc_data_in[2]^crc_data_in[30]^crc_data_in[32]^crc_data_in[33]^crc_data_in[34]^crc_data_in[36]^crc_data_in[4]^crc_data_in[7]^crc_data_in[8]^crc_data_now[10]^crc_data_now[11]^crc_data_now[12]^crc_data_now[15]^crc_data_now[18]^crc_data_now[1]^crc_data_now[20]^crc_data_now[23]^crc_data_now[24]^crc_data_now[27]^crc_data_now[29]^crc_data_now[30]^crc_data_now[3]^crc_data_now[8]^crc_data_now[9]);
        crc_data_new[26] =  (crc_data_in[11]^crc_data_in[12]^crc_data_in[13]^crc_data_in[21]^crc_data_in[22]^crc_data_in[24]^crc_data_in[28]^crc_data_in[30]^crc_data_in[33]^crc_data_in[35]^crc_data_in[36]^crc_data_in[3]^crc_data_in[5]^crc_data_in[7]^crc_data_in[8]^crc_data_in[9]^crc_data_now[10]^crc_data_now[18]^crc_data_now[19]^crc_data_now[1]^crc_data_now[20]^crc_data_now[22]^crc_data_now[23]^crc_data_now[24]^crc_data_now[26]^crc_data_now[28]^crc_data_now[3]^crc_data_now[7]^crc_data_now[9]);
        crc_data_new[27] =  (crc_data_in[0]^crc_data_in[12]^crc_data_in[13]^crc_data_in[15]^crc_data_in[18]^crc_data_in[19]^crc_data_in[1]^crc_data_in[21]^crc_data_in[23]^crc_data_in[24]^crc_data_in[28]^crc_data_in[2]^crc_data_in[30]^crc_data_in[31]^crc_data_in[34]^crc_data_in[35]^crc_data_in[36]^crc_data_in[4]^crc_data_in[5]^crc_data_in[7]^crc_data_in[9]^crc_data_now[0]^crc_data_now[10]^crc_data_now[12]^crc_data_now[13]^crc_data_now[16]^crc_data_now[18]^crc_data_now[19]^crc_data_now[1]^crc_data_now[22]^crc_data_now[24]^crc_data_now[26]^crc_data_now[27]^crc_data_now[29]^crc_data_now[30]^crc_data_now[31]^crc_data_now[3]^crc_data_now[7]^crc_data_now[8]);
        crc_data_new[28] =  (crc_data_in[10]^crc_data_in[12]^crc_data_in[13]^crc_data_in[14]^crc_data_in[15]^crc_data_in[17]^crc_data_in[19]^crc_data_in[22]^crc_data_in[23]^crc_data_in[24]^crc_data_in[28]^crc_data_in[31]^crc_data_in[32]^crc_data_in[33]^crc_data_in[34]^crc_data_in[35]^crc_data_in[36]^crc_data_in[3]^crc_data_in[4]^crc_data_in[5]^crc_data_in[9]^crc_data_now[0]^crc_data_now[12]^crc_data_now[14]^crc_data_now[16]^crc_data_now[17]^crc_data_now[18]^crc_data_now[19]^crc_data_now[21]^crc_data_now[22]^crc_data_now[26]^crc_data_now[27]^crc_data_now[28]^crc_data_now[3]^crc_data_now[7]^crc_data_now[8]^crc_data_now[9]);
        crc_data_new[29] =  (crc_data_in[11]^crc_data_in[12]^crc_data_in[13]^crc_data_in[14]^crc_data_in[16]^crc_data_in[18]^crc_data_in[21]^crc_data_in[22]^crc_data_in[23]^crc_data_in[27]^crc_data_in[2]^crc_data_in[30]^crc_data_in[31]^crc_data_in[32]^crc_data_in[33]^crc_data_in[34]^crc_data_in[35]^crc_data_in[3]^crc_data_in[4]^crc_data_in[8]^crc_data_in[9]^crc_data_now[0]^crc_data_now[10]^crc_data_now[13]^crc_data_now[15]^crc_data_now[17]^crc_data_now[18]^crc_data_now[19]^crc_data_now[1]^crc_data_now[20]^crc_data_now[22]^crc_data_now[23]^crc_data_now[27]^crc_data_now[28]^crc_data_now[29]^crc_data_now[4]^crc_data_now[8]^crc_data_now[9]);
        crc_data_new[30] =  (crc_data_in[10]^crc_data_in[11]^crc_data_in[12]^crc_data_in[13]^crc_data_in[15]^crc_data_in[17]^crc_data_in[1]^crc_data_in[20]^crc_data_in[21]^crc_data_in[22]^crc_data_in[26]^crc_data_in[29]^crc_data_in[2]^crc_data_in[30]^crc_data_in[31]^crc_data_in[32]^crc_data_in[33]^crc_data_in[34]^crc_data_in[3]^crc_data_in[7]^crc_data_in[8]^crc_data_now[0]^crc_data_now[10]^crc_data_now[11]^crc_data_now[14]^crc_data_now[16]^crc_data_now[18]^crc_data_now[19]^crc_data_now[1]^crc_data_now[20]^crc_data_now[21]^crc_data_now[23]^crc_data_now[24]^crc_data_now[28]^crc_data_now[29]^crc_data_now[2]^crc_data_now[30]^crc_data_now[5]^crc_data_now[9]);
        crc_data_new[31] =  (crc_data_in[0]^crc_data_in[10]^crc_data_in[11]^crc_data_in[12]^crc_data_in[14]^crc_data_in[16]^crc_data_in[19]^crc_data_in[1]^crc_data_in[20]^crc_data_in[21]^crc_data_in[25]^crc_data_in[28]^crc_data_in[29]^crc_data_in[2]^crc_data_in[30]^crc_data_in[31]^crc_data_in[32]^crc_data_in[33]^crc_data_in[6]^crc_data_in[7]^crc_data_in[9]^crc_data_now[0]^crc_data_now[10]^crc_data_now[11]^crc_data_now[12]^crc_data_now[15]^crc_data_now[17]^crc_data_now[19]^crc_data_now[1]^crc_data_now[20]^crc_data_now[21]^crc_data_now[22]^crc_data_now[24]^crc_data_now[25]^crc_data_now[29]^crc_data_now[2]^crc_data_now[30]^crc_data_now[31]^crc_data_now[3]^crc_data_now[6]);
        crc = ''.join(str(num) for num in crc_data_new)
        return crc
    
    
def main():
    parser = argparse.ArgumentParser(description="Auto Process")

    # Add optional arguments
    parser.add_argument('--rbt_folder', type=str, help="Input .rbt folder path")
    parser.add_argument('--file', type=str, help="Only process this specific file")
    parser.add_argument('--file_suffix', type=str, default=FILE_ENDWITH, help="Suffix to add to the new .rbt file (default: _HybrdChip)")
    parser.add_argument('--PCIE', action='store_true', help="Enable PCIE processing (Default: False)")
    parser.add_argument('--GTP', action='store_true', help="Enable GTP processing (Default: False)")
    parser.add_argument('--CRC', action='store_true', help="Enable CRC (Default: False)")
    parser.add_argument('--TRIM', action='store_true', help="Enable TRIM processing (Default: False)")

    # 解析参数
    args = parser.parse_args()

    # Display help if no arguments are provided
    if not any(vars(args).values()):
        parser.print_help()
        return

    logging.info(f"Parameters:")
    logging.info(f"\trbt_folder: {args.rbt_folder}")
    logging.info(f"\trbt_file: {args.file}")
    logging.info(f"\tfile_suffix: {args.file_suffix}")
    logging.info(f"\tPCIE: {args.PCIE}")
    logging.info(f"\tGTP: {args.GTP}")
    logging.info(f"\tCRC: {args.CRC}")
    logging.info(f"\tTRIM: {args.TRIM}\n")
    
    bit_parser = BitstreamParser(args.file, args.CRC)
    
    if args.GTP:
        # 处理GTP
        for item in GTP_CONFIG:
            bit_parser.set_data_with_frame_word_bit(item["data"], item["frame"],  item["word"], item["bit"])

    if args.PCIE:
        # 处理PCIE
        for index in PCIE_CHECK:
            check_group = PCIE_CHECK[index]
            cur_group_have_value = False
            for item in check_group:
                bit = bit_parser.get_data_with_frame_word_bit(item["frame"],  item["word"], item["bit"])
                if bit == "1":
                    # 有任意一个为1，这组就无法修改
                    cur_group_have_value = True
                    break
            if cur_group_have_value:
                # 下一组
                continue
            else:
                # 如果这一组全为0，则这组可修改
                config_group = PCIE_CONFIG[index]
                for item in config_group:
                    bit_parser.set_data_with_frame_word_bit(item["data"], item["frame"],  item["word"], item["bit"])
                break
        else:
            # 执行到此表示无法修改
            raise ValueError("规则无法适配")
    
    if args.CRC:
        # 计算CRC
        bit_parser.calculate_crc()
    else:
        # 关闭CRC
        bit_parser.disable_crc()
        
    if args.TRIM:
        bit_parser.set_trim()
            
    bit_parser.save_file(args.file_suffix)
if __name__ == "__main__":
    main()