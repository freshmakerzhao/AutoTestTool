
import struct
import logging
import argparse
import COMMON.config as config
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
                bitstream_obj.rbt_cfg_content_pre[i].append_data(config.CMD_MASK_01_STR)
                bitstream_obj.rbt_cfg_content_pre[i].append_data(config.CMD_MASK_03_STR)
                bitstream_obj.rbt_cfg_content_pre[i].append_data(config.CMD_TRIM_01_STR)
                if vccm_value == 105:
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(config.VCCM_DATA_105_STR)
                elif vccm_value == 106:
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(config.VCCM_DATA_106_STR)
                elif vccm_value == 107:
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(config.VCCM_DATA_107_STR)
                elif vccm_value == 108:
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(config.VCCM_DATA_108_STR)
                elif vccm_value == 109:
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(config.VCCM_DATA_109_STR)
                elif vccm_value == 110:
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(config.VCCM_DATA_110_STR)
                elif vccm_value == 111:
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(config.VCCM_DATA_111_STR)
                elif vccm_value == 112:
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(config.VCCM_DATA_112_STR)
                else:
                    raise ValueError("vccm_value 配置错误")
                break
    elif bitstream_obj.file_type == ".bit" or bitstream_obj.file_type == ".bin":
        for i in range(len(bitstream_obj.bit_cfg_content_pre)):
            if bitstream_obj.bit_cfg_content_pre[i].cmd_name == "COR1":
                cor1_data = utils.bytes_to_binary(bitstream_obj.bit_cfg_content_pre[i].get_data_from_index(1))
                cor1_data = utils.update_data_by_index(cor1_data,[12,10],["1","1"])
                bitstream_obj.bit_cfg_content_pre[i].set_data_to_index(1, utils.binary_str_to_bytes(cor1_data))
                bitstream_obj.bit_cfg_content_pre[i].append_data(config.CMD_MASK_01_BYTE)
                bitstream_obj.bit_cfg_content_pre[i].append_data(config.CMD_MASK_03_BYTE)
                bitstream_obj.bit_cfg_content_pre[i].append_data(config.CMD_TRIM_01_BYTE)
                if vccm_value == 105:
                    bitstream_obj.bit_cfg_content_pre[i].append_data(config.VCCM_DATA_105_BYTE)
                elif vccm_value == 106:
                    bitstream_obj.bit_cfg_content_pre[i].append_data(config.VCCM_DATA_106_BYTE)
                elif vccm_value == 107:
                    bitstream_obj.bit_cfg_content_pre[i].append_data(config.VCCM_DATA_107_BYTE)
                elif vccm_value == 108:
                    bitstream_obj.bit_cfg_content_pre[i].append_data(config.VCCM_DATA_108_BYTE)
                elif vccm_value == 109:
                    bitstream_obj.bit_cfg_content_pre[i].append_data(config.VCCM_DATA_109_BYTE)
                elif vccm_value == 110:
                    bitstream_obj.bit_cfg_content_pre[i].append_data(config.VCCM_DATA_110_BYTE)
                elif vccm_value == 111:
                    bitstream_obj.bit_cfg_content_pre[i].append_data(config.VCCM_DATA_111_BYTE)
                elif vccm_value == 112:
                    bitstream_obj.bit_cfg_content_pre[i].append_data(config.VCCM_DATA_112_BYTE)
                else:
                    raise ValueError("vccm_value 配置错误")
                break

vccm_data_str_map = {
    105: config.VCCM_DATA_105_STR,
    106: config.VCCM_DATA_106_STR,
    107: config.VCCM_DATA_107_STR,
    108: config.VCCM_DATA_108_STR,
    109: config.VCCM_DATA_109_STR,
    110: config.VCCM_DATA_110_STR,
    111: config.VCCM_DATA_111_STR,
    112: config.VCCM_DATA_112_STR,
    115: config.VCCM_DATA_115_STR
}

vccm_data_byte_map = {
    105: config.VCCM_DATA_105_BYTE,
    106: config.VCCM_DATA_106_BYTE,
    107: config.VCCM_DATA_107_BYTE,
    108: config.VCCM_DATA_108_BYTE,
    109: config.VCCM_DATA_109_BYTE,
    110: config.VCCM_DATA_110_BYTE,
    111: config.VCCM_DATA_111_BYTE,
    112: config.VCCM_DATA_112_BYTE,
    115: config.VCCM_DATA_115_BYTE
}

