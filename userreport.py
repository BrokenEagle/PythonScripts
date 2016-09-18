#USERREPORT.PY
"""Primary use is to collect all information on users for a specific category"""

#PYTHON IMPORTS
import os
import csv
import sys
import argparse

#LOCAL IMPORTS
from misc import PutGetData,PutGetUnicode,DebugPrint,DebugPrintInput,FindUnicode,MakeUnicodePrintable,\
				HasMonthPassed,HasDayPassed,DaysToSeconds,SecondsToDays,\
				WithinOneSecond,GetCurrentTime,TurnDebugOn,TurnDebugOff
from danbooru import SubmitRequest,JoinArgs,GetArgUrl,GetPageUrl,ProcessTimestamp
from myglobal import workingdirectory,datafilepath,csvfilepath

#MODULE GLOBAL VARIABLES
userdictfile = workingdirectory + datafilepath + '%suserdict.txt'
usertagdictfile = workingdirectory + datafilepath + 'usertagdict.txt'
csvfile = workingdirectory + csvfilepath + '%s.csv'
tagdictfile = workingdirectory + "tagdict.txt"

versionedtypes = ['post','upload','pool','note','artist_commentary','artist','wiki_page']
nonversionedtypes = ['comment','forum_post','forum_topic','post_appeal','bulk_update_request','tag_implication','tag_alias']
validtypes = versionedtypes + nonversionedtypes
typeextracolumns = {'post':14,'upload':13,'pool':5,'note':7,'artist_commentary':6,'artist':9,'wiki_page':5,'comment':6,'forum_post':1,'forum_topic':1,'post_appeal':1,'bulk_update_request':2,'tag_implication':1,'tag_alias':1}
typelimits = {'post':400,'upload':200,'pool':50,'note':200,'artist_commentary':200,'artist':50,'wiki_page':50,'comment':200,'forum_post':50,'forum_topic':50,'post_appeal':50,'bulk_update_request':50,'tag_implication':50,'tag_alias':50}

disregardtags = ['tagme','commentary','check_commentary','translated','partially_translated',\
				'check_translation','annotated','partially_annotated','check_my_note','check_pixiv_source']
tagtypedict = {'general':0,'character':4,'copyright':3,'artist':1}

#MAIN function

