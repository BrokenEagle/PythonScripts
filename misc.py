#MISC.PY
#Include functions that are program independent here

#PYTHON IMPORTS
import inspect
import argparse
import re
import os
import sys
import time
import urllib.request

#LOCAL GLOBALS

debugModule = {}

#EXTERNAL FUNCTIONS

#General functions

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

#IO/String functions

def CreateDirectory(filepath):
	"""Create the directory path if it doesn't already exist"""
	directory = GetDirectory(filepath)
	if not os.path.exists(directory):
		os.makedirs(directory)

def DownloadFile(localfilepath,serverfilepath):
	"""Download a remote file to a local location"""
	#Create the directory for the local file if it doesn't already exist
	CreateDirectory(localfilepath)
	print(localfilepath,serverfilepath)
	#Does the file already exist with a size > 0
	if (not os.path.exists(localfilepath)) or ((os.stat(localfilepath)).st_size == 0):
		while True:
			with open(localfilepath,'wb') as outfile:
				while True:
					try:
						response = urllib.request.urlopen(serverfilepath)
						if response.status == 200:
							break
					except:
						print("Unexpected error:", sys.exc_info()[0],sys.exc_info()[1])
						input()
						pass
					if not AbortRetryFail(serverfilepath,(response.status,response.reason)):
						return -1
				if not (outfile.write(response.read())):
					if not AbortRetryFail(localfilepath,outfile):
						return -1
				else:
					return 0

def GetDirectory(filepath):
	return filepath[:filepath.rfind('\\')]

def GetFilename(filepath):
	return filepath[filepath.rfind('\\')+1:]

def GetHTTPDirectory(webpath):
	return webpath[:webpath.rfind('/')]

def GetHTTPFilename(webpath):
	start = webpath.rfind('/')+1
	isextras = webpath.rfind('?')
	end = isextras if isextras > 0 else len(webpath)+1
	return webpath[start:end]

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

#Time functions

def GetCurrentTime():
	return time.time()

def HasMonthPassed(starttime,endtime):
	return (((starttime - endtime)/(60*60*24*30)) > 1.0)

def HasDayPassed(starttime,endtime):
	return (((starttime - endtime)/(60*60*24)) > 1.0)

def HasHourPassed(starttime,endtime):
	return (((starttime - endtime)/(60*60)) > 1.0)

def WithinOneSecond(starttime,endtime):
	return ((abs(starttime-endtime)) < 1.0)

def DaysToSeconds(intime):
	return (intime * 60*60*24)

def SecondsToDays(intime):
	return intime / (60*60*24)

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

def DebugPrintInput(*args):
	if GetCallerModule(2).f_globals['__name__'] in debugModule:
		print(*args)
		input()

def DebugPrint(*args):
	if GetCallerModule(2).f_globals['__name__'] in debugModule:
		print(*args)

def SafePrint(*args):
	temp = ''
	for arg in args:
		if type(arg) == type(''):
			temp += arg + ' '
		else:
			temp += repr(arg) + ' '
	temp.strip()
	print(temp.encode('ascii','replace').decode())
	return temp
