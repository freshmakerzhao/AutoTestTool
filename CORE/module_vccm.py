
import struct
import logging
import argparse
from COMMON.config import ConfigurationPacket
import COMMON.utils as utils
from collections import defaultdict

# 这里处理的是10到112
def process_vccm(bitstream_obj, vccm_value=105):
    # 拿到数据帧之前的寄存器
    if bitstream_obj.file_type == ".rbt":
        for i in range(len(bitstream_obj.rbt_cfg_content_pre)):
            if bitstream_obj.rbt_cfg_content_pre[i].cmd_name == "COR1":
                cor1_data = bitstream_obj.rbt_cfg_content_pre[i].get_data_from_index(1)
                cor1_data = utils.update_data_by_index(cor1_data,[12,10],["1","1"])
                bitstream_obj.rbt_cfg_content_pre[i].set_data_to_index(1, cor1_data)
                bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_MASK.value.binstr)
                bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_MASK_VCCM.value.binstr)
                bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_TRIM.value.binstr)
                if vccm_value == 105:
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_105.value.binstr)
                elif vccm_value == 106:
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_106.value.binstr)
                elif vccm_value == 107:
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_107.value.binstr)
                elif vccm_value == 108:
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_108.value.binstr)
                elif vccm_value == 109:
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_109.value.binstr)
                elif vccm_value == 110:
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_110.value.binstr)
                elif vccm_value == 111:
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_111.value.binstr)
                elif vccm_value == 112:
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_112.value.binstr)
                else:
                    raise ValueError("vccm_value 配置错误")
                break
    elif bitstream_obj.file_type == ".bit" or bitstream_obj.file_type == ".bin":
        for i in range(len(bitstream_obj.bit_cfg_content_pre)):
            if bitstream_obj.bit_cfg_content_pre[i].cmd_name == "COR1":
                cor1_data = utils.bytes_to_binary(bitstream_obj.bit_cfg_content_pre[i].get_data_from_index(1))
                cor1_data = utils.update_data_by_index(cor1_data,[12,10],["1","1"])
                bitstream_obj.bit_cfg_content_pre[i].set_data_to_index(1, utils.binary_str_to_bytes(cor1_data))
                bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_MASK.value.byte)
                bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_MASK_VCCM.value.byte)
                bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_TRIM.value.byte)
                if vccm_value == 105:
                    bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_112.value.byte)
                elif vccm_value == 106:
                    bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_112.value.byte)
                elif vccm_value == 107:
                    bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_112.value.byte)
                elif vccm_value == 108:
                    bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_112.value.byte)
                elif vccm_value == 109:
                    bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_112.value.byte)
                elif vccm_value == 110:
                    bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_112.value.byte)
                elif vccm_value == 111:
                    bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_112.value.byte)
                elif vccm_value == 112:
                    bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_112.value.byte)
                else:
                    raise ValueError("vccm_value 配置错误")
                break

vccm_data_str_map = {
    105: ConfigurationPacket.PacketTemplate.DATA_VCCM_105.value.binstr,
    106: ConfigurationPacket.PacketTemplate.DATA_VCCM_106.value.binstr,
    107: ConfigurationPacket.PacketTemplate.DATA_VCCM_107.value.binstr,
    108: ConfigurationPacket.PacketTemplate.DATA_VCCM_108.value.binstr,
    109: ConfigurationPacket.PacketTemplate.DATA_VCCM_109.value.binstr,
    110: ConfigurationPacket.PacketTemplate.DATA_VCCM_110.value.binstr,
    111: ConfigurationPacket.PacketTemplate.DATA_VCCM_111.value.binstr,
    112: ConfigurationPacket.PacketTemplate.DATA_VCCM_112.value.binstr,
    115: ConfigurationPacket.PacketTemplate.DATA_VCCM_115.value.binstr
}

vccm_data_byte_map = {
    105: ConfigurationPacket.PacketTemplate.DATA_VCCM_105.value.byte,
    106: ConfigurationPacket.PacketTemplate.DATA_VCCM_106.value.byte,
    107: ConfigurationPacket.PacketTemplate.DATA_VCCM_107.value.byte,
    108: ConfigurationPacket.PacketTemplate.DATA_VCCM_108.value.byte,
    109: ConfigurationPacket.PacketTemplate.DATA_VCCM_109.value.byte,
    110: ConfigurationPacket.PacketTemplate.DATA_VCCM_110.value.byte,
    111: ConfigurationPacket.PacketTemplate.DATA_VCCM_111.value.byte,
    112: ConfigurationPacket.PacketTemplate.DATA_VCCM_112.value.byte,
    115: ConfigurationPacket.PacketTemplate.DATA_VCCM_115.value.byte
}

vswl_data_str_map = {
    1075: "01100",  # 1.075V 
    1100: "11011",  # 1.100V 
    1125: "11010",  # 1.125V 
    1150: "11001",  # 1.150V 
    1175: "11000",  # 1.175V 
    1200: "10111",  # 1.200V 
    1225: "10110",  # 1.225V 
    1250: "10101",  # 1.250V 
    1275: "10100",  # 1.275V 
    1300: "00011",  # 1.300V 
    1325: "00010",  # 1.325V 
    1350: "00001",  # 1.350V 
    1375: "11111",  # 1.375V 
    1400: "00000",  # 1.400V 
    1425: "11110",  # 1.425V 
    1450: "11101",  # 1.450V 
    1475: "11100",  # 1.475V 
    1500: "01010",  # 1.500V 
}