def main(args):
	"""Main function; 
	args: Instance of argparse.Namespace
	"""
	global userdictfile,csvfile
	
	#TurnDebugOn()	#uncomment this line to see debugging in this module
	#TurnDebugOn('danbooru')	#uncomment this line to see debugging in danbooru module
	
	if(args.category) not in validtypes:
		print("Invalid category")
		return -1
	
	#Set variables according to the current category
	typename = args.category
	typelimit = typelimits[typename]
	userdictfile = userdictfile % typename
	csvfile = csvfile % typename
	
	#Check to see if we are starting new, or are resuming progress
	if os.path.exists(userdictfile) and not (args.new):
		startid,beginningid,starttime,userdict = PutGetData(userdictfile,'r')
		
		#Prepare for the first API call to Danbooru
		urladd = (JoinArgs(GetArgUrl('limit','',typelimit),GetPageUrl(startid)))
	else:
		userdict = {}
		starttime = GetCurrentTime()
		beginningid = None
	
	#Prepare for the first API call to Danbooru
	if (typename == 'forum_topic') or (typename == 'bulk_update_request') or \
		(typename == 'tag_implication') or (typename == 'tag_alias'):
		#Setting the page argument fixes ordering issues for the above categories
		#It's set very high to prevent any actual instances from being above it
		urladd=JoinArgs(GetArgUrl('limit','',typelimit),GetPageUrl(100000))
	else:
		urladd=JoinArgs(GetArgUrl('limit','',typelimit))
	
	#'post' and 'upload' use a tag dictionary to check tag type (i.e. general, artist, character, copyright, empty)
	if typename == 'post' or typename == 'upload':
		if os.path.exists(tagdictfile):
			tagdict = PutGetData(tagdictfile,'r')
		else:
			tagdict = {}
	
	#Keep track of the tags added/removed
	if typename=='post':
		if (os.path.exists(usertagdictfile)) and (not (args.new)):
			usertagdict = PutGetUnicode(usertagdictfile,'r')
		else:
			usertagdict = {}
	
	#For uploads, update tag dictionary with recent aliases to remove false tag errors
	if typename == 'upload':
		#Check for new aliases and update tag dictionary
		updatetagdictwaliases(starttime,tagdict)
		PutGetData(tagdictfile,'w',tagdict)
		#There is a category 'upload', but the data isn't as good as in 'post_versions'
		controller = 'post_versions'
	elif typename in versionedtypes:
		controller = typename + '_versions'
	elif typename == 'tag_alias':
		controller = 'tag_aliases'
	elif typename in nonversionedtypes:
		controller = '%ss' % typename
	
	#Set preloop variables
	currentday = 0
	currentid = 0
	
	#Process through a month's worth of instances
	while True:
		#Comments require an additional URL argument (otherwise, it'll return posts and not comments)
		if typename == 'comment':
			urladd = urladd + '&' + GetArgUrl('group_by','',typename)
		
		#Send API request to Danbooru; response will be an indexed list of dictionaries
		typelist = SubmitRequest('list',controller,urladdons=urladd)
		
		#Initialize beginningid if we're starting anew
		if (beginningid == None) and (len(typelist)>0): beginningid = typelist[0]['id']
		
		#Iterate through and process each instance
		for i in range(0,len(typelist)):
			
			#Initialize some loop variables according to type
			currentid = typelist[i]['id']
			if typename in versionedtypes:
				currenttime = ProcessTimestamp(typelist[i]['updated_at'])
				userid = typelist[i]['updater_id']
			elif typename in nonversionedtypes:
				currenttime = ProcessTimestamp(typelist[i]['created_at'])
				if typename == 'bulk_update_request':
					userid = typelist[i]['user_id']
				else:
					userid = typelist[i]['creator_id']
			
			#For post changes, skip all post changes that are uploads
			if typename == 'post' and (isupload(typelist[i])):
				continue
			
			#For uploads, skip all post changes that aren't uploads
			if typename == 'upload' and not (isupload(typelist[i])):
				continue
			
			#FOR loop exit condition
			if HasMonthPassed(starttime,currenttime):
				break
			
			#For each instance found, update user Totals column count
			if userid not in userdict:
				userdict[userid] = [1] + [0]*typeextracolumns[typename]
			else:
				userdict[userid][0] += 1
			
			#Go to each types's handler function to process more data
			if typename=='post':
				updatepostdata(userid,userdict,typelist[i],tagdict,usertagdict)
			elif typename=='upload':
				updateuploaddata(userid,userdict,typelist[i],tagdict)
			elif typename=='comment':
				updatecommentdata(userid,userdict,typelist[i])
			elif typename=='forum_post':
				updateforumpostdata(userid,userdict,typelist[i])
			elif typename=='forum_topic':
				updateforumtopicdata(userid,userdict,typelist[i])
			elif typename=='post_flag' or typename=='post_appeal':
				updatepostappealdata(userid,userdict,typelist[i])
			elif typename=='bulk_update_request':
				updatebulkupdaterequestdata(userid,userdict,typelist[i])
			elif (typename == 'tag_alias') or (typename == 'tag_implication'):
				updatetagaliasimplicationdata(userid,userdict,typelist[i])
			else:
				updateextradata(userid,userdict,typelist[i],typename)
		
		#Save tag dictionary at this point for 'upload'
		if typename == 'post' or typename=='upload':
			#Tried several different checks for Unicode errors, but they still occurred :(
			#This prevents the saved tag dictionary from being destroyed
			try:
				PutGetData('d:\\temp\\temp.txt','w',tagdict)
			except UnicodeEncodeError as inst:
				print(MakeUnicodePrintable(inst.object[inst.start-5:inst.end+5]))
				input()
			PutGetData(tagdictfile,'w',tagdict)
		
		if typename == 'post':
			PutGetUnicode(usertagdictfile,'w',usertagdict)
		
		#Also save the user data at this point
		PutGetData(userdictfile,'w',[currentid,beginningid,starttime,userdict])
		
		#WHILE loop exit condition
		if HasMonthPassed(starttime,currenttime):
			break
		
		#Print some screen feedback so we know where we're at
		if HasDayPassed(starttime-currenttime,DaysToSeconds(currentday)):
			currentday = int(SecondsToDays(starttime-currenttime))
			print(currentday, end="", flush=True)
		else:
			print(':', end="", flush=True)
		
		#Get ready for the next API call to Danbooru
		urladd = (JoinArgs(GetArgUrl('limit','',typelimit),GetPageUrl(currentid)))
	
	#As a final act, also write a CSV file
	with open(csvfile,'w',newline='') as outfile:
		writer = csv.writer(outfile)
		for key in userdict:
			writer.writerow([key]+userdict[key])
	
	print("\nDone!")

