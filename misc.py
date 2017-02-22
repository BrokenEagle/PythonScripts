#MISC.PY
#Include functions that are program independent here

#PYTHON IMPORTS
import os
import sys
import time
import inspect
import hashlib
import urllib.request

#LOCAL GLOBALS

debugModule = {}

#EXTERNAL FUNCTIONS

#General functions

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

#List functions

def RemoveDuplicates(values,transform=None,sort=None,reverse=False):
	"""Remove duplicates found in a list with an optional transformation and sorting"""
	output = []
	seen = []
	
	#Only useful if a transformation is also applied
	if sort != None:
		values = sorted(values, key=sort, reverse=reverse)
	
	valuesprime = values
	if transform != None:
		valuesprime = list(map(transform,values))
	
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

def CreateOpen(filepath,optype):
	CreateDirectory(filepath)
	return open(filepath,optype)

def DownloadFile(localfilepath,serverfilepath,headers={},timeout=60):
	"""Download a remote file to a local location"""
	#Create the directory for the local file if it doesn't already exist
	CreateDirectory(localfilepath)
	#Does the file already exist with a size > 0
	if (not os.path.exists(localfilepath)) or ((os.stat(localfilepath)).st_size == 0):
		while True:
			with open(localfilepath,'wb') as outfile:
				while True:
					try:
						req = urllib.request.Request(serverfilepath)
						for item in headers:
							req.add_header(item,headers[item])
						response = urllib.request.urlopen(req,timeout=timeout)
						if response.status == 200:
							break
						if not AbortRetryFail(serverfilepath,(response.status,response.reason)):
							return -1
					except urllib.error.HTTPError as inst:
						response = inst
						if response.status >= 500 and response.status < 600:
							print("Server Error! Sleeping 30 seconds...")
							time.sleep(30)
							continue
						print(serverfilepath,response.status,response.reason)
						return -1
					except:
						print("Unexpected error:", sys.exc_info()[0],sys.exc_info()[1])
						if not AbortRetryFail(serverfilepath,sys.exc_info()[1],localfilepath,serverfilepath,headers):
							return -1
				if not (outfile.write(response.read())):
					if not AbortRetryFail(localfilepath,outfile):
						return -1
				else:
					return 0
	return 0

def TouchFile(fname, times=None):
	with open(fname, 'a'):
		os.utime(fname, times)

def GetDirectory(filepath):
	return filepath[:filepath.rfind('\\')]

def GetFilename(filepath):
	return filepath[filepath.rfind('\\')+1:]

def GetHTTPDirectory(webpath):
	return webpath[:webpath.rfind('/')+1]

def GetHTTPFilename(webpath):
	start = webpath.rfind('/')+1
	isextras = webpath.rfind('?')
	end = isextras if isextras > 0 else len(webpath)+1
	return webpath[start:end]

def GetFileExtension(filepath):
	return filepath[filepath.rfind('.')+1:]

def PutGetRaw(filepath,optype,data=None):
	CreateDirectory(filepath)
	with open(filepath, optype) as f:
		if optype[0] == 'w':
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

def LoadInitialValues(file,defaultvalues=None,unicode=False):
		if os.path.exists(file):
			print("Opening",file)
			if unicode: 
				return PutGetUnicode(file,'r')
			return PutGetData(file,'r')
		elif defaultvalues==None:
			print(file,"not found")
			exit(-1)
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

def GetLineNumber():
	return inspect.getframeinfo(GetCallerModule(2)).lineno

def GetFileName():
	return GetFilename(inspect.getframeinfo(GetCallerModule(2)).filename)

def DebugPrintInput(*args,**kwargs):
	if GetCallerModule(2).f_globals['__name__'] in debugModule:
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
	print(temp.encode('ascii','replace').decode(),**kwargs)
	return temp
