
import struct
import logging
import argparse
import COMMON.config as config
import COMMON.utils as utils
from collections import defaultdict

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
                word = utils.bytes_to_binary(bitstream_obj.bit_cfg_content_pre[i].get_data_from_index(1))
                word = word[:-13] + "1" + word[-12:]
                bitstream_obj.bit_cfg_content_pre[i].set_data_to_index(1, utils.binary_str_to_bytes(word))
                bitstream_obj.bit_cfg_content_pre[i].append_data(config.CMD_MASK_01_BYTE)
                bitstream_obj.bit_cfg_content_pre[i].append_data(config.CMD_MASK_02_BYTE)
                bitstream_obj.bit_cfg_content_pre[i].append_data(config.CMD_TRIM_01_BYTE)
                bitstream_obj.bit_cfg_content_pre[i].append_data(config.CMD_TRIM_02_BYTE)
    
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
