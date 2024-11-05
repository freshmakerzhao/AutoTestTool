import enum
import utils

DUMMY_STR = "11111111111111111111111111111111"
DUMMY_BYTE = b'\xFF\xFF\xFF\xFF'

SYNC_WORD_STR = "10101010100110010101010101100110"
SYNC_WORD_BYTE = b'\xAA\x99\x55\x66'

BUS_WIDTH_AUTO_DETECT_01_STR = "00000000000000000000000010111011"
BUS_WIDTH_AUTO_DETECT_01_BYTE = b'\x00\x00\x00\xBB'

BUS_WIDTH_AUTO_DETECT_02_STR = "00010001001000100000000001000100"
BUS_WIDTH_AUTO_DETECT_02_BYTE = b'\x11\x22\x00\x44'

NOOP_STR = "00100000000000000000000000000000"
NOOP_BYTE = b'\x20\x00\x00\x00'

FDRI_STR = "00110000000000000100000000000000"
FDRI_BYTE = b'\x30\x00\x40\x00'

CRC_STR = '00110000000000000000000000000001'
CRC_BIT = b'\x30\x00\x00\x01'

CMD_RCRC_01_STR = '00110000000000001000000000000001'
CMD_RCRC_02_STR = '00000000000000000000000000000111'

CMD_RCRC_01_BYTE = b'\x30\x00\x80\x01'
CMD_RCRC_02_BYTE = b'\x00\x00\x00\x07'

COR1_STR = '00110000000000011100000000000001'
COR1_BYTE = b'\x30\x01\xC0\x01'

CMD_MASK_01_STR = '00110000000000001100000000000001'
CMD_MASK_02_STR = '10000000000000000000000000000000'
CMD_TRIM_01_STR = '00110000000000110110000000000001'
CMD_TRIM_02_STR = '10000000000000000000000000000000'

CMD_MASK_01_BYTE = b'\x30\x00\xC0\x01'
CMD_MASK_02_BYTE = b'\x80\x00\x00\x00'
CMD_TRIM_01_BYTE = b'\x30\x03\x60\x01'
CMD_TRIM_02_BYTE = b'\x80\x00\x00\x00'

