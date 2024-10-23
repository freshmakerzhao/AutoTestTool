import pandas as pd
WRITE_CONTENT = False

compress_rbt = []
FAR_REGISTER        = "30002001"
CMD_REGISTER        = "30008001"
CMD_WCFG            = "00000001"
NOOP                = "20000000"
FDRI_REGISTER_101   = "30004065"
FDRI_DATA           = "55555555"
CMD_MFW             = "00000002"
MFWR_REGISTER_8     = "30014008"
MFWR_REGISTER_4     = "30014004"
ZERO                = "00000000"
HEX_LIST = ["FFFFFFFF" for _ in range(101)]
rbt_file_path = r"E:\File_Wechat\WeChat Files\wxid_shoeeihphwsh22\FileStorage\File\构造压缩位流需求\FF.rbt"

constraints_list = [4, 14, 24, 34, 44, 55, 65, 75, 85, 95]
constraints_bit = 14

def create_frame_address_register_binary(type, tb, row, col, min_value):
    # 构造32位二进制数
    binary = (type << 23) | (tb << 22) | (row << 17) | (col << 7) | min_value
    # 转换为32位二进制字符串
    return format(binary, '032b')

def create_binary_from_hex(hex_value, is_constraints=False):
    """
    将十六进制字符串转换为32位二进制字符串。

    参数:
    hex_value (str): 十六进制字符串，例如 '30002001'。

    返回:
    str: 32位二进制字符串，例如 '00110000000000000000000000000001'。
    """
    binary_value = format(int(hex_value, 16), '032b')
    if is_constraints:
        binary_value = binary_value[:constraints_bit] + '0' + binary_value[constraints_bit+1:]
    return binary_value

def insert_word(word, content=None):
    """
    将32位二进制字符串插入到 compress_rbt 列表中。

    参数:
    word (str): 32位二进制字符串，必须仅包含 '0' 和 '1'，长度为32位。
    content (str): 改行word的解释，非None时插入
    异常:
    ValueError: 如果 word 不是有效的32位二进制字符串，将引发此异常。
    """
    if len(word) != 32 or not all(c in '01' for c in word):
        raise ValueError("word must be a 32-bit binary string")
    if WRITE_CONTENT:
        if content is not None:
            compress_rbt.append(word+"\t"+content)
        else:
            compress_rbt.append(word)
    else:
        compress_rbt.append(word)

def insert_multiple_words_from_hex(hex_list, cur_type):
    """
    将包含十六进制字符串的列表中的每个值转换为32位二进制字符串，并插入到 compress_rbt 列表中。

    参数:
    hex_list (list of str): 包含十六进制字符串的列表，例如 ['55555555', '12345678']。
    """
    for index, hex_value in enumerate(hex_list):
        if cur_type == 1: 
            if index in constraints_list:
                insert_word(create_binary_from_hex(hex_value, True), " word:"+str(index))
                continue
        insert_word(create_binary_from_hex(hex_value), " word:"+str(index))

# 文件名
filename = r"E:\File_Wechat\WeChat Files\wxid_shoeeihphwsh22\FileStorage\File\构造压缩位流需求\7A100_structure.csv"

# 读取 CSV 文件
df = pd.read_csv(filename)

# 筛选出存在空值的行
# columns_to_check = ['TYPE', 'TOP/BOTTOM', 'ROWS', 'COLS', 'FRAMES']
# rows_with_na = df[df[columns_to_check].isna().any(axis=1)]

# 处理缺失值
# df.fillna({'TYPE': 0, 'ROWS': 0, 'COLS': 0, 'FRAMES': 0}, inplace=True)

# 替换 TOP/BOTTOM 列中的 'T' 为 0，'B' 为 1
df['TOP/BOTTOM'] = df['TOP/BOTTOM'].replace({'T': 0, 'B': 1})

# 转换为整数类型
df[['TYPE', 'ROWS', 'COLS', 'FRAMES', 'TOP/BOTTOM']] = df[['TYPE', 'ROWS', 'COLS', 'FRAMES', 'TOP/BOTTOM']].fillna(-1)
df = df.astype({'TYPE': int, 'ROWS': int, 'COLS': int, 'FRAMES': int, 'TOP/BOTTOM':int})

# 初始化变量
cur_type = cur_tb = cur_rows = cur_cols = cur_frames = 0
is_first_row = True
is_new_row = True 

