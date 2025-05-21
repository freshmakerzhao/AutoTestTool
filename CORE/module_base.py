import logging
import COMMON.config as config
import COMMON.utils as utils
from collections import defaultdict

# 配置日志级别和格式
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# logging.basicConfig(level=logging.WARNING,  format='%(asctime)s - %(levelname)s - %(message)s')
# logging.basicConfig(level=logging.INFO,  format='%(asctime)s - %(levelname)s - %(message)s')

# ====================== GTP 修改位置和数据 ====================== 
GTP_CONFIG = [
    {"frame": 3829, "word":  0, "bit": 2, "data": "1"},
    {"frame": 3829, "word": 22, "bit": 2, "data": "1"},
    {"frame": 3829, "word": 57, "bit": 2, "data": "1"},
    {"frame": 3829, "word": 79, "bit": 2, "data": "1"}
]
# ====================== GTP 修改位置和数据 ====================== 

# ====================== PCIE 校验位 ====================== 
PCIE_CHECK = {
    0:[
        {"frame": 3454, "word":  20, "bit": 26, "data": "1"},
        {"frame": 3455, "word":  20, "bit": 24, "data": "1"},
        {"frame": 3455, "word":  20, "bit": 21, "data": "1"},
        {"frame": 3475, "word":  21, "bit":  8, "data": "1"},
        {"frame": 3479, "word":  21, "bit":  8, "data": "1"},
        
    ],
    1:[ 
        {"frame": 3454, "word":  22, "bit": 12, "data": "1"},   
        {"frame": 3462, "word":  22, "bit": 15, "data": "1"},    
        {"frame": 3475, "word":  22, "bit":  8, "data": "1"},   
        {"frame": 3479, "word":  22, "bit":  8, "data": "1"}
    ],
    2:[
        {"frame": 3455, "word":  22, "bit":  7, "data": "1"},
        {"frame": 3462, "word":  22, "bit": 14, "data": "1"},    
        {"frame": 3475, "word":  22, "bit":  0, "data": "1"},
        {"frame": 3479, "word":  22, "bit":  0, "data": "1"}
    ]
}
# ====================== PCIE 校验位 ====================== 

# ====================== PCIE 修改位置 ====================== 
PCIE_CONFIG = {
    0:[
        {"frame": 3454, "word":  20, "bit": 26, "data": "1"},
        {"frame": 3454, "word":  20, "bit": 25, "data": "1"},
        {"frame": 3455, "word":  20, "bit": 24, "data": "1"},
        {"frame": 3455, "word":  20, "bit": 21, "data": "1"},
        {"frame": 3475, "word":  21, "bit":  8, "data": "1"},
        {"frame": 3479, "word":  21, "bit":  8, "data": "1"},
        {"frame": 3829, "word":   0, "bit":  2, "data": "1"},
        {"frame": 3829, "word":  22, "bit":  2, "data": "1"},
        {"frame": 3829, "word":  57, "bit":  2, "data": "1"},
        {"frame": 3829, "word":  79, "bit":  2, "data": "1"}
    ],
    1:[
        {"frame": 3454, "word":  20, "bit": 25, "data": "1"},   
        {"frame": 3454, "word":  20, "bit": 22, "data": "1"},   
        {"frame": 3454, "word":  22, "bit": 12, "data": "1"},   
        {"frame": 3462, "word":  22, "bit": 15, "data": "1"},   
        {"frame": 3468, "word":  22, "bit": 15, "data": "1"},   
        {"frame": 3475, "word":  22, "bit":  8, "data": "1"},   
        {"frame": 3479, "word":  22, "bit":  8, "data": "1"},
        {"frame": 3829, "word":   0, "bit":  2, "data": "1"},
        {"frame": 3829, "word":  22, "bit":  2, "data": "1"},
        {"frame": 3829, "word":  57, "bit":  2, "data": "1"},
        {"frame": 3829, "word":  79, "bit":  2, "data": "1"}  
    ],
    2:[
        {"frame": 3454, "word":  20, "bit": 25, "data": "1"},
        {"frame": 3454, "word":  20, "bit": 22, "data": "1"},
        {"frame": 3455, "word":  22, "bit":  7, "data": "1"},
        {"frame": 3462, "word":  22, "bit": 14, "data": "1"},
        {"frame": 3468, "word":  22, "bit": 15, "data": "1"},
        {"frame": 3475, "word":  22, "bit":  0, "data": "1"},
        {"frame": 3479, "word":  22, "bit":  0, "data": "1"}, 
        {"frame": 3829, "word":   0, "bit":  2, "data": "1"},
        {"frame": 3829, "word":  22, "bit":  2, "data": "1"},
        {"frame": 3829, "word":  57, "bit":  2, "data": "1"},
        {"frame": 3829, "word":  79, "bit":  2, "data": "1"}  
    ]
}
# ====================== PCIE 修改位置 ====================== 

