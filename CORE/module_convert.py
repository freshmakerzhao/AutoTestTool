import struct
import logging
import argparse
import COMMON.config as config
import COMMON.utils as utils
from collections import defaultdict
from datetime import datetime

def process_convert(bitstream_obj, target_type, output_file_path=None):
    stats = {"code": 200, "msg": ""}
    if target_type in bitstream_obj.file_type:
        stats["code"] = 400
        stats["msg"] = "文件类型一致"
        return stats
    
    # rbt 转 bit 和 bin
    if bitstream_obj.file_type == ".rbt":
        rbt_header_content = process_rbt_header_content(bitstream_obj.rbt_annotation_content)
        rbt_cfg_content_pre_hex_content = rbt_content_to_hex(bitstream_obj.rbt_cfg_content_pre)
        rbt_data_content_hex_content = rbt_content_to_hex(bitstream_obj.rbt_data_content)
        rbt_cfg_content_after_hex_content = rbt_content_to_hex(bitstream_obj.rbt_cfg_content_after)
        
        hex_str = "".join(
            rbt_cfg_content_pre_hex_content +
            rbt_data_content_hex_content +
            rbt_cfg_content_after_hex_content
        )
        
        # 计算长度
        byte_nums = len(bitstream_obj.rbt_data_content)
        for item in bitstream_obj.rbt_cfg_content_pre:
            byte_nums += item.get_data_len()
        for item in bitstream_obj.rbt_cfg_content_after:
            byte_nums += item.get_data_len()
        byte_nums = byte_nums * 32

        if target_type == "bin":
            write_hex_content_to_file(hex_str, output_file_path)
        elif target_type == "bit":
            rbt_header_content["bytes_len"] = byte_nums
            write_hex_content_to_file(hex_str, output_file_path, rbt_header_content=rbt_header_content)
            
def process_rbt_header_content(rbt_annotation_content):
    """
    从一个包含bitstream信息的字符串列表中提取如下字段：
      - bits: 位长度
      - part_name: Part 字段
      - top_module_name: 从 Design name 字段中提取 top module
      - userid: 从 Design name 字段中提取的 UserID
      - tools_version: 从 Design name 字段中提取的 Version

    如果某个字段缺失，则使用默认值并发出警告。
    """
    # 定义默认值
    result = {
        "bits": -1,
        "part_name": "7a100tfgg484",
        "top_module_name": "top",
        "userid": "0XFFFFFFFF",
        "tools_version": "2020.1",
        "ymd": "2023/04/24",   # 年/月/日
        "hms": "05:02:01"    # 时:分:秒
    }
    for line in rbt_annotation_content:
        line = line.strip()
        # "Design name:   xilinx_pcie_2_1_rport_7x;UserID=0XFFFFFFFF;Version=2020.2"
        if line.startswith("Design name:"):
            content_line = line[len("Design name:"):].strip()
            content_list = content_line.split(";")
            if content_list and content_list[0].strip():
                top_module_name = content_list[0].strip()
                if top_module_name:
                    result["top_module_name"] = top_module_name
                else:
                    result["top_module_name"] = "top"
                    logging.warning(f"rbt文件中未找到 top module name, 默认值为 top")
            else:
                result["top_module_name"] = "top"
                logging.warning(f"rbt文件中未找到 top module name, 默认值为 top")
            for item in content_list[1:]:
                item = item.strip()
                if item.startswith("UserID="):
                    userid = item[len("UserID="):].strip()
                    if userid:
                        result["userid"] = userid
                    else:
                        result["userid"] = "0XFFFFFFFF"
                        logging.warning(f"rbt文件中未找到 userid, 默认值为 0XFFFFFFFF")
                elif item.startswith("Version="):
                    tools_version = item[len("Version="):].strip()
                    if tools_version:
                        result["tools_version"] = tools_version
                    else:
                        result["tools_version"] = "2020.1"
                        logging.warning(f"rbt文件中未找到 version, 默认值为 2020.1")
        # 处理 Part 行，例如："Part:          7a100tfgg484"
        elif line.startswith("Part:"):
            part_name = line[len("Part:"):].strip()
            if part_name:
                result["part_name"] = part_name
            else:
                result["part_name"] = "7a100tfgg484"
                logging.warning(f"rbt文件中未找到 Part 字段, 默认值为 7a100tfgg484")
        # 处理 Bits 行，例如："Bits:          30606304"
        elif line.startswith("Bits:"):
            bits = line[len("Bits:"):].strip()
            if bits:
                result["bits"] = bits
            else:
                result["bits"] = -1
                logging.warning(f"rbt文件中未找到 Bits 字段")
                
    now = datetime.now()
    result["ymd"] = now.strftime("%Y/%m/%d")
    result["hms"] = now.strftime("%H:%M:%S")
    return result

