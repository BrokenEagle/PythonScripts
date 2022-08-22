#MISC.PY
#Include functions that are program independent here

#PYTHON IMPORTS
import os
import re
import sys
import time
import uuid
import json
import gzip
import inspect
import hashlib
import requests
import platform

#LOCAL GLOBALS

debugModule = {}
currentOS = None
romanrg = re.compile(r'^M?M?M?(CM|CD|D?C?C?C?)(XC|XL|L?X?X?X?)(IX|IV|V?I?I?I?)$',re.IGNORECASE)
#from myglobal import workingdirectory #, temppath
#TEMP_DIRECTORY = os.path.join(workingdirectory, temppath)

#EXTERNAL FUNCTIONS

#General functions

def GetCurrentOS():
    """Set and return the current platform"""
    global currentOS
    
    if currentOS != None:
        return currentOS
    else:
        currentOS = platform.system()
        if currentOS in ['Linux', 'Darwin'] or currentOS.startswith('CYGWIN'):
            currentOS = "Linux"
        elif currentOS != "Windows":
            print("Program use is currently only for Windows/Linux!")
            exit(-1)
        return currentOS

def BlankFunction(*args,**kwargs):
    pass

def GetCallerModule(level):
    caller = inspect.currentframe()
    for i in range(0,level):
        caller = caller.f_back
    return caller

def SetPrecision(number,precision):
    placenum = 10**precision
    return (int(number*placenum))/placenum

def AbortRetryFail(*args):
    """Exception/Error handler"""
    for arg in args:
        SafePrint(arg)
    while True:
        keyinput = input("(A)bort, (R)etry, (F)ail? ")
        if keyinput.lower() == 'a':
            return False
        if keyinput.lower() == 'r':
            return True
        if keyinput.lower() == 'f':
            sys.exit(-1)

def GetBufferChecksum(buffer):
    hasher = hashlib.md5()
    hasher.update(buffer)
    return hasher.hexdigest()

def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def StaticVars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate

#Dict functions

def AddDictEntry(indict,key,entry):
    indict[key] = indict[key] + [entry] if key in indict else [entry]

def IncDictEntry(indict,key):
    indict[key] = indict[key] + 1 if key in indict else 1

def SetIntersectDict(indict,intersectlist):
    tempdict = indict.copy()
    for key in indict:
        if key not in intersectlist:
            del tempdict[key]
    return tempdict

def SetDifferenceDict(indict,differencelist):
    tempdict = indict.copy()
    for key in indict:
        if key in differencelist:
            del tempdict[key]
    return tempdict

def MinimumCutoffDict(indict,cutoff,sortcolumn=None):
    """Remove dictionary entries that don't meet a cutoff for a column"""
    tempdict = indict.copy()
    for key in indict:
        if sortcolumn == None:
            testvalue = indict[key]
        else:
            testvalue = indict[key][sortcolumn]
        if testvalue < cutoff:
            del tempdict[key]
    return tempdict

#List functions

def RemoveDuplicates(values,transform=None,sort=None,reverse=False):
    """Remove duplicates found in a list with an optional transformation and sorting"""
    output = []
    seen = []
    
    #Only useful if a transformation is also applied
    if sort != None:
        values = sorted(values, key=sort, reverse=reverse)
    DebugPrint("Values:",values)
    valuesprime = values
    if transform != None:
        valuesprime = list(map(transform,values))
    DebugPrint("Valuesprime:",valuesprime)
    for i in range(0,len(valuesprime)):
        if valuesprime[i] not in seen:
            output.append(values[i])
            seen.append(valuesprime[i])
    
    return output

def GetOrderedIntersection(lista,listb):
    """Return the intersection of lista/listb with lista's order"""
    
    diff = list(set(lista).difference(listb))
    templist = lista.copy()
    for i in range(0,len(diff)):
        temp = templist.pop(templist.index(diff[i]))
    return templist

def IsOrderChange(prelist,postlist):
    """Disregarding adds/removes, are the elements of prelist/postlist in the same order"""
    
    prelistprime = GetOrderedIntersection(prelist,postlist)
    postlistprime = GetOrderedIntersection(postlist,prelist)
    return not(prelistprime == postlistprime)

def IsAddItem(prelist,postlist):
    """Has an element been added between pre/post list"""
    
    return len(GetAddItem(prelist,postlist)) > 0

