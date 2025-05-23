import logging
from CORE.bitstream_parser import BitstreamParser
import os
from CORE.process_runner import run_convert_task

def run_convert_cli(args):
    run_convert_task(args.file, args.to_fmt)
