# UTILITY/__INIT__.PY

# ## PYTHON IMPORTS
import os


# ## FUNCTIONS

def get_environment_variable(key, default, parser=str):
    value = os.environ.get(key)
    return default if value is None else parser(value)
