#MYGLOBAL.PY
"""Primary use is to store environment variables"""

#GLOBAL VARIABLES

#Other domains include hijiribe, sonohara, and testbooru
booru_domain = "http://danbooru.donmai.us"

"""Remove the preceding and following triple apostrophes ''' in the Windows or Linux section"""

###WINDOWS###
'''
"""Filepaths need to end with a double backslash ('\\')"""
"""All backslashes ('\') in a filepath need to be double escaped ('\\')"""
workingdirectory = "D:\\temp\\"
datafilepath = "data\\"
csvfilepath = "csv\\"
jsonfilepath = "json\\"
dtextfilepath = "dtext\\"
imagefilepath = "pictures\\"
'''

###LINUX###
'''
"""Filepaths need to end with a forwardslash ('/')"""
workingdirectory = "/home/USERNAME/temp/"
datafilepath = "data/"
csvfilepath = "csv/"
jsonfilepath = "json/"
dtextfilepath = "dtext/"
imagefilepath = "pictures/"
'''

"""Uncomment the following lines (remove the '#') and enter user specific info"""
#username = "USERNAME_GOES_HERE"
#apikey = "API_KEY_GOES_HERE"
#pixivusername = "USERNAME_GOES_HERE"
#pixivpassword = "PASSWORD_GOES_HERE"
