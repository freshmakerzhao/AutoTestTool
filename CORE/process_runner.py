import logging
import COMMON.config as config
from CORE.bitstream_parser import BitstreamParser
from CORE import module_base, module_crc, module_refresh

FILE_ENDWITH = "_new"

def run_task(
    file, 
    device = "MC1P110", 
    file_suffix = FILE_ENDWITH,
    pcie = False, 
    gtp = False, 
    crc = False, 
    compress = False,
    trim = False, 
    delete_ghigh = False,
    readback_refresh = None, 
    timer_refresh=None,
):
    dev = config.DEVICE_MAP.get(device.upper(), "MC1P110")
    bitsteam_obj = BitstreamParser(dev, file, crc)

    if gtp:
        module_base.process_gtp_config(bitsteam_obj)

    if pcie:
        module_base.process_pcie_config(bitsteam_obj)

    if trim:
        module_base.process_trim(bitsteam_obj)

    if delete_ghigh:
        module_base.delete_ghigh(bitsteam_obj)

    if timer_refresh:
        module_refresh.timer_refresh(bitsteam_obj, timer_refresh)

    if readback_refresh:
        module_refresh.readback_refresh(bitsteam_obj, readback_refresh)

    if crc:
        module_crc.calculate_crc(bitsteam_obj)
    else:
        module_crc.disable_crc(bitsteam_obj)

    if compress:
        module_base.process_compress(bitsteam_obj)

    return bitsteam_obj.save_file(file_suffix)