# 将32位二进制一个元素的list转为4字节十六进制一个元素的bit list
def rbt_content_to_hex(binary_content):
    hex_list = []
    for line in binary_content:
        binary_data = line.strip()
        cur_len = len(binary_data)
        try:
            # 使用列表推导式将每 4 位二进制转换为十六进制
            hex_list.append(''.join(utils.binary_to_bytes(binary_data[i:i+4]) for i in range(0, cur_len, 4)))
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
    return hex_list


def write_hex_content_to_file(hex_str, file_path, rbt_header_content = None):
    with open(file_path, 'wb') as file:
        if rbt_header_content:
            bit_header = bytearray()
            # 同步字
            bit_header.extend(b'\x00\x09\x0F\xF0\x0F\xF0\x0F\xF0\x0F\xF0\x00\x00\x01')
            # ============================ a ============================
            bit_header.extend(b'\x61')
            group_a = rbt_header_content["top_module_name"] + ";" + "UserID=" + rbt_header_content["userid"] + ";" + "Version=" + rbt_header_content["tools_version"]
            group_a_byte = group_a.encode("utf-8")
            group_a_byte_length = len(group_a_byte) + 1
            bit_header.append((group_a_byte_length >> 8) & 0xFF)
            bit_header.append(group_a_byte_length & 0xFF)
            bit_header.extend(group_a_byte)
            bit_header.append(0x00)
            # ============================ a ============================
            
            # ============================ b ============================
            bit_header.extend(b'\x62')
            group_b_byte = rbt_header_content["part_name"].encode("utf-8")
            group_b_byte_length = len(group_b_byte) + 1
            bit_header.append((group_b_byte_length >> 8) & 0xFF)
            bit_header.append(group_b_byte_length & 0xFF)
            bit_header.extend(group_b_byte)
            bit_header.append(0x00)
            # ============================ b ============================
            
            # ============================ c ============================
            bit_header.extend(b'\x63')
            group_c_byte = rbt_header_content["ymd"].encode("utf-8")
            group_c_byte_length = len(group_c_byte) + 1
            bit_header.append((group_c_byte_length >> 8) & 0xFF)
            bit_header.append(group_c_byte_length & 0xFF)
            bit_header.extend(group_c_byte)
            bit_header.append(0x00)
            # ============================ c ============================
            
            # ============================ d ============================
            bit_header.extend(b'\x64')
            group_d_byte = rbt_header_content["hms"].encode("utf-8")
            group_d_byte_length = len(group_d_byte) + 1
            bit_header.append((group_d_byte_length >> 8) & 0xFF)
            bit_header.append(group_d_byte_length & 0xFF)
            bit_header.extend(group_d_byte)
            bit_header.append(0x00)
            # ============================ d ============================
            
            # ============================ e ============================
            bit_header.extend(b'\x65')
            group_e_byte = rbt_header_content["bytes_len"].to_bytes(4, byteorder='big')
            bit_header.extend(group_e_byte)
            # ============================ e ============================
            file.write(bit_header)
            
        # 将十六进制字符串转换为字节
        bytes_to_write = bytes.fromhex(hex_str)
        file.write(bytes_to_write)
