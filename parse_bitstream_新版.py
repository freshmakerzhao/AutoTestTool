import os 
import struct
import logging
import argparse
import enum

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

    def get_type_1_packet_content(self, word):
        header_type = self.get_packet_type(word)
        opcode = self.OpCode((word >> 27) & 0x3)
        address = self.Address((word >> 13) & 0x1F)
        reserved = (word >> 11) & 0x3
        word_count = word & 0x7FF
        return {
                "header_type":header_type,
                "opcode":opcode,
                "address":address,
                "reserved":reserved,
                "word_count":word_count
            }
    
class BitstreamReader:
    def __init__(self, byte_content: bytes):
        """
        初始化 BitstreamReader

        参数:
            byte_content (bytes): 码流内容
        """
        # 全部内容
        self.byte_content = byte_content
        # 字节长度
        self.byte_content_len = len(byte_content)
        # 读取位置
        self.byte_content_cur_loc = 0
        
        # 存储头部信息，FF之前
        self.bit_head_content = b''
         # 存储头部配置信息
        self.bit_cfg_content_pre = []
        # 存储码流主体内容
        self.bit_data_content = []
        # 存储后续配置信息
        self.bit_cfg_content_after = []
        
        # 文件读取路径
        # self.file_path = file_path
        # # 文件类型
        # self.file_type = file_type
    
    def load_file(self, file_type: str) -> None:
        pass            
        
    # 解析位流，读取头部信息    
    def parse_head_content(self) -> None:
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
        self.bit_head_content += self.read_bytes(2) # 标识
        self.bit_head_content += self.read_bytes(11) # 内容
        start_index += 13
        # ========== 起始数据 ============
        
        # ========== 标识符A ============
        self.bit_head_content += self.read_bytes(1) # 标识 b'\x61'
        cur_group_length = self.read_bytes(2)
        self.bit_head_content += cur_group_length  # 内容 该组字节长度
        group_length = struct.unpack('>H', cur_group_length)[0]
        self.bit_head_content += self.read_bytes(group_length) # 文件路径、Version、UserID
        start_index += 3
        end_index = start_index + group_length
        logging.debug(f"\tA content: {self.bit_head_content[start_index:end_index].hex()}")
        show_ascii_content(self.bit_head_content[start_index:end_index])
        start_index = end_index
        # ========== 标识符A ============
        
        # ========== 标识符B ============
        self.bit_head_content += self.read_bytes(1) # 标识 b'\x62'
        cur_group_length = self.read_bytes(2)
        self.bit_head_content += cur_group_length  # 内容 该组字节长度
        group_length = struct.unpack('>H', cur_group_length)[0]
        self.bit_head_content += self.read_bytes(group_length) # part name
        start_index += 3
        end_index = start_index + group_length
        logging.debug(f"\tB content: {self.bit_head_content[start_index:end_index].hex()}")
        show_ascii_content(self.bit_head_content[start_index:end_index])
        start_index = end_index
        # ========== 标识符B ============
        
        # ========== 标识符C ============
        self.bit_head_content += self.read_bytes(1) # 标识 b'\x63'
        cur_group_length = self.read_bytes(2)
        self.bit_head_content += cur_group_length  # 内容 该组字节长度
        group_length = struct.unpack('>H', cur_group_length)[0]
        self.bit_head_content += self.read_bytes(group_length) # 年/月/日
        start_index += 3
        end_index = start_index + group_length
        logging.debug(f"\tC content: {self.bit_head_content[start_index:end_index].hex()}")
        show_ascii_content(self.bit_head_content[start_index:end_index])
        start_index = end_index
        # ========== 标识符C ============

        # ========== 标识符D ============
        self.bit_head_content += self.read_bytes(1) # 标识 b'\x64'
        cur_group_length = self.read_bytes(2)
        self.bit_head_content += cur_group_length  # 内容 该组字节长度
        group_length = struct.unpack('>H', cur_group_length)[0]
        self.bit_head_content += self.read_bytes(group_length) # 时:分:秒
        start_index += 3
        end_index = start_index + group_length
        logging.debug(f"\tD content: {self.bit_head_content[start_index:end_index].hex()}")
        show_ascii_content(self.bit_head_content[start_index:end_index])
        start_index = end_index
        # ========== 标识符D ============

        # ========== 标识符E ============
        self.bit_head_content += self.read_bytes(1) # 标识 b'\x65'
        self.bit_head_content += self.read_bytes(4) # 位流的总长度
        start_index += 1
        end_index = start_index + 4
        logging.debug(f"\tE content: {self.bit_head_content[start_index:end_index].hex()}")
        show_number_content(self.bit_head_content[start_index:end_index])
        start_index = end_index
        # ========== 标识符E ============
            
    # 解析位流，读取cfg内容
    def parse_cfg_content(self) -> None: 
        
        while True:
            word = self.read_bytes(4)
            if not word:
                break  # 到达文件末尾，停止读取
            if len(word) < 4:
                # 如果最后的 chunk 不足 4 个字节，输出提示
                logging.warning(f"Warning: Last chunk is less than 4 bytes: {word.hex()}")
            
            # 存入cfg中
            self.bit_cfg_content_pre.append(word)
            
            content = ConfigurationPacket.get_type_1_packet_content(word)
            if content.get("header_type", -1) == 1 \
                and content.get("opcode", ConfigurationPacket.OpCode.UNKNOWN) == ConfigurationPacket.OpCode.WRITE \
                and content.get("address", ConfigurationPacket.Address.UNKNOWN) == ConfigurationPacket.Address.FDRI:
        
        
        
                    
        # self.type = word >> 29 
        # self.opcode = self.OpCode((word >> 27) & 0x3)
        # if self.type == 1:
        #     # address拿到的参与crc的内容
        #     self.address = self.Address((word >> 13) & 0x1F)
        #     word_count = word & 0x7FF
        # elif self.type == 2:
        #     if packet is None:
        #         raise Exception(f'Type 2 packet require previous packet')
        #     if packet.type != 1:
        #         raise Exception(f'Type 2 packet require previous Type 1 packet')
        #     self.address = packet.address
        #     word_count = word & 0x07FFFFFF
            
        # header
        pass
        
    def read_bit_or_bin_file_and_parse(self, file_type: str) -> None:
        # ============================================ bit header ============================================
        if file_type == "bit":
            self.parse_head_content()
        # ============================================ bit header ============================================
        
        # ============================================ cfg content ============================================
        self.parse_cfg_content()
        # ============================================ cfg content ============================================
        
        
        # ============================================ data frame ============================================
        
        
        # ============================================ data frame ============================================
        
        # ========== 读取剩余内容 ============
        while True:
            chunk = self.read_bytes(4)
            if not chunk:
                break  # 到达文件末尾，停止读取
            if len(chunk) < 4:
                # 如果最后的 chunk 不足 4 个字节，输出提示
                logging.warning(f"Warning: Last chunk is less than 4 bytes: {chunk.hex()}")
            self.bit_data_content.append(chunk)
        # ========== 读取剩余内容 ============
    
    def read_bytes(self, read_length: int) -> bytes:
        """
        从当前位置读取指定长度的字节。

        参数:
            read_length (int): 要读取的字节长度。

        返回:
            bytes: 读取的字节数据。

        异常:
            ValueError: 如果读取操作超出内容范围。
        """
        # if self.byte_content_cur_loc + read_length > self.byte_content_len:
        #     error_msg = f"Attempted to read {read_length} bytes from position {self.byte_content_cur_loc}, " \
        #                 f"which exceeds the content length {self.byte_content_len}."
        #     logging.error(error_msg)
        #     raise ValueError(error_msg)
        
        if self.byte_content_cur_loc + read_length > self.byte_content_len:
            return b''
        data = self.byte_content[self.byte_content_cur_loc : self.byte_content_cur_loc + read_length]
        self.byte_content_cur_loc += read_length
        return data
    
    
INPUT_FILE_PATH = r"E:\workspace\parse_bitstream\parse_bitstream\data\system_wrapper_1_原版.bit"
# 打开文件，以二进制模式('rb')读取
with open(INPUT_FILE_PATH, 'rb') as file:
    # 读取整个文件内容
    byte_content = file.read()
reader = BitstreamReader(byte_content)
reader.read_bit_or_bin_file_and_parse("bit")