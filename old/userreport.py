#USERREPORT.PY
"""Primary use is to collect all information on users for a specific category"""

#PYTHON IMPORTS
import os
import csv
import sys
import time
from argparse import ArgumentParser

#LOCAL IMPORTS
from misc import PutGetData,PutGetUnicode,DebugPrint,DebugPrintInput,FindUnicode,MakeUnicodePrintable,\
				HasMonthPassed,HasDayPassed,DaysToSeconds,SecondsToDays,IsAddItem,IsRemoveItem,IsOrderChange,\
				WithinOneSecond,GetCurrentTime,TurnDebugOn,TurnDebugOff,TouchFile,GetAddItem,GetRemoveItem,\
				MonthsToSeconds,SafePrint
from danbooru import SubmitRequest,IDPageLoop,JoinArgs,GetArgUrl2,GetPageUrl,GetLimitUrl,GetSearchUrl,ProcessTimestamp,\
					GetTagCategory,IsDisregardTag,MetatagExists,SourceExists,ParentExists,RatingExists,IsUpload,\
					IsParentChange,IsSourceChange,IsRatingChange,DateStringInput,TimestampInput
from myglobal import workingdirectory,datafilepath,csvfilepath

#MODULE GLOBAL VARIABLES
prioruserdictfile = workingdirectory + datafilepath + 'prior%suserdict.txt'
userdictfile = workingdirectory + datafilepath + '%suserdict.txt'
currentuserdictfile = None
csvfile = workingdirectory + csvfilepath + '%s.csv'
tagdictfile = workingdirectory + "tagdict.txt"
watchdogfile = workingdirectory + "watchdog.txt"

versionedtypes = ['post','upload','pool','note','artist_commentary','artist','wiki_page']
nonversionedtypes = ['comment','forum_post','forum_topic','post_appeal','bulk_update_request','tag_implication','tag_alias']
validtypes = versionedtypes + nonversionedtypes
typeextracolumns = {'post':14,'upload':13,'pool':7,'note':7,'artist_commentary':6,'artist':9,'wiki_page':5,'comment':6,'forum_post':1,'forum_topic':1,'post_appeal':1,'bulk_update_request':2,'tag_implication':1,'tag_alias':1}
typelimits = {'post':200,'upload':100,'pool':10,'note':25,'artist_commentary':25,'artist':10,'wiki_page':10,'comment':50,'forum_post':10,'forum_topic':10,'post_appeal':10,'bulk_update_request':10,'tag_implication':10,'tag_alias':10}
typetableheaders = {
	'post':['userid','total','parent','rating','source','+gentag','+chartag','+copytag','+arttag','+emptytag','-gentag','-chartag','-copytag','-arttag','-emptytag','other'],
	'upload':['userid','total','modbypass','deleted','parent','source','safe','ques','expl','gentag','chartag','copytag','arttag','emptytag','obsolete'],
	'note':['userid','total','create','edit','move','resize','delete','undelete','other'],
	'artist_commentary':['userid','total','create','orig_title','orig_descr','trans_title','trans_descr','other'],
	'pool':['userid','total','create','add','remove','order','other'],
	'artist':['userid','total','create','name','other_name','url','group','delete','undelete','wiki','other'],
	'wiki_page':['userid','total','create','title','other_names','body','other'],
	'comment':['userid','total','update','bump','pos_count','neg_count','cum_score','delete'],
	'forum_post':['userid','total','update'],
	'forum_topic':['userid','total','response_count'],
	'post_appeal':['userid','total','unsuccessful'],
	'tag_alias':['userid','total','approved'],
	'tag_implication':['userid','total','approved'],
	'bulk_update_request':['userid','total','approved','rejected']
	}
tagtypedict = {'general':0,'character':4,'copyright':3,'artist':1}