for index, row in df.iterrows():
    if row['TYPE'] == 1:
        print(1)
    
    if "PADFRM" in row['BLKTYPE'] or "PADFRAME" in row['BLKTYPE']:
        continue

    # 第一行，初始化变量
    if index == 0:
        cur_type = row['TYPE']
        cur_tb = row['TOP/BOTTOM']
        cur_rows = row['ROWS']
        cur_cols = row['COLS']
        cur_frames = row['FRAMES']

        insert_word(create_binary_from_hex(FAR_REGISTER),"Write Reg:FAR, word:1")
        insert_word(create_frame_address_register_binary(cur_type, cur_tb, cur_rows, cur_cols, 0),"type:"+str(cur_type)+" tb:"+str(cur_tb)+" row:"+str(cur_rows)+" col:"+str(cur_cols)+" min:"+str(0)+" ")
        insert_word(create_binary_from_hex(CMD_REGISTER), "Write Reg:CMD, word:1")
        insert_word(create_binary_from_hex(CMD_WCFG), "command:WCFG ")
        insert_word(create_binary_from_hex(NOOP), "NOP")

        insert_word(create_binary_from_hex(FDRI_REGISTER_101), "Write Reg:FDRI, word:101")
        insert_multiple_words_from_hex(HEX_LIST, cur_type)

        insert_word(create_binary_from_hex(CMD_REGISTER), "Write Reg:CMD, word:1")
        insert_word(create_binary_from_hex(CMD_MFW) ,"command:MFW ")
        for _ in range(12):
            insert_word(create_binary_from_hex(NOOP), "NOP")
        insert_word(create_binary_from_hex(MFWR_REGISTER_8), "Write Reg:MFWR, word:8")
        for _ in range(8):
            insert_word(create_binary_from_hex(ZERO))
        if cur_type == 1:
            for _ in range(8):
                insert_word(create_binary_from_hex(NOOP), "NOP")
        continue

    # 检查是否与上一行相同（除了 FRAMES）
    if (row['TYPE'] == cur_type and
        row['TOP/BOTTOM'] == cur_tb and
        row['ROWS'] == cur_rows and
        row['COLS'] == cur_cols):
        # 累加 FRAMES
        if row['FRAMES'] > 0:
            cur_frames += row['FRAMES']
        else:
            raise ValueError("FRAMES should be greater than or equal to 0")
    else:
        # 处理剩余的frame
        for frame_index in range(1 if is_new_row else 0,cur_frames):
            # ========== one frame ==========
            insert_word(create_binary_from_hex(FAR_REGISTER),"Write Reg:FAR, word:1")
            insert_word(create_frame_address_register_binary(cur_type, cur_tb, cur_rows, cur_cols, frame_index),"type:"+str(cur_type)+" tb:"+str(cur_tb)+" row:"+str(cur_rows)+" col:"+str(cur_cols)+" min:"+str(frame_index)+" ")
            insert_word(create_binary_from_hex(MFWR_REGISTER_4), "Write Reg:MFWR, word:4")
            for _ in range(4):
                insert_word(create_binary_from_hex(ZERO))
            if cur_type == 1:
                for _ in range(8):
                    insert_word(create_binary_from_hex(NOOP), "NOP")
            # ========== one frame ==========
            
        is_new_row = False   
        # 判断是否下一个 row、tb、type
        if (row['TYPE'] != cur_type or 
            row['TOP/BOTTOM'] != cur_tb or 
            row['ROWS'] != cur_rows):
            
            insert_word(create_binary_from_hex(CMD_REGISTER), "Write Reg:CMD, word:1")
            insert_word(create_binary_from_hex(CMD_WCFG), "command:WCFG")
            insert_word(create_binary_from_hex(NOOP), "NOP")
            insert_word(create_binary_from_hex(FAR_REGISTER),"Write Reg:FAR, word:1")
            insert_word(create_frame_address_register_binary(row['TYPE'], row['TOP/BOTTOM'], row['ROWS'], row['COLS'], 0),"type:"+str(row['TYPE'])+" tb:"+str(row['TOP/BOTTOM'])+" row:"+str(row['ROWS'])+" col:"+str(row['COLS'])+" min:"+str(0)+" ")
            insert_word(create_binary_from_hex(NOOP), "NOP")
            insert_word(create_binary_from_hex(FDRI_REGISTER_101), "Write Reg:FDRI, word:101")
            insert_multiple_words_from_hex(HEX_LIST, row['TYPE'])

            insert_word(create_binary_from_hex(CMD_REGISTER), "Write Reg:CMD, word:1")
            insert_word(create_binary_from_hex(CMD_MFW) ,"command:MFW ")
            for _ in range(12):
                insert_word(create_binary_from_hex(NOOP), "NOP")
            insert_word(create_binary_from_hex(MFWR_REGISTER_8), "Write Reg:MFWR, word:8")
            for _ in range(8):
                insert_word(create_binary_from_hex(ZERO))
            if row['TYPE'] == 1:
                for _ in range(8):
                    insert_word(create_binary_from_hex(NOOP), "NOP")
            is_new_row = True
            
            
        is_first_row = False 
        # 更新记录值
        cur_type = row['TYPE']
        cur_tb = row['TOP/BOTTOM']
        cur_rows = row['ROWS']
        cur_cols = row['COLS']
        cur_frames = row['FRAMES']

if cur_frames>0:
    for frame_index in range(0,cur_frames):
        # ========== one frame ==========
        insert_word(create_binary_from_hex(FAR_REGISTER),"Write Reg:FAR, word:1")
        insert_word(create_frame_address_register_binary(cur_type, cur_tb, cur_rows, cur_cols, frame_index),"type:"+str(cur_type)+" tb:"+str(cur_tb)+" row:"+str(cur_rows)+" col:"+str(cur_cols)+" min:"+str(frame_index)+" ")
        insert_word(create_binary_from_hex(MFWR_REGISTER_4), "Write Reg:MFWR, word:4")
        for _ in range(4):
            insert_word(create_binary_from_hex(ZERO))
        if cur_type == 1:
            for _ in range(8):
                insert_word(create_binary_from_hex(NOOP), "NOP")
        # ========== one frame ==========
        
f = open(rbt_file_path,'w')
for line in compress_rbt:
    f.write(str(line)+'\n')
f.close()