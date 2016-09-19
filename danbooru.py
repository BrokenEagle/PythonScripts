#DANBOORU.PY

#Include functions related to Danbooru here

#PYTHON IMPORTS
import os
import re
import sys
import time
from datetime import datetime
import argparse
import urllib.request
import urllib.parse

#MY IMPORTS
from misc import DebugPrint,DebugPrintInput,CreateDirectory,AbortRetryFail,DownloadFile
from myglobal import username,apikey,workingdirectory,imagefilepath

#LOCAL GLOBALS

dateregex = '^[0-9]{4,4}-[0-9]{2,2}-[0-9]{2,2}$'
idregex = '(\\d+)\.\.(\\d+)'

#The following are needed to properly evaluate the JSON responses from Danbooru
null = None
true = True
false = False

#Danbooru URL Constants
danbooru_domain = 'http://danbooru.donmai.us'
danbooru_auth = '?login=%s&api_key=%s'

#For building Danbooru URL's and methods on the fly based on the operation type
#Only list, create, show, update, delete and count have been tested
danbooru_ops = {'list':('.json','GET'),'create':('.json','POST'),'show':('/%d.json','GET'),'update':('/%d.json','PUT'),'delete':('/%d.json','DELETE'),'revert':('/%d/revert.json','PUT'),'copy_notes':('/%d/copy_notes.json','PUT'),'banned':('banned.json','GET'),'undelete':('%d/undelete.json','POST'),'create_or_update':('create_or_update.json','POST'),'count':('counts/posts.json','GET')}

#CLASSES

class DanbooruError(Exception):
    """Base class for exceptions in this module. (Currently unused)"""
    pass

#EXTERNAL FUNCTIONS

def SubmitRequest(opname,typename,id = None,urladdons = '',senddata = None):
	"""Send an API request to Danbooru. The following operations require different positional arguments:
	list: urladdons; show: id; create: senddata; update: id, senddata; delete: id; count: urladdons
	
	Opname and typename are passed in as strings.
	Ex: SubmitRequest('show','posts',id=1234567)
	"""
	urlsubmit = GetDanbooruUrl(opname,typename)
	if id != None:
		urlsubmit = urlsubmit % (id,username,apikey)
	else:
		urlsubmit = urlsubmit % (username,apikey)
	urlsubmit += urladdons
	httpmethod = danbooru_ops[opname][1]
	while True:
		#Failures occur most often in two places. The first is communicating with Danbooru
		try:
			DebugPrintInput(repr(urlsubmit),repr(senddata),repr(httpmethod))
			req = urllib.request.Request(url=urlsubmit,data=senddata,method=httpmethod)
			httpresponse = urllib.request.urlopen(req)
			DebugPrintInput(httpresponse.status,httpresponse.reason)
		except urllib.error.HTTPError as inst:
			if AbortRetryFail(urlsubmit,senddata,httpmethod,inst):
				continue
			else:
				return -1
		except:
			print(urlsubmit,httpmethod)
			print("Unexpected error:", sys.exc_info()[0],sys.exc_info()[1])
			raise
		#Success, and the server returned something to evaluate
		if httpresponse.status == 200:
			#The second most common error is evaluating the response from Danbooru.
			#If the response is particularly large, the following will hang.
			#This can be detected by the printing of "Before Eval" without the subsequent "After Eval"
			DebugPrint("Before Eval")
			try:
				evaltemp = httpresponse.read()
				submittemp = eval((evaltemp).decode(encoding='utf-8'))
			except SyntaxError as inst:
				print(evaltemp)
				print(urlsubmit,httpmethod)
				print(inst)
				sys.exit(-1)
			DebugPrint("After Eval")
			return submittemp
		#Success, but the server returned nothing back to evaluate
		elif (httpresponse.status > 200) and (httpresponse.status < 300):
			return httpresponse
		#Anything other than a 200 or 204 should raise an exception and be caught above
		#The following is just in case the above is not true
		elif not AbortRetryFail(urlsubmit,(httpresponse.status,httpresponse.reason)):
			return -1

