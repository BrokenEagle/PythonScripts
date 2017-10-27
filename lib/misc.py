#MISC.PY
#Include functions that are program independent here

#PYTHON IMPORTS
import os
import re
import sys
import time
import inspect
import hashlib
import requests
import platform

#LOCAL GLOBALS

debugModule = {}
currentOS = None
romanrg = re.compile(r'^M?M?M?(CM|CD|D?C?C?C?)(XC|XL|L?X?X?X?)(IX|IV|V?I?I?I?)$',re.IGNORECASE)

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

#IO/String functions

def CreateDirectory(filepath):
    """Create the directory path if it doesn't already exist"""
    directory = GetDirectory(filepath)
    if not os.path.exists(directory):
        os.makedirs(directory)

def CreateOpen(*args,**kwargs):
    CreateDirectory(args[0])
    return open(*args,**kwargs)

def DownloadFile(localfilepath,serverfilepath,headers={},timeout=30,userinput=False):
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
    return [filename for filename in next(os.walk(directory))[2]]

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

def PutGetRaw(filepath,optype,data=None):
    CreateDirectory(filepath)
    with open(filepath, optype) as f:
        if optype[0] in ['w','a']:
            f.write(data)
        elif optype[0] == 'r':
            return f.read()

def PutGetData(filepath,optype,data=None):
    if optype[0] == 'w':
        PutGetRaw(filepath,optype,data=repr(data))
    elif optype[0] == 'r':
        return eval(PutGetRaw(filepath,optype))

def PutGetUnicode(filepath,optype,data=None):
    if optype[0] == 'w':
        PutGetRaw(filepath,optype[0]+'b',data=repr(data).encode('UTF'))
    elif optype[0] == 'r':
        return eval((PutGetRaw(filepath,optype[0]+'b')).decode('UTF'))

def LoadInitialValues(file,defaultvalues=None,unicode=False,isnew=False):
        if os.path.exists(file) and not isnew:
            print("Opening",file)
            if unicode: 
                return PutGetUnicode(file,'r')
            return PutGetData(file,'r')
        elif defaultvalues==None:
            if isnew:
                print("No default values")
            else:
                print(file,"not found")
            return -1
        else:
            return defaultvalues

def WriteUnicode(outfile,string):
    outfile.write(string.encode('UTF'))

def FindUnicode(string):
    for i in range(0,len(string)):
        if ord(string[i]) > 0x7f:
            return i
    return -1

def MakeUnicodePrintable(string):
    while True:
        ret = FindUnicode(string)
        if ret < 0:
            break
        string = string[:ret] + hex(ord(string[ret])) + string[ret+1:]
    return string

def PrintChar(char):
    print(char, end="", flush=True)

def TitleExcept(string):
    return ' '.join(map(lambda x:x.title() if x not in ['a', 'an', 'of', 'the', 'is'] else x,string.split()))

def TitleRoman(string):
    return ' '.join(map(lambda x:x.upper() if romanrg.match(x) else TitleExcept(x),string.split()))

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
def TurnDebugOn(modulename=None):
    global debugModule
    if (modulename==None):
        modulename = GetCallerModule(2).f_globals['__name__']
    debugModule[modulename] = True

def TurnDebugOff(modulename=None):
    global debugModule
    if modulename==None:
        modulename = GetCallerModule(2).f_globals['__name__']
    temp = debugModule.pop(modulename)

def GetDebugName():
    print("Module name:",GetCallerModule(2).f_globals['__name__'])

def GetLineNumber():
    return inspect.getframeinfo(GetCallerModule(2)).lineno

def GetFileName():
    return GetFilename(inspect.getframeinfo(GetCallerModule(2)).filename)

def DebugPrintInput(*args,safe=False,**kwargs):
    if GetCallerModule(2).f_globals['__name__'] in debugModule:
        if safe:
            SafePrint(*args,**kwargs)
        else:
            print(*args,**kwargs)
        input()

def DebugPrint(*args,safe=False,**kwargs):
    if GetCallerModule(2).f_globals['__name__'] in debugModule:
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

