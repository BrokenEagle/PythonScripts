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
from urllib.error import HTTPError

#MY IMPORTS
from misc import DebugPrint,DebugPrintInput,CreateDirectory,AbortRetryFail,DownloadFile,BlankFunction
from myglobal import username,apikey,workingdirectory,imagefilepath,booru_domain

#LOCAL GLOBALS

wikilinkregex = re.compile(r'\[\[([^\|\]]+)\|?[^\]]*\]\]')
dateregex = re.compile(r"""^([\d]{4}-[\d]{2}-[\d]{2})?		#Date1
							(?:\.\.)?						#Non-capturing group for ..
							(?(1)(?<=\.\.))					#If Date1 exists, ensure .. exists
							([\d]{4}-[\d]{2}-[\d]{2})?$		#Date2""",re.X)
idregex = re.compile(r'^(\d+)?(?:\.\.)?(\d+)?$')
ageregex = re.compile(r"""^([\d]+(?:s|m[io]|h|d|w|y))?		#Age1
							(?:\.\.)?						#Non-capturing group for ..
							(?(1)(?<=\.\.))					#If Age1 exists, ensure .. exists
							([\d]+(?:s|m[io]|h|d|w|y))?$	#Age2""",re.X)
agetypedict = {'s':1,'mi':60,'h':60*60,'d':60*60*24,'w':60*60*24*7,'mo':60*60*24*30,'y':60*60*24*365}
disregardtags = ['tagme','commentary','check_commentary','translated','partially_translated','check_translation','annotated','partially_annotated','check_my_note','check_pixiv_source']

#The following are needed to properly evaluate the JSON responses from Danbooru
null = None
true = True
false = False

#Danbooru URL Constants
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
	retry = 0
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
		except HTTPError as inst:
			if AbortRetryFail(urlsubmit,senddata,httpmethod,inst):
				continue
			else:
				return -1
		except TimeoutError:
			print("\nTimed out! Retrying in 60 seconds")
			if retry > 2:
				raise
			time.sleep(60)
			retry += 1
			continue
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
		return booru_domain + postdict["preview_file_url"]
	if size=="medium":
		return booru_domain + postdict["large_file_url"]
	if size=="large":
		return booru_domain + postdict["file_url"]

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
		if len(typelist) < limit:
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

def IDListLoop(type,idlist,iteration,inputs={}):
	"""Standard loop iterating through a list of IDs"""
	
	for num in idlist:
		item = SubmitRequest('show',type,id=num)
		if len(item) == 0:
			continue
		ret = iteration(item,**inputs)
		if ret < 0:
			return
		elif ret > 0:
			continue
		print('.', end="", flush=True)

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
	match = dateregex.match(string)
	if match == None:
		raise argparse.ArgumentTypeError("Date input must be of format 'YYYY-MM-DD'")
	if (match.group(1) == None) and (match.group(2) == None):
		raise argparse.ArgumentTypeError("At least one date must be included")
	if (match.group(1) != None) and (match.group(2) != None):
		if time.strptime(match.group(1),'%Y-%m-%d') > time.strptime(match.group(2),'%Y-%m-%d'):
			raise argparse.ArgumentTypeError("1st date must be before 2nd date")
	return match.group()

def IDStringInput(string):
	match = idregex.match(string)
	if match == None:
		raise argparse.ArgumentTypeError("ID input must be of format 'Start#..End#'")
	start = int(match.group(1))
	end = int(match.group(2))
	
	if start > end:
		raise argparse.ArgumentTypeError("Start ID must be less than End ID")
	return match.group()

def AgeStringInput(string):
	match = ageregex.match(string)
	if match == None:
		raise argparse.ArgumentTypeError("Age input must be of format 'Start..End'\nValid qualifiers are 's','mi','h','d','w','mo','y'")
	if (match.group(1) == None) and (match.group(2) == None):
		raise argparse.ArgumentTypeError("At least one age specifier must be used")
	if (match.group(1) != None) and (match.group(2) != None):
		if (int(re.search(r'[\d]+',match.group(1)).group()) * agetypedict[re.search(r'[^\d]+',match.group(1)).group()]) > (int(re.search(r'[\d]+',match.group(2)).group()) * agetypedict[re.search(r'[^\d]+',match.group(2)).group()]):
			raise argparse.ArgumentTypeError("Start specifier must be less than end specifier")
	return match.group()

#POST SPECIFIC FUNCTIONS

def IsUpload(postver):
	return (len(postver['unchanged_tags']) == 0) and (len(postver['added_tags']) > 0)

def HasChild(postver):
	return postver['has_visible_children']

def HasParent(postver):
	return (postver['parent_id'] != None)

def HasRelated(postver):
	return (HasParent(postver) or HasChild(postver))

def IsTagAdd(postver):
	if (len(postver['unchanged_tags']) > 0) and (len(postver['added_tags']) > 0):
		return (len(postver['added_tags'].split())) > MetatagCount(postver['added_tags'])
	return False

def IsTagRemove(postver):
	if (len(postver['unchanged_tags']) > 0) and (len(postver['removed_tags']) > 0):
		return (len(postver['removed_tags'].split())) > MetatagCount(postver['removed_tags'])
	return False

def MetatagExists(string):
	return (ParentExists(string) or SourceExists(string) or RatingExists(string))

def ParentExists(string):
	return ((string.find("parent:")) >= 0)

def SourceExists(string):
	return ((string.find("source:")) >= 0)

def RatingExists(string):
	return ((string.find("rating:")) >= 0)

def IsParentChange(postver):
	return (ParentExists(postver['added_tags']) or ParentExists(postver['removed_tags'])) and not IsUpload(postver)

def IsRatingChange(postver):
	return RatingExists(postver['added_tags']) and RatingExists(postver['removed_tags'])

def IsSourceChange(postver):
	return (SourceExists(postver['added_tags']) or SourceExists(postver['removed_tags'])) and not IsUpload(postver)

def MetatagCount(string):
	return ParentCount(string) + SourceCount(string) + RatingCount(string)

def ParentCount(string):
	return 1 if ParentExists(string) else 0

def RatingCount(string):
	return 1 if RatingExists(string) else 0

def SourceCount(string):
	return 1 if SourceExists(string) else 0

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

#DTEXT HELPER FUNCTIONS

def GetWikiLinks(string):
	return list(map(lambda x:x.lower().replace(' ','_'),wikilinkregex.findall(string)))

#INTERNAL HELPER FUNCTIONS

def GetDanbooruUrl(opname,typename):
	"""Build Danbooru URL on the fly"""
	return (booru_domain + '/' + typename + danbooru_ops[opname][0]+danbooru_auth)