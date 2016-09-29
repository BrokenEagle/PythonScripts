#DANBOORU.PY

#Include functions related to Danbooru here

#PYTHON IMPORTS
import re
import sys
import time
from datetime import datetime
import argparse
import urllib.request
import urllib.parse

#MY IMPORTS
from misc import DebugPrint,DebugPrintInput,CreateDirectory,AbortRetryFail,DownloadFile,BlankFunction
from myglobal import username,apikey,workingdirectory,imagefilepath

#LOCAL GLOBALS

dateregex = '^([0-9]{4}-[0-9]{2}-[0-9]{2})?(\\.\\.)?([0-9]{4}-[0-9]{2}-[0-9]{2})?$'
idregex = '^(\\d+)?(\\.\\.)?(\\d+)?$'
ageregex = '^([0-9]*)([dhimoswy]*)?(\\.\\.)?([0-9]*)?([dhimoswy]*)$'
agetypedict = {'s':1,'mi':60,'h':60*60,'d':60*60*24,'w':60*60*24*7,'mo':60*60*24*30,'y':60*60*24*365}
disregardtags = ['tagme','commentary','check_commentary','translated','partially_translated','check_translation','annotated','partially_annotated','check_my_note','check_pixiv_source']

#The following are needed to properly evaluate the JSON responses from Danbooru
null = None
true = True
false = False

#Danbooru URL Constants
danbooru_domain = 'http://danbooru.donmai.us'
danbooru_auth = '?login=%s&api_key=%s'

#For building Danbooru URL's and methods on the fly based on the operation type
#Only list, create, show, update, delete, revert, undo and count have been tested
danbooru_ops = {'list':('.json','GET'),'create':('.json','POST'),'show':('/%d.json','GET'),'update':('/%d.json','PUT'),'delete':('/%d.json','DELETE'),'revert':('/%d/revert.json','PUT'),'copy_notes':('/%d/copy_notes.json','PUT'),'banned':('banned.json','GET'),'undelete':('/%d/undelete.json','POST'),'undo':('/%d/undo.json','PUT'),'create_or_update':('create_or_update.json','POST'),'count':('counts/posts.json','GET')}

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

def GetPostCount(searchtags):
	urladd = JoinArgs(GetArgUrl2('tags',searchtags))
	return SubmitRequest('count','',urladdons=urladd)['counts']['posts']

#LOOP CONSTRUCTS

def IDPageLoop(type,limit,iteration,addonlist=[],inputs={},firstloop=[],postprocess=BlankFunction):
	"""Standard loop using 'ID' pages to iterate
	'firstloop' is for types that require the pageID to sort properly, e.g. forum topics,
	or for continuing from the last saved location, such as in the case of a crash
	"""
	currentid = -1
	urladd = JoinArgs(GetLimitUrl(limit),*firstloop,*addonlist)
	while True:
		typelist = SubmitRequest('list',type,urladdons=urladd)
		if len(typelist) == 0:
			return currentid
		for item in typelist:
			currentid = item['id']
			if iteration(item,**inputs) < 0:
				return currentid
		postprocess(typelist,**inputs)
		urladd = JoinArgs(GetLimitUrl(limit),GetPageUrl(currentid),*addonlist)
		print(':', end="", flush=True)

def NumPageLoop(type,limit,iteration,addonlist=[],inputs={},page=1,postprocess=BlankFunction):
	"""Standard loop using page numbers to iterate"""
	
	idseen = []
	while True:
		urladd = JoinArgs(GetLimitUrl(limit),GetPageNumUrl(page),*addonlist)
		typelist = SubmitRequest('list',type,urladdons=urladd)
		if len(typelist) == 0:
			return page
		idlist = []
		for item in typelist:
			if item['id'] in idseen:
				continue
			idlist += [item['id']]
			if iteration(item,**inputs) < 0:
				return page
		postprocess(typelist,**inputs)
		idseen = idlist; page += 1
		print(':', end="", flush=True)

#LOOP ITERABLES

