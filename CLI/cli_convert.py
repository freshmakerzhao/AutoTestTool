import logging
from CORE.bitstream_parser import BitstreamParser

def run_convert_cli(args):
    try:
        logging.info(f"[转换] 正在处理文件：{args.file}")
        parser = BitstreamParser("MC1P110", args.file, enable_crc=False)
        new_path = parser.save_file(file_suffix=f"_converted.{args.to_fmt}", format_override=args.to_fmt)
        logging.info(f"✅ 转换完成，保存至: {new_path}")
    except Exception as e:
        logging.error(f"[CONVERT ERROR] {e}")