#MAIN function
def main(args):
	"""Main function; 
	args: Instance of argparse.Namespace
	"""
	global userdictfile,prioruserdictfile,currentuserdictfile,csvfile
	
	#TurnDebugOn()	#uncomment this line to see debugging in this module
	#TurnDebugOn('danbooru')	#uncomment this line to see debugging in danbooru module
	
	if(args.category) not in validtypes:
		print("Invalid category")
		return -1
	
	#Set variables according to the current category
	typename = args.category
	userdictfile = userdictfile % typename
	prioruserdictfile = prioruserdictfile % typename
	csvfile = csvfile % typename
	inputdict = {'typename':typename,'prior':args.prior}
	
	#Check to see if we are starting new, or are resuming progress
	if args.prior:
		currentuserdictfile = prioruserdictfile
		if os.path.exists(prioruserdictfile) and not args.new:
			print("Opening",prioruserdictfile)
			startid,inputdict['starttime'],inputdict['endtime'],inputdict['userdict'] = PutGetData(prioruserdictfile,'r')
			
			#Continue from the last saved location
		else:
			print("Opening",userdictfile)
			startid,inputdict['starttime'],inputdict['endtime'],inputdict['userdict'] = PutGetData(userdictfile,'r')
			inputdict['starttime'] -= MonthsToSeconds(1)
			inputdict['endtime'] -= MonthsToSeconds(1)
			inputdict['userdict'] = {}
		
		startid = [GetPageUrl(startid)]
	else:
		currentuserdictfile = userdictfile
		if os.path.exists(userdictfile) and not args.new:
			print("Opening",userdictfile)
			startid,inputdict['starttime'],inputdict['endtime'],inputdict['userdict'] = PutGetData(userdictfile,'r')
			
			#Continue from the last saved location
			startid = [GetPageUrl(startid)]
		else:
			if (typename == 'forum_topic') or (typename == 'bulk_update_request') or \
				(typename == 'tag_implication') or (typename == 'tag_alias'):
				#Setting the page argument fixes ordering issues for the above categories
				#It's set very high to prevent any actual instances from being above it
				startid = [GetPageUrl(1000000)]
			else:
				startid = []
			
			inputdict['userdict'] = {}
			
			if args.timestamp != None:
				inputdict['starttime'] = args.timestamp[0]
				inputdict['endtime'] = args.timestamp[1]
			else:
				if args.date != None:
					inputdict['starttime'] = time.mktime(time.strptime(args.date,"%Y-%m-%d"))
				else:
					inputdict['starttime'] = GetCurrentTime()
				inputdict['endtime'] = inputdict['starttime'] - MonthsToSeconds(1)
	
	#'post' and 'upload' use a tag dictionary to check tag type (i.e. general, artist, character, copyright, empty)
	if (typename == 'post' or typename == 'upload') and os.path.exists(tagdictfile) and not args.prior: 
		print("Opening",tagdictfile)
		inputdict['tagdict'] = PutGetUnicode(tagdictfile,'r')
	else: 
		inputdict['tagdict'] = {}
	
	#Set the appropriate Danbooru controller that will handle all requests
	if typename == 'upload':
		if not args.prior:
			#Check for new aliases and update tag dictionary
			print("Updating tag dictionary with new aliases")
			#Tag aliases require sequential paging to list in the correct order
			correctorder = [GetPageUrl(100000)]
			IDPageLoop('tag_aliases',typelimits['tag_alias'],TagdictAliasIteration,firstloop=correctorder,inputs=inputdict)
			PutGetUnicode(tagdictfile,'w',inputdict['tagdict'])
			#There is a category 'upload', but the data isn't as good as in 'post_versions'
		controller = 'post_versions'
	elif typename in versionedtypes:
		controller = typename + '_versions'
	elif typename == 'tag_alias':
		controller = 'tag_aliases'
	elif typename in nonversionedtypes:
		controller = '%ss' % typename
	
	#Comments require an additional URL argument (otherwise, it'll return posts and not comments)
	if typename == 'comment':
		urladds = [GetArgUrl2('group_by',typename)]
	else:
		urladds = []
	
	#Set other preloop variables
	inputdict['currentday'] = [0]
	
	#Execute main loop
	print("Starting main loop...")
	lastid = IDPageLoop(controller,typelimits[typename],UserReportIteration,addonlist=urladds,\
							inputs=inputdict,firstloop=startid,postprocess=UserReportPostprocess)
	
	#Now that we're done, let's do one last final save
	if (typename == 'post' or typename=='upload') and not args.prior:
		PutGetUnicode(tagdictfile,'w',inputdict['tagdict'])
	PutGetData(currentuserdictfile,'w',[lastid,inputdict['starttime'],inputdict['endtime'],inputdict['userdict']])
	
	if not args.prior:
		#As a final act, also write a CSV file
		with open(csvfile,'w',newline='') as outfile:
			writer = csv.writer(outfile)
			writer.writerow(typetableheaders[typename])
			for key in inputdict['userdict']:
				writer.writerow([key]+inputdict['userdict'][key])
	
	print("\nDone!")

