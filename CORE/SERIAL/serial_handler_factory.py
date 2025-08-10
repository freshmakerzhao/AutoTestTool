from CORE.SERIAL.cli_serial_handler import CLISerialHandler
from CORE.SERIAL.gui_serial_handler import GUISerialEventHandler

def create_handler(mode: str, handler_name: str, gui_page=None):
    if mode == "cli":
        return CLISerialHandler(handler_name)
    elif mode == "gui":
        if gui_page is None:
            raise ValueError("GUI handler 需要传入 GUI 界面引用")
        return GUISerialEventHandler(handler_name, gui_page)
    else:
        raise ValueError(f"未知模式: {mode}")
