# UTILITY/__INIT__.PY

# ## PYTHON IMPORTS
import os
import re


# ## FUNCTIONS

def get_environment_variable(key, default, parser=str):
    value = os.environ.get(key)
    return default if value is None else parser(value)


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