def GetAddItem(prelist,postlist):
    return list(set(postlist).difference(prelist))

def IsRemoveItem(prelist,postlist):
    """Has an element been removed between pre/post list"""
    
    return len(GetRemoveItem(prelist,postlist)) > 0

def GetRemoveItem(prelist,postlist):
    return list(set(prelist).difference(postlist))

#IO functions

def CreateDirectory(filepath):
    """Create the directory path if it doesn't already exist"""
    directory = GetDirectory(filepath)
    if not os.path.exists(directory):
        os.makedirs(directory)

def CreateOpen(*args,**kwargs):
    CreateDirectory(args[0])
    return open(*args,**kwargs)

def DownloadFile(localfilepath,serverfilepath,headers={},timeout=30,userinput=False,silence=False):
    """Download a remote file to a local location"""
    #Create the directory for the local file if it doesn't already exist
    CreateDirectory(localfilepath)
    #Does the file already exist with a size > 0
    if (not os.path.exists(localfilepath)) or ((os.stat(localfilepath)).st_size == 0):
        while True:
            try:
                response = requests.get(serverfilepath,headers=headers,timeout=timeout)
            except KeyboardInterrupt:
                exit(0)
            except requests.exceptions.ReadTimeout:
                print("\nDownload timed out!")
                continue
            except:
                print("Unexpected error:", sys.exc_info()[0],sys.exc_info()[1])
                if not AbortRetryFail(serverfilepath,sys.exc_info()[1],localfilepath,serverfilepath,headers):
                    return -1
                continue
            if response.status_code == 200:
                break
            if response.status_code >= 500 and response.status_code < 600:
                    print("Server Error! Sleeping 30 seconds...")
                    time.sleep(30)
                    continue
            if not userinput or not AbortRetryFail(serverfilepath,(response.status_code,response.reason)):
                if silence == False:
                    print(serverfilepath,response.status_code,response.reason)
                return -1
        with open(localfilepath,'wb') as outfile:
            if not (outfile.write(response.content)):
                if not AbortRetryFail(localfilepath,outfile):
                    return -1
    return 0