#TAG FUNCTIONS

def gettaginfo(tagname,postid):
	"""Query danbooru for the category of a tag"""
	
	#Check for unicode characters in the tagname
	if FindUnicode(tagname) >= 0:
		return -1
	
	#Prepare for tag query to Danbooru
	urladd = JoinArgs(GetArgUrl('search','name',tagname))
	
	#Send API request to Danbooru; response will be an indexed list of dictionaries
	taglist = SubmitRequest('list','tags',urladdons = urladd)
	
	if len(taglist) == 1:
		#If the length of the list is one, then we found an exact match
		return taglist[0]['category']
	else:
		#Otherwise the tag doesn't exist or it's empty
		DebugPrint("Tag Error2",tagname,postid)
		
		#Return a nonexistant tag category enumeration for internal use only
		return 2

def foundunicodeintag(type,id):
	"""Store where unicode tags were found for later investigation"""
	with open(workingdirectory + 'unicode.txt','a') as f:
		f.write("\nFound unicode in " + type + ' ' + str(id))

def isdisregardtag(tagname):
	if (tagname in disregardtags) or (tagname[-8:]=='_request'):
		return True
	return False

def updatetagdictwaliases(starttime,tagdict):
	"""Update the tag dictionary with all aliases created over the last month"""
	
	#The page argument must be used, or Danbooru won't sort them by ID number :(
	#A very large ID number is used to guarantee that the most recent aliases will be returned
	urladd = (JoinArgs(GetArgUrl('limit','',typelimits['tag_alias']),GetPageUrl(100000)))
	
	#Process through a month's worth of aliases
	while True:
		#Send API request to Danbooru; response will be an indexed list of dictionaries
		tagaliaslist = SubmitRequest('list','tag_aliases',urladdons=urladd)
		
		#Iterate through and process each alias
		for i in range(0,len(tagaliaslist)):
			currenttime = ProcessTimestamp(tagaliaslist[i]['updated_at'])
			
			#If the alias went active after the current data collection started...
			#... or if it's still a pending, then continue on
			if (currenttime > starttime) or (tagaliaslist[i]['status']=='pending'):
				continue
			
			currentid = tagaliaslist[i]['id']
			
			#Function exit condition
			if HasMonthPassed(starttime,currenttime):
				return
			
			#Check if the consequent name already exists in the Tag Dictionary
			if tagaliaslist[i]['consequent_name'] in tagdict:
				#If so, then just return it
				DebugPrint(tagaliaslist[i]['consequent_name'],'found in tagdict')
				tagtype = tagdict[tagaliaslist[i]['consequent_name']]
			else:
				#Otherwise, we need to query Danbooru
				DebugPrint(tagaliaslist[i]['consequent_name'],'not found in tagdict')
				tagtype = gettaginfo(tagaliaslist[i]['consequent_name'],0)
				
				#If unicode was found, then document for later and continue
				if(tagtype < 0):
					foundunicodeintag('tag alias',tagaliaslist[i]['id'])
					continue
			
			#Update tag dictionary with tagtype info
			tagdict[tagaliaslist[i]['antecedent_name']] = tagtype
		
		#Get ready for the next API call to Danbooru
		urladd = JoinArgs(GetPageUrl(currentid),GetArgUrl('limit','',typelimits['tag_alias']))