# 修改trim0寄存器，从0置1  
def process_trim(bitsteam_obj):
    # 拿到数据帧之前的寄存器
    if bitsteam_obj.file_type == ".rbt":
        for i in range(len(bitsteam_obj.rbt_cfg_content_pre)):
            if bitsteam_obj.rbt_cfg_content_pre[i].cmd_name == "COR1":
                new_line = bitsteam_obj.rbt_cfg_content_pre[i].get_data_from_index(1)[:-13] + "1" + bitsteam_obj.rbt_cfg_content_pre[i].get_data_from_index(1)[-12:]
                bitsteam_obj.rbt_cfg_content_pre[i].set_data_to_index(1, new_line)
                bitsteam_obj.rbt_cfg_content_pre[i].append_data(config.CMD_MASK_01_STR)
                bitsteam_obj.rbt_cfg_content_pre[i].append_data(config.CMD_MASK_02_STR)
                bitsteam_obj.rbt_cfg_content_pre[i].append_data(config.CMD_TRIM_01_STR)
                bitsteam_obj.rbt_cfg_content_pre[i].append_data(config.CMD_TRIM_02_STR)
    elif bitsteam_obj.file_type == ".bit" or bitsteam_obj.file_type == ".bin":
        for i in range(len(bitsteam_obj.bit_cfg_content_pre)):
            if bitsteam_obj.bit_cfg_content_pre[i].cmd_name == "COR1":
                word = utils.bytes_to_binary(bitsteam_obj.bit_cfg_content_pre[i].get_data_from_index(1))
                word = word[:-13] + "1" + word[-12:]
                bitsteam_obj.bit_cfg_content_pre[i].set_data_to_index(1, utils.binary_str_to_bytes(word))
                bitsteam_obj.bit_cfg_content_pre[i].append_data(config.CMD_MASK_01_BYTE)
                bitsteam_obj.bit_cfg_content_pre[i].append_data(config.CMD_MASK_02_BYTE)
                bitsteam_obj.bit_cfg_content_pre[i].append_data(config.CMD_TRIM_01_BYTE)
                bitsteam_obj.bit_cfg_content_pre[i].append_data(config.CMD_TRIM_02_BYTE)
            
# 修改gtp     
def process_gtp_config(bitsteam_obj):
    for item in GTP_CONFIG:
        bitsteam_obj.set_data_with_frame_word_bit(
            item["data"], item["frame"], item["word"], item["bit"]
        )
  
# 处理PCIE    
def process_pcie_config(bitsteam_obj):
    # 处理PCIE
    for index in PCIE_CHECK:
        check_group = PCIE_CHECK[index]
        cur_group_have_value = False
        for item in check_group:
            bit = bitsteam_obj.get_data_with_frame_word_bit(item["frame"],  item["word"], item["bit"])
            if bit == "1":
                # 有任意一个为1，这组就无法修改
                cur_group_have_value = True
                break
        if cur_group_have_value:
            # 下一组
            continue
        else:
            # 如果这一组全为0，则这组可修改
            config_group = PCIE_CONFIG[index]
            for item in config_group:
                bitsteam_obj.set_data_with_frame_word_bit(item["data"], item["frame"],  item["word"], item["bit"])
            break
    else:
        raise ValueError("PCIE 规则无法适配")

