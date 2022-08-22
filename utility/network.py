# UTILITY/NETWORK.PY

# ## PYTHON IMPORTS
import time
import requests


# ## FUNCTIONS

def get_http_data(server_filepath, method='get', **args):
    if 'timeout' not in args:
        args['timeout'] = 10
    request_method = getattr(requests, method)
    for i in range(4):
        try:
            response = request_method(server_filepath, **args)
        except requests.exceptions.ReadTimeout:
            continue
        except Exception as e:
            return "Unexpected error: %s" % str(e)
        if response.status_code == 200:
            return response.content
        if response.status_code >= 500 and response.status_code < 600:
            print("Server error; sleeping...")
            time.sleep(15)
            continue
    return "HTTP %d - %s" % (response.status_code, response.reason)
