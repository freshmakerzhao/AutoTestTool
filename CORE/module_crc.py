
import logging
import COMMON.config as config
import COMMON.utils as utils
import struct

# 关闭CRC    
def disable_crc(bitstream_obj):
    if bitstream_obj.is_compress == False:
        # 拿到数据帧之后的寄存器
        if bitstream_obj.file_type == ".rbt":
            for i in range(len(bitstream_obj.rbt_cfg_content_after)):
                if bitstream_obj.rbt_cfg_content_after[i].cmd_name == "CRC":
                    bitstream_obj.rbt_cfg_content_after[i].set_data_to_index(0, config.CMD_RCRC_01_STR)
                    bitstream_obj.rbt_cfg_content_after[i].set_data_to_index(1, config.CMD_RCRC_02_STR)
        elif bitstream_obj.file_type == ".bit" or bitstream_obj.file_type == ".bin":
            for i in range(len(bitstream_obj.bit_cfg_content_after)):
                if bitstream_obj.bit_cfg_content_after[i].cmd_name == "CRC":
                    bitstream_obj.bit_cfg_content_after[i].set_data_to_index(0, config.CMD_RCRC_01_BYTE)
                    bitstream_obj.bit_cfg_content_after[i].set_data_to_index(1, config.CMD_RCRC_02_BYTE)
    else:
        # 逆序遍历压缩位流 compress_data
        # 找到两个crc位置，记录下来loc1,loc2
        # 分别将loc1和loc2以及loc1+1，loc2+1的位置设置为RCRC
        loc_crc_1 = -1
        loc_crc_2 = -1
        if bitstream_obj.file_type == ".rbt":
            compress_data_content_len = len(bitstream_obj.rbt_compress_data_content)
            for index in range(compress_data_content_len-1,-1,-1):
                if compress_data_content_len - index > 600:
                    break
                line = bitstream_obj.rbt_compress_data_content[index]
                word_type = bitstream_obj.cfg_obj.get_packet_type(line, "str")
                
                if line == config.NOOP_STR:
                    continue
                elif line == config.DUMMY_STR:
                    continue
                elif line == config.SYNC_WORD_STR:
                    continue
                elif line == config.BUS_WIDTH_AUTO_DETECT_01_STR or line == config.BUS_WIDTH_AUTO_DETECT_02_STR:
                    continue
                
                packet_content = {}
                if word_type == 1:
                    packet_content = bitstream_obj.cfg_obj.get_type_1_packet_content(line, "str")
                elif word_type == 2:
                    packet_content = bitstream_obj.cfg_obj.get_type_2_packet_content(line, "str")
                    
                if packet_content.get("address", bitstream_obj.cfg_obj.Address.UNKNOWN) == bitstream_obj.cfg_obj.Address.CRC:
                    if loc_crc_1 == -1:
                        # 找到第一个crc
                        loc_crc_1 = index
                    else:
                        loc_crc_2 = index
                        break
                
                if index > 0 \
                    and bitstream_obj.rbt_compress_data_content[index] == config.CMD_RCRC_02_STR \
                    and bitstream_obj.rbt_compress_data_content[index-1] == config.CMD_RCRC_01_STR:
                    if loc_crc_1 == -1:
                        # 找到第一个crc
                        loc_crc_1 = index-1
                    else:
                        loc_crc_2 = index-1
                        break
                    
            if loc_crc_1 != -1:
                bitstream_obj.rbt_compress_data_content[loc_crc_1] = config.CMD_RCRC_01_STR
                bitstream_obj.rbt_compress_data_content[loc_crc_1+1] = config.CMD_RCRC_02_STR
            if loc_crc_2 != -1:
                bitstream_obj.rbt_compress_data_content[loc_crc_2] = config.CMD_RCRC_01_STR
                bitstream_obj.rbt_compress_data_content[loc_crc_2+1] = config.CMD_RCRC_02_STR
                
        elif bitstream_obj.file_type == ".bit" or bitstream_obj.file_type == ".bin":
            compress_data_content_len = len(bitstream_obj.bit_compress_data_content)
            for index in range(compress_data_content_len-1,-1,-1):
                if compress_data_content_len - index > 600:
                    break
                line = bitstream_obj.bit_compress_data_content[index]
                word_content = struct.unpack('>I', line)[0] # 转无符号整型
                word_type = bitstream_obj.cfg_obj.get_packet_type(word_content, "int")
                
                if line == config.NOOP_BYTE:
                    continue
                elif line == config.DUMMY_BYTE:
                    continue
                elif line == config.SYNC_WORD_BYTE:
                    continue
                elif line == config.BUS_WIDTH_AUTO_DETECT_01_BYTE or line == config.BUS_WIDTH_AUTO_DETECT_02_BYTE:
                    continue
                
                packet_content = {}
                if word_type == 1:
                    packet_content = bitstream_obj.cfg_obj.get_type_1_packet_content(word_content, "int")
                elif word_type == 2:
                    packet_content = bitstream_obj.cfg_obj.get_type_2_packet_content(word_content, "int")
                    
                if packet_content.get("address", bitstream_obj.cfg_obj.Address.UNKNOWN) == bitstream_obj.cfg_obj.Address.CRC:
                    if loc_crc_1 == -1:
                        # 找到第一个crc
                        loc_crc_1 = index
                    else:
                        loc_crc_2 = index
                        break
                    
                if index > 0 \
                    and bitstream_obj.bit_compress_data_content[index] == config.CMD_RCRC_02_BYTE \
                    and bitstream_obj.bit_compress_data_content[index-1] == config.CMD_RCRC_01_BYTE:
                    if loc_crc_1 == -1:
                        # 找到第一个crc
                        loc_crc_1 = index-1
                    else:
                        loc_crc_2 = index-1
                        break
                    
            if loc_crc_1 != -1:
                bitstream_obj.bit_compress_data_content[loc_crc_1] = config.CMD_RCRC_01_BYTE
                bitstream_obj.bit_compress_data_content[loc_crc_1+1] = config.CMD_RCRC_02_BYTE
            if loc_crc_2 != -1:
                bitstream_obj.bit_compress_data_content[loc_crc_2] = config.CMD_RCRC_01_BYTE
                bitstream_obj.bit_compress_data_content[loc_crc_2+1] = config.CMD_RCRC_02_BYTE
                    