# delete_ghigh
def delete_ghigh(bitsteam_obj):
    # 拿到数据帧之后的寄存器
    if bitsteam_obj.file_type == ".rbt":
        bitsteam_obj.rbt_cfg_content_after = [item for item in bitsteam_obj.rbt_cfg_content_after
                            if not (item.cmd_name == "CMD" and (item.get_data_from_index(1) == "00000000000000000000000000000011"))]
    elif bitsteam_obj.file_type == ".bit" or bitsteam_obj.file_type == ".bin":
        bitsteam_obj.bit_cfg_content_after = [item for item in bitsteam_obj.bit_cfg_content_after
                            if not (item.cmd_name == "CMD" and (item.get_data_from_index(1) == b"\x00\x00\x00\x03"))]
           
def process_compress(bitsteam_obj):
    # 数据帧特征值作为key
    # value : 
    # {   
    #     "FAR": {
    #         "frame_type": 0,
    #         "region_type": 0,
    #         "row_num": 0,
    #         "col_num": 0,
    #         "frame_index": 0
    #     },
    #     "index":{
    #         "start_index":0,
    #         "end_index":101
    #     },
    #     "feature": "123"
    # }
    
    # 每个row相互独立
    data_frame_features_index = defaultdict(list)
    start_index = 0
    end_index = 101 # 这里是开区间，不包括101
    cur_row = 0
    frame_count = 0
    all_frame_count = 0
    
    # ================================= 解析位流 开始 =========================================
    for frame_type_key, frame_type_value in getattr(config, bitsteam_obj.device + "_FRAME_STRUCT").items():
        
        # type 0 type 1
        data_frame_features_index[frame_type_key] = {}
        
        # 遍历 frame_type 层
        for region_type_key, region_type_value in frame_type_value.items():
            
            # top bottom
            data_frame_features_index[frame_type_key][region_type_key] = {}
            
            # 遍历 region_type 层
            for row_num_key, row_data in region_type_value.items():
                
                # row 0 1
                data_frame_features_index[frame_type_key][region_type_key][row_num_key] = defaultdict(list)
                frame_count = 0
                # 遍历 row_num 层
                for col_num_key, group_data_item in row_data.items():
                    # group_data_item 包含 FAR 和 frame_count
                    frame_count += group_data_item["frame_count"]
                    word_count = group_data_item["frame_count"] * 101 # 这里拿到word数
                    end_index = start_index + word_count
                    
                    # 每次拿一帧的数据计算
                    frame_index = 0
                    for index in range(start_index, end_index, 101):
                        if bitsteam_obj.file_type == ".rbt":
                            feature = utils.get_feature(bitsteam_obj.rbt_data_content[index:index+101] , "str")
                        elif bitsteam_obj.file_type == ".bit" or bitsteam_obj.file_type == ".bin":
                            feature = utils.get_feature(bitsteam_obj.bit_data_content[index:index+101] , "int")
                            
                        
                        # 添加到字典
                        data_frame_features_index[frame_type_key][region_type_key][row_num_key][feature].append(
                            {
                                "FAR": {
                                    "frame_type": group_data_item["FAR"]["frame_type"],
                                    "region_type": group_data_item["FAR"]["region_type"],
                                    "row_num": group_data_item["FAR"]["row_num"],
                                    "col_num": group_data_item["FAR"]["col_num"],
                                    "frame_index": frame_index
                                },
                                "index": {
                                    "start_index": index,
                                    "end_index": index + 101
                                },
                                "feature": feature
                            }
                        )
                        frame_index += 1
                    
                    # 更新 start_index
                    start_index = end_index
                    
                # 完成一个row后，start_index需要向后跳两帧，这里有两帧的pad
                start_index += 101*2
                
                all_frame_count += frame_count
    # ================================= 解析位流 结束 =========================================
    
    new_data_frame = [] # 存储新生成的data frame
    is_first = True
    config_suffix = "_STR" if bitsteam_obj.file_type == ".rbt" else "_BYTE"
    
    # 构造FAR
    def get_frame_address_register(frame_type, region_type, row_num, col_num, frame_index):
        # 00000000000000000000000000000000	frame_type:0 region_type:0 row_num:0 col_num:0 frame_index:0
        # 构造32位二进制数
        decimal_value = (frame_type << 23) | (region_type << 22) | (row_num << 17) | (col_num << 7) | frame_index
        
        if bitsteam_obj.file_type == ".rbt":
            # 转换为32位二进制字符串
            return format(decimal_value, '032b')
        elif bitsteam_obj.file_type == ".bit" or bitsteam_obj.file_type == ".bin":
            return utils.decimal_to_bytes(decimal_value)
            
    # 获取Totalword
    def get_total_word(word_count):
        # 将 word_count 转换为 28 位的二进制字符串，不足 28 位补 0，超出则截取
        word_count_binary = f'{word_count:028b}'[-28:]
        fixed_part = "0101"
        total_word = fixed_part + word_count_binary
        if bitsteam_obj.file_type == ".rbt":
            return total_word
        elif bitsteam_obj.file_type == ".bit" or bitsteam_obj.file_type == ".bin":
            return utils.binary_str_to_bytes(total_word)
            
    # 构造可变的cmd
    def get_cmd_from_word_count(word_count,cmd):
        # 将 word_count 转换为 11 位的二进制字符串，不足 11 位补 0，超出则截取
        word_count_binary = f'{word_count:011b}'[-11:]
        if cmd == "FDRI":
            fixed_part = "001100000000000001000"
        elif cmd == "MFWR":
            fixed_part = "001100000000000101000"
        else:
            pass
        
        # 拼接前 22 位和后 11 位的 word_count(二进制字符串)
        frame_data_register_input = fixed_part + word_count_binary
        
        if bitsteam_obj.file_type == ".rbt":
            return frame_data_register_input
        elif bitsteam_obj.file_type == ".bit" or bitsteam_obj.file_type == ".bin":
            return utils.binary_str_to_bytes(frame_data_register_input)
            
    # 插入数据，方便维护
    def insert_data(content):
        new_data_frame.append(content)
        
    def insert_multiple_words(content):
        new_data_frame.extend(content)
    
    # ================================= 构造压缩位流数据帧部分 开始 =========================================
    for frame_type_key, frame_type_value in data_frame_features_index.items():
        # 遍历 frame_type 层
        for region_type_key, region_type_value in frame_type_value.items():
            # 遍历 region_type 层
            for row_num_key, row_data in region_type_value.items():
                # 遍历 row_num 层,每个元素
                # feature : 
                # [{   
                #     "FAR": {
                #         "frame_type": 0,
                #         "region_type": 0,
                #         "row_num": 0,
                #         "col_num": 0,
                #         "frame_index": 0
                #     },
                #     "index":{
                #         "start_index":0,
                #         "end_index":101
                #     },
                #     "feature": "123"
                # },
                # ...]
                
                # 获取当前row出现的所有特征值，方便后续做单帧判断
                features_list = list(row_data.keys())
                features_list_len = len(features_list)
                feature_index = 0
                
                while feature_index < features_list_len:
                    current_feature = features_list[feature_index]
                    
                    # 当前特征值下帧数目
                    group_len = len(row_data[current_feature])
                
                    if group_len > 1:
                        # 多帧数据
                        # ================= 首帧格式 ======================
                        if is_first:
                            insert_data(getattr(config, "FAR"+config_suffix))
                            insert_data(get_frame_address_register(row_data[current_feature][0]["FAR"]["frame_type"], row_data[current_feature][0]["FAR"]["region_type"], row_data[current_feature][0]["FAR"]["row_num"], row_data[current_feature][0]["FAR"]["col_num"], row_data[current_feature][0]["FAR"]["frame_index"]))
                            insert_data(getattr(config, "CMD"+config_suffix))
                            insert_data(getattr(config, "WCFG"+config_suffix))
                            insert_data(getattr(config, "NOOP"+config_suffix))
                            insert_data(get_cmd_from_word_count(101, "FDRI"))
                            
                            if bitsteam_obj.file_type == ".rbt":
                                insert_multiple_words(bitsteam_obj.rbt_data_content[row_data[current_feature][0]['index']['start_index']:row_data[current_feature][0]['index']['end_index']])
                            elif bitsteam_obj.file_type == ".bit" or bitsteam_obj.file_type == ".bin":
                                insert_multiple_words(bitsteam_obj.bit_data_content[row_data[current_feature][0]['index']['start_index']:row_data[current_feature][0]['index']['end_index']])
                            
                            is_first = False
                        else:
                            insert_data(getattr(config, "CMD"+config_suffix))
                            insert_data(getattr(config, "WCFG"+config_suffix))
                            insert_data(getattr(config, "NOOP"+config_suffix))
                            insert_data(getattr(config, "FAR"+config_suffix))
                            insert_data(get_frame_address_register(row_data[current_feature][0]["FAR"]["frame_type"], row_data[current_feature][0]["FAR"]["region_type"], row_data[current_feature][0]["FAR"]["row_num"], row_data[current_feature][0]["FAR"]["col_num"], row_data[current_feature][0]["FAR"]["frame_index"]))
                            insert_data(getattr(config, "NOOP"+config_suffix))
                            insert_data(get_cmd_from_word_count(101, "FDRI"))
                            if bitsteam_obj.file_type == ".rbt":
                                insert_multiple_words(bitsteam_obj.rbt_data_content[row_data[current_feature][0]['index']['start_index']:row_data[current_feature][0]['index']['end_index']])
                            elif bitsteam_obj.file_type == ".bit" or bitsteam_obj.file_type == ".bin":
                                insert_multiple_words(bitsteam_obj.bit_data_content[row_data[current_feature][0]['index']['start_index']:row_data[current_feature][0]['index']['end_index']])

                        insert_data(getattr(config, "CMD"+config_suffix))
                        insert_data(getattr(config, "MFW"+config_suffix))
                        for _ in range(12):
                            insert_data(getattr(config, "NOOP"+config_suffix))
                        insert_data(get_cmd_from_word_count(8, "MFWR"))
                        for _ in range(8):
                            insert_data(getattr(config, "ZERO"+config_suffix))
                        
                        if frame_type_key == "frame_type_1":
                            # type 1时，头帧要等待8个 cycle，后续数据才能继续写入
                            for _ in range(8):
                                insert_data(getattr(config, "NOOP"+config_suffix))
                        # ================= 首帧格式 ======================
                            
                        # 从第二帧开始, 压缩写入
                        for frame_index in range(1, group_len):
                            insert_data(getattr(config, "FAR"+config_suffix))
                            insert_data(get_frame_address_register(row_data[current_feature][frame_index]["FAR"]["frame_type"], row_data[current_feature][frame_index]["FAR"]["region_type"], row_data[current_feature][frame_index]["FAR"]["row_num"], row_data[current_feature][frame_index]["FAR"]["col_num"], row_data[current_feature][frame_index]["FAR"]["frame_index"]))
                            insert_data(get_cmd_from_word_count(4, "MFWR"))
                            for _ in range(4):
                                insert_data(getattr(config, "ZERO"+config_suffix))
                            if frame_type_key == "frame_type_1":
                                # type 1时，数据写入后要等待8个 cycle
                                for _ in range(8):
                                    insert_data(getattr(config, "NOOP"+config_suffix))
                        
                        # 到下一个
                        feature_index += 1;        
                    elif group_len == 1:
                        # 单帧时

                        # 需要判断下面的帧是否为单帧，直到找到一个非单帧结束
                        # 单帧连续时，将连续单帧一起写入，再加pad
                        
                        # 创建一个存储单帧 feature 的list
                        single_feature_list = [current_feature]
                        # 拿到单帧信息，将当前帧的end_index作为判断依据，方便下一单帧判断是否连续
                        last_frame_index = row_data[current_feature][0]["index"]["end_index"]
                        feature_index += 1
                        
                        while feature_index < features_list_len:
                            if len(row_data[features_list[feature_index]]) == 1 and row_data[features_list[feature_index]][0]["index"]["start_index"] == last_frame_index:
                                # 单帧连续时
                                # 更新
                                last_frame_index = row_data[features_list[feature_index]][0]["index"]["end_index"]
                                # 记录单帧特征，后续通过这些特征拼接位流
                                single_feature_list.append(features_list[feature_index])
                                feature_index += 1
                                continue
                            else:
                                break
                            
                        # 此时 single_feature_list 中存放着连续单帧
                    
                        insert_data(getattr(config, "CMD"+config_suffix))
                        insert_data(getattr(config, "WCFG"+config_suffix))
                        insert_data(getattr(config, "NOOP"+config_suffix))
                        insert_data(getattr(config, "FAR"+config_suffix))
                        # current_feature 是 单帧列表中的第一个帧
                        insert_data(get_frame_address_register(row_data[current_feature][0]["FAR"]["frame_type"], row_data[current_feature][0]["FAR"]["region_type"], row_data[current_feature][0]["FAR"]["row_num"], row_data[current_feature][0]["FAR"]["col_num"], row_data[current_feature][0]["FAR"]["frame_index"]))
                        insert_data(getattr(config, "NOOP"+config_suffix))
                        single_word_count = (len(single_feature_list)+1)*101
                        
                        # ================ 方案一 ================ 
                        if single_word_count < 2048:
                            insert_data(get_cmd_from_word_count(single_word_count, "FDRI"))
                        else:
                            # FDRI cmd 低11位表示 word count ，最大为2047，超过这个数目，需要额外的一行作为表示
                            insert_data(get_cmd_from_word_count(0, "FDRI"))
                            insert_data(get_total_word(single_word_count))
                        # 插入这些单帧
                        for feature_key in single_feature_list:
                            if bitsteam_obj.file_type == ".rbt":
                                insert_multiple_words(bitsteam_obj.rbt_data_content[row_data[feature_key][0]['index']['start_index']:row_data[feature_key][0]['index']['end_index']])
                            elif bitsteam_obj.file_type == ".bit" or bitsteam_obj.file_type == ".bin":
                                insert_multiple_words(bitsteam_obj.bit_data_content[row_data[feature_key][0]['index']['start_index']:row_data[feature_key][0]['index']['end_index']])
                        # 最后插入 pad frame
                        for _ in range(101):
                            insert_data(getattr(config, "ZERO"+config_suffix))
                        # ================ 方案一 ================ 
                            
                        # ================ 方案二 ================ 
                        # if single_word_count < 2048:
                        #     insert_data(get_cmd_from_word_count(single_word_count, "FDRI"))
                        #     # 插入这些单帧
                        #     for feature_key in single_feature_list:
                        #         if bitsteam_obj.file_type == ".rbt":
                        #             insert_multiple_words(bitsteam_obj.rbt_data_content[row_data[feature_key][0]['index']['start_index']:row_data[feature_key][0]['index']['end_index']])
                        #         elif bitsteam_obj.file_type == ".bit" or bitsteam_obj.file_type == ".bin":
                        #             insert_multiple_words(bitsteam_obj.bit_data_content[row_data[feature_key][0]['index']['start_index']:row_data[feature_key][0]['index']['end_index']])
                        #         
                        #     # 最后插入 pad frame
                        #     for _ in range(101):
                        #         insert_data(getattr(config, "ZERO"+config_suffix))
                        # else:
                        #     # FDRI cmd 低11位表示 word count ，最大为2047，超过这个数目，需要额外的一行作为表示
                        #     insert_data(get_cmd_from_word_count(0, "FDRI"))
                        #     insert_data(get_total_word(single_word_count))
                        #     # 插入这些单帧
                        #     for feature_key in single_feature_list:
                        #         if bitsteam_obj.file_type == ".rbt":
                        #             insert_multiple_words(bitsteam_obj.rbt_data_content[row_data[feature_key][0]['index']['start_index']:row_data[feature_key][0]['index']['end_index']])
                        #         elif bitsteam_obj.file_type == ".bit" or bitsteam_obj.file_type == ".bin":
                        #             insert_multiple_words(bitsteam_obj.bit_data_content[row_data[feature_key][0]['index']['start_index']:row_data[feature_key][0]['index']['end_index']])
                        #     for _ in range(101):
                        #         insert_data(getattr(config, "ZERO"+config_suffix))
                        #     insert_data(getattr(config, "CMD"+config_suffix))
                        #     insert_data(getattr(config, "MFW"+config_suffix))
                        #     for _ in range(12):
                        #         insert_data(getattr(config, "NOOP"+config_suffix))
                        #     insert_data(get_cmd_from_word_count(8, "MFWR"))
                        #     for _ in range(8):
                        #         insert_data(getattr(config, "ZERO"+config_suffix))
                        # ================ 方案二 ================ 
                    else:
                        # 异常情况
                        print(456)
                        break
        
    # ================================= 构造压缩位流数据帧部分 结束 =========================================
    
    # ================================= 构造压缩位流寄存器部分 开始 =========================================
    
        # 拿到数据帧之前的寄存器
    if bitsteam_obj.file_type == ".rbt":
        for i in range(len(bitsteam_obj.rbt_cfg_content_pre)):
            # 连续的MASK CTL1才需要修改
            if bitsteam_obj.rbt_cfg_content_pre[i].cmd_name == "MASK" and i < len(bitsteam_obj.rbt_cfg_content_pre)-1 and bitsteam_obj.rbt_cfg_content_pre[i+1].cmd_name == "CTL1":
                # 对 MASK 的低12位做修改，从 0 -> 1
                new_line = bitsteam_obj.rbt_cfg_content_pre[i].get_data_from_index(1)[:-13] + "1" + bitsteam_obj.rbt_cfg_content_pre[i].get_data_from_index(1)[-12:]
                bitsteam_obj.rbt_cfg_content_pre[i].set_data_to_index(1, new_line)
                # 对 CTL1 的低12位做修改，从 0 -> 1
                new_line = bitsteam_obj.rbt_cfg_content_pre[i+1].get_data_from_index(1)[:-13] + "1" + bitsteam_obj.rbt_cfg_content_pre[i+1].get_data_from_index(1)[-12:]
                bitsteam_obj.rbt_cfg_content_pre[i+1].set_data_to_index(1, new_line)
    elif bitsteam_obj.file_type == ".bit" or bitsteam_obj.file_type == ".bin":
        for i in range(len(bitsteam_obj.bit_cfg_content_pre)):
            if bitsteam_obj.bit_cfg_content_pre[i].cmd_name == "MASK" and i < len(bitsteam_obj.bit_cfg_content_pre)-1 and bitsteam_obj.bit_cfg_content_pre[i+1].cmd_name == "CTL1":
                word = utils.bytes_to_binary(bitsteam_obj.bit_cfg_content_pre[i].get_data_from_index(1))
                word = word[:-13] + "1" + word[-12:]
                bitsteam_obj.bit_cfg_content_pre[i].set_data_to_index(1, utils.binary_str_to_bytes(word))
                word = utils.bytes_to_binary(bitsteam_obj.bit_cfg_content_pre[i+1].get_data_from_index(1))
                word = word[:-13] + "1" + word[-12:]
                bitsteam_obj.bit_cfg_content_pre[i+1].set_data_to_index(1, utils.binary_str_to_bytes(word))
    
        # 拿到数据帧之后的寄存器
    if bitsteam_obj.file_type == ".rbt":
        cur_index = 0
        while cur_index < len(bitsteam_obj.rbt_cfg_content_after):
            # CMD 且 command:DGHIGH/LFRM 时，做插入
            if bitsteam_obj.rbt_cfg_content_after[cur_index].cmd_name == "CMD" \
                and bitsteam_obj.rbt_cfg_content_after[cur_index].data_len == 2 \
                and bitsteam_obj.rbt_cfg_content_after[cur_index].get_data_from_index(1)[-2:] == "11":
                        
                # 此时需要在 cur_index+1位置插入两个 Item MASK CTL1
                # MASK
                item = bitsteam_obj.PacketItem("MASK")
                item.set_opcode(0)
                item.append_data("00000000000000000001000000000000")
                bitsteam_obj.rbt_cfg_content_after.insert(cur_index+1, item)
                
                # CTL1
                item = bitsteam_obj.PacketItem("CTL1")
                item.set_opcode(0)
                item.append_data("00000000000000000000000000000000")
                bitsteam_obj.rbt_cfg_content_after.insert(cur_index+2, item)
                
                cur_index += 2  # 跳过插入的元素
            cur_index += 1
    elif bitsteam_obj.file_type == ".bit" or bitsteam_obj.file_type == ".bin":
        cur_index = 0
        while cur_index < len(bitsteam_obj.bit_cfg_content_after):
            # CMD 且 command:DGHIGH/LFRM 时，做插入
            if bitsteam_obj.bit_cfg_content_after[cur_index].cmd_name == "CMD" \
                and bitsteam_obj.bit_cfg_content_after[cur_index].data_len == 2 \
                and bitsteam_obj.bit_cfg_content_after[cur_index].get_data_from_index(1)[-1:] == b"\x03":
                    
                # 此时需要在 cur_index+1位置插入两个 Item MASK CTL1
                # MASK
                item = bitsteam_obj.PacketItem("MASK")
                item.set_opcode(0)
                item.append_data(b"\x00\x00\x10\x00")
                bitsteam_obj.bit_cfg_content_after.insert(cur_index+1, item)
                
                # CTL1
                item = bitsteam_obj.PacketItem("CTL1")
                item.set_opcode(0)
                item.append_data(b"\x00\x00\x00\x00")
                bitsteam_obj.bit_cfg_content_after.insert(cur_index+2, item)
                
                cur_index += 2  # 跳过插入的元素
            cur_index += 1
    
    # ================================= 构造压缩位流寄存器部分 结束 =========================================
    
    if bitsteam_obj.file_type == ".rbt":
        bitsteam_obj.rbt_data_content = new_data_frame
        for i in range(len(bitsteam_obj.rbt_cfg_content_pre)-1, 0, -1):
            if bitsteam_obj.rbt_cfg_content_pre[i].cmd_name == "FAR":
                bitsteam_obj.rbt_cfg_content_pre = bitsteam_obj.rbt_cfg_content_pre[:i]
                break
        else:
            raise ValueError("配置寄存器存在问题")
    elif bitsteam_obj.file_type == ".bit" or bitsteam_obj.file_type == ".bin":
        bitsteam_obj.bit_data_content = new_data_frame
        for i in range(len(bitsteam_obj.bit_cfg_content_pre)-1, 0, -1):
            if bitsteam_obj.bit_cfg_content_pre[i].cmd_name == "FAR":
                bitsteam_obj.bit_cfg_content_pre = bitsteam_obj.bit_cfg_content_pre[:i]
                break
        else:
            raise ValueError("配置寄存器存在问题")