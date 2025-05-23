
import COMMON.config as config
import COMMON.utils as utils
import struct
import logging

BITS_CMD = 'Bits:'

class BitstreamParser:
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
            
    def __init__(self, device: str, input_file_path: str, enable_crc: bool):
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
        self.own_crc_is_enable = False # 码流本身是否开启CRC
        
        self.device = device # 器件类型
        self.is_compress = False # 是否压缩，默认非压缩
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
        # 存储压缩码流主体内容
        self.bit_compress_data_content = []
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
        # 存储压缩码流主体内容
        self.rbt_compress_data_content = []
        # 存储后续配置信息
        self.rbt_cfg_content_after = []
        # ======================= rbt =====================     
        
        self.cfg_obj = config.ConfigurationPacket()
        
        self.load_file()
    
    def load_file(self) -> None:
        # 根据类型读取文件内容
        self.file_path_except_type, self.file_type = utils.get_file_type(self.input_file_path)
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
        if self.is_compress == False:
            self.parse_rbt_data_content()
        # 到 FDRI data word XXXX 结束，其中 XXXX 指的是 parse_rbt_cfg_content_pre 解析出来的 self.word_count
        # ============================================ data frame ============================================
        
        # ============================================ cfg content after ============================================
        # 对于没有关闭CRC的位流，此处从 30000001 开始
        if self.is_compress == False:
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
        if self.is_compress == False:
            utils.log_debug_with_description(len(self.rbt_annotation_content), description="头部注释信息行数")
            utils.log_debug_with_description(len(self.rbt_cfg_content_pre), description="数据帧之前的寄存器行数")
            utils.log_debug_with_description(len(self.rbt_data_content), description="数据行数")
            cur_group_len = 0
            for item in self.rbt_cfg_content_after:
                cur_group_len += item.get_data_len()
            utils.log_debug_with_description(cur_group_len, description="数据帧之后的寄存器行数")
            utils.log_debug_with_description(len(self.rbt_annotation_content) + len(self.rbt_cfg_content_pre) + len(self.rbt_data_content) + cur_group_len, description="总行数")
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
        rbt_cfg_content_pre_len = 0
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
            
            if line == config.NOOP_STR:
                item = self.PacketItem("NOOP")
                item.set_opcode(-1)
                word_count = 0
            elif line == config.DUMMY_STR:
                item = self.PacketItem("DUMMY")
                item.set_opcode(-1)
                word_count = 0
            elif line == config.SYNC_WORD_STR:
                item = self.PacketItem("SYNC_WORD")
                item.set_opcode(-1)
                word_count = 0
            elif line == config.BUS_WIDTH_AUTO_DETECT_01_STR or line == config.BUS_WIDTH_AUTO_DETECT_02_STR:
                item = self.PacketItem("BUS_WIDTH")
                item.set_opcode(-1)
                word_count = 0
            else:
                item = self.PacketItem(self.cfg_obj.get_cmd_name(packet_content.get("address")))
                item.set_opcode(packet_content.get("opcode", -1))
            
            item.append_data(self.rbt_content[index]) # 插入cmd
            
            for i in range(word_count):
                index += 1
                item.append_data(self.rbt_content[index])
                
            index += 1
            self.rbt_cfg_content_pre.append(item)
            
            rbt_cfg_content_pre_len += 1
            if rbt_cfg_content_pre_len > 1 \
                and self.rbt_cfg_content_pre[rbt_cfg_content_pre_len-1].cmd_name == "CTL1" \
                and self.rbt_cfg_content_pre[rbt_cfg_content_pre_len-2].cmd_name == "MASK":
                # 连续，data[12]为1，表示压缩位流
                ctl1_data = self.rbt_cfg_content_pre[rbt_cfg_content_pre_len-1].get_data_from_index(1)
                mask_data = self.rbt_cfg_content_pre[rbt_cfg_content_pre_len-2].get_data_from_index(1)
                if ctl1_data[-13] == "1" and mask_data[-13] == "1":
                    self.is_compress = True
            
            # 对于普通位流，当 FDRI 时
            if packet_content.get("header_type", -1) == 1 \
                and packet_content.get("opcode", self.cfg_obj.OpCode.UNKNOWN) == self.cfg_obj.OpCode.WRITE \
                and packet_content.get("address", self.cfg_obj.Address.UNKNOWN) == self.cfg_obj.Address.FDRI \
                and self.is_compress == False:
                word_content = self.rbt_content[index]
                item = self.PacketItem("WORD_COUNT")
                item.set_opcode(-1)
                item.append_data(word_content)
                self.rbt_cfg_content_pre.append(item)
                rbt_cfg_content_pre_len += 1
                self.word_count = self.cfg_obj.get_type_2_packet_content(word_content,"str").get("word_count",0)
                self.rbt_content_cur_loc = index+1
                break
            # 对于压缩位流，当 FDRI 时，将后续所有内容放入 rbt_compress_data_content,临时解决
            if packet_content.get("header_type", -1) == 1 \
                and packet_content.get("opcode", self.cfg_obj.OpCode.UNKNOWN) == self.cfg_obj.OpCode.WRITE \
                and packet_content.get("address", self.cfg_obj.Address.UNKNOWN) == self.cfg_obj.Address.FDRI \
                and self.is_compress == True:
                    self.rbt_compress_data_content.extend(self.rbt_content[index:])
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
            
            if line == config.NOOP_STR:
                item = self.PacketItem("NOOP")
                item.set_opcode(-1)
                word_count = 0
            elif line == config.DUMMY_STR:
                item = self.PacketItem("DUMMY")
                item.set_opcode(-1)
                word_count = 0
            elif line == config.SYNC_WORD_STR:
                item = self.PacketItem("SYNC_WORD")
                item.set_opcode(-1)
                word_count = 0
            elif line == config.BUS_WIDTH_AUTO_DETECT_01_STR or line == config.BUS_WIDTH_AUTO_DETECT_02_STR:
                item = self.PacketItem("BUS_WIDTH")
                item.set_opcode(-1)
                word_count = 0
            else:
                item = self.PacketItem(self.cfg_obj.get_cmd_name(packet_content.get("address")))
                item.set_opcode(packet_content.get("opcode", -1))
            
                
            item.append_data(self.rbt_content[self.rbt_content_cur_loc]) # 插入cmd
            
            for i in range(word_count):
                self.rbt_content_cur_loc += 1
                item.append_data(self.rbt_content[self.rbt_content_cur_loc])
            
            # 记录crc
            if item.cmd_name == "CRC":
                self.own_crc_is_enable = True # 如果存在crc cmd 就证明该位流开启了CRC
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
        utils.show_ascii_content(self.bit_head_byte_content[start_index:end_index])
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
        utils.show_ascii_content(self.bit_head_byte_content[start_index:end_index])
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
        utils.show_ascii_content(self.bit_head_byte_content[start_index:end_index])
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
        utils.show_ascii_content(self.bit_head_byte_content[start_index:end_index])
        start_index = end_index
        # ========== 标识符D ============

        # ========== 标识符E ============
        self.bit_head_byte_content += self.read_bit_bytes(1) # 标识 b'\x65'
        self.bit_head_byte_content += self.read_bit_bytes(4) # 位流的总长度
        start_index += 1
        end_index = start_index + 4
        logging.debug(f"\tE content: {self.bit_head_byte_content[start_index:end_index].hex()}")
        utils.show_number_content(self.bit_head_byte_content[start_index:end_index])
        start_index = end_index
        # ========== 标识符E ============
    
    # 解析位流，读取cfg内容
    def parse_bit_cfg_content_pre(self) -> None: 
        bit_cfg_content_pre_len = 0
        while True:
            word = self.read_bit_bytes(4)
            utils.log_debug_with_description(utils.bytes_to_binary(word))
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
            
            if word == config.NOOP_BYTE:
                item = self.PacketItem("NOOP")
                item.set_opcode(-1)
                word_count = 0
            elif word == config.DUMMY_BYTE:
                item = self.PacketItem("DUMMY")
                item.set_opcode(-1)
                word_count = 0
            elif word == config.SYNC_WORD_BYTE:
                item = self.PacketItem("SYNC_WORD")
                item.set_opcode(-1)
                word_count = 0
            elif word == config.BUS_WIDTH_AUTO_DETECT_01_BYTE or word == config.BUS_WIDTH_AUTO_DETECT_02_BYTE:
                item = self.PacketItem("BUS_WIDTH")
                item.set_opcode(-1)
                word_count = 0
            else:
                item = self.PacketItem(self.cfg_obj.get_cmd_name(packet_content.get("address")))
                item.set_opcode(packet_content.get("opcode", -1))
            
            item.append_data(word) # 插入cmd
            
            for i in range(word_count):
                item.append_data(self.read_bit_bytes(4))
                
            self.bit_cfg_content_pre.append(item)      
            bit_cfg_content_pre_len += 1      
            
            if bit_cfg_content_pre_len > 1 \
                and self.bit_cfg_content_pre[bit_cfg_content_pre_len-1].cmd_name == "CTL1" \
                and self.bit_cfg_content_pre[bit_cfg_content_pre_len-2].cmd_name == "MASK":
                # 连续，data[12]为1，表示压缩位流
                ctl1_data = utils.bytes_to_binary(self.bit_cfg_content_pre[bit_cfg_content_pre_len-1].get_data_from_index(1))
                mask_data = utils.bytes_to_binary(self.bit_cfg_content_pre[bit_cfg_content_pre_len-2].get_data_from_index(1))
                if ctl1_data[-13] == "1" and mask_data[-13] == "1":
                    self.is_compress = True
                    
            # 读取到 FDRI 后，读取结束 30004000
            if packet_content.get("header_type", -1) == 1 \
                and packet_content.get("opcode", self.cfg_obj.OpCode.UNKNOWN) == self.cfg_obj.OpCode.WRITE \
                and packet_content.get("address", self.cfg_obj.Address.UNKNOWN) == self.cfg_obj.Address.FDRI \
                and self.is_compress == False:
                    word = self.read_bit_bytes(4)
                    item = self.PacketItem("WORD_COUNT")
                    item.set_opcode(-1)
                    item.append_data(word)
                    self.bit_cfg_content_pre.append(item)
                    bit_cfg_content_pre_len += 1
                    word_content = struct.unpack('>I', word)[0] # 转无符号整型
                    # 拿到 word_count，其单位是word，换成字节*4
                    self.word_count = self.cfg_obj.get_type_2_packet_content(word_content, "int").get("word_count",0)
                    self.bit_data_content_byte_count = self.word_count * 4
                    break
                
            # 对于压缩位流，当 FDRI 时，将后续所有内容放入 bit_compress_data_content,临时解决
            if packet_content.get("header_type", -1) == 1 \
                and packet_content.get("opcode", self.cfg_obj.OpCode.UNKNOWN) == self.cfg_obj.OpCode.WRITE \
                and packet_content.get("address", self.cfg_obj.Address.UNKNOWN) == self.cfg_obj.Address.FDRI \
                and self.is_compress == True:
                    for i in range(self.bit_byte_content_cur_loc, self.bit_byte_content_len, 4):
                        word = self.read_bit_bytes(4)
                        self.bit_compress_data_content.append(word)
        
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
            
            if word == config.NOOP_BYTE:
                item = self.PacketItem("NOOP")
                item.set_opcode(-1)
                word_count = 0
            elif word == config.DUMMY_BYTE:
                item = self.PacketItem("DUMMY")
                item.set_opcode(-1)
                word_count = 0
            elif word == config.SYNC_WORD_BYTE:
                item = self.PacketItem("SYNC_WORD")
                item.set_opcode(-1)
                word_count = 0
            elif word == config.BUS_WIDTH_AUTO_DETECT_01_BYTE or word == config.BUS_WIDTH_AUTO_DETECT_02_BYTE:
                item = self.PacketItem("BUS_WIDTH")
                item.set_opcode(-1)
                word_count = 0
            else:
                item = self.PacketItem(self.cfg_obj.get_cmd_name(packet_content.get("address")))
                item.set_opcode(packet_content.get("opcode", -1))
                
            item.append_data(word) # 插入cmd

            for i in range(word_count):
                item.append_data(self.read_bit_bytes(4))
                
            # 记录crc
            if item.cmd_name == "CRC":
                self.own_crc_is_enable = True # 如果存在crc cmd 就证明该位流开启了CRC
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
        if self.is_compress == False:
            self.parse_bit_data_content()
        # 到 FDRI data word XXXX 结束，其中 XXXX 指的是 parse_bit_cfg_content_pre 解析出来的 self.word_count
        # ============================================ data frame ============================================
        
        # ============================================ cfg content after ============================================
        # 对于没有关闭CRC的位流，此处从 30000001 开始
        if self.is_compress == False:
            self.parse_bit_cfg_content_aft()
        # 到 码流末尾 结束
        # ============================================ cfg content after ============================================
        
        # ============================================ debug ============================================
        # len(self.bit_head_byte_content)) 头部信息字节数
        # len(self.bit_cfg_content_pre)) 数据帧之前的寄存器所占word数，*4为字节数
        # len(self.bit_data_content)) 数据帧所占word数，*4为字节数
        # len(self.bit_cfg_content_after)) 数据帧之后的寄存器所占word数，*4为字节数
        
        if self.is_compress == False:
            # 四个字节数相加为整段位流长度
            utils.log_debug_with_description(len(self.bit_head_byte_content), 'X', '头部信息字节数')
            
            bit_cfg_content_pre_len = 0
            for item in self.bit_cfg_content_pre:
                bit_cfg_content_pre_len += item.get_data_len()
            utils.log_debug_with_description(bit_cfg_content_pre_len*4, 'X', '数据帧之前的寄存器字节数')
            utils.log_debug_with_description(len(self.bit_data_content)*4, 'X', '数据帧字节数')
            
            bit_cfg_content_after_len = 0
            for item in self.bit_cfg_content_after:
                bit_cfg_content_after_len += item.get_data_len()
            utils.log_debug_with_description(bit_cfg_content_after_len*4, 'X', '数据帧之后的寄存器字节数')
            utils.log_debug_with_description(bit_cfg_content_after_len*4 + len(self.bit_data_content)*4 + bit_cfg_content_pre_len*4 + len(self.bit_head_byte_content), 'X', '总字节数')
        # ============================================ debug ============================================
          
    def set_data_with_frame_word_bit(self, data, frame, word, bit):
        try:
            # === 参数验证 ===
            if not (0 <= bit <= 31):
                raise ValueError(f"无效 bit 值: {bit}，应为 0~31 之间的整数")

            line_index = frame * 101 + word
            bit_index = 31 - bit  # 右高位，对应字符串的低索引

            # === 文件类型为 .bit/.bin ===
            if self.file_type in [".bit", ".bin"]:
                if not (0 <= line_index < len(self.bit_data_content)):
                    raise IndexError(f"bit_data_content 越界，line_index={line_index}，长度={len(self.bit_data_content)}")

                original_bytes = self.bit_data_content[line_index]
                try:
                    word_str = utils.bytes_to_binary(original_bytes)
                except Exception as e:
                    raise ValueError(f"无法将 bytes 转换为 binary 字符串，原始值={original_bytes}: {e}")

                if len(word_str) != 32:
                    raise ValueError(f"转换后的 binary 字符串长度异常: {len(word_str)}，应为32")

                word_str = word_str[:bit_index] + data + (word_str[bit_index+1:] if bit_index < 31 else "")
                self.bit_data_content[line_index] = utils.binary_str_to_bytes(word_str)

            # === 文件类型为 .rbt ===
            elif self.file_type == ".rbt":
                if not (0 <= line_index < len(self.rbt_data_content)):
                    raise IndexError(f"rbt_data_content 越界，line_index={line_index}，长度={len(self.rbt_data_content)}")

                line = self.rbt_data_content[line_index]
                if len(line) != 32:
                    raise ValueError(f"rbt_data_content[{line_index}] 长度不为 32，实际长度: {len(line)}")

                self.rbt_data_content[line_index] = line[:bit_index] + data + (line[bit_index+1:] if bit_index < 31 else "")

            else:
                raise ValueError(f"不支持的文件类型: {self.file_type}")

        except Exception as e:
            # 添加更多上下文信息
            raise RuntimeError(
                f"设置 bit 值失败：frame={frame}, word={word}, bit={bit}, data={data}, file_type={self.file_type}\n"
                f"错误信息: {e}"
            ) from e
          
    def get_data_with_frame_word_bit(self, frame, word, bit):
        print("frame: ", frame, "word: ", word, "bit: ", bit)
        line_index = frame*101 + word
        bit_index = 31 - bit # 这里是因为bit从右往左算，而index从左往右算
        if self.file_type == ".bit" or self.file_type == ".bin":
            word = utils.bytes_to_binary(self.bit_data_content[line_index])
            return word[bit_index]
        elif self.file_type == ".rbt":
            return self.rbt_data_content[line_index][bit_index]
        else:
            raise ValueError("文件格式错误")      

    def get_data_frame(self, frame):
        pass
    
    def get_data_word(self, frame, word):
        print("frame: ", frame, "word: ", word)
        line_index = frame*101 + word
        if self.file_type == ".bit" or self.file_type == ".bin":
            word = utils.bytes_to_binary(self.bit_data_content[line_index])
            return word
        elif self.file_type == ".rbt":
            return self.rbt_data_content[line_index]
        else:
            raise ValueError("文件格式错误") 
    
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
    
    # file_suffix表示文件名称后缀，不影响类型
    # output_file_path表示文件存储路径，不带文件类型
    def save_file(self, file_suffix = "", output_file_path = ""):
        if output_file_path == "":
            new_file_path = self.file_path_except_type + file_suffix + self.file_type
        else:
            new_file_path = output_file_path + self.file_type
            
        # 为压缩位流临时做一个存储方法
        if self.is_compress == True:
            if self.file_type == ".rbt":
                # 计算长度
                byte_nums = len(self.rbt_compress_data_content)
                for item in self.rbt_cfg_content_pre:
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
                    for line in self.rbt_compress_data_content:
                        f.write(line + '\n')
            elif self.file_type == ".bit" or self.file_type == ".bin":
                with open(new_file_path, 'wb') as file:  
                    # 计算长度
                    bit_len = len(self.bit_compress_data_content)
                    for item in self.bit_cfg_content_pre:
                        bit_len += item.get_data_len()
                    bit_len = bit_len * 4
                    length_bytes_struct = struct.pack('>I', bit_len)
                    self.bit_head_byte_content = self.bit_head_byte_content[:-4] + length_bytes_struct
                    file.write(self.bit_head_byte_content)
                    for item in self.bit_cfg_content_pre:
                        values = item.get_all_data()
                        for word in values:
                            file.write(word)
                    for byte_elem in self.bit_compress_data_content:
                        file.write(byte_elem)
            else:
                raise ValueError("文件格式错误")
        else:
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
        return new_file_path