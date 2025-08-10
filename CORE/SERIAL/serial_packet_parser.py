from enum import Enum
from typing import Optional
from CORE.SERIAL.serial_state import SerialHistory


class AckType(Enum):
    CLKCFG = "CLKCFG"
    BITACK = "BITACK"
    VOLGET = "VOLGET"
    CURGET = "CURGET"

class CommandType(Enum):
    VOLGET = "VOLGET"
    CURGET = "CURGET"
    CURSHW = "CURSHW"
    BITACK = "BITACK"
    CLKCFG = "CLKCFG"
    GETMOD = "GETMOD"
    RDBACK = "RDBACK"
    RDBREG = "RDBREG"
    CLKGET = "CLKGET"
    TMPGET = "TMPGET"
    VERGET = "VERGET"
    INAGET = "INAGET"
    BITGET = "BITGET"

class IgnoreType(Enum):
    recv = "recv"

class SerialPacketParser:
    def __init__(self, event_router=None):
        self.event_router = event_router  # 用于触发 ACK

    def parse(self, line: str):
        if "MC1P" not in line or len(line) < 15:
            return
        SerialHistory.append_log(line)
        parts = line.split("MC1P")
        for raw_packet in parts:
            packet = raw_packet.strip()
            if len(packet) < 11:
                continue

            tokens = packet.split()
            if len(tokens) < 2:
                continue

            cmd_type = tokens[0]
            if cmd_type == "TPS_set_vol":
                print(line)
            if cmd_type in IgnoreType.__members__:
                return

            if cmd_type not in CommandType.__members__:
                print(f"[SerialPacketParser Warning] {cmd_type} is not in CommandType\n")
                return
            command = CommandType(cmd_type)

            # 调用不同的解析函数
            if command == CommandType.VOLGET:
                return self.parse_volget(tokens)
            elif command == CommandType.CURGET:
                return self.parse_curget(tokens)
            elif command == CommandType.CLKCFG:
                return self.parse_clkcfg(tokens)

    def parse_volget(self, tokens):
        self.event_router.trigger_ack(AckType.VOLGET)
        # MC1PVOLGET + 长度004A + 13路电压
        if len(tokens) != 15:
            print("[SerialPacketParser Error] VOLGET 格式错误")
            return
        vcc_values = tokens[2:2+11] # 11路VCC
        vcc_names = [
            "VCCO_0", "VCCBRAM", "VCCAUX", "VCCINT",
            "VCCO_16", "VCCO_15", "VCCO_14", "VCCO_13",
            "VCCO_34", "MGTAVTT", "MGTAVCC"
        ]
        vcc_dict = dict(zip(vcc_names, vcc_values))
        if tokens[13] == "1" or tokens[13] == "0":
            vcc_dict["VCCADC"] = tokens[13]
        else:
            vcc_dict["VCCADC"] = "-1"
            print(f"[SerialPacketParser Warning] {tokens} VCCADC is invalid")
        
        if tokens[14] == "1" or tokens[14] == "0":
            vcc_dict["VCCREF"] = tokens[14]
        else:
            vcc_dict["VCCREF"] = "-1"
            print(f"[SerialPacketParser Warning] {tokens} VCCREF is invalid")
        
        return self._build_data(CommandType.VOLGET, vcc_dict)

    def parse_curget(self, tokens):
        if len(tokens) != 14:
            print("CURGET 格式错误")
        return self._build_data(CommandType.CURGET, {})
        
    def parse_clkcfg(self, tokens):
        self.event_router.trigger_ack(AckType.CLKCFG)
        return self._build_data(CommandType.CLKCFG, {})

    def _build_data(self, data_type: CommandType, data_content: dict):
        return dict(data_type=data_type, data_content=data_content)