#POST SPECIFIC FUNCTIONS#

def updatepostdata(userid,userdict,typeinfo,tagdict,usertagdict):
	"""Update post columns for userid"""
	postid = typeinfo['post_id']
	dirty = 0
	if isparentchange(typeinfo):
		DebugPrint("Parent Change")
		dirty = 1
		userdict[userid][1] += 1
	if isratingchange(typeinfo):
		DebugPrint("Rating Change")
		dirty = 1
		userdict[userid][2] += 1
	if issourcechange(typeinfo):
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
		populateusertagdict(userid,typeinfo['added_tags'].split(),usertagdict)
		DebugPrint("Tag Remove")
		dirty = 1
	
	tagtypes = counttags(typeinfo['removed_tags'].split(),tagdict,postid)
	userdict[userid][9] += tagtypes[0]						#general
	userdict[userid][10] += tagtypes[4]						#character
	userdict[userid][11] += tagtypes[3]						#copyright
	userdict[userid][12] += tagtypes[1]						#artist
	userdict[userid][13] += tagtypes[2]						#empty
	if any(tagtypes):
		populateusertagdict(userid,typeinfo['removed_tags'].split(),usertagdict)
		DebugPrint("Tag Remove")
		dirty = 1
	
	if dirty == 0:
		DebugPrint("Other")
		userdict[userid][14] += 1
	
	DebugPrintInput('----------')

def populateusertagdict(userid,taglist,usertagdict):
	for tag in taglist:
		if metatagexists(tag):
			continue
		if userid not in usertagdict:
			usertagdict[userid]={}
		usertagdict[userid][tag] = (usertagdict[userid][tag] + 1) if (tag in usertagdict[userid]) else 1
		

def metatagexists(string):
	return (parentexists(string) or sourceexists(string) or ratingexists(string))

def parentexists(string):
	return ((string.find("parent:")) >= 0)

def sourceexists(string):
	return ((string.find("source:")) >= 0)

def ratingexists(string):
	return ((string.find("rating:")) >= 0)

def metatagcount(string):
	return parentcount(string) + sourcecount(string) + ratingcount(string)

def parentcount(string):
	if parentexists(string): return 1
	else: return 0

def sourcecount(string):
	if sourceexists(string): return 1
	else: return 0

def ratingcount(string):
	if ratingexists(string): return 1
	else: return 0

def isupload(postdict):
	return (len(postdict['unchanged_tags']) == 0) and (len(postdict['added_tags']) > 0)

def istagadd(postdict):
	if (len(postdict['unchanged_tags']) > 0) and (len(postdict['added_tags']) > 0):
		return (len(postdict['added_tags'].split())) > metatagcount(postdict['added_tags'])
	return False

def istagremove(postdict):
	if (len(postdict['unchanged_tags']) > 0) and (len(postdict['removed_tags']) > 0):
		return (len(postdict['removed_tags'].split())) > metatagcount(postdict['removed_tags'])
	return False

def isparentchange(postdict):
	return (parentexists(postdict['added_tags']) or parentexists(postdict['removed_tags'])) and not isupload(postdict)

def isratingchange(postdict):
	return ratingexists(postdict['added_tags']) and ratingexists(postdict['removed_tags'])

def issourcechange(postdict):
	return (sourceexists(postdict['added_tags']) or sourceexists(postdict['removed_tags'])) and not isupload(postdict)

#UPLOAD SPECIFIC FUNCTIONS

def updateuploaddata(userid,userdict,typelist,tagdict):
	tagstring = typelist['tags'].split()
	postid = typelist['post_id']
	returnvalue = getpostdata(postid,tagstring,tagdict)
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

