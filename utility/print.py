# UTILITY/PRINT.PY

# ## PYTHON IMPORTS
import sys
import uuid
import colorama
import traceback


# ## FUNCTIONS

def normal_print(*args, trim=False, **kwargs):
    print(_coalesce_arguments(args, trim), **kwargs)


def print_char(char):
    print(char[0], end="", flush=True)


def safe_print(*args, trim=False, **kwargs):
    print(_coalesce_arguments(args, trim).encode('ascii', 'backslashreplace').decode(), **kwargs)


def print_info(*args, trim=False, **kwargs):
    msg = _coalesce_arguments(args, trim)
    print(colorama.Fore.GREEN + colorama.Style.BRIGHT + msg + colorama.Style.RESET_ALL, **kwargs)


def print_warning(*args, trim=False, **kwargs):
    msg = _coalesce_arguments(args, trim)
    print(colorama.Fore.YELLOW + colorama.Style.BRIGHT + msg + colorama.Style.RESET_ALL, **kwargs)


def print_error(*args, trim=False, **kwargs):
    msg = _coalesce_arguments(args, trim)
    print(colorama.Fore.RED + colorama.Style.BRIGHT + msg + colorama.Style.RESET_ALL, **kwargs)


def buffered_print(name, safe=False, header=True, trim=False, sep=" ", end="\n"):
    buffer_key = name + " - " + uuid.uuid1().hex
    if header:
        print("\n++++++++++ %s ++++++++++\n" % buffer_key, flush=True)
    print_func = safe_print if safe else normal_print
    print_buffer = []

    def accumulator(*args):
        nonlocal print_buffer
        print_buffer += [*args, end]

    def printer():
        nonlocal print_buffer
        top_header = "========== %s ==========" % buffer_key
        print_buffer = ["\n", top_header, "\n"] + print_buffer
        print_buffer += [("=" * len(top_header)), "\n"]
        print_str = sep.join(map(str, print_buffer))
        print_func(print_str, trim=trim, flush=True)

    setattr(accumulator, 'print', printer)
    return accumulator


def exception_print(error):
    print(repr(error))
    traceback.print_tb(error.__traceback__)


def abort_retry_fail(*args):
    """Exception/Error handler"""
    safe_print(*args)
    while True:
        keyinput = input("(A)bort, (R)etry, (F)ail? ")
        if keyinput.lower() == 'a':
            return False
        if keyinput.lower() == 'r':
            return True
        if keyinput.lower() == 'f':
            sys.exit(-1)


# #### Private

def _coalesce_arguments(args, trim):
    temp = ''
    for arg in args:
        if type(arg) is str:
            temp += arg + ' '
        else:
            temp += repr(arg) + ' '
    return temp.strip() if trim else temp