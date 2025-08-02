from enum import Enum
from typing import Optional


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

class SerialPacketParser:
    def __init__(self, event_router=None):
        self.event_router = event_router  # 用于触发 ACK

    def parse(self, line: str):
        if "MC1P" not in line or len(line) < 15:
            return
        parts = line.split("MC1P")
        for raw_packet in parts:
            packet = raw_packet.strip()
            if len(packet) < 11:
                continue

            tokens = packet.split()
            if len(tokens) < 2:
                continue

            cmd_type = tokens[0]
            try:
                if cmd_type not in CommandType.__members__:
                    print(f"[SerialPacketParser Warning] {cmd_type} is not in CommandType")
                    return
                command = CommandType(cmd_type)
                ack_type = AckType[cmd_type]

                if command.name in AckType.__members__ and self.event_router:
                    ack_type = AckType[command.name]
                    self.event_router.trigger_ack(ack_type)
            except KeyError:
                pass 

            # 调用不同的解析函数
            if command == CommandType.VOLGET:
                self.parse_volget(tokens)
            elif command == CommandType.CURGET:
                self.parse_curget(tokens)
            elif command == CommandType.CLKCFG:
                pass
            # ... 添加更多 cmd_type 的解析逻辑

    def parse_volget(self, tokens):
        if len(tokens) != 15:
            print("VOLGET 格式错误")
            return
        vcc_values = tokens[2:2+11]  # 假设11个VCC
        vcc_adc = tokens[13]
        vcc_ref = tokens[14]
        # 调用某个全局回调或更新状态
        print("VCC values:", vcc_values, "ADC:", vcc_adc, "REF:", vcc_ref)

    def parse_curget(self, tokens):
        if len(tokens) != 14:
            print("CURGET 格式错误")
            return
        # 同理解析 current
