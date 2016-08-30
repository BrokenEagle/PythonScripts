#MISC.PY
"""Functions that are program independent go here"""

#PYTHON IMPORTS
import os
import sys
import time
import inspect

#MODULE GLOBAL VARIABLES

debugModule = {}

#EXTERNAL FUNCTIONS

def RemoveDuplicates(values):
    output = []
    seen = set()
    for value in values:
        if value not in seen:
            output.append(value)
            seen.add(value)
    return output

#IO/String functions

def CreateDirectory(filepath):
	directory = filepath[:filepath.rfind('\\')]
	if not os.path.exists(directory):
		os.makedirs(directory)

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

def WithinOneSecond(starttime,endtime):
	return ((abs(starttime-endtime)) < 1.0)

def DaysToSeconds(intime):
	return (intime * 60*60*24)

def SecondsToDays(intime):
	return intime / (60*60*24)

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

#INTERNAL FUNCTIONS

def GetCallerModule(level):
	caller = inspect.currentframe()
	for i in range(0,level):
		caller = caller.f_back
	return caller