import os 
import struct
import logging
import argparse
import enum

# logging.basicConfig(level=logging.WARNING)  # 正常模式
logging.basicConfig(level=logging.DEBUG)  # 调试模式

file_path = r"E:\CodeSpace_vscode\P_筛片脚本\xilinx_pcie_2_1_rport_7x_xilinx.bit"

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
        
    def get_type_2_packet_content(self, word):
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
        
        self.cfg_obj = ConfigurationPacket()
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
        self.bit_head_byte_content += self.read_bytes(2) # 标识
        self.bit_head_byte_content += self.read_bytes(11) # 内容
        start_index += 13
        # ========== 起始数据 ============
        
        # ========== 标识符A ============
        self.bit_head_byte_content += self.read_bytes(1) # 标识 b'\x61'
        cur_group_length = self.read_bytes(2)
        self.bit_head_byte_content += cur_group_length  # 内容 该组字节长度
        group_length = struct.unpack('>H', cur_group_length)[0]
        self.bit_head_byte_content += self.read_bytes(group_length) # 文件路径、Version、UserID
        start_index += 3
        end_index = start_index + group_length
        logging.debug(f"\tA content: {self.bit_head_byte_content[start_index:end_index].hex()}")
        show_ascii_content(self.bit_head_byte_content[start_index:end_index])
        start_index = end_index
        # ========== 标识符A ============
        
        # ========== 标识符B ============
        self.bit_head_byte_content += self.read_bytes(1) # 标识 b'\x62'
        cur_group_length = self.read_bytes(2)
        self.bit_head_byte_content += cur_group_length  # 内容 该组字节长度
        group_length = struct.unpack('>H', cur_group_length)[0]
        self.bit_head_byte_content += self.read_bytes(group_length) # part name
        start_index += 3
        end_index = start_index + group_length
        logging.debug(f"\tB content: {self.bit_head_byte_content[start_index:end_index].hex()}")
        show_ascii_content(self.bit_head_byte_content[start_index:end_index])
        start_index = end_index
        # ========== 标识符B ============
        
        # ========== 标识符C ============
        self.bit_head_byte_content += self.read_bytes(1) # 标识 b'\x63'
        cur_group_length = self.read_bytes(2)
        self.bit_head_byte_content += cur_group_length  # 内容 该组字节长度
        group_length = struct.unpack('>H', cur_group_length)[0]
        self.bit_head_byte_content += self.read_bytes(group_length) # 年/月/日
        start_index += 3
        end_index = start_index + group_length
        logging.debug(f"\tC content: {self.bit_head_byte_content[start_index:end_index].hex()}")
        show_ascii_content(self.bit_head_byte_content[start_index:end_index])
        start_index = end_index
        # ========== 标识符C ============

        # ========== 标识符D ============
        self.bit_head_byte_content += self.read_bytes(1) # 标识 b'\x64'
        cur_group_length = self.read_bytes(2)
        self.bit_head_byte_content += cur_group_length  # 内容 该组字节长度
        group_length = struct.unpack('>H', cur_group_length)[0]
        self.bit_head_byte_content += self.read_bytes(group_length) # 时:分:秒
        start_index += 3
        end_index = start_index + group_length
        logging.debug(f"\tD content: {self.bit_head_byte_content[start_index:end_index].hex()}")
        show_ascii_content(self.bit_head_byte_content[start_index:end_index])
        start_index = end_index
        # ========== 标识符D ============

        # ========== 标识符E ============
        self.bit_head_byte_content += self.read_bytes(1) # 标识 b'\x65'
        self.bit_head_byte_content += self.read_bytes(4) # 位流的总长度
        start_index += 1
        end_index = start_index + 4
        logging.debug(f"\tE content: {self.bit_head_byte_content[start_index:end_index].hex()}")
        show_number_content(self.bit_head_byte_content[start_index:end_index])
        start_index = end_index
        # ========== 标识符E ============
            
    # 解析位流，读取cfg内容
    def parse_cfg_content_pre(self) -> None: 
        while True:
            word = self.read_bytes(4)
            print(bytes_to_binary(word))
            if not word:
                break  # 到达文件末尾，停止读取
            if len(word) < 4:
                # 如果最后的 chunk 不足 4 个字节，输出提示
                logging.warning(f"Warning: Last chunk is less than 4 bytes: {word.hex()}")
            
            # 存入cfg中
            self.bit_cfg_content_pre.append(word)
            word_content = struct.unpack('>I', word)[0] # 转无符号整型
            
            if word_content == 0b11111111111111111111111111111111:
                # DUMMY
                continue
            elif word_content == 0b10101010100110010101010101100110:
                # SYNC WORD
                continue
            elif word_content == 0b00000000000000000000000010111011 or word_content == 0b00010001001000100000000001000100:
                # BUS WIDTH AUTO DETECT
                continue
            elif word_content == 0b00100000000000000000000000000000:
                # NOP
                continue
            
            content = self.cfg_obj.get_type_1_packet_content(word_content)
            # 读取到 FDRI 后，读取结束 30004000
            if content.get("header_type", -1) == 1 \
                and content.get("opcode", self.cfg_obj.OpCode.UNKNOWN) == self.cfg_obj.OpCode.WRITE \
                and content.get("address", self.cfg_obj.Address.UNKNOWN) == self.cfg_obj.Address.FDRI:
                    word = self.read_bytes(4)
                    self.bit_cfg_content_pre.append(word)
                    word_content = struct.unpack('>I', word)[0] # 转无符号整型
                    # 拿到 word_count，其单位是word，换成字节*4
                    self.word_count = self.cfg_obj.get_type_2_packet_content(word_content).get("word_count",0)
                    self.bit_data_content_byte_count = self.word_count * 4
                    break
               
    # 解析位流，读取cfg内容
    def parse_cfg_content_aft(self) -> None: 
        while True:
            word = self.read_bytes(4)
            if not word:
                break  # 到达文件末尾，停止读取
            if len(word) < 4:
                # 如果最后的 chunk 不足 4 个字节，输出提示
                logging.warning(f"Warning: Last chunk is less than 4 bytes: {word.hex()}")
            
            # 存入cfg中
            self.bit_cfg_content_after.append(word)
        
    def parse_data_content(self) -> None: 
        data_content = self.read_bytes(self.bit_data_content_byte_count)
        for i in range(0,self.bit_data_content_byte_count,4):
            self.bit_data_content.append(data_content[i:i+4])
    
    def read_bit_or_bin_file_and_parse(self, file_type: str) -> None:
        # ============================================ bit header ============================================
        if file_type == "bit":
            self.parse_head_content()
        # ============================================ bit header ============================================
        
        # ============================================ cfg content pre ============================================
        # 从 FFFFFFFF 开始
        self.parse_cfg_content_pre()
        # 到 30004000 XXXXXXXX 结束，其中 XXXXXXXX 的低27位标识接下来 data frame 的长度
        # self.word_count 为 接下来有多少个 word
        # self.bit_data_content_byte_count 为 接下来有多少个字节
        # 1个word为4字节，1字节为8位
        # ============================================ cfg content pre ============================================
                
        # ============================================ data frame ============================================
        # 从 FDRI data word 1 开始
        self.parse_data_content()
        # 到 FDRI data word XXXX 结束，其中 XXXX 指的是 parse_cfg_content_pre 解析出来的 self.word_count
        # ============================================ data frame ============================================
        
        # ============================================ cfg content after ============================================
        # 对于没有关闭CRC的位流，此处从 30000001 开始
        self.parse_cfg_content_aft()
        # 到 码流末尾 结束
        # ============================================ cfg content after ============================================
        
        # len(self.bit_cfg_content_pre) + len(self.bit_data_content) + len(self.bit_cfg_content_after) == 总word数量
        
        # len(self.bit_head_byte_content)) 头部信息字节数
        # len(self.bit_cfg_content_pre)) 数据帧之前的寄存器所占word数，*4为字节数
        # len(self.bit_data_content)) 数据帧所占word数，*4为字节数
        # len(self.bit_cfg_content_after)) 数据帧之后的寄存器所占word数，*4为字节数
        # 四个字节数相加为整段位流长度
        print(format(len(self.bit_head_byte_content), 'X'))
        print(format(len(self.bit_cfg_content_pre)*4, 'X'))
        print(format(len(self.bit_data_content)*4, 'X'))
        print(format(len(self.bit_cfg_content_after)*4, 'X'))
        print(len(self.bit_cfg_content_after)*4 + len(self.bit_data_content)*4 + len(self.bit_cfg_content_pre)*4 + len(self.bit_head_byte_content))
    
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
print(123)