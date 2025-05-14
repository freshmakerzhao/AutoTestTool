import argparse, logging, sys
from CORE.parse_bitstream import run_bit_process, FILE_ENDWITH

def main():
    parser = argparse.ArgumentParser(description="Auto Process")
    parser.add_argument('--file', required=True)
    parser.add_argument('--device', default="MC1P110")
    parser.add_argument('--file_suffix', default=FILE_ENDWITH)
    parser.add_argument('--PCIE', action='store_true')
    parser.add_argument('--GTP', action='store_true')
    parser.add_argument('--CRC', action='store_true')
    parser.add_argument('--COMPRESS', action='store_true')
    parser.add_argument('--TRIM', action='store_true')
    parser.add_argument('--DELETE_GHIGH', action='store_true')
    parser.add_argument('--readback_refresh', action='store_true')

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        run_bit_process(
            file=args.file,
            device=args.device,
            file_suffix=args.file_suffix,
            pcie=args.PCIE,
            gtp=args.GTP,
            crc=args.CRC,
            compress=args.COMPRESS,
            trim=args.TRIM,
            delete_ghigh=args.DELETE_GHIGH,
            readback_refresh=args.readback_refresh,
        )
    except Exception as exc:
        logging.error("❌ %s", exc)
        sys.exit(1)

if __name__ == "__main__":
    main()
