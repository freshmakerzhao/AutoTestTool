
import struct
import logging
import argparse
import COMMON.config as config
import COMMON.utils as utils
from collections import defaultdict

# 设置定时刷新
def timer_refresh(bitstream_obj, RHBD_DATA_STR="00000000000000000000000000000000"):
    # 长度必须是 32
    if len(RHBD_DATA_STR) != 32:
        raise ValueError("RHBD_DATA_STR 长度不合法，必须为 32 位")

    # 只能包含 0 或 1
    if not set(RHBD_DATA_STR) <= {"0", "1"}:
        raise ValueError("RHBD_DATA_STR 只能是二进制字符串，包含 0 或 1")

    # 拿到数据帧之前的寄存器
    if bitstream_obj.file_type == ".rbt":
        cur_index = 0
        while cur_index < len(bitstream_obj.rbt_cfg_content_pre):
            if bitstream_obj.rbt_cfg_content_pre[cur_index].cmd_name == "COR0":
                # 更新COR0
                cur_cor_reg  = bitstream_obj.rbt_cfg_content_pre[cur_index].get_data_from_index(0)
                cur_cor_data = bitstream_obj.rbt_cfg_content_pre[cur_index].get_data_from_index(1)
                new_cor_data = utils.update_data_by_index(cur_cor_data,[30,29,28],["0","1","0"])
                bitstream_obj.rbt_cfg_content_pre[cur_index].set_data_to_index(1, new_cor_data)
                
                # ============ 插入noop * 2 ============ 
                for _ in range(2):
                    item = bitstream_obj.PacketItem("NOOP")
                    item.set_opcode(-1)
                    item.append_data(config.NOOP_STR)
                    bitstream_obj.rbt_cfg_content_pre.insert(cur_index+1, item)
                    cur_index += 1
                # ============ 插入noop * 2 ============ 
                
                # ============ 插入RHBD ============ 
                item = bitstream_obj.PacketItem("RHBD")
                item.set_opcode(-1)
                item.append_data(config.RHBD_REG_STR)
                line = config.ZERO_DATA_STR
                new_line = utils.update_data_by_index(line,[4],["1"])
                item.append_data(new_line)
                bitstream_obj.rbt_cfg_content_pre.insert(cur_index+1, item)
                cur_index += 1
                # ============ 插入RHBD ============ 
                
                # ============ 插入noop * 2 ============ 
                for _ in range(2):
                    item = bitstream_obj.PacketItem("NOOP")
                    item.set_opcode(-1)
                    item.append_data(config.NOOP_STR)
                    bitstream_obj.rbt_cfg_content_pre.insert(cur_index+1, item)
                    cur_index += 1
                # ============ 插入noop * 2 ============ 
                
                # ============ 插入COR0  ============ 
                new_cor_data = utils.update_data_by_index(cur_cor_data,[30,29,28],["0","0","1"])
                item = bitstream_obj.PacketItem("COR0")
                item.set_opcode(2)
                item.append_data(cur_cor_reg)
                item.append_data(new_cor_data)
                bitstream_obj.rbt_cfg_content_pre.insert(cur_index+1, item)
                cur_index += 1
                # ============ 插入COR0  ============ 
                
                # ============ 插入noop * 2 ============ 
                for _ in range(2):
                    item = bitstream_obj.PacketItem("NOOP")
                    item.set_opcode(-1)
                    item.append_data(config.NOOP_STR)
                    bitstream_obj.rbt_cfg_content_pre.insert(cur_index+1, item)
                    cur_index += 1
                # ============ 插入noop * 2 ============ 
                
                # ============ 插入RHBD ============ 
                item = bitstream_obj.PacketItem("RHBD")
                item.set_opcode(-1)
                item.append_data(config.RHBD_REG_STR)
                item.append_data(RHBD_DATA_STR)
                bitstream_obj.rbt_cfg_content_pre.insert(cur_index+1, item)
                cur_index += 1
                # ============ 插入RHBD ============ 
                
                # ============ 插入noop * 2 ============ 
                for _ in range(2):
                    item = bitstream_obj.PacketItem("NOOP")
                    item.set_opcode(-1)
                    item.append_data(config.NOOP_STR)
                    bitstream_obj.rbt_cfg_content_pre.insert(cur_index+1, item)
                    cur_index += 1
                # ============ 插入noop * 2 ============ 
                break
            cur_index += 1
    elif bitstream_obj.file_type == ".bit" or bitstream_obj.file_type == ".bin":         
                # word = utils.bytes_to_binary(bitstream_obj.bit_cfg_content_pre[i].get_data_from_index(1))
        while cur_index < len(bitstream_obj.bit_cfg_content_pre):
            if bitstream_obj.bit_cfg_content_pre[cur_index].cmd_name == "COR0":
                # 更新COR0
                cor_data = utils.bytes_to_binary(bitstream_obj.bit_cfg_content_pre[cur_index].get_data_from_index(1))
                new_cor_data = utils.update_data_by_index(cor_data,[30,29,28],["0","1","0"])
                bitstream_obj.bit_cfg_content_pre[cur_index].set_data_to_index(1, utils.binary_str_to_bytes(new_cor_data))
                
                # ============ 插入noop * 2 ============ 
                for _ in range(2):
                    item = bitstream_obj.PacketItem("NOOP")
                    item.set_opcode(-1)
                    item.append_data(config.NOOP_BYTE)
                    bitstream_obj.bit_cfg_content_pre.insert(cur_index+1, item)
                    cur_index += 1
                # ============ 插入noop * 2 ============ 
                
                
                # ============ 插入RHBD ============ 
                item = bitstream_obj.PacketItem("RHBD")
                item.set_opcode(-1)
                item.append_data(config.RHBD_REG_BYTE)
                item.append_data(utils.binary_str_to_bytes(RHBD_DATA_STR))
                bitstream_obj.bit_cfg_content_pre.insert(cur_index+1, item)
                cur_index += 1
                # ============ 插入RHBD ============ 
                
                # ============ 插入noop * 2 ============ 
                for _ in range(2):
                    item = bitstream_obj.PacketItem("NOOP")
                    item.set_opcode(-1)
                    item.append_data(config.NOOP_BYTE)
                    bitstream_obj.bit_cfg_content_pre.insert(cur_index+1, item)
                    cur_index += 1
                # ============ 插入noop * 2 ============ 
                break
            cur_index += 1
    
