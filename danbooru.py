#DANBOORU.PY
"""Functions that help communicate with Danbooru go here"""

#PYTHON IMPORTS
import sys
import time
import urllib.request
import urllib.parse

#LOCAL IMPORTS
import misc
from myglobal import username,apikey,workingdirectory,imagefilepath

#MODULE GLOBAL VARIABLES

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
			misc.DebugPrintInput(repr(urlsubmit),repr(senddata),repr(httpmethod))
			req = urllib.request.Request(url=urlsubmit,data=senddata,method=httpmethod)
			httpresponse = urllib.request.urlopen(req)
			misc.DebugPrintInput(httpresponse.status,httpresponse.reason)
		except urllib.error.HTTPError as inst:
			if AbortRetryFail(urlsubmit,inst):
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
			misc.DebugPrint("Before Eval")
			try:
				evaltemp = httpresponse.read()
				submittemp = eval((evaltemp).decode(encoding='utf-8'))
			except SyntaxError as inst:
				print(evaltemp)
				print(urlsubmit,httpmethod)
				print(inst)
				sys.exit(-1)
			misc.DebugPrint("After Eval")
			return submittemp
		#Success, but the server returned nothing back to evaluate
		elif httpresponse.status == 204:
			return httpresponse
		#Anything other than a 200 or 204 should raise an exception and be caught above
		#The following is just in case the above is not true
		elif not AbortRetryFail(urlsubmit,(httpresponse.status,httpresponse.reason)):
			return -1

def GetCurrFilePath(postdict):
	"""Get filepath for storing server medium files on local system.
	Input is a post dictionary obtained from Danbooru with either 'list' or 'show'.
	"""
	if postdict["has_large"] == True:
		if postdict["file_ext"] == "zip":
			currfile = workingdirectory + imagefilepath + postdict["md5"] + '.webm'
		else:#
			currfile = workingdirectory + imagefilepath + postdict["md5"] + '.jpg'
	else:
		currfile = workingdirectory + imagefilepath + postdict["md5"] + '.' + postdict["file_ext"]
	return currfile

def GetServFilePath(postdict):
	"""Get serverpath for medium files
	Input is a post dictionary obtained from Danbooru with either 'list' or 'show'.
	"""
	return danbooru_domain + postdict["large_file_url"]

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

def GetPageUrl(id):
	"""Get the page argument for all ID's below the parameter 'id'"""
	return GetArgUrl('page','','b'+str(id))

def EncodeData(typename,keyname,data):
	"""Encode data for the senddata parameter of SubmitRequest."""
	return (GetArgUrl(typename,keyname,data)).encode('ascii')

def ProcessTimestamp(timestring):
	return time.mktime(time.strptime(timestring[:19],"%Y-%m-%dT%H:%M:%S"))

#INTERNAL FUNCTIONS

def GetDanbooruUrl(opname,typename):
	"""Build Danbooru URL on the fly"""
	return (danbooru_domain + '/' + typename + danbooru_ops[opname][0]+danbooru_auth)

def AbortRetryFail(url,reason):
	"""Exception/Error handler"""
	print(url)
	print(reason)
	while True:
		keyinput = input("(A)bort, (R)etry, (F)ail? ")
		if keyinput.lower() == 'a':
			return False
		if keyinput.lower() == 'r':
			return True
		if keyinput.lower() == 'f':
			sys.exit(-1)