# 计算crc
def calculate_crc(bitstream_obj):
    # 拿到数据帧之前的寄存器
    if bitstream_obj.file_type == ".rbt":
        # ============== 第一段 =====================
        crc_start_flag = False
        # 1. 拿到数据帧前的寄存器，确定RCRC位置
        for item in bitstream_obj.rbt_cfg_content_pre:
            if item.opcode == -1 or item.opcode.value != 2 or item.cmd_name == "RHBD":
                # 不参与运算
                continue
            else:
                # 参与运算
                words_len = item.get_data_len()
                for index in range(1, words_len):
                    if item.get_data_from_index(0) == config.CMD_RCRC_01_STR and item.get_data_from_index(1) == config.CMD_RCRC_02_STR:
                        # 从这里开始，后面的寄存器参与运算
                        crc_start_flag = True
                        continue
                    if crc_start_flag:
                        # 计算crc
                        # 拿到cmd本身
                        cmd_word = item.get_data_from_index(0) # rbt
                        # 拿到当前cmd下的word
                        cur_word = item.get_data_from_index(index) # rbt
                        
                        crc_data_in = bitstream_obj.cfg_obj.make_len_37_crc_data_in(cur_word, cmd_word, "str")
                        bitstream_obj.crc_01 = bitstream_obj.icap_crc(crc_data_in, bitstream_obj.crc_01)
        # 00010010000111000110100110000001                
        for word in bitstream_obj.rbt_data_content:
            # 计算crc
            crc_data_in = bitstream_obj.cfg_obj.make_len_37_crc_data_in(word, config.FDRI_STR, "str")
            bitstream_obj.crc_01 = bitstream_obj.icap_crc(crc_data_in, bitstream_obj.crc_01)
        print("第一段crc数据：%s" ,bitstream_obj.crc_01)
        # ============== 第一段 =====================
        
        # ============== 第二段 =====================
        crc_cmd_count = 0 # crc命令计数器，每遇到一次crc，就记一次，第二次时完成计算
        rbt_cfg_content_after_len = len(bitstream_obj.rbt_cfg_content_after)
        # 这里从索引2开始，因为数据帧后的寄存器0,1位置为CRC write
        for cfg_index in range(rbt_cfg_content_after_len):
            item = bitstream_obj.rbt_cfg_content_after[cfg_index]
            if item.opcode == -1 or item.opcode.value != 2 or item.cmd_name == "RHBD":
                # 不参与运算
                continue
            else:
                # 参与运算
                words_len = item.get_data_len()
                for data_index in range(1, words_len):
                    if bitstream_obj.own_crc_is_enable:
                            # 当开启crc时，遇到 crc 计数一次
                        if item.get_data_from_index(0) == config.CRC_STR:
                            if crc_cmd_count == 0:
                                # 第一个
                                bitstream_obj.rbt_cfg_content_after[cfg_index].set_data_to_index(0, config.CRC_STR)
                                bitstream_obj.rbt_cfg_content_after[cfg_index].set_data_to_index(1, bitstream_obj.crc_01)
                            elif crc_cmd_count == 1:
                                # 第二个
                                bitstream_obj.rbt_cfg_content_after[cfg_index].set_data_to_index(0, config.CRC_STR)
                                bitstream_obj.rbt_cfg_content_after[cfg_index].set_data_to_index(1, bitstream_obj.crc_02)
                            crc_cmd_count += 1
                            break
                    else:
                        # 当没有开启crc, 遇到cmd + 07时，计数一次
                        if words_len == 2 \
                            and item.get_data_from_index(0) == config.CMD_RCRC_01_STR \
                            and item.get_data_from_index(1) == config.CMD_RCRC_02_STR:
                            # 将得到的crc赋值给 bit_cfg_content_after 
                            if crc_cmd_count == 0:
                                # 第一个
                                bitstream_obj.rbt_cfg_content_after[cfg_index].set_data_to_index(0, config.CRC_STR)
                                bitstream_obj.rbt_cfg_content_after[cfg_index].set_data_to_index(1, bitstream_obj.crc_01)
                            elif crc_cmd_count == 1:
                                # 第二个
                                bitstream_obj.rbt_cfg_content_after[cfg_index].set_data_to_index(0, config.CRC_STR)
                                bitstream_obj.rbt_cfg_content_after[cfg_index].set_data_to_index(1, bitstream_obj.crc_02)
                            crc_cmd_count += 1
                            break
                    
                    # 计算crc
                    # 拿到cmd本身
                    cmd_word = item.get_data_from_index(0) # RBT
                    # 拿到当前cmd下的word
                    cur_word = item.get_data_from_index(data_index) # RBT
                    
                    crc_data_in = bitstream_obj.cfg_obj.make_len_37_crc_data_in(cur_word, cmd_word, "str")
                    # print("第二段数据：%s" ,crc_data_in)
                    bitstream_obj.crc_02 = bitstream_obj.icap_crc(crc_data_in, bitstream_obj.crc_02)
            if crc_cmd_count == 2:
                # 遇到两次crc，计算完成
                break
        print("第二段crc数据：%s" ,bitstream_obj.crc_02)
        # ============== 第二段 =====================
        
    elif bitstream_obj.file_type == ".bit" or bitstream_obj.file_type == ".bin":
        # ============== 第一段 =====================
        crc_start_flag = False
        # 1. 拿到数据帧前的寄存器，确定RCRC位置
        for item in bitstream_obj.bit_cfg_content_pre:
            if item.opcode == -1 or item.opcode.value != 2 or item.cmd_name == "RHBD":
                # 不参与运算
                continue
            else:
                # 参与运算
                words_len = item.get_data_len()
                for index in range(1, words_len):
                    if item.get_data_from_index(0) == config.CMD_RCRC_01_BYTE and item.get_data_from_index(1) == config.CMD_RCRC_02_BYTE:
                        # 从这里开始，后面的寄存器参与运算
                        crc_start_flag = True
                        continue
                    if crc_start_flag:
                        # 计算crc
                        # 拿到cmd本身
                        cmd_word = item.get_data_from_index(0) # 字节
                        # 拿到当前cmd下的word
                        cur_word = item.get_data_from_index(index) # 字节
                        
                        crc_data_in = bitstream_obj.cfg_obj.make_len_37_crc_data_in(cur_word, cmd_word, "byte")
                        bitstream_obj.crc_01 = bitstream_obj.icap_crc(crc_data_in, bitstream_obj.crc_01)
        # 00010010000111000110100110000001                
        for word in bitstream_obj.bit_data_content:
            # 计算crc
            crc_data_in = bitstream_obj.cfg_obj.make_len_37_crc_data_in(word, config.FDRI_BYTE, "byte")
            bitstream_obj.crc_01 = bitstream_obj.icap_crc(crc_data_in, bitstream_obj.crc_01)
                        
        print(bitstream_obj.crc_01) # 01111100100101011110011001111001 7C95E679
                    
        # ============== 第一段 =====================
        
        
        # ============== 第二段 =====================
        # bitstream_obj.crc_02 = bitstream_obj.crc_01
        crc_cmd_count = 0 # crc命令计数器，每遇到一次crc，就记一次，第二次时完成计算
        bit_cfg_content_after_len = len(bitstream_obj.bit_cfg_content_after)
        for cfg_index in range(bit_cfg_content_after_len):
            item = bitstream_obj.bit_cfg_content_after[cfg_index]
            if item.opcode == -1 or item.opcode.value != 2 or item.cmd_name == "RHBD":
                # 不参与运算
                continue
            else:
                # 参与运算
                words_len = item.get_data_len()
                for data_index in range(1, words_len):
                    if bitstream_obj.own_crc_is_enable:
                            # 当开启crc时，遇到 crc 计数一次
                        if item.get_data_from_index(0) == config.CRC_BIT:
                            if crc_cmd_count == 0:
                                # 第一个
                                bitstream_obj.bit_cfg_content_after[cfg_index].set_data_to_index(0, config.CRC_BIT)
                                bitstream_obj.bit_cfg_content_after[cfg_index].set_data_to_index(1, utils.binary_str_to_bytes(bitstream_obj.crc_01))
                            elif crc_cmd_count == 1:
                                # 第二个
                                bitstream_obj.bit_cfg_content_after[cfg_index].set_data_to_index(0, config.CRC_BIT)
                                bitstream_obj.bit_cfg_content_after[cfg_index].set_data_to_index(1, utils.binary_str_to_bytes(bitstream_obj.crc_02))
                            crc_cmd_count += 1
                            break
                    else:
                        # 当没有开启crc, 遇到cmd + 07时，计数一次
                        if words_len == 2 \
                            and item.get_data_from_index(0) == config.CMD_RCRC_01_BYTE \
                            and item.get_data_from_index(1) == config.CMD_RCRC_02_BYTE:
                            # 将得到的crc赋值给 bit_cfg_content_after 
                            if crc_cmd_count == 0:
                                # 第一个
                                bitstream_obj.bit_cfg_content_after[cfg_index].set_data_to_index(0, config.CRC_BIT)
                                bitstream_obj.bit_cfg_content_after[cfg_index].set_data_to_index(1, utils.binary_str_to_bytes(bitstream_obj.crc_01))
                            elif crc_cmd_count == 1:
                                # 第二个
                                bitstream_obj.bit_cfg_content_after[cfg_index].set_data_to_index(0, config.CRC_BIT)
                                bitstream_obj.bit_cfg_content_after[cfg_index].set_data_to_index(1, utils.binary_str_to_bytes(bitstream_obj.crc_02))
                            crc_cmd_count += 1
                            break
                    # 计算crc
                    # 拿到cmd本身
                    cmd_word = item.get_data_from_index(0) # 字节
                    # 拿到当前cmd下的word
                    cur_word = item.get_data_from_index(data_index) # 字节
                    
                    crc_data_in = bitstream_obj.cfg_obj.make_len_37_crc_data_in(cur_word, cmd_word, "byte")
                    int_value = int(''.join(map(str, crc_data_in)), 2)
                    hex_str = f"{int_value:x}"
                    bitstream_obj.crc_02 = bitstream_obj.icap_crc(crc_data_in, bitstream_obj.crc_02)
            if crc_cmd_count == 2:
                # 遇到两次crc，计算完成
                break
        print(bitstream_obj.crc_02) # 11100011101011010111111010100101 E3AD7EA5
        # ============== 第二段 =====================
                
# 迭代crc
def icap_crc(crc_data_in, crc):
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