MC1P110_FRAME_STRUCT = {
    "frame_type_0": {
        "region_type_0": {
            "row_num_0": {
                "col_num_0": {
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 0
                    },
                    "frame_count": 42
                },
                "col_num_1": {
                    "frame_count": 30,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 1
                    }
                },
                "col_num_2": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 2
                    }
                },
                "col_num_3": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 3
                    }
                },
                "col_num_4": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 4
                    }
                },
                "col_num_5": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 5
                    }
                },
                "col_num_6": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 6
                    }
                },
                "col_num_7": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 7
                    }
                },
                "col_num_8": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 8
                    }
                },
                "col_num_9": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 9
                    }
                },
                "col_num_10": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 10
                    }
                },
                "col_num_11": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 11
                    }
                },
                "col_num_12": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 12
                    }
                },
                "col_num_13": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 13
                    }
                },
                "col_num_14": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 14
                    }
                },
                "col_num_15": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 15
                    }
                },
                "col_num_16": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 16
                    }
                },
                "col_num_17": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 17
                    }
                },
                "col_num_18": {
                    "frame_count": 30,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 18
                    }
                },
                "col_num_19": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 19
                    }
                },
                "col_num_20": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 20
                    }
                },
                "col_num_21": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 21
                    }
                },
                "col_num_22": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 22
                    }
                },
                "col_num_23": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 23
                    }
                },
                "col_num_24": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 24
                    }
                },
                "col_num_25": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 25
                    }
                },
                "col_num_26": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 26
                    }
                },
                "col_num_27": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 27
                    }
                },
                "col_num_28": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 28
                    }
                },
                "col_num_29": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 29
                    }
                },
                "col_num_30": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 30
                    }
                },
                "col_num_31": {
                    "frame_count": 30,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 31
                    }
                },
                "col_num_32": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 32
                    }
                },
                "col_num_33": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 33
                    }
                },
                "col_num_34": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 34
                    }
                },
                "col_num_35": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 35
                    }
                },
                "col_num_36": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 36
                    }
                },
                "col_num_37": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 37
                    }
                },
                "col_num_38": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 38
                    }
                },
                "col_num_39": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 39
                    }
                },
                "col_num_40": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 40
                    }
                },
                "col_num_41": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 41
                    }
                },
                "col_num_42": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 42
                    }
                },
                "col_num_43": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 43
                    }
                },
                "col_num_44": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 44
                    }
                },
                "col_num_45": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 45
                    }
                },
                "col_num_46": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 46
                    }
                },
                "col_num_47": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 47
                    }
                },
                "col_num_48": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 48
                    }
                },
                "col_num_49": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 49
                    }
                },
                "col_num_50": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 50
                    }
                },
                "col_num_51": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 51
                    }
                },
                "col_num_52": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 52
                    }
                },
                "col_num_53": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 53
                    }
                },
                "col_num_54": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 54
                    }
                },
                "col_num_55": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 55
                    }
                },
                "col_num_56": {
                    "frame_count": 30,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 56
                    }
                },
                "col_num_57": {
                    "frame_count": 42,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 57
                    }
                }
            },
            "row_num_1": {
                "col_num_0": {
                    "frame_count": 42,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 0
                    }
                },
                "col_num_1": {
                    "frame_count": 30,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 1
                    }
                },
                "col_num_2": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 2
                    }
                },
                "col_num_3": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 3
                    }
                },
                "col_num_4": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 4
                    }
                },
                "col_num_5": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 5
                    }
                },
                "col_num_6": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 6
                    }
                },
                "col_num_7": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 7
                    }
                },
                "col_num_8": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 8
                    }
                },
                "col_num_9": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 9
                    }
                },
                "col_num_10": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 10
                    }
                },
                "col_num_11": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 11
                    }
                },
                "col_num_12": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 12
                    }
                },
                "col_num_13": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 13
                    }
                },
                "col_num_14": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 14
                    }
                },
                "col_num_15": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 15
                    }
                },
                "col_num_16": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 16
                    }
                },
                "col_num_17": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 17
                    }
                },
                "col_num_18": {
                    "frame_count": 30,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 18
                    }
                },
                "col_num_19": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 19
                    }
                },
                "col_num_20": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 20
                    }
                },
                "col_num_21": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 21
                    }
                },
                "col_num_22": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 22
                    }
                },
                "col_num_23": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 23
                    }
                },
                "col_num_24": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 24
                    }
                },
                "col_num_25": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 25
                    }
                },
                "col_num_26": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 26
                    }
                },
                "col_num_27": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 27
                    }
                },
                "col_num_28": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 28
                    }
                },
                "col_num_29": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 29
                    }
                },
                "col_num_30": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 30
                    }
                },
                "col_num_31": {
                    "frame_count": 30,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 31
                    }
                },
                "col_num_32": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 32
                    }
                },
                "col_num_33": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 33
                    }
                },
                "col_num_34": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 34
                    }
                },
                "col_num_35": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 35
                    }
                },
                "col_num_36": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 36
                    }
                },
                "col_num_37": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 37
                    }
                },
                "col_num_38": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 38
                    }
                },
                "col_num_39": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 39
                    }
                },
                "col_num_40": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 40
                    }
                },
                "col_num_41": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 41
                    }
                },
                "col_num_42": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 42
                    }
                },
                "col_num_43": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 43
                    }
                },
                "col_num_44": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 44
                    }
                },
                "col_num_45": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 45
                    }
                },
                "col_num_46": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 46
                    }
                },
                "col_num_47": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 47
                    }
                },
                "col_num_48": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 48
                    }
                },
                "col_num_49": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 49
                    }
                },
                "col_num_50": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 50
                    }
                },
                "col_num_51": {
                    "frame_count": 32,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 51
                    }
                }
            }
        },
        "region_type_1": {
            "row_num_0": {
                "col_num_0": {
                    "frame_count": 42,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 0
                    }
                },
                "col_num_1": {
                    "frame_count": 30,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 1
                    }
                },
                "col_num_2": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 2
                    }
                },
                "col_num_3": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 3
                    }
                },
                "col_num_4": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 4
                    }
                },
                "col_num_5": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 5
                    }
                },
                "col_num_6": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 6
                    }
                },
                "col_num_7": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 7
                    }
                },
                "col_num_8": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 8
                    }
                },
                "col_num_9": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 9
                    }
                },
                "col_num_10": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 10
                    }
                },
                "col_num_11": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 11
                    }
                },
                "col_num_12": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 12
                    }
                },
                "col_num_13": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 13
                    }
                },
                "col_num_14": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 14
                    }
                },
                "col_num_15": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 15
                    }
                },
                "col_num_16": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 16
                    }
                },
                "col_num_17": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 17
                    }
                },
                "col_num_18": {
                    "frame_count": 30,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 18
                    }
                },
                "col_num_19": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 19
                    }
                },
                "col_num_20": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 20
                    }
                },
                "col_num_21": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 21
                    }
                },
                "col_num_22": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 22
                    }
                },
                "col_num_23": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 23
                    }
                },
                "col_num_24": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 24
                    }
                },
                "col_num_25": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 25
                    }
                },
                "col_num_26": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 26
                    }
                },
                "col_num_27": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 27
                    }
                },
                "col_num_28": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 28
                    }
                },
                "col_num_29": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 29
                    }
                },
                "col_num_30": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 30
                    }
                },
                "col_num_31": {
                    "frame_count": 30,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 31
                    }
                },
                "col_num_32": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 32
                    }
                },
                "col_num_33": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 33
                    }
                },
                "col_num_34": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 34
                    }
                },
                "col_num_35": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 35
                    }
                },
                "col_num_36": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 36
                    }
                },
                "col_num_37": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 37
                    }
                },
                "col_num_38": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 38
                    }
                },
                "col_num_39": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 39
                    }
                },
                "col_num_40": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 40
                    }
                },
                "col_num_41": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 41
                    }
                },
                "col_num_42": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 42
                    }
                },
                "col_num_43": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 43
                    }
                },
                "col_num_44": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 44
                    }
                },
                "col_num_45": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 45
                    }
                },
                "col_num_46": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 46
                    }
                },
                "col_num_47": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 47
                    }
                },
                "col_num_48": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 48
                    }
                },
                "col_num_49": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 49
                    }
                },
                "col_num_50": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 50
                    }
                },
                "col_num_51": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 51
                    }
                },
                "col_num_52": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 52
                    }
                },
                "col_num_53": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 53
                    }
                },
                "col_num_54": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 54
                    }
                },
                "col_num_55": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 55
                    }
                },
                "col_num_56": {
                    "frame_count": 30,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 56
                    }
                },
                "col_num_57": {
                    "frame_count": 42,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 57
                    }
                }
            },
            "row_num_1": {
                "col_num_0": {
                    "frame_count": 42,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 0
                    }
                },
                "col_num_1": {
                    "frame_count": 30,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 1
                    }
                },
                "col_num_2": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 2
                    }
                },
                "col_num_3": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 3
                    }
                },
                "col_num_4": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 4
                    }
                },
                "col_num_5": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 5
                    }
                },
                "col_num_6": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 6
                    }
                },
                "col_num_7": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 7
                    }
                },
                "col_num_8": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 8
                    }
                },
                "col_num_9": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 9
                    }
                },
                "col_num_10": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 10
                    }
                },
                "col_num_11": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 11
                    }
                },
                "col_num_12": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 12
                    }
                },
                "col_num_13": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 13
                    }
                },
                "col_num_14": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 14
                    }
                },
                "col_num_15": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 15
                    }
                },
                "col_num_16": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 16
                    }
                },
                "col_num_17": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 17
                    }
                },
                "col_num_18": {
                    "frame_count": 30,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 18
                    }
                },
                "col_num_19": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 19
                    }
                },
                "col_num_20": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 20
                    }
                },
                "col_num_21": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 21
                    }
                },
                "col_num_22": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 22
                    }
                },
                "col_num_23": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 23
                    }
                },
                "col_num_24": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 24
                    }
                },
                "col_num_25": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 25
                    }
                },
                "col_num_26": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 26
                    }
                },
                "col_num_27": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 27
                    }
                },
                "col_num_28": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 28
                    }
                },
                "col_num_29": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 29
                    }
                },
                "col_num_30": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 30
                    }
                },
                "col_num_31": {
                    "frame_count": 30,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 31
                    }
                },
                "col_num_32": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 32
                    }
                },
                "col_num_33": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 33
                    }
                },
                "col_num_34": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 34
                    }
                },
                "col_num_35": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 35
                    }
                },
                "col_num_36": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 36
                    }
                },
                "col_num_37": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 37
                    }
                },
                "col_num_38": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 38
                    }
                },
                "col_num_39": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 39
                    }
                },
                "col_num_40": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 40
                    }
                },
                "col_num_41": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 41
                    }
                },
                "col_num_42": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 42
                    }
                },
                "col_num_43": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 43
                    }
                },
                "col_num_44": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 44
                    }
                },
                "col_num_45": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 45
                    }
                },
                "col_num_46": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 46
                    }
                },
                "col_num_47": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 47
                    }
                },
                "col_num_48": {
                    "frame_count": 28,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 48
                    }
                },
                "col_num_49": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 49
                    }
                },
                "col_num_50": {
                    "frame_count": 36,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 50
                    }
                },
                "col_num_51": {
                    "frame_count": 32,
                    "FAR": {
                        "frame_type": 0,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 51
                    }
                }
            }
        }
    },
    "frame_type_1": {
        "region_type_0": {
            "row_num_0": {
                "col_num_0": {
                    "frame_count": 128,
                    "FAR": {
                        "frame_type": 1,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 0
                    }
                },
                "col_num_1": {
                    "frame_count": 128,
                    "FAR": {
                        "frame_type": 1,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 1
                    }
                },
                "col_num_2": {
                    "frame_count": 128,
                    "FAR": {
                        "frame_type": 1,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 2
                    }
                },
                "col_num_3": {
                    "frame_count": 128,
                    "FAR": {
                        "frame_type": 1,
                        "region_type": 0,
                        "row_num": 0,
                        "col_num": 3
                    }
                }
            },
            "row_num_1": {
                "col_num_0": {
                    "frame_count": 128,
                    "FAR": {
                        "frame_type": 1,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 0
                    }
                },
                "col_num_1": {
                    "frame_count": 128,
                    "FAR": {
                        "frame_type": 1,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 1
                    }
                },
                "col_num_2": {
                    "frame_count": 128,
                    "FAR": {
                        "frame_type": 1,
                        "region_type": 0,
                        "row_num": 1,
                        "col_num": 2
                    }
                }
            }
        },
        "region_type_1": {
            "row_num_0": {
                "col_num_0": {
                    "frame_count": 128,
                    "FAR": {
                        "frame_type": 1,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 0
                    }
                },
                "col_num_1": {
                    "frame_count": 128,
                    "FAR": {
                        "frame_type": 1,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 1
                    }
                },
                "col_num_2": {
                    "frame_count": 128,
                    "FAR": {
                        "frame_type": 1,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 2
                    }
                },
                "col_num_3": {
                    "frame_count": 128,
                    "FAR": {
                        "frame_type": 1,
                        "region_type": 1,
                        "row_num": 0,
                        "col_num": 3
                    }
                }
            },
            "row_num_1": {
                "col_num_0": {
                    "frame_count": 128,
                    "FAR": {
                        "frame_type": 1,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 0
                    }
                },
                "col_num_1": {
                    "frame_count": 128,
                    "FAR": {
                        "frame_type": 1,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 1
                    }
                },
                "col_num_2": {
                    "frame_count": 128,
                    "FAR": {
                        "frame_type": 1,
                        "region_type": 1,
                        "row_num": 1,
                        "col_num": 2
                    }
                }
            }
        }
    }
}

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
        CTL1 = 24
        UNKNOWN_30 = 30 #if next packet is Type2 and bcout_cnt(ib) = 0, set bocut_flag(ib) <= '1' and bout_cnt(ib) <= word count
        BSPI = 31
        
    @enum.unique
    class OpCode(enum.Enum):
        UNKNOWN = -1
        NOOP = 0
        READ = 1
        WRITE = 2
    
    def get_cmd_name(self, key):
        return self.cmd_name_map.get(key, self.Address.UNKNOWN)
    
    # 传入整型，返回其type
    def get_packet_type(self, word, content_type = "int"):
        if content_type != "int":
            word = int(word, 2)
        return word >> 29 
    
    # 传入整型，返回其opcode
    def get_opcode(self, word, content_type = "int"):
        if content_type != "int":
            word = int(word, 2)
        return self.OpCode((word >> 27) & 0x3) 

    # 根据传入word获取其type1格式的数据，content_type为int时，直接读，str时转换后再读
    def get_type_1_packet_content(self, word, content_type = "int"):
        if content_type != "int":
            word = int(word, 2)
        header_type = self.get_packet_type(word) # [31:29]
        opcode = self.OpCode((word >> 27) & 0x3) # [28:27]
        address = self.Address((word >> 13) & 0x1F) # [26:13] 取低5位
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
    def get_type_2_packet_content(self, word, content_type = "int"):
        if content_type != "int":
            word = int(word, 2)
        header_type = self.get_packet_type(word) # [31:29]
        opcode = self.OpCode((word >> 27) & 0x3) # [28:27]
        word_count = word & 0x7FFFFFF # [26:0]
        return {
                "header_type":header_type,
                "opcode":opcode,
                "word_count":word_count
            }
        
    def make_len_37_crc_data_in(self, word, cmd_word, content_type = "byte"):
        if content_type == "byte":
            word = utils.bytes_to_binary(word)
            cmd_word = utils.bytes_to_binary(cmd_word)
        address = cmd_word[14:19]
        crc_data_in = address + word
        return ([int(i) for i in crc_data_in[::-1]])
    
    def __init__(self) -> None:
        self.cmd_name_map = {    
            self.Address.UNKNOWN : "UNKNOWN",
            self.Address.CRC : "CRC",
            self.Address.FAR : "FAR",
            self.Address.FDRI : "FDRI",
            self.Address.FDRO : "FDRO",
            self.Address.CMD : "CMD",
            self.Address.CTL0 : "CTL0",
            self.Address.MASK : "MASK",
            self.Address.STAT : "STAT",
            self.Address.LOUT : "LOUT",
            self.Address.COR0 : "COR0",
            self.Address.MFWR : "MFWR",
            self.Address.CBC : "CBC",
            self.Address.IDCODE : "IDCODE",
            self.Address.AXSS : "AXSS",
            self.Address.COR1 : "COR1",
            self.Address.UNKNOWN_15 : "UNKNOWN_15",
            self.Address.WBSTAR : "WBSTAR",
            self.Address.TIMER : "TIMER",
            self.Address.UNKNOWN_18 : "UNKNOWN_18",
            self.Address.POST_CRC : "POST_CRC",
            self.Address.UNKNOWN_20 : "UNKNOWN_20",
            self.Address.UNKNOWN_21 : "UNKNOWN_21",
            self.Address.BOOTSTS : "BOOTSTS",
            self.Address.CTL1 : "CTL1",
            self.Address.UNKNOWN_30 : "UNKNOWN_30",
            self.Address.BSPI : "BSPI"
        }