def getpostdata(postid,tagstringver,tagdict):
	"""Compare and contrast the version data with the current post data
	
	Globals used: tagtypedict
	"""
	#Send API request to Danbooru; response will be a dictionary
	postshow = SubmitRequest('show','posts',id=postid)
	
	#First update the Tag dictionary while we have all this good data
	#This reduces the amount of misses later on
	#
	for key in tagtypedict:
		#Get the tag string in the post dictionary for each tag type
		tags = postshow['tag_string_'+key].split()
		
		#Iterate through each tag
		for i in range(0,len(tags)):
			
			if FindUnicode(tags[i]) < 0:
				#If no unicode was found, then update the Tag dictionary
				tagdict[tags[i]] = tagtypedict[key]
			else:
				#If unicode was found, then document for later and continue
				foundunicodeintag('post',postid)
	
	#Done updating tagdict, now get data from post info
	
	returnvalue = [0,0,0]
	#First get the mod queue and deleted status
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
		if (tagstringver[i] not in tagstringpost) and not (isdisregardtag(tagstringver[i])) and \
			(tagstringver[i] in tagdict) and (tagdict[tagstringver[i]]!=2):
			DebugPrintInput("Tag error1",tagstringver[i],postid)
			returnvalue[2] += 1
	
	return returnvalue

def counttags(tagstring,tagdict,postid):
	"""Count all the tags for each category"""
	
	tagcount = [0]*5
	tagmiss = 0
	
	#Iterate through each tag in the tag string
	for i in range(0,len(tagstring)):
		
		if metatagexists(tagstring[i]):
			#Don't count metatags
			continue
		
		if isdisregardtag(tagstring[i]):
			#Don't count request tags
			continue
		
		if (tagstring[i] in tagdict):
			#Found in the Tag dictionary, so record the result
			tagcount[tagdict[tagstring[i]]] += 1
		else:
			#Not found in the Tag dictionary, so we need to do extra processing
			tagmiss = 1
			
			#Get the category of the new tag
			returntag = gettaginfo(tagstring[i],postid)
			
			#If unicode was found, then document for later and continue
			if returntag < 0:
				foundunicodeintag('post',postid)
				
				#Unicode errors are counted the same as empty tags
				tagcount[2] += 1
				continue
			
			#Record the result
			tagdict[tagstring[i]] = returntag
			
			#Update the tag count
			tagcount[returntag] += 1
			
			#Print some feedback
			#DebugPrint(".",end="",flush=True)
	
	#Print some more feedback
	#if tagmiss == 1:
		#DebugPrint("T",end="",flush=True)
	
	return tagcount

#GENERAL VERSIONS FUNCTIONS

def updateextradata(userid,userdict,currversiondata,typename):
	if typename == 'artist_commentary': lookupid = 'post_id'
	else: lookupid = typename+'_id'
	urladd = JoinArgs(GetArgUrl('search',lookupid,currversiondata[lookupid]), \
				GetPageUrl(currversiondata['id']),GetArgUrl('limit','',1))
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
		DebugPrint("Reisize note")
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
	
	DebugPrintInput('----------')

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
	
	DebugPrintInput('----------')

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
	if isaddpost(prepoollist,postpoollist):
		DebugPrint("Add post")
		dirty = 1
		userdict[userid][2] += 1
	if isremovepost(prepoollist,postpoollist):
		DebugPrint("Remove post")
		dirty = 1
		userdict[userid][3] += 1
	if isorderchange(prepoollist,postpoollist):
		DebugPrint("Order change")
		dirty = 1
		userdict[userid][4] += 1
	if dirty == 0:
		DebugPrint("Other")
		userdict[userid][5] += 1

def getorderedintersection(lista,listb):
	diff = list(set(lista).difference(listb))
	templist = lista.copy()
	for i in range(0,len(diff)):
		temp = templist.pop(templist.index(diff[i]))
	return templist

def isorderchange(prepoolarray,postpoolarray):
	preprime = getorderedintersection(prepoolarray,postpoolarray)
	postprime = getorderedintersection(postpoolarray,prepoolarray)
	return not(preprime == postprime)

def isaddpost(prepoolarray,postpoolarray):
	return len(set(postpoolarray).difference(prepoolarray)) > 0

def isremovepost(prepoolarray,postpoolarray):
	return len(set(prepoolarray).difference(postpoolarray)) > 0

