# CONFIG/DEFAULT.PY

# ## DIRECTORY VARIABLES

'''WINDOWS'''
"""Filepaths need to end with a double backslash ('\\')"""
"""All backslashes ('\') in a filepath need to be double escaped ('\\')"""

WORKING_DIRECTORY = 'C:\\Temp\\'

'''LINUX'''
"""Filepaths need to end with a forwardslash ('/')"""
'''
WORKING_DIRECTORY = "/tmp/"
'''

"""Subdirectory paths should not begin or end with a directory separator ('\' or '/')"""
DATA_FILEPATH = 'data'
CSV_FILEPATH = 'csv'
JSON_FILEPATH = 'json'
DTEXT_FILEPATH = 'dtext'
MEDIA_FILEPATH = 'media'
TEMP_FILEPATH = 'temp'

"""Path for loading the .env to load environment variables from. Can either be a relative or an absolute path"""
DOTENV_FILEPATH = None


# ## NETWORK VARIABLES

DANBOORU_HOSTNAME = 'https://danbooru.donmai.us'

# #### Danbooru API tokens

DANBOORU_USERNAME = None
DANBOORU_APIKEY = None

# #### Pixiv browser tokens
"""Log into Twitter and get these values from the cookies."""

PIXIV_USERNAME = None
PIXIV_PHPSESSID = None  # PHPSESSID

# #### Twitter browser tokens
"""Log into Twitter and get these values from the cookies."""

TWITTER_USER_TOKEN = None  # auth_token
TWITTER_CSRF_TOKEN = None  # ct0

# #### Twitter V1 API tokens

TWITTER_V1_CONSUMER_KEY = None
TWITTER_V1_CONSUMER_SECRET = None
TWITTER_V1_ACCESS_TOKEN = None
TWITTER_V1_ACCESS_SECRET = None

# #### Twitter V2 API tokens

TWITTER_V2_API_KEY = None
TWITTER_V2_API_KEY_SECRET = None
TWITTER_V2_API_BEARER_TOKEN = None

# #### Pawoo credentials

PAWOO_USERNAME = None
PAWOO_PASSWORD = None
PAWOO_USERID = None

# ## OTHER VARIABLES

DEBUG_MODE = False