def process_vccm_and_vswl(bitstream_obj, vccm_value=105, vswl_selected: int = 1050):
    # 拿到数据帧之前的寄存器
    is_modiy_flag = False
    if bitstream_obj.file_type == ".rbt":
        for i in range(len(bitstream_obj.rbt_cfg_content_pre)):
            if bitstream_obj.rbt_cfg_content_pre[i].cmd_name == "COR1":
                cor1_data = bitstream_obj.rbt_cfg_content_pre[i].get_data_from_index(1)
                cor1_data = utils.update_data_by_index(cor1_data,[12,11,10],["1","0","1"])
                bitstream_obj.rbt_cfg_content_pre[i].set_data_to_index(1, cor1_data)
                bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_MASK.value.binstr)
                bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_MASK_VCCM.value.binstr)
                bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_TRIM.value.binstr)
                if vccm_value in vccm_data_str_map:
                    vccm_data = vccm_data_str_map.get(vccm_value)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(vccm_data)
                else:
                    raise ValueError("vccm_value 配置错误")
                
                if vccm_value == 115:
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_COR1.value.binstr)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_COR1_115_01.value.binstr)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_MASK.value.binstr)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_MASK_115_02.value.binstr)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_TRIM.value.binstr)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_TRIM_115_03.value.binstr)
                
                if vswl_selected in vswl_data_str_map:
                    # 新增 VS_WL 6行
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_COR1.value.binstr)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VSWL_COR1_01.value.binstr)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_MASK.value.binstr)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VSWL_MASK_02.value.binstr)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_TRIM.value.binstr)
                    vswl_06_data = ConfigurationPacket.PacketTemplate.DATA_VSWL_TRIM_03.value.binstr
                    
                    update_data = list(vswl_data_str_map.get(vswl_selected))
                    vswl_06_data = utils.update_data_by_index(vswl_06_data,[26,25,24,23,22],update_data)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(vswl_06_data)
            
            # 找连续的MASK+CTL1做修改，且仅改第一次
            if vccm_value == 115 \
                and i < len(bitstream_obj.rbt_cfg_content_pre)-1 \
                and bitstream_obj.rbt_cfg_content_pre[i].cmd_name == "MASK" \
                and bitstream_obj.rbt_cfg_content_pre[i+1].cmd_name == "CTL1" \
                and not is_modiy_flag:
                is_modiy_flag = True
                mask_data = bitstream_obj.rbt_cfg_content_pre[i].get_data_from_index(1)
                mask_data = utils.update_data_by_index(mask_data,[17,16,15,14,13,10,9,8,7,6],["1","1","1","1","1","1","1","1","1","1"])
                bitstream_obj.rbt_cfg_content_pre[i].set_data_to_index(1, mask_data)
                
    elif bitstream_obj.file_type == ".bit" or bitstream_obj.file_type == ".bin":
        for i in range(len(bitstream_obj.bit_cfg_content_pre)):
            if bitstream_obj.bit_cfg_content_pre[i].cmd_name == "COR1":
                cor1_data = utils.bytes_to_binary(bitstream_obj.bit_cfg_content_pre[i].get_data_from_index(1))
                cor1_data = utils.update_data_by_index(cor1_data,[12,11,10],["1","0","1"])
                bitstream_obj.bit_cfg_content_pre[i].set_data_to_index(1, utils.binary_str_to_bytes(cor1_data))
                bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_MASK.value.byte)
                bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_MASK_VCCM.value.byte)
                bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_TRIM.value.byte)
                if vccm_value in vccm_data_byte_map:
                    vccm_data = vccm_data_byte_map.get(vccm_value)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(vccm_data)
                else:
                    raise ValueError("vccm_value 配置错误")
                
                if vccm_value == 115:
                    bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_COR1.value.byte)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_COR1_115_01.value.byte)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_MASK.value.byte)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_MASK_115_02.value.byte)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_TRIM.value.byte)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VCCM_TRIM_115_03.value.byte)

                if vswl_selected in vswl_data_str_map:
                    # 新增 VS_WL 6行
                    bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_COR1.value.byte)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VSWL_COR1_01.value.byte)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_MASK.value.byte)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.DATA_VSWL_MASK_02.value.byte)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(ConfigurationPacket.PacketTemplate.CONFIG_TRIM.value.byte)
                    vswl_06_data = ConfigurationPacket.PacketTemplate.DATA_VSWL_TRIM_03.value.byte
                    
                    update_data = list(vswl_data_str_map.get(vswl_selected))
                    vswl_06_data = utils.update_data_by_index(vswl_06_data,[26,25,24,23,22],update_data)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(utils.binary_str_to_bytes(vswl_06_data))
            # 找连续的MASK+CTL1做修改，且仅改第一次
            if vccm_value == 115 \
                and i < len(bitstream_obj.bit_cfg_content_pre)-1 \
                and bitstream_obj.bit_cfg_content_pre[i].cmd_name == "MASK"\
                and bitstream_obj.bit_cfg_content_pre[i+1].cmd_name == "CTL1"\
                and not is_modiy_flag:
                is_modiy_flag = True
                mask_data = utils.bytes_to_binary(bitstream_obj.bit_cfg_content_pre[i].get_data_from_index(1))
                mask_data = utils.update_data_by_index(mask_data,[17,16,15,14,13,10,9,8,7,6],["1","1","1","1","1","1","1","1","1","1"])
                bitstream_obj.bit_cfg_content_pre[i].set_data_to_index(1, utils.binary_str_to_bytes(mask_data))