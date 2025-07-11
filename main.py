import sys

def run_cli():
    from CLI import main_shell
    main_shell.main()

def run_gui():
    from GUI import app
    app.main()

def is_ui_args():
    args = [arg.lower() for arg in sys.argv[1:]]
    return '-ui' in args

if __name__ == '__main__':
    if is_ui_args():
        run_gui()
    else:
        run_cli()