#Loop functions

startedyet = False

def UserReportIteration(item,typename,starttime,endtime,userdict,prior,tagdict,**kwargs):
	global startedyet
	
	if typename in versionedtypes:
		timestamp = item['updated_at']
		userid = item['updater_id']
	elif typename in nonversionedtypes:
		timestamp = item['created_at']
		if typename == 'bulk_update_request': userid = item['user_id']
		else: userid = item['creator_id']
	
	currenttime = ProcessTimestamp(timestamp)
	if starttime < currenttime:
		return 0
	elif startedyet == False:
		startedyet = True
		print('S',end='',flush=True)
	
	#For post changes, skip all post changes that are uploads
	if typename == 'post' and (IsUpload(item)):
		return 0
	
	#For uploads, skip all post changes that aren't uploads
	if typename == 'upload' and not (IsUpload(item)):
		return 0
	
	#Main exit condition
	if endtime > currenttime:
		return -1
	
	#For each instance found, update user Totals column count
	if prior:
		if typename == 'upload':
			if userid not in userdict:
				userdict[userid] = [0,0]
			userdict[userid][0] += 1
			userdict[userid][1] += len(item['tags'].split())
		else:
			userdict[userid] = [userdict[userid][0] + 1] if (userid in userdict) else [1]
		return 0
	else:
		if userid not in userdict: 
			userdict[userid] = [1] + [0]*typeextracolumns[typename]
		else: 
			userdict[userid][0] += 1
	
	#Go to each types's handler function to process more data
	if typename=='post':
		updatepostdata(userid,userdict,item,tagdict)
	elif typename=='upload':
		updateuploaddata(userid,userdict,item,tagdict)
	elif typename=='comment':
		updatecommentdata(userid,userdict,item)
	elif typename=='forum_post':
		updateforumpostdata(userid,userdict,item)
	elif typename=='forum_topic':
		updateforumtopicdata(userid,userdict,item)
	elif typename=='post_flag' or typename=='post_appeal':
		updatepostappealdata(userid,userdict,item)
	elif typename=='bulk_update_request':
		updatebulkupdaterequestdata(userid,userdict,item)
	elif (typename == 'tag_alias') or (typename == 'tag_implication'):
		updatetagaliasimplicationdata(userid,userdict,item)
	else:
		updateextradata(userid,userdict,item,typename)
	DebugPrintInput('----------')
	return 0

def UserReportPostprocess(typelist,typename,starttime,endtime,userdict,tagdict,currentday,prior,**kwargs):
	#Save tag dictionary at this point for 'upload'
	if (typename == 'post' or typename=='upload') and not prior:
		PutGetUnicode(tagdictfile,'w',tagdict)
	
	#Also save the user data at this point
	PutGetData(currentuserdictfile,'w',[typelist[-1]['id'],starttime,endtime,userdict])
	TouchFile(watchdogfile)
	
	#Print some extra screen feedback so we know where we're at
	if typename in versionedtypes:
		currenttime = ProcessTimestamp(typelist[-1]['updated_at'])
	elif typename in nonversionedtypes:
		currenttime = ProcessTimestamp(typelist[-1]['created_at'])
	DebugPrint(starttime,currenttime)
	if HasDayPassed(starttime-currenttime,DaysToSeconds(currentday[0])):
		currentday[0] = int(SecondsToDays(starttime-currenttime))
		print(currentday[0], end="", flush=True)

#TAG FUNCTIONS

def TagdictAliasIteration(tagalias,starttime,tagdict,**kwargs):
	"""Update tag dictionary with all tag aliases that went active during the user report period (1 Month)"""
	
	currenttime = ProcessTimestamp(tagalias['updated_at'])
	
	if (currenttime > starttime) or (tagalias['status']=='pending'):
		return 0
	
	#Main exit condition
	if HasMonthPassed(starttime,currenttime):
		return -1
	
	#Check if the consequent name already exists in the Tag Dictionary
	if tagalias['consequent_name'] in tagdict:
		DebugPrint(tagalias['consequent_name'],'found in tagdict')
		tagtype = tagdict[tagalias['consequent_name']]
	else:
		DebugPrint(tagalias['consequent_name'],'not found in tagdict')
		
		#If unicode is found, then document for later and continue
		if FindUnicode(tagalias['consequent_name']) >= 0:
			foundunicodeintag('tag alias',tagalias['id'])
			return 0
		
		tagtype = GetTagCategory(tagalias['consequent_name'])
	
	#Update tag dictionary with tagtype info
	tagdict[tagalias['antecedent_name']] = tagtype
	
	return 0

