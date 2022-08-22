
# UTILITY/DATA.PY

# ## PYTHON IMPORTS
import re
import json
import math
import hashlib
import inspect
import platform


# ## GLOBAL VARIABLES

DEBUG_MODULE = {}
CURRENT_OS = None
ROMAN_RG = re.compile(r'^M?M?M?(CM|CD|D?C?C?C?)(XC|XL|L?X?X?X?)(IX|IV|V?I?I?I?)$', re.IGNORECASE)


# ## FUNCTIONS

# #### General functions

def get_current_os():
    """Set and return the current platform"""
    global CURRENT_OS
    if CURRENT_OS is not None:
        return CURRENT_OS
    CURRENT_OS = platform.system()
    if CURRENT_OS in ['Linux', 'Darwin'] or CURRENT_OS.startswith('CYGWIN'):
        CURRENT_OS = "Linux"
    elif CURRENT_OS != "Windows":
        print("Program use is currently only for Windows/Linux!")
        exit(-1)
    return CURRENT_OS


def blank_function(*args, **kwargs):
    pass


def get_caller_module(level):
    caller = inspect.currentframe()
    for i in range(0, level):
        caller = caller.f_back
    return caller


def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


# #### Data functions

def get_buffer_checksum(buffer):
    hasher = hashlib.md5()
    hasher.update(buffer)
    return hasher.hexdigest()


def decode_unicode(byte_string):
    try:
        decoded_string = byte_string.decode('utf')
    except Exception:
        print("Unable to decode data!")
        return
    return decoded_string


def decode_json(string):
    try:
        data = json.loads(string)
    except Exception:
        print("Invalid data!")
        return
    return data


def readable_bytes(bytes):
    i = math.floor(math.log(bytes) / math.log(1024))
    sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    return str(set_precision((bytes / math.pow(1024, i)), 2)) + ' ' + sizes[i]


# #### String functions

def display_case(string):
    return ' '.join(map(str.title, string.split('_')))


def kebab_case(string):
    string = re.sub(r'([a-z])([A-Z])', r'\g<1>-\g<2>', string)
    string = re.sub(r'[\s_]+', '-', string)
    return string.lower()


def snake_case(string):
    string = re.sub(r'([a-z])([A-Z])', r'\g<1>_\g<2>', string)
    string = re.sub(r'[\s-]+', '_', string)
    return string.lower()


def camel_case(string):
    def dashscore_repl(match):
        return match.group(1).upper()
    string = re.sub(r'[-_]([a-z])', dashscore_repl, string)
    return string[0].upper() + string[1:]


def title_except(string):
    return ' '.join(map(lambda x: x.title() if x not in ['a', 'an', 'of', 'the', 'is'] else x, string.split()))


def title_roman(string):
    return ' '.join(map(lambda x: x.upper() if ROMAN_RG.match(x) else title_except(x), string.split()))


def fixup_crlf(text):
    return re.sub(r'(?<!\r)\n', '\r\n', text)


def max_string_length(string, length):
    if len(string) > length:
        string = string[:length - 3] + '...'
    return string


# #### Boolean functions

def is_truthy(string):
    truth_match = re.match(r'^(?:t(?:rue)?|y(?:es)?|1)$', string, re.IGNORECASE)
    return truth_match is not None


def is_falsey(string):
    false_match = re.match(r'^(?:f(?:alse)?|n(?:o)?|0)$', string, re.IGNORECASE)
    return false_match is not None


def eval_bool_string(string):
    if is_truthy(string):
        return True
    if is_falsey(string):
        return False


# #### Number functions

def set_precision(number, precision):
    placenum = 10**precision
    return (int(number * placenum)) / placenum


# #### Dict functions

def safe_get(input_dict, *keys):
    for key in keys:
        try:
            input_dict = input_dict[key]
        except (KeyError, TypeError):
            return None
    return input_dict


def safe_check(input_dict, valtype, *keys):
    value = safe_get(input_dict, *keys)
    return isinstance(value, valtype)


def add_dict_entry(indict, key, entry):
    indict[key] = indict[key] + [entry] if key in indict else [entry]


def inc_dict_entry(indict, key):
    indict[key] = indict[key] + 1 if key in indict else 1


def permit_dict_keys(indict, intersect_list):
    tempdict = indict.copy()
    for key in indict:
        if key not in intersect_list:
            del tempdict[key]
    return tempdict


def reject_dict_keys(indict, difference_list):
    tempdict = indict.copy()
    for key in indict:
        if key in difference_list:
            del tempdict[key]
    return tempdict


def merge_dicts(a, b):
    for key in b:
        if key in a and isinstance(a[key], dict) and isinstance(b[key], dict):
            merge_dicts(a[key], b[key])
        else:
            a[key] = b[key]
    return a


# #### List functions

def remove_duplicates(values, transform=None, sort=None, reverse=False):
    """Remove duplicates found in a list with an optional transformation and sorting"""
    output = []
    seen = []
    # Only useful if a transformation is also applied
    if sort is not None:
        values = sorted(values, key=sort, reverse=reverse)
    valuesprime = values
    if transform is not None:
        valuesprime = list(map(transform, values))
    for i in range(0, len(valuesprime)):
        if valuesprime[i] not in seen:
            output.append(values[i])
            seen.append(valuesprime[i])
    return output


def get_ordered_intersection(lista, listb):
    """Return the intersection of lista/listb with lista's order"""
    diff = list(set(lista).difference(listb))
    templist = lista.copy()
    for i in range(0, len(diff)):
        templist.pop(templist.index(diff[i]))
    return templist


def is_order_change(prelist, postlist):
    """Disregarding adds/removes, are the elements of prelist/postlist in the same order"""
    prelistprime = get_ordered_intersection(prelist, postlist)
    postlistprime = get_ordered_intersection(postlist, prelist)
    return not (prelistprime == postlistprime)


def is_add_item(prelist, postlist):
    """Has an element been added between pre/post list"""
    return any(get_add_item(prelist, postlist))


def get_add_item(prelist, postlist):
    return list(set(postlist).difference(prelist))


def is_remove_item(prelist, postlist):
    """Has an element been removed between pre/post list"""
    return len(get_remove_item(prelist, postlist)) > 0


def get_remove_item(prelist, postlist):
    return list(set(prelist).difference(postlist))