def GetCurrFilePath(postdict,size="medium"):
	"""Get filepath for storing server different sized files on local system.
	Input is a post dictionary obtained from Danbooru with either 'list' or 'show'.
	"""
	if size == "small":
		return workingdirectory + imagefilepath + postdict["md5"] + '.jpg'
	if size == "medium":
		fileext = postdict["large_file_url"][postdict["large_file_url"].rfind('.'):]
		return workingdirectory + imagefilepath + postdict["md5"] + fileext
	if size == "large":
		return workingdirectory + imagefilepath + postdict["md5"] + '.' + postdict["file_ext"]

def GetServFilePath(postdict,size="medium"):
	"""Get serverpath for different sized files
	Input is a post dictionary obtained from Danbooru with either 'list' or 'show'.
	"""
	if size=="small":
		return danbooru_domain + postdict["preview_file_url"]
	if size=="medium":
		return danbooru_domain + postdict["large_file_url"]
	if size=="large":
		return danbooru_domain + postdict["file_url"]

def DownloadPostImage(postdict,size="medium"):
	"""Download a post image from Danbooru"""
	
	localfilepath = GetCurrFilePath(postdict,size)
	serverfilepath = GetServFilePath(postdict,size)
	DebugPrintInput(localfilepath,serverfilepath)
	return DownloadFile(localfilepath,serverfilepath)

#EXTERNAL HELPER FUNCTIONS

def JoinArgs(*args):
	"""Take multiple URL arguments of form "name=val" and concatenate them together"""
	string = ''
	for arg in args:
		string = string + '&' + arg
	return string

def GetArgUrl(typename,keyname,data):
	"""Parameters are for URL arguments as such: typename[keyname]=data or typename=data
	E.g. notes[post_id]=1234, would be EncodeData('notes','post_id',1234)
	"""
	if keyname == '':
		return urllib.parse.urlencode(eval("{'%s':%s}" % (typename,repr(data))))
	else:
		return urllib.parse.urlencode(eval("{'%s[%s]':%s}" % (typename,keyname,repr(data))))

def GetArgUrl2(typename,data):
	return GetArgUrl(typename,'',data)

def GetArgUrl3(typename,keyname,data):
	return GetArgUrl(typename,keyname,data)

def GetPageUrl(id):
	"""Get the page argument for all ID's below the parameter 'id'"""
	return GetArgUrl('page','','b'+str(id))

def EncodeData(typename,keyname,data):
	"""Encode data for the senddata parameter of SubmitRequest."""
	return (GetArgUrl(typename,keyname,data)).encode('ascii')

def JoinData(*args):
	"""Take multiple POST arguments of form "name=val" and concatenate them together"""
	bytes = b''
	for arg in args:
		bytes += arg + b'&'
	return bytes[:-1]

def ProcessTimestamp(timestring):
	datetuple = datetime.strptime(timestring,"%Y-%m-%dT%H:%M:%S.%fZ")
	return time.mktime(datetuple.timetuple()) + (datetuple.microsecond/1000000)

def DateStringInput(string):
	match = re.match(dateregex,string)
	if match == None:
		raise argparse.ArgumentTypeError("Date input must be of format 'YYYY-MM-DD'")
	return match.group()

def IDStringInput(string):
	match = re.match(idregex,string)
	if match == None:
		raise argparse.ArgumentTypeError("ID input must be of format 'Start#..End#'")
	start = int(match.group(1))
	end = int(match.group(2))
	if start > end:
		raise argparse.ArgumentTypeError("Start ID must be less than End ID")
	return match.group()

def HasChild(postdict):
	return postdict['has_visible_children']

def HasParent(postdict):
	return (postdict['parent_id'] != None)

def HasRelated(postdict):
	return (HasParent(postdict) or HasChild(postdict))


#INTERNAL HELPER FUNCTIONS

def GetDanbooruUrl(opname,typename):
	"""Build Danbooru URL on the fly"""
	return (danbooru_domain + '/' + typename + danbooru_ops[opname][0]+danbooru_auth)