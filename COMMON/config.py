import enum
import COMMON.utils as utils
import struct
from dataclasses import dataclass
@dataclass(frozen=True)
class PacketContent:
    binstr: str
    @property
    def byte(self):
        return int(self.binstr, 2).to_bytes(4, 'big')

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
        UNKNOWN_23 = 23
        CTL1 = 24
        UNKNOWN_25 = 25
        UNKNOWN_26 = 26
        TRIM = 27
        RHBD = 28
        UNKNOWN_29 = 29
        UNKNOWN_30 = 30 #if next packet is Type2 and bcout_cnt(ib) = 0, set bocut_flag(ib) <= '1' and bout_cnt(ib) <= word count
        BSPI = 31
    @enum.unique
    class OpCode(enum.Enum):
        UNKNOWN = -1
        NOOP = 0
        READ = 1
        WRITE = 2
        Reserved = 3

    @staticmethod
    def get_address_name(key):
        return ConfigurationPacket.ADDRESS_NAME_TO_STR.get(key, ConfigurationPacket.Address.UNKNOWN)
    
    # 传入整型，返回其type
    @staticmethod
    def get_packet_type(word, content_type = "int"):
        if content_type != "int":
            word = int(word, 2)
        return word >> 29 
    
    # 传入整型，返回其opcode
    @staticmethod
    def get_opcode(word, content_type = "int"):
        if content_type != "int":
            word = int(word, 2)
        return ConfigurationPacket.OpCode((word >> 27) & 0x3) 
    
    # TODO 遇见无法识别的寄存器当作正常数据并给出提示
    # 根据传入word获取其type1格式的数据，content_type为int时，直接读，str时转换后再读
    @staticmethod
    def get_type_1_packet_content(word, content_type = "int"):
        if content_type != "int":
            word = int(word, 2)
        header_type = ConfigurationPacket.get_packet_type(word) # [31:29]
        opcode = ConfigurationPacket.OpCode((word >> 27) & 0x3) # [28:27]
        address = ConfigurationPacket.Address((word >> 13) & 0x1F) # [26:13] 取低5位
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
    @staticmethod
    def get_type_2_packet_content(word, content_type = "int"):
        if content_type != "int":
            word = int(word, 2)
        header_type = ConfigurationPacket.get_packet_type(word) # [31:29]
        opcode = ConfigurationPacket.OpCode((word >> 27) & 0x3) # [28:27]
        word_count = word & 0x7FFFFFF # [26:0]
        return {
                "header_type":header_type,
                "opcode":opcode,
                "word_count":word_count
            }
    @staticmethod
    def make_len_37_crc_data_in(word, cmd_word, content_type = "byte"):
        if content_type == "byte":
            word = utils.bytes_to_binary(word)
            cmd_word = utils.bytes_to_binary(cmd_word)
        address = cmd_word[14:19]
        crc_data_in = address + word
        return ([int(i) for i in crc_data_in[::-1]])
    
    @staticmethod
    def build_configuration_packet(packet_type: int, opcode: int, word_count: int, address_name: str, output_format='byte'):
        if packet_type == 1:
            if address_name not in ConfigurationPacket.STR_TO_ADDRESS:
                raise ValueError(f"未知 address_name : {address_name}")
            address = ConfigurationPacket.STR_TO_ADDRESS.get(address_name.upper())
  
            if not (0 <= word_count <= 0x7FF):
                raise ValueError("Type 1 word_count 范围 0~2047")
            packet_content = (0b001 << 29) | ((opcode & 0x3) << 27) | ((address & 0x1F) << 13) | (0 << 11) | (word_count & 0x7FF)
        elif packet_type == 2:
            if not (0 <= word_count <= 0x7FFFFFF):
                raise ValueError("Type 2 word_count 范围 0~134217727")
            packet_content = (0b010 << 29) | ((opcode & 0x3) << 27) | (word_count & 0x7FFFFFF)
        else:
            raise ValueError("仅支持 Type 1和Type 2")

        # 返回不同格式
        if output_format == 'int':
            return struct.pack(">I", packet_content)
        elif output_format == 'str':
            return f"{packet_content:032b}"
        else:
            raise ValueError("output_format 仅支持 'int', 'str'")
        
    # Address和字符串互查
    ADDRESS_NAME_TO_STR = {a: a.name for a in Address}
    STR_TO_ADDRESS = {a.name.upper(): a for a in Address}

   # Packet 内容模板
    class PacketTemplate(enum.Enum):
        # 指令部分
        CONFIG_NOOP                      = PacketContent("00100000000000000000000000000000")
        CONFIG_FDRI                      = PacketContent("00110000000000000100000000000000")
        CONFIG_CRC                       = PacketContent("00110000000000000000000000000001")
        CONFIG_COR1                      = PacketContent("00110000000000011100000000000001")
        CONFIG_RHBD                      = PacketContent("00110000000000111000000000000001")
        CONFIG_MASK                      = PacketContent("00110000000000001100000000000001")
        CONFIG_CTL1                      = PacketContent("00110000000000110000000000000001")
        CONFIG_FAR                       = PacketContent("00110000000000000010000000000001")
        CONFIG_CMD                       = PacketContent("00110000000000001000000000000001")
        CONFIG_TRIM                      = PacketContent("00110000000000110110000000000001")

        # 数据部分
        DATA_ZERO                        = PacketContent("00000000000000000000000000000000")
        DATA_DUMMY                       = PacketContent("11111111111111111111111111111111")
        DATA_SYNC_WORD                   = PacketContent("10101010100110010101010101100110")
        DATA_BUS_WIDTH_AUTO_DETECT_01    = PacketContent("00000000000000000000000010111011")
        DATA_BUS_WIDTH_AUTO_DETECT_02    = PacketContent("00010001001000100000000001000100")
        DATA_WCFG                        = PacketContent("00000000000000000000000000000001")
        DATA_MFW                         = PacketContent("00000000000000000000000000000010")
        DATA_RCRC                        = PacketContent("00000000000000000000000000000111")
        DATA_MASK_TRIM                   = PacketContent("10000000000000000000000000000000")
        DATA_MASK_VCCM                   = PacketContent("11111111111100000000000000000000")

        DATA_VCCM_105                    = PacketContent("11111111111100000000000000000000") # 1.05V
        DATA_VCCM_106                    = PacketContent("00010000010000000000000000000000") # 1.06V
        DATA_VCCM_107                    = PacketContent("00100000100000000000000000000000") # 1.07V
        DATA_VCCM_108                    = PacketContent("00110000110000000000000000000000") # 1.08V
        DATA_VCCM_109                    = PacketContent("01000101000100000000000000000000") # 1.09V
        DATA_VCCM_110                    = PacketContent("01010101010100000000000000000000") # 1.10V
        DATA_VCCM_111                    = PacketContent("01100101100100000000000000000000") # 1.11V
        DATA_VCCM_112                    = PacketContent("01111001111000000000000000000000") # 1.12V
        DATA_VCCM_115                    = PacketContent("01111101111100000000000000000000") # 1.124V, 仅在1.15时使用，因此命名115

        DATA_VCCM_COR1_115_01            = PacketContent("00000000000000000001100000000000") 
        DATA_VCCM_MASK_115_02            = PacketContent("00000000000000111111000000111111") 
        DATA_VCCM_TRIM_115_03            = PacketContent("00000000000000011011000000011011") 

        DATA_VSWL_COR1_01                = PacketContent("00000000000000000001000000000000") 
        DATA_VSWL_MASK_02                = PacketContent("00000111110000000000000000000000") 
        DATA_VSWL_TRIM_03                = PacketContent("00000110110000000000000000000000") 