# 设置回读刷新
def readback_refresh(bitstream_obj, RHBD_DATA_STR="00000000000000000000000000000000"):
    # 长度必须是 32
    if len(RHBD_DATA_STR) != 32:
        raise ValueError("RHBD_DATA_STR 长度不合法，必须为 32 位")

    # 只能包含 0 或 1
    if not set(RHBD_DATA_STR) <= {"0", "1"}:
        raise ValueError("RHBD_DATA_STR 只能是二进制字符串，包含 0 或 1")

    # 拿到数据帧之前的寄存器
    if bitstream_obj.file_type == ".rbt":
        cur_index = 0
        while cur_index < len(bitstream_obj.rbt_cfg_content_pre):
            if bitstream_obj.rbt_cfg_content_pre[cur_index].cmd_name == "COR0":
                # 更新COR0
                cor_data = bitstream_obj.rbt_cfg_content_pre[cur_index].get_data_from_index(1)
                new_cor_data = utils.update_data_by_index(cor_data,[30,29,28],["0","1","0"])
                bitstream_obj.rbt_cfg_content_pre[cur_index].set_data_to_index(1, new_cor_data)
                
                # ============ 插入noop * 2 ============ 
                for _ in range(2):
                    item = bitstream_obj.PacketItem("NOOP")
                    item.set_opcode(-1)
                    item.append_data(config.NOOP_STR)
                    bitstream_obj.rbt_cfg_content_pre.insert(cur_index+1, item)
                    cur_index += 1
                # ============ 插入noop * 2 ============ 
                
                # ============ 插入RHBD ============ 
                item = bitstream_obj.PacketItem("RHBD")
                item.set_opcode(-1)
                item.append_data(config.RHBD_REG_STR)
                item.append_data(RHBD_DATA_STR)
                bitstream_obj.rbt_cfg_content_pre.insert(cur_index+1, item)
                cur_index += 1
                # ============ 插入RHBD ============ 
                
                # ============ 插入noop * 2 ============ 
                for _ in range(2):
                    item = bitstream_obj.PacketItem("NOOP")
                    item.set_opcode(-1)
                    item.append_data(config.NOOP_STR)
                    bitstream_obj.rbt_cfg_content_pre.insert(cur_index+1, item)
                    cur_index += 1
                # ============ 插入noop * 2 ============ 
                break
            cur_index += 1
    elif bitstream_obj.file_type == ".bit" or bitstream_obj.file_type == ".bin":         
                # word = utils.bytes_to_binary(bitstream_obj.bit_cfg_content_pre[i].get_data_from_index(1))
        while cur_index < len(bitstream_obj.bit_cfg_content_pre):
            if bitstream_obj.bit_cfg_content_pre[cur_index].cmd_name == "COR0":
                # 更新COR0
                cor_data = utils.bytes_to_binary(bitstream_obj.bit_cfg_content_pre[cur_index].get_data_from_index(1))
                new_cor_data = utils.update_data_by_index(cor_data,[30,29,28],["0","1","0"])
                bitstream_obj.bit_cfg_content_pre[cur_index].set_data_to_index(1, utils.binary_str_to_bytes(new_cor_data))
                
                # ============ 插入noop * 2 ============ 
                for _ in range(2):
                    item = bitstream_obj.PacketItem("NOOP")
                    item.set_opcode(-1)
                    item.append_data(config.NOOP_BYTE)
                    bitstream_obj.bit_cfg_content_pre.insert(cur_index+1, item)
                    cur_index += 1
                # ============ 插入noop * 2 ============ 
                
                
                # ============ 插入RHBD ============ 
                item = bitstream_obj.PacketItem("RHBD")
                item.set_opcode(-1)
                item.append_data(config.RHBD_REG_BYTE)
                item.append_data(utils.binary_str_to_bytes(RHBD_DATA_STR))
                bitstream_obj.bit_cfg_content_pre.insert(cur_index+1, item)
                cur_index += 1
                # ============ 插入RHBD ============ 
                
                # ============ 插入noop * 2 ============ 
                for _ in range(2):
                    item = bitstream_obj.PacketItem("NOOP")
                    item.set_opcode(-1)
                    item.append_data(config.NOOP_BYTE)
                    bitstream_obj.bit_cfg_content_pre.insert(cur_index+1, item)
                    cur_index += 1
                # ============ 插入noop * 2 ============ 
                break
            cur_index += 1
