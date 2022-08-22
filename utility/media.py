# UTILITY/FILE.PY

# ## PYTHON IMPORTS
import os

# ## LOCAL IMPORTS
from .network import get_http_data
from .file import create_directory, put_get_raw
from .print import abort_retry_fail


# ## FUNCTIONS

def download_file(local_filepath, server_filepath, headers={}, timeout=30, userinput=False):
    """Download a remote file to a local location"""
    # Create the directory for the local file if it doesn't already exist
    create_directory(local_filepath)
    # Does the file already exist with a size > 0
    if (os.path.exists(local_filepath)) and ((os.stat(local_filepath)).st_size > 0):
        return 0
    while True:
        buffer = get_http_data(server_filepath, headers=headers, timeout=timeout)
        if isinstance(buffer, str):
            if userinput and abort_retry_fail(buffer):
                continue
            return -1
        put_get_raw(local_filepath, 'wb', buffer)
        return len(buffer)