def counttags(tagstring,tagdict,postid):
	"""Count all the tags for each category"""
	
	tagcount = [0]*5
	tagmiss = 0 #Used only for printing feedback
	
	for i in range(0,len(tagstring)):
		
		if MetatagExists(tagstring[i]):
			continue
		
		if IsDisregardTag(tagstring[i]):
			continue
		
		if (tagstring[i] in tagdict):
			tagcount[tagdict[tagstring[i]]] += 1
		else:
			#If unicode is found, then document for later and continue
			if FindUnicode(tagstring[i]) >= 0:
				foundunicodeintag('post',postid)
				continue
			
			tagmiss = 1 
			returntag = GetTagCategory(tagstring[i])
			tagdict[tagstring[i]] = returntag
			tagcount[returntag] += 1
			
			#Print some feedback
			DebugPrint(".",end="",flush=True)
	
	#Print some more feedback
	if tagmiss == 1:
		DebugPrint("T",end="",flush=True)
	
	return tagcount

def foundunicodeintag(type,id):
	"""Store where unicode tags were found for later investigation"""
	with open(workingdirectory + 'unicode.txt','a') as f:
		f.write("\nFound unicode in " + type + ' ' + str(id))

#POST SPECIFIC FUNCTIONS#

def updatepostdata(userid,userdict,typeinfo,tagdict):
	"""Update post columns for userid"""
	
	postid = typeinfo['post_id']
	dirty = 0
	if IsParentChange(typeinfo):
		DebugPrint("Parent Change")
		dirty = 1
		userdict[userid][1] += 1
	if IsRatingChange(typeinfo):
		DebugPrint("Rating Change")
		dirty = 1
		userdict[userid][2] += 1
	if IsSourceChange(typeinfo):
		DebugPrint("Source")
		dirty = 1
		userdict[userid][3] += 1
	
	tagtypes = counttags(typeinfo['added_tags'].split(),tagdict,postid)
	userdict[userid][4] += tagtypes[0]						#general
	userdict[userid][5] += tagtypes[4]						#character
	userdict[userid][6] += tagtypes[3]						#copyright
	userdict[userid][7] += tagtypes[1]						#artist
	userdict[userid][8] += tagtypes[2]						#empty
	if any(tagtypes):
		DebugPrint("Tag Remove")
		dirty = 1
	
	tagtypes = counttags(typeinfo['removed_tags'].split(),tagdict,postid)
	userdict[userid][9] += tagtypes[0]						#general
	userdict[userid][10] += tagtypes[4]						#character
	userdict[userid][11] += tagtypes[3]						#copyright
	userdict[userid][12] += tagtypes[1]						#artist
	userdict[userid][13] += tagtypes[2]						#empty
	if any(tagtypes):
		DebugPrint("Tag Remove")
		dirty = 1
	
	if dirty == 0:
		DebugPrint("Other")
		userdict[userid][14] += 1

#UPLOAD SPECIFIC FUNCTIONS

def updateuploaddata(userid,userdict,typelist,tagdict):
	tagstring = typelist['tags'].split()
	postid = typelist['post_id']
	returnvalue = getlatestpostdata(postid,tagstring,tagdict)
	userdict[userid][1] += returnvalue[0]	#mod bypass
	userdict[userid][2] += returnvalue[1]	#deleted
	if typelist['parent_id']!=None:
		userdict[userid][3] += 1
	if len(typelist['source']) != 0:
		userdict[userid][4] += 1
	if typelist['rating'] == 's':
		userdict[userid][5] += 1
	if typelist['rating'] == 'q':
		userdict[userid][6] += 1
	if typelist['rating'] == 'e':
		userdict[userid][7] += 1
	tagtypes = counttags(tagstring,tagdict,postid)
	userdict[userid][8] += tagtypes[0]						#general
	userdict[userid][9] += tagtypes[4]						#character
	userdict[userid][10] += tagtypes[3]						#copyright
	userdict[userid][11] += tagtypes[1]						#artist
	userdict[userid][12] += tagtypes[2]						#empty
	userdict[userid][13] += returnvalue[2]					#removed