def iscreatepool(): #will be figured out from pool versions list for each pool
	pass

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
	
	urladd = JoinArgs(GetArgUrl('search','title',currversiondata['name']))
	
	#Send API request to Danbooru; response will be an indexed list of dictionaries
	artistwiki = SubmitRequest('list','wiki_pages',urladdons=urladd)
	
	if len(artistwiki)==1: 
		#Found an exact match; otherwise there is no wiki page
		
		artistwiki = artistwiki.pop()
		artistvertime = ProcessTimestamp(currversiondata['updated_at'])
		
		#Search through the list wiki page versions
		#NOTE: 	Being lazy and searching with a high limit instead of handling page crossings
		#		Will fail if the number of versions created in the last month is very large
		urladd = JoinArgs(GetArgUrl('search','wiki_page',artistwiki['id']),GetArgUrl('limit','',typelimits['wiki_page']))
		
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
	
	DebugPrintInput('----------')

#WIKI PAGE SPECIFIC FUNCTIONS

def updatewikipagedata(userid,userdict,currversiondata,priorversiondata):
	dirty = 0
	artwikiedit = 0
	createevent = 0
	
	#Wiki page version do not have the category, but the wiki page does
	
	#Send API request to Danbooru; response will be a dictionary
	wikipage=SubmitRequest('show','wiki_pages',id=currversiondata['wiki_page_id'])
	
	if wikipage['category_name']==1: 
		#Was this an artist-type wiki page?
		
		wikivertime = ProcessTimestamp(currversiondata['updated_at'])
		
		#Search through the list artist versions
		#NOTE: 	Being lazy and searching with a high limit instead of handling page crossings
		#		Will fail if the number of versions created in the last month is very large
		urladd = JoinArgs(GetArgUrl('search','name',currversiondata['title']),GetArgUrl('limit','',typelimits['artist']))
		
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
		userdict[userid][2] += 1
		return
	
	priorversiondata = priorversiondata.pop()
	
	if (currversiondata['title'] != priorversiondata['title']) and (artwikiedit==0):
		DebugPrint("Title")
		dirty = 1
		userdict[userid][2] += 1
	if currversiondata['other_names'] != priorversiondata['other_names'] and (artwikiedit==0): #no need to test for art wiki since this can't be modified from artist entry
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
	
	DebugPrintInput("-------")

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
	
	DebugPrintInput("-------")

def updateforumpostdata(userid,userdict,typeentry):
	if ProcessTimestamp(typeentry['created_at']) != (ProcessTimestamp(typeentry['updated_at'])):
		DebugPrint("Forum update")
		userdict[userid][1] += 1
	
	DebugPrintInput("-------")

def updateforumtopicdata(userid,userdict,typeentry):
	userdict[userid][1] += typeentry['response_count']	#total replies
	
	DebugPrintInput("User",userid,"Current replies",userdict[userid][1])

def updatepostappealdata(userid,userdict,typeentry):
	if typeentry['is_resolved']==True:
		DebugPrint("Unsuccessful")
		userdict[userid][1] += 1
	
	DebugPrintInput("-------")

def updatetagaliasimplicationdata(userid,userdict,typeentry):
	if typeentry['status']=='active':
		DebugPrint("Approved")
		userdict[userid][1] += 1
	
	DebugPrintInput("-------")

def updatebulkupdaterequestdata(userid,userdict,typeentry):
	if typeentry['status']=='approved':
		DebugPrint("Approved")
		userdict[userid][1] += 1
	elif typeentry['status']=='rejected':
		DebugPrint("Rejected")
		userdict[userid][2] += 1
	
	DebugPrintInput("-------")

if __name__ =='__main__':
	parser = argparse.ArgumentParser(description="Generate a Danbooru User Report")
	parser.add_argument('category',help="post, upload, note, artist_commentary, pool, "
						"artist, wiki_page, forum_topic, forum_post, tag_implication, "
						"tag_alias, bulk_update_request, post_appeal, comment")
	parser.add_argument('--new', help="Create a new user report",action="store_true")
	args = parser.parse_args()
	main(args)