def TouchFile(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

def GetDirectoryListing(directory):
    try:
        return [filename for filename in next(os.walk(directory))[2]]
    except Exception as e:
        print ("Error with directory listing:", directory, e)

def GetSubdirectoryListing(directory):
    return [subdir for subdir in next(os.walk(directory))[1]]

def GetDirectory(filepath):
    if GetCurrentOS() == 'Windows':
        return filepath[:filepath.rfind('\\')+1]
    else:
        return filepath[:filepath.rfind('/')+1]

def GetFilename(filepath):
    if GetCurrentOS() == 'Windows':
        return filepath[filepath.rfind('\\')+1:]
    else:
        return filepath[filepath.rfind('/')+1:]

def GetHTTPDirectory(webpath):
    return webpath[:webpath.rfind('/')+1]

def GetHTTPFilename(webpath):
    start = webpath.rfind('/')+1
    isextras = webpath.rfind('?')
    end = isextras if isextras > 0 else len(webpath)+1
    return webpath[start:end]

def GetFileExtension(filepath):
    return filepath[filepath.rfind('.')+1:]

def GetFileNameOnly(filepath):
    filename = GetFilename(filepath)
    return filename[:filename.rfind('.')]

def GetDirectorySeparator():
    if GetCurrentOS() == "Windows":
        return "\\"
    else:
        return "/"

def JoinDirectories(directorylist):
    return GetDirectorySeparator().join(directorylist)

"""
def PutGetRaw(filepath,optype,data=None):
    if filepath != os.devnull:
        CreateDirectory(filepath)
    with open(filepath, optype) as f:
        if optype[0] in ['w','a']:
            f.write(data)
        elif optype[0] == 'r':
            return f.read()
"""

def PutGetRaw(filepath, optype, data=None, safe=False, zip=False):
    if filepath != os.devnull:
        CreateDirectory(filepath)
        if optype[0] == 'r' and not os.path.exists(filepath):
            return
    if optype[0] in ['w', 'a']:
        return PutRaw(filepath, optype, data, safe, zip)
    elif optype[0] == 'r':
        return GetRaw(filepath, optype, zip)

# with open(filepath, optype) as file:
def PutRaw(filepath, optype, data, safe, zip):
    write, encode, plus = re.match(r'([wa])(b?)(\+?)', optype).groups()
    if (encode or zip) and not isinstance(data, bytes):
        data = data.encode('utf')
    if safe:
        return SafePutRaw(filepath, optype, data, zip)
    fopen = gzip.open if zip else open
    with fopen(filepath, optype) as file:
        return file.write(data)

def SafePutRaw(filepath, optype, data, zip):
    # 1. Write the data to disk in a separate location
    temp_subdir = str(uuid.uuid4())
    temp_filepath = os.path.join(TEMP_DIRECTORY, temp_subdir, GetFilename(filepath))
    CreateDirectory(temp_filepath)
    fopen = gzip.open if zip else open
    with fopen(temp_filepath, optype) as file:
        output = file.write(data)
        if not output:
            return None
    time.sleep(0.2) # Give some time for the OS to catch up... reduces exceptions
    # 2. Read the data from disk and compare to the original
    check_content = GetRaw(temp_filepath, 'rb', zip)
    encoded_data = data.encode('utf') if isinstance(data, str) else data
    if GetBufferChecksum(encoded_data) != GetBufferChecksum(check_content):
        return None
    # 3. Get the original data before moving
    old_data = GetRaw('rb', read_optype, False) if os.path.exists(filepath) else None
    if not SafeMove(temp_filepath, filepath):
        # 4. If there was a move error, restore the original data if possible
        if old_data is not None:
            for i in range(3):
                if PutRaw(filepath, 'wb', old_data, False, False):
                    break
                time.sleep(0.5)
            else:
                raise Exception(f"Unable to save data to file: {filepath}; tmp: {temp_filepath}")
        return None
    os.rmdir(os.path.join(TEMP_DIRECTORY, temp_subdir))
    return output

def SafeMove(old_filepath, new_filepath):
    try:
        os.replace(old_filepath, new_filepath)
    except Exception as e:
        print(e, old_filepath, new_filepath)
        return False
    return True

def GetRaw(filepath, optype, zip):
    fopen = gzip.open if zip else open
    [encode, plus] = re.match(r'r(b?)(\+?)', optype).groups()
    with fopen(filepath, optype) as file:
        try:
            load = file.read()
        except Exception as e:
            print(e, filepath)
            return
    return DecodeUnicode(load) if not encode else load

def PutGetData(filepath,optype,data=None):
    if optype[0] == 'w':
        PutGetRaw(filepath,optype,data=repr(data))
    elif optype[0] == 'r':
        load = PutGetRaw(filepath,optype)
        return eval(load)

def PutGetUnicode(filepath,optype,data=None):
    if optype[0] == 'w':
        PutGetRaw(filepath,optype[0]+'b',data=repr(data).encode('UTF'))
    elif optype[0] == 'r':
        return eval((PutGetRaw(filepath,optype[0]+'b')).decode('UTF'))

def DecodeUnicode(byte_string):
    if not isinstance(byte_string, bytes):
        return byte_string
    try:
        decoded_string = byte_string.decode('utf')
    except Exception:
        print("Unable to decode data!")
        return
    return decoded_string

def DecodeJSON(string):
    try:
        data = json.loads(string)
    except Exception:
        print("Invalid data!")
        return
    return data

def PutGetJSON(filepath, optype, data=None, unicode=False):
    if optype[0] in ['w', 'a']:
        save_data = json.dumps(data, ensure_ascii=unicode)
        # Try writing to null device first to avoid clobbering the files upon errors
        PutGetRaw(os.devnull, optype, save_data, unicode)
        return PutGetRaw(filepath, optype, save_data, unicode)
    if optype[0] == 'r':
        load = PutGetRaw(filepath, optype, None, unicode)
        if load is not None:
            return DecodeJSON(load)

def LoadInitialValues(file,defaultvalues=None,unicode=False,isnew=False,silence=False):
        if os.path.exists(file) and not isnew:
            if not silence:
                print("Opening",file)
            if unicode: 
                return PutGetUnicode(file,'r')
            return PutGetData(file,'r')
        elif defaultvalues==None:
            if isnew and not silence:
                print("No default values")
            elif not silence:
                print(file,"not found")
            return -1
        else:
            return defaultvalues

def WriteUnicode(outfile,string):
    outfile.write(string.encode('UTF'))

#String functions

def FindUnicode(string):
    for i in range(0,len(string)):
        if (isinstance(string,str) and ord(string[i]) > 0x7f) or (isinstance(string,bytes) and string[i] > 0x7f):
            return i
    return -1

def MakeUnicodePrintable(string):
    while True:
        ret = FindUnicode(string)
        if ret < 0:
            break
        string = string[:ret] + (hex(ord(string[ret])) if isinstance(string,str) else hex(string[ret]).encode()) + string[ret+1:]
    return string

def PrintChar(char):
    print(char, end="", flush=True)

def TitleExcept(string):
    return ' '.join(map(lambda x:x.title() if x not in ['a', 'an', 'of', 'the', 'is'] else x,string.split()))

def TitleRoman(string):
    return ' '.join(map(lambda x:x.upper() if romanrg.match(x) else TitleExcept(x),string.split()))

def MaxStringLength(string,length):
    if len(string) > length:
        string = string[:length-3]+'...'
    return string

#Time functions

def GetCurrentTime():
    return time.time()

def GetCurrentTimeZulu():
    return time.mktime(time.gmtime())

def HasMonthPassed(starttime,endtime,num=1):
    return (((starttime - endtime)/MonthsToSeconds(num)) > 1.0)

def HasWeekPassed(starttime,endtime,num=1):
    return (((starttime - endtime)/WeeksToSeconds(num)) > 1.0)

def HasDayPassed(starttime,endtime,num=1):
    return (((starttime - endtime)/DaysToSeconds(num)) > 1.0)

def HasHourPassed(starttime,endtime,num=1):
    return (((starttime - endtime)/HoursToSeconds(num)) > 1.0)

def WithinOneSecond(starttime,endtime):
    return ((abs(starttime-endtime)) < 1.0)

def MonthsToSeconds(intime):
    return (intime * 60*60*24*30)

def WeeksToSeconds(intime):
    return (intime * 60*60*24*7)

def DaysToSeconds(intime):
    return (intime * 60*60*24)

def HoursToSeconds(intime):
    return (intime * 60*60)

def SecondsToMonths(intime):
    return intime / (60*60*24*30)

def SecondsToWeeks(intime):
    return intime / (60*60*24*7)

def SecondsToDays(intime):
    return intime / (60*60*24)

def SecondsToHours(intime):
    return intime / (60*60)

def AddDays(timestring,days):
    return time.strftime("%Y-%m-%d",(time.gmtime(time.mktime(time.strptime(timestring,"%Y-%m-%d"))+DaysToSeconds(days))))

def GetDate(epochtime):
    return time.strftime("%Y-%m-%d",time.gmtime(epochtime))

#Debug functions
def ProcessDebugArgs(input):
    if input is None: return
    debug_modules = input.split()
    for module in debug_modules:
        if module == 'self':
            TurnDebugOn()
        else:
            TurnDebugOn(module)

def TurnDebugOn(modulename=None):
    global debugModule
    if (modulename==None):
        modulename = GetModulename()
    debugModule[modulename] = True

def TurnDebugOff(modulename=None):
    global debugModule
    if modulename==None:
        modulename = GetModulename()
    temp = debugModule.pop(modulename)

def GetModulename(extra=0):
    module = GetCallerModule(2+extra)
    return module.f_globals['__name__'] if module.f_globals['__name__'] != '__main__' else GetFileNameOnly(GetCallerModule(2).f_globals['__file__'])
    #return GetFileNameOnly(GetCallerModule(2).f_globals['__file__'])
    #return GetCallerModule(2).f_globals['__name__']

def GetFuncName(level):
    return inspect.stack()[level].function

def GetLineNumber():
    return inspect.getframeinfo(GetCallerModule(2)).lineno

def GetFileName():
    return GetFilename(inspect.getframeinfo(GetCallerModule(2)).filename)

def IsDebug(extra=1):
    return GetModulename(1+extra) in debugModule

def DebugPrintInput(*args,safe=False,**kwargs):
    if IsDebug():
        if safe:
            SafePrint(*args,**kwargs)
        else:
            print(*args,**kwargs)
        input()

def DebugPrint(*args,safe=False,**kwargs):
    if IsDebug():
        if safe:
            SafePrint(*args,**kwargs)
        else:
            print(*args,**kwargs)

def SafePrint(*args,**kwargs):
    temp = ''
    for arg in args:
        if type(arg) == type(''):
            temp += arg + ' '
        else:
            temp += repr(arg) + ' '
    temp.strip()
    print(temp.encode('ascii','backslashreplace').decode(),**kwargs)