def getlatestpostdata(postid,tagstringver,tagdict):
	"""Compare and contrast the version data with the current post data
	
	Globals used: tagtypedict
	"""
	#Get the lastest post data
	postshow = SubmitRequest('show','posts',id=postid)
	
	#First update the Tag dictionary while we have all this good data; This reduces the amount of misses later on
	for key in tagtypedict:
		tags = postshow['tag_string_'+key].split()
		for i in range(0,len(tags)):
			if FindUnicode(tags[i]) < 0:
				tagdict[tags[i]] = tagtypedict[key]
			else:
				foundunicodeintag('post',postid)
	
	#Done updating tagdict, now get data from post info
	returnvalue = [0,0,0]
	if (postshow['approver_id']==None) and (not postshow['is_deleted']) and (not postshow['is_pending']):
		DebugPrint("Mod Queue Bypass")
		returnvalue[0] = 1
	elif (postshow['is_deleted']):
		DebugPrint("Deleted")
		returnvalue[1] = 1
	
	#Now compare the version's list of tags with the post's list of tags
	tagstringpost = postshow['tag_string'].split()
	for i in range(0,len(tagstringver)):
		#Is the tag:
		#1. Not in the current version
		#2. Not one of the tags to disregard
		#3. Not a Unicode tag
		#4. Not an empty tag
		if (tagstringver[i] not in tagstringpost) and not (IsDisregardTag(tagstringver[i])) and \
			(tagstringver[i] in tagdict) and (tagdict[tagstringver[i]]!=2):
			DebugPrintInput("Tag error1",tagstringver[i],postid)
			returnvalue[2] += 1
	
	return returnvalue

#GENERAL VERSIONS FUNCTIONS

def updateextradata(userid,userdict,currversiondata,typename):
	"""Get prior version for all versioned categories (except for post)"""
	
	if typename == 'artist_commentary': 
		lookupid = 'post_id'
	else: 
		lookupid = typename+'_id'
	
	urladd = JoinArgs(GetSearchUrl(lookupid,currversiondata[lookupid]),GetPageUrl(currversiondata['id']),GetLimitUrl(1))
	priorversiondata = SubmitRequest('list',typename + '_versions',urladdons=urladd)
	
	if typename == 'note':
		updatenotedata(userid,userdict,currversiondata,priorversiondata)
	if typename == 'artist_commentary':
		updatecommentarydata(userid,userdict,currversiondata,priorversiondata)
	if typename == 'pool':
		updatepooldata(userid,userdict,currversiondata,priorversiondata)
	if typename == 'artist':
		updateartistdata(userid,userdict,currversiondata,priorversiondata)
	if typename == 'wiki_page':
		updatewikipagedata(userid,userdict,currversiondata,priorversiondata)

#NOTE SPECIFIC FUNCTIONS

def updatenotedata(userid,userdict,currversiondata,priorversiondata):
	dirty = 0
	
	if len(priorversiondata)==0:
		DebugPrint("Create")
		userdict[userid][1] += 1
		return
	
	priorversiondata = priorversiondata.pop()
	
	if currversiondata['body'] != priorversiondata['body']:
		DebugPrint("Edit note")
		dirty = 1
		userdict[userid][2] += 1
	if (currversiondata['x'] != priorversiondata['x']) or (currversiondata['y'] != priorversiondata['y']):
		DebugPrint("Move note")
		dirty = 1
		userdict[userid][3] += 1
	if (currversiondata['width'] != priorversiondata['width']) or (currversiondata['height'] != priorversiondata['height']):
		DebugPrint("Resize note")
		dirty = 1
		userdict[userid][4] += 1
	if (currversiondata['is_active'] == False) and (priorversiondata['is_active'] == True):
		DebugPrint("Delete note")
		dirty = 1
		userdict[userid][5] += 1
	if (currversiondata['is_active'] == True) and (priorversiondata['is_active'] == False):
		DebugPrint("Undelete note")
		dirty = 1
		userdict[userid][6] += 1
	if dirty == 0:
		DebugPrint("Other")
		userdict[userid][7] += 1

#ARTIST COMMENTARY SPECIFIC FUNCTIONS