def DownloadPostImageIteration(post,related=False,size="medium"):
	"""To be called with loop construct to download images"""
	
	#Download post image from server to local
	DownloadPostImage(post,size)
	
	#Are we downloading all child/parent posts?
	if related and (HasChild(post) or HasParent(post)):
		totaldownloaded = len(DownloadRelatedPostImages(post,post['id']))
		print("(R%d)" % totaldownloaded,end="",flush=True)
	
	#Print some feedback
	print('.', end="", flush=True)
	return 0

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
	return GetArgUrl2('page','b'+str(id))

def GetLimitUrl(limit):
	return GetArgUrl2('limit',limit)

def GetPageNumUrl(pagenum):
	return GetArgUrl2('page',pagenum)

def GetSearchUrl(keyname,data):
	return GetArgUrl3('search',keyname,data)

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
	if (match.group(1) == None) and (match.group(3) == None):
		raise argparse.ArgumentTypeError("At least one date must be included")
	if (match.group(1) != None) and (match.group(3) != None):
		if time.strptime(match.group(1),'%Y-%m-%d') > time.strptime(match.group(3),'%Y-%m-%d'):
			raise argparse.ArgumentTypeError("1st date must be before 2nd date")
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

def AgeStringInput(string):
	match = re.match(ageregex,string)
	if match == None:
		raise argparse.ArgumentTypeError("Age input must be of format 'Start..End'\nValid qualifiers are 's','mi','h','d','w','mo','y'")
	if match.group(1) == match.group(2) == match.group(4) == match.group(5) == '':
		raise argparse.ArgumentTypeError("At least one age specifier must be used")
	if (match.group(1) == "" and match.group(2) != "") or \
		(match.group(2) == "" and match.group(1) != "") or \
		(match.group(4) == "" and match.group(5) != "") or \
		(match.group(5) == "" and match.group(4) != ""):
		raise argparse.ArgumentTypeError("Specificers must include both a number and type")
	if ((match.group(2) != "") and (match.group(2) not in agetypedict)) or \
		((match.group(5) != "") and (match.group(5) not in agetypedict)):
		raise argparse.ArgumentTypeError("Invalid specifier type")
	if ((match.group(1) != "") and (match.group(4) != "")) and \
		(int(match.group(1)) * agetypedict[match.group(2)]) > (int(match.group(4)) * agetypedict[match.group(5)]):
		raise argparse.ArgumentTypeError("Start specifier must be less than end specifier")
	return match.group()

#POST SPECIFIC FUNCTIONS

def IsUpload(postdict):
	return (len(postdict['unchanged_tags']) == 0) and (len(postdict['added_tags']) > 0)

def HasChild(postdict):
	return postdict['has_visible_children']

def HasParent(postdict):
	return (postdict['parent_id'] != None)

def HasRelated(postdict):
	return (HasParent(postdict) or HasChild(postdict))

def MetatagExists(string):
	return (ParentExists(string) or SourceExists(string) or RatingExists(string))

def ParentExists(string):
	return ((string.find("parent:")) >= 0)

def SourceExists(string):
	return ((string.find("source:")) >= 0)

def RatingExists(string):
	return ((string.find("rating:")) >= 0)

#TAG SPECIFIC FUNCTIONS

def GetTagCategory(tagname):
	"""Query danbooru for the category of a tag"""
	
	#Send tag query to Danbooru
	urladd = JoinArgs(GetSearchUrl('name',tagname))
	taglist = SubmitRequest('list','tags',urladdons = urladd)
	
	#If the length of the list is one, then we found an exact match
	if len(taglist) == 1:
		return taglist[0]['category']
	
	#Otherwise the tag doesn't exist or it's empty
	DebugPrint("Empty Tag",tagname)
	
	#Return a nonexistant tag category enumeration for internal use only
	return 2

def IsDisregardTag(tagname):
	return true if (tagname in disregardtags) or (tagname[-8:]=='_request') else False

#INTERNAL HELPER FUNCTIONS

def GetDanbooruUrl(opname,typename):
	"""Build Danbooru URL on the fly"""
	return (danbooru_domain + '/' + typename + danbooru_ops[opname][0]+danbooru_auth)