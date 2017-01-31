#temp2.py
#PYTHON IMPORTS
import os
import csv
import sys
import json
import time
import argparse

#LOCAL IMPORTS
from misc import PutGetData,PutGetUnicode,DebugPrint,DebugPrintInput,FindUnicode,MakeUnicodePrintable,\
				HasMonthPassed,HasDayPassed,DaysToSeconds,SecondsToDays,WithinOneSecond,GetCurrentTime,\
				TurnDebugOn,TurnDebugOff,SafePrint,CreateOpen,TouchFile
from danbooru import SubmitRequest,IDPageLoop,JoinArgs,GetArgUrl2,GetPageUrl,ProcessTimestamp,IsUpload,\
				IsTagAdd,IsTagRemove,MetatagExists,GetTagCategory,DateStringInput
from myglobal import workingdirectory,datafilepath,csvfilepath,jsonfilepath

#GLOBAL VARIABLES
startedyet = False
usertagdictfile = workingdirectory + datafilepath + "usertagdict.txt"
userjsonfile = workingdirectory + jsonfilepath + "%susertags.json"
sitejsonfile = workingdirectory + jsonfilepath + "%ssitetags.json"
tagdictfile = workingdirectory + "tagdict.txt"
watchdogfile = workingdirectory + "watchdog.txt"
tagtypedict = {0:'gentags',4:'chartags',3:'copytags',1:'arttags',2:'emptytags'}

def main(args):
	global usertagdictfile,userjsonfile,sitejsonfile
	#TurnDebugOn('danbooru')
	
	if os.path.exists(usertagdictfile) and not args.new:
		print("Opening",usertagdictfile)
		startid,starttime,postusertagdict,uploadusertagdict = PutGetUnicode(usertagdictfile,'r')
		startid = [GetPageUrl(startid)]
	else:
		startid = []
		postusertagdict = {}
		uploadusertagdict = {}
		currenttime = GetCurrentTime()
		inputtime = time.mktime(time.strptime(args.date,"%Y-%m-%d"))
		if currenttime < inputtime:
			starttime = currenttime
		else:
			starttime = inputtime
	
	if os.path.exists(tagdictfile): 
		print("Opening",tagdictfile)
		tagdict = PutGetUnicode(tagdictfile,'r')
	else: 
		print("No tag dict file!")
		sys.exit(-1)
	
	#Set other preloop variables
	currentday = [0]
	inputdict = {'starttime':starttime,'postusertagdict':postusertagdict,'uploadusertagdict':uploadusertagdict,'tagdict':tagdict,'currentday':currentday}
	
	print("Starting main loop...")
	lastid = IDPageLoop('post_versions',500,TopTagsIteration,firstloop=startid,inputs=inputdict,postprocess=TopTagsPostprocess)
	
	#Now that we're done, let's do one last final save
	print("Writing", usertagdictfile)
	PutGetUnicode(usertagdictfile,'w',[lastid,starttime,postusertagdict,uploadusertagdict])
	
	print("Writing", tagdictfile)
	PutGetUnicode(tagdictfile,'w',tagdict)
	
	print("Creating ALL user tag dict")
	allusertagdict = uploadusertagdict.copy()
	for user in postusertagdict:
		if user not in allusertagdict: 
			allusertagdict[user]={0:{},1:{},2:{},3:{},4:{}}
		for category in postusertagdict[user]:
			for tag in postusertagdict[user][category]:
				if tag in allusertagdict[user][category]:
					allusertagdict[user][category][tag] += postusertagdict[user][category][tag]
				else:
					allusertagdict[user][category][tag] = postusertagdict[user][category][tag]
	
	createjsonfiles("post",postusertagdict)
	createjsonfiles("upload",uploadusertagdict)
	createjsonfiles("all",allusertagdict)
	
	print("Done!")

def createjsonfiles(category,usertagdict):
	localuserjsonfile = userjsonfile % category
	localsitejsonfile = sitejsonfile % category
	print("Writing", localuserjsonfile)
	usertags = []
	for user in usertagdict:
		usertags += [{'id':user,'gentags':usertagdict[user][0],'arttags':usertagdict[user][1],'emptytags':usertagdict[user][2],'copytags':usertagdict[user][3],'chartags':usertagdict[user][4]}]
	with CreateOpen(localuserjsonfile, 'w') as outfile:
		json.dump(usertags, outfile)
	
	print("Writing", localsitejsonfile)
	sitetags = {'gentags':{},'arttags':{},'emptytags':{},'copytags':{},'chartags':{}}
	for user in usertagdict:
		for category in usertagdict[user]:
			for tag in usertagdict[user][category]:
				sitetags[tagtypedict[category]][tag] = (sitetags[tagtypedict[category]][tag] + usertagdict[user][category][tag]) if (tag in sitetags[tagtypedict[category]]) else (usertagdict[user][category][tag])
	with CreateOpen(localsitejsonfile, 'w') as outfile:
		json.dump(sitetags, outfile)

def TopTagsIteration(postver,starttime,postusertagdict,uploadusertagdict,tagdict,**kwargs):
	global startedyet
	
	currenttime = ProcessTimestamp(postver['updated_at'])
	userid = postver['updater_id']
	
	if starttime < currenttime:
		return 0
	elif startedyet == False:
		startedyet = True
		print('S',end='',flush=True)
	
	if HasMonthPassed(starttime,currenttime):
		return -1
	
	if IsUpload(postver):
		populateusertagdict(userid,postver['tags'].split(),uploadusertagdict,tagdict)
	
	if IsTagAdd(postver):
		populateusertagdict(userid,postver['added_tags'].split(),postusertagdict,tagdict)
	
	if IsTagRemove(postver):
		populateusertagdict(userid,postver['removed_tags'].split(),postusertagdict,tagdict)
	
	return 0

def TopTagsPostprocess(postverlist,starttime,postusertagdict,uploadusertagdict,currentday,**kwargs):
	currenttime = ProcessTimestamp(postverlist[-1]['updated_at'])
	
	#Save the current progress
	PutGetUnicode(usertagdictfile,'w',[postverlist[-1]['id'],starttime,postusertagdict,uploadusertagdict])
	
	TouchFile(watchdogfile)
	
	#Print some screen feedback so we know where we're at
	if HasDayPassed(starttime-currenttime,DaysToSeconds(currentday[0])):
		currentday[0] = int(SecondsToDays(starttime-currenttime))
		print(currentday[0], end="", flush=True)

def populateusertagdict(userid,taglist,usertagdict,tagdict):
	for tag in taglist:
		
		if tag in tagdict:
			category = tagdict[tag]
		else:
			if FindUnicode(tag):
				continue
			category = GetTagCategory(tag)
			tagdict[tag]=category
		
		if MetatagExists(tag):
			continue
		
		if userid not in usertagdict: usertagdict[userid]={0:{},1:{},2:{},3:{},4:{}}
		usertagdict[userid][category][tag] = (usertagdict[userid][category][tag] + 1) if (tag in usertagdict[userid][category]) else 1

if __name__=='__main__':
	parser = argparse.ArgumentParser(description="Gather tag metric data")
	parser.add_argument('--new', help="Start new collection",action="store_true")
	parser.add_argument('-d','--date',type=DateStringInput,help="Date to start the report",default='2050-01-01')
	args = parser.parse_args()
	main(args)