vswl_data_str_map = {
    1075: config.VS_WL_1075_STR,
    1100: config.VS_WL_1100_STR,
    1125: config.VS_WL_1125_STR,
    1150: config.VS_WL_1150_STR,
    1175: config.VS_WL_1175_STR,
    1200: config.VS_WL_1200_STR,
    1225: config.VS_WL_1225_STR,
    1250: config.VS_WL_1250_STR,
    1275: config.VS_WL_1275_STR,
    1300: config.VS_WL_1300_STR,
    1325: config.VS_WL_1325_STR,
    1350: config.VS_WL_1350_STR,
    1375: config.VS_WL_1375_STR,
    1400: config.VS_WL_1400_STR,
    1425: config.VS_WL_1425_STR,
    1450: config.VS_WL_1450_STR,
    1475: config.VS_WL_1475_STR,
    1500: config.VS_WL_1500_STR,
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
                bitstream_obj.rbt_cfg_content_pre[i].append_data(config.CMD_MASK_01_STR)
                bitstream_obj.rbt_cfg_content_pre[i].append_data(config.CMD_MASK_03_STR)
                bitstream_obj.rbt_cfg_content_pre[i].append_data(config.CMD_TRIM_01_STR)
                if vccm_value in vccm_data_str_map:
                    vccm_data = vccm_data_str_map.get(vccm_value)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(vccm_data)
                else:
                    raise ValueError("vccm_value 配置错误")
                
                if vccm_value == 115:
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(config.SPECIFIC_115_01_STR)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(config.SPECIFIC_115_02_STR)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(config.SPECIFIC_115_03_STR)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(config.SPECIFIC_115_04_STR)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(config.SPECIFIC_115_05_STR)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(config.SPECIFIC_115_06_STR)
                
                if vswl_selected in vswl_data_str_map:
                    # 新增 VS_WL 6行
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(config.SPECIFIC_VS_WL_01_STR)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(config.SPECIFIC_VS_WL_02_STR)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(config.SPECIFIC_VS_WL_03_STR)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(config.SPECIFIC_VS_WL_04_STR)
                    bitstream_obj.rbt_cfg_content_pre[i].append_data(config.SPECIFIC_VS_WL_05_STR)
                    vswl_06_data = config.SPECIFIC_VS_WL_06_STR
                    
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
                bitstream_obj.bit_cfg_content_pre[i].append_data(config.CMD_MASK_01_BYTE)
                bitstream_obj.bit_cfg_content_pre[i].append_data(config.CMD_MASK_03_BYTE)
                bitstream_obj.bit_cfg_content_pre[i].append_data(config.CMD_TRIM_01_BYTE)
                if vccm_value in vccm_data_byte_map:
                    vccm_data = vccm_data_byte_map.get(vccm_value)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(vccm_data)
                else:
                    raise ValueError("vccm_value 配置错误")
                
                if vccm_value == 115:
                    bitstream_obj.bit_cfg_content_pre[i].append_data(config.SPECIFIC_115_01_BYTE)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(config.SPECIFIC_115_02_BYTE)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(config.SPECIFIC_115_03_BYTE)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(config.SPECIFIC_115_04_BYTE)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(config.SPECIFIC_115_05_BYTE)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(config.SPECIFIC_115_06_BYTE)

                if vswl_selected in vswl_data_str_map:
                    # 新增 VS_WL 6行
                    bitstream_obj.bit_cfg_content_pre[i].append_data(config.SPECIFIC_VS_WL_01_BYTE)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(config.SPECIFIC_VS_WL_02_BYTE)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(config.SPECIFIC_VS_WL_03_BYTE)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(config.SPECIFIC_VS_WL_04_BYTE)
                    bitstream_obj.bit_cfg_content_pre[i].append_data(config.SPECIFIC_VS_WL_05_BYTE)
                    
                    vswl_06_data = config.SPECIFIC_VS_WL_06_STR
                    
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