def updatecommentarydata(userid,userdict,currversiondata,priorversiondata):
	dirty = 0
	
	if len(priorversiondata)==0:
		DebugPrint("Create")
		userdict[userid][1] += 1
		return
	
	priorversiondata = priorversiondata.pop()
	
	if currversiondata['original_title'] != priorversiondata['original_title']:
		DebugPrint("Orig Title")
		dirty = 1
		userdict[userid][2] += 1
	if currversiondata['original_description'] != priorversiondata['original_description']:
		DebugPrint("Orig Descr")
		dirty = 1
		userdict[userid][3] += 1
	if currversiondata['translated_title'] != priorversiondata['translated_title']:
		DebugPrint("Trans Title")
		dirty = 1
		userdict[userid][4] += 1
	if currversiondata['translated_description'] != priorversiondata['translated_description']:
		DebugPrint("Trans Descr")
		dirty = 1
		userdict[userid][5] += 1
	if dirty == 0:
		DebugPrint("Other")
		userdict[userid][6] += 1

#POOL SPECIFIC FUNCTIONS

def updatepooldata(userid,userdict,currversiondata,priorversiondata):
	dirty = 0
	
	if len(priorversiondata)==0:
		DebugPrint("Create")
		userdict[userid][1] += 1
		return
	
	priorversiondata = priorversiondata.pop()
	
	postpoollist = list(map(int,currversiondata['post_ids'].split()))
	prepoollist = list(map(int,priorversiondata['post_ids'].split())) #page crossing will cause failure here
	if IsAddItem(prepoollist,postpoollist):
		DebugPrint("Add post")
		dirty = 1
		userdict[userid][2] += 1
		
		obsolete = GetObsoleteAdd(currversiondata,GetAddItem(prepoollist,postpoollist))
		if obsolete > 0:
			DebugPrint("Obsolete Add")
			userdict[userid][5] += 1
	if IsRemoveItem(prepoollist,postpoollist):
		DebugPrint("Remove post")
		dirty = 1
		userdict[userid][3] += 1
		
		obsolete = GetObsoleteRemove(currversiondata,GetRemoveItem(prepoollist,postpoollist))
		if obsolete > 0:
			DebugPrint("Obsolete Remove")
			userdict[userid][6] += obsolete
	if IsOrderChange(prepoollist,postpoollist):
		DebugPrint("Order change")
		dirty = 1
		userdict[userid][4] += 1
	if dirty == 0:
		DebugPrint("Other")
		userdict[userid][7] += 1

def GetObsoleteAdd(currversion,postlist):
	startid = [GetPageUrl(currversion['id'],above=True)]
	urladds = [GetSearchUrl('pool_id',currversion['pool_id'])]
	inputdict = {'postlist':[postlist],'obsolete':[0]}
	IDPageLoop('pool_versions',100,GetObsoleteAddIterator,firstloop=startid,addonlist=urladds,inputs=inputdict,reverselist=True)
	return inputdict['obsolete'][0]

def GetObsoleteAddIterator(poolver,postlist,obsolete):
	poolidlist = list(map(int,poolver['post_ids'].split()))
	templist=postlist[0]
	for i in reversed(range(0,len(postlist[0]))):
		if postlist[0][i] not in poolidlist:
			obsolete[0] += 1
			templist.pop(i)
	postlist[0] = templist
	if len(postlist[0]) == 0:
		return -1
	return 0

def GetObsoleteRemove(currversion,postlist):
	startid = [GetPageUrl(currversion['id'],above=True)]
	urladds = [GetSearchUrl('pool_id',currversion['pool_id'])]
	inputdict = {'postlist':[postlist],'obsolete':[0]}
	IDPageLoop('pool_versions',100,GetObsoleteRemoveIterator,firstloop=startid,addonlist=urladds,inputs=inputdict,reverselist=True)
	return inputdict['obsolete'][0]

def GetObsoleteRemoveIterator(poolver,postlist,obsolete):
	poolidlist = list(map(int,poolver['post_ids'].split()))
	templist=postlist[0]
	for i in reversed(range(0,len(postlist[0]))):
		if postlist[0][i] in poolidlist:
			obsolete[0] += 1
			templist.pop(i)
	postlist[0] = templist
	if len(postlist[0]) == 0:
		return -1
	return 0

#ARTIST SPECIFIC FUNCTIONS

def updateartistdata(userid,userdict,currversiondata,priorversiondata):
	dirty = 0
	
	if len(priorversiondata)==0:
		DebugPrint("Create")
		userdict[userid][1] += 1
		return
	
	priorversiondata = priorversiondata.pop()
	
	if currversiondata['name'] != priorversiondata['name']:
		DebugPrint("Name")
		dirty = 1
		userdict[userid][2] += 1
	if currversiondata['other_names'] != priorversiondata['other_names']:
		DebugPrint("Other Name")
		dirty = 1
		userdict[userid][3] += 1
	if currversiondata['url_string'] != priorversiondata['url_string']:
		DebugPrint("URL")
		dirty = 1
		userdict[userid][4] += 1
	if currversiondata['group_name'] != priorversiondata['group_name']:
		DebugPrint("Group")
		dirty = 1
		userdict[userid][5] += 1
	if (currversiondata['is_active'] == False) and (priorversiondata['is_active'] == True):
		DebugPrint("Delete")
		dirty = 1
		userdict[userid][6] += 1
	if (currversiondata['is_active'] == True) and (priorversiondata['is_active'] == False):
		DebugPrint("Undelete")
		dirty = 1
		userdict[userid][7] += 1
	
	#Done getting all the information from the version info
	#Now let's search for a corresponding wiki page
	
	urladd = GetSearchUrl('title',currversiondata['name'])
	
	#Send API request to Danbooru; response will be an indexed list of dictionaries
	artistwiki = SubmitRequest('list','wiki_pages',urladdons=urladd)
	
	if len(artistwiki)==1: 
		#Found an exact match; otherwise there is no wiki page
		
		artistwiki = artistwiki.pop()
		artistvertime = ProcessTimestamp(currversiondata['updated_at'])
		
		#Search through the list wiki page versions
		#NOTE: 	Being lazy and searching with a high limit instead of handling page crossings
		#		Will fail if the number of versions created in the last month is very large
		urladd = JoinArgs(GetSearchUrl('wiki_page_id',artistwiki['id']),GetLimitUrl(typelimits['wiki_page']))
		
		#Send API request to Danbooru; response will be an indexed list of dictionaries
		wikiversionlist = SubmitRequest('list','wiki_page_versions',urladdons=urladd)
		
		#Iterate through the list of wiki versions
		for i in range(0,len(wikiversionlist)):
			wikivertime = ProcessTimestamp(wikiversionlist[i]['updated_at'])
			
			if (WithinOneSecond(artistvertime,wikivertime)) and (currversiondata['updater_id']==wikiversionlist[i]['updater_id']):
				#Is the wiki version timestamp within one second of the artist version timestamp
				#and were the versions created by the same user?
				if (i==(len(wikiversionlist)-1)) or (wikiversionlist[i]['body'] != wikiversionlist[i+1]['body']):
					#Is this the first version or was the body changed between versions?
					DebugPrintInput("Wiki",userid,artistwiki['id'],currversiondata['artist_id'],i,len(wikiversionlist))
					dirty=1
					userdict[userid][8] += 1
					break
			
			if i == 199:
				#This watches for page crossings since we don't handle them
				print('Page border violation!')
				input()
	if dirty == 0:
		DebugPrint("Other")
		userdict[userid][9] += 1

#WIKI PAGE SPECIFIC FUNCTIONS

