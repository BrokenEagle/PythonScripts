# CONFIG/__INIT__.PY

# flake8: noqa

# ## PYTHON IMPORTS
import os
import dotenv
import logging

# ## PACKAGE IMPORTS
from utility import get_environment_variable, eval_bool_string

# ## LOCAL IMPORTS
from .default import *

# ## GLOBAL VARIABLES

LIBRARY_VERSION = '2.0.0'

# ## INTITIALIZATION

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

try:
    if not get_environment_variable('DEFAULT_CONFIG', False):
        from .local import *
except ImportError:
    logger.warning("Unable to load 'config\\local.py , using default config instead.")

# #### Load .env file into environment variables if set

dotenv_logger = logging.getLogger('dotenv.main')
dotenv_logger.setLevel(logging.INFO)
dotenv_logger.addHandler(logging.StreamHandler())
DOTENV_FILEPATH = get_environment_variable('DOTENV_FILEPATH', DOTENV_FILEPATH)
if DOTENV_FILEPATH is not None:
    dotenv_logger.info("\n[PID %d] Loading DOTENV file: %s" % (os.getpid(), DOTENV_FILEPATH))
    dotenv.load_dotenv(dotenv_path=DOTENV_FILEPATH, override=True, verbose=True)

# #### Environment-settable variables

settable_variables =\
    [
    'DANBOORU_HOSTNAME', 'WORKING_DIRECTORY', 'DANBOORU_USERNAME', 'DANBOORU_APIKEY', 'PIXIV_PHPSESSID',
    'TWITTER_USER_TOKEN', 'TWITTER_CSRF_TOKEN', 'TWITTER_V1_CONSUMER_KEY', 'TWITTER_V1_CONSUMER_SECRET',
    'TWITTER_V1_ACCESS_TOKEN', 'TWITTER_V1_ACCESS_SECRET', 'TWITTER_V2_API_KEY', 'TWITTER_V2_API_KEY_SECRET',
    'TWITTER_V2_API_BEARER_TOKEN', 'PAWOO_USERNAME', 'PAWOO_PASSWORD', ('PAWOO_USERID', int),
    ('DEBUG_MODE', eval_bool_string)
    ]

for var in settable_variables:
    key, parser = var if isinstance(var, tuple) else (var, None)
    globals()[key] = get_environment_variable(key, globals()[key], parser)

# #### Constructed config variables

DATA_DIRECTORY = os.path.join(WORKING_DIRECTORY, DATA_FILEPATH)
CSV_DIRECTORY = os.path.join(WORKING_DIRECTORY, CSV_FILEPATH)
JSON_DIRECTORY = os.path.join(WORKING_DIRECTORY, JSON_FILEPATH)
DTEXT_DIRECTORY = os.path.join(WORKING_DIRECTORY, DTEXT_FILEPATH)
MEDIA_DIRECTORY = os.path.join(WORKING_DIRECTORY, MEDIA_FILEPATH)
TEMP_DIRECTORY = os.path.join(WORKING_DIRECTORY, TEMP_FILEPATH)