def updatewikipagedata(userid,userdict,currversiondata,priorversiondata):
	dirty = 0
	artwikiedit = 0
	createevent = 0
	
	#First, check to see if the wiki version is a result of an artist edit
	#Wiki page version does not have the category, but the wiki page does
	
	wikipage=SubmitRequest('show','wiki_pages',id=currversiondata['wiki_page_id'])
	
	if wikipage['category_name']==1: 
		#Was this an artist-type wiki page?
		
		wikivertime = ProcessTimestamp(currversiondata['updated_at'])
		
		#Search through the list artist versions
		#NOTE: 	Being lazy and searching with a high limit instead of handling page crossings
		#		Will fail if the number of versions created in the last month is very large
		urladd = JoinArgs(GetSearchUrl('name',currversiondata['title']),GetLimitUrl(typelimits['artist']))
		
		#Send API request to Danbooru; response will be a list of dictionaries
		artistverlist = SubmitRequest('list','artist_versions',urladdons=urladd)
		
		#Iterate through the list of artist versions
		for i in range(0,len(artistverlist)):
			artistvertime = ProcessTimestamp(artistverlist[i]['updated_at'])
			
			if (WithinOneSecond(artistvertime,wikivertime)) and (currversiondata['updater_id']==artistverlist[i]['updater_id']):
				#Is the wiki version timestamp within one second of the artist version timestamp
				#and were the versions created by the same user?
				DebugPrintInput("Art Wiki Change",currversiondata['wiki_page_id'],artistverlist[i]['artist_id'],i,len(artistverlist))
				
				#Remove the count of this version from the totals
				userdict[userid][0] -= 1 
				return
			
			if i == 199:
				#This watches for page crossings since we don't handle them
				print('Page border violation!')
				input()
	
	if len(priorversiondata)==0:
		DebugPrint("Create")
		userdict[userid][1] += 1
		return
	
	priorversiondata = priorversiondata.pop()
	
	if (currversiondata['title'] != priorversiondata['title']) and (artwikiedit==0):
		DebugPrint("Title")
		dirty = 1
		userdict[userid][2] += 1
	if currversiondata['other_names'] != priorversiondata['other_names'] and (artwikiedit==0):
		DebugPrint("Original names")
		dirty = 1
		userdict[userid][3] += 1
	if (currversiondata['body'] != priorversiondata['body']) and (artwikiedit==0):
		DebugPrint("Body")
		dirty = 1
		userdict[userid][4] += 1
	if (dirty == 0):
		DebugPrint("Other change")
		userdict[userid][5] += 1

#NONVERSIONED SPECIFIC FUNCTIONS

def updatecommentdata(userid,userdict,typeentry):
	if ProcessTimestamp(typeentry['created_at']) != (ProcessTimestamp(typeentry['updated_at'])):
		DebugPrint("Comment update")
		userdict[userid][1] += 1
	if typeentry['do_not_bump_post'] == False:
		DebugPrint("Comment bump")
		userdict[userid][2] += 1
	if typeentry['score'] > 0:
		DebugPrint("Positive comm")
		userdict[userid][3] += 1
	if typeentry['score'] < 0:
		DebugPrint("Negative comm")
		userdict[userid][4] += 1
	userdict[userid][5] += typeentry['score']	#cumulative score
	DebugPrintInput("User",userid,"Current score",userdict[userid][5])
	if typeentry['is_deleted'] == True:
		DebugPrint("Comment delete")
		userdict[userid][6] += 1

def updateforumpostdata(userid,userdict,typeentry):
	if ProcessTimestamp(typeentry['created_at']) != (ProcessTimestamp(typeentry['updated_at'])):
		DebugPrint("Forum update")
		userdict[userid][1] += 1

def updateforumtopicdata(userid,userdict,typeentry):
	userdict[userid][1] += typeentry['response_count']	#total replies
	
	DebugPrintInput("User",userid,"Current replies",userdict[userid][1])

def updatepostappealdata(userid,userdict,typeentry):
	if typeentry['is_resolved']==True:
		DebugPrint("Unsuccessful")
		userdict[userid][1] += 1

def updatetagaliasimplicationdata(userid,userdict,typeentry):
	if typeentry['status']=='active':
		DebugPrint("Approved")
		userdict[userid][1] += 1

def updatebulkupdaterequestdata(userid,userdict,typeentry):
	if typeentry['status']=='approved':
		DebugPrint("Approved")
		userdict[userid][1] += 1
	elif typeentry['status']=='rejected':
		DebugPrint("Rejected")
		userdict[userid][2] += 1

if __name__ =='__main__':
	parser = ArgumentParser(description="Generate a Danbooru User Report")
	parser.add_argument('category',help="post, upload, note, artist_commentary, pool, "
						"artist, wiki_page, forum_topic, forum_post, tag_implication, "
						"tag_alias, bulk_update_request, post_appeal, comment")
	parser.add_argument('--prior',help="Get the prior month",action="store_true",default=False)
	parser.add_argument('--new', help="Create a new user report",action="store_true",default=False)
	parser.add_argument('-d','--date',type=DateStringInput,help="Date to start the report")
	parser.add_argument('-t','--timestamp',type=TimestampInput,help="Timestamp ranges for the report")
	args = parser.parse_args()
	
	main(args)