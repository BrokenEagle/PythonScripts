#DTEXTTABLE.PY
"""Primary use is to take the data collected by userreport.py and create a DText table"""

#PYTHON IMPORTS
import os
import sys
import time
import argparse
from functools import reduce
from collections import OrderedDict

#LOCAL IMPORTS
from misc import PutGetData,PutGetUnicode,CreateDirectory,SafePrint
from myglobal import workingdirectory,datafilepath,dtextfilepath
from danbooru import SubmitRequest,GetArgUrl
from userreport import userdictfile,usertagdictfile,versionedtypes,nonversionedtypes,validtypes

#MODULE GLOBAL VARIABLES
builderlevel = 32
adminlevel = 50

dtextfile = workingdirectory + dtextfilepath + '%sdtexttable.txt'

ordercutoff = {'pool':0,'note':0,'artist_commentary':0,'artist':0,'wiki_page':0,'post':0,'upload':50,'comment':0,'forum_post':0,'forum_topic':0,'post_appeal':0,'bulk_update_request':0,'tag_alias':0,'tag_implication':0}
membercutoff = {'pool':40,'note':250,'artist_commentary':50,'artist':40,'wiki_page':25,'post':500,'upload':100,'comment':100,'forum_post':25,'forum_topic':4,'post_appeal':2,'bulk_update_request':2,'tag_alias':2,'tag_implication':2}
buildercutoff = {'pool':40,'note':250,'artist_commentary':50,'artist':40,'wiki_page':25,'post':500,'upload':250,'comment':100,'forum_post':25,'forum_topic':4,'post_appeal':2,'bulk_update_request':2,'tag_alias':2,'tag_implication':2}
tablecutoff = {}

pretableheader = "[table]\r\n[thead]\r\n[tr]\r\n[th]Rank[/th]\r\n[th]Username[/th]\r\n"
posttableheader = "[/tr]\r\n[/thead]\r\n[tbody]\r\n"

postcolumns = "[th]Total[/th]\r\n[th]Parent[/th]\r\n[th]Rating[/th]\r\n[th]Source[/th]\r\n"+\
				"[th]+-GenTag[/th]\r\n[th]+-CharTag[/th]\r\n[th]+-CopyTag[/th]\r\n[th]+-ArtTag[/th]\r\n[th]+-EmptyTag[/th]\r\n"+\
				"[th]Other[/th]\r\n"
uploadcolumns = "[th]Total[/th]\r\n[th]Queue Bypass[/th]\r\n[th]Deleted[/th]\r\n[th]Parent[/th]\r\n[th]Source[/th]\r\n" + \
				"[th]S[/th]\r\n[th]Q[/th]\r\n[th]E[/th]\r\n[th]GenTag[/th]\r\n[th]CharTag[/th]\r\n" + \
				"[th]CopyTag[/th]\r\n[th]ArtTag[/th]\r\n[th]Tag Error[/th]\r\n[th]Removes[/th]\r\n"
poolcolumns = "[th]Total[/th]\r\n[th]Creates[/th]\r\n[th]Adds[/th]\r\n[th]Removes[/th]\r\n" + \
				"[th]Orders[/th]\r\n[th]Other[/th]\r\n"
notecolumns = "[th]Total[/th]\r\n[th]Creates[/th]\r\n[th]Body Edits[/th]\r\n[th]Moves[/th]\r\n" + \
				"[th]Resizes[/th]\r\n[th]Deletes[/th]\r\n" + \
				"[th]Undeletes[/th]\r\n[th]Other[/th]\r\n"
commentarycolumns = "[th]Total[/th]\r\n[th]Creates[/th]\r\n[th]Orig Title[/th]\r\n[th]Orig Descr[/th]\r\n" + \
				"[th]Trans Title[/th]\r\n[th]Trans Descr[/th]\r\n" + \
				"[th]Other[/th]\r\n"
artistcolumns = "[th]Total[/th]\r\n[th]Creates[/th]\r\n[th]Name[/th]\r\n[th]Other Names[/th]\r\n" + \
				"[th]URL[/th]\r\n[th]Group[/th]\r\n" + \
				"[th]Deletes[/th]\r\n[th]Undeletes[/th]\r\n" + \
				"[th]Wiki[/th]\r\n[th]Other[/th]\r\n"
wikipagecolumns = "[th]Total[/th]\r\n[th]Creates[/th]\r\n[th]Title[/th]\r\n[th]Other Names[/th]\r\n" + \
				"[th]Body Edits[/th]\r\n[th]Other[/th]\r\n"

commentcolumns = "[th]Total[/th]\r\n[th]Updates[/th]\r\n[th]Bumps[/th]\r\n" + \
				"[th]# with Pos Score[/th]\r\n[th]# with Neg Score[/th]\r\n" + \
				"[th]Cumulative Score[/th]\r\n[th]Deletes[/th]\r\n"
forumpostcolumns = "[th]Total[/th]\r\n[th]Updates[/th]\r\n"
forumtopiccolumns = "[th]Total[/th]\r\n[th]Replies[/th]\r\n"
postappealcolumns = "[th]Total[/th]\r\n[th]Successful[/th]\r\n"
aliasimplicationcolumns = "[th]Total[/th]\r\n[th]Approved[/th]\r\n"
BURcolumns = "[th]Total[/th]\r\n[th]Approved[/th]\r\n[th]Rejected[/th]\r\n"

uploadtagcolumns = "[th]Tags/ Upload[/th]\r\n[th]Uploads[/th]\r\n"
posttagcountcolumns = "[th]Total[/th]\r\n[th]Tags[/th]\r\n"

#MAIN FUNCTION

def main(args):
	"""Main function; 
	args: Instance of argparse.Namespace
	"""
	global userdictfile,dtextfile,tablecutoff
	
	#TurnDebugOn('danbooru')	#uncomment this line to see debugging in danbooru module
	
	if(args.category) not in validtypes:
		print("Invalid category")
		return -1
	
	#Set variables according to the current type
	typename = args.category
	userdictfile = userdictfile % typename
	membertype = args.memberlevel
	tableorder = args.ranking
	tablesize = args.tablesize
	sorttype = args.sorttype
	
	#Set the danbooru controller that will handle the API calls
	if typename == 'upload':
		controller = 'post_versions'
	elif typename in versionedtypes:
		controller = typename + '_versions'
	elif typename == 'tag_alias':
		controller = 'tag_aliases'
	elif typename in nonversionedtypes:
		controller = '%ss' % typename
	
	#Check to see that the data file was created with versions.py
	if not os.path.exists(userdictfile):
		print("No data file")
		return -1
	
	#Open the user dictionary for sorting
	endid,startid,starttime,userdict = PutGetData(userdictfile,'r')
	print(len(userdict))
	
	usertagdict = {}
	if typename=='post' and args.sorttype=='tagcount':
		if os.path.exists(usertagdictfile):
			usertagdict = PutGetUnicode(usertagdictfile,'r')
			for key in usertagdict:
				usertagdict[key] = OrderedDict(sorted(usertagdict[key].items(), key=lambda x:x[1], reverse=True))
		else:
			print("No user tag dict file")
			return -1
	
	#Set the cutoff membertype
	if membertype == 'member':
		tablecutoff = membercutoff
	else:
		tablecutoff = buildercutoff
	
	#Unset some variables, just in case
	if tableorder == '':
		sorttype = ''
		tableorder = ''
		tablesize = 0
	
	if typename == 'post':
		userdict = updatepostcolumns(userdict,sorttype)
	elif typename == 'upload':
		userdict = updateuploadcolumns(userdict,sorttype)
	print(len(userdict))
	#Set the name of the dtext file according to the various parameters
	dtextfile = dtextfile % (typename+membertype+tableorder+sorttype)
	
	#Sort the user dictionary by the Total column
	if tableorder == 'bottom':
		Ouserdict = OrderedDict(sorted(userdict.items(), key=lambda x:x[1], reverse=False))
	else:
		Ouserdict = OrderedDict(sorted(userdict.items(), key=lambda x:x[1], reverse=True))
	
	#Get a copy that we can manipulate for displaying
	displaydict = Ouserdict.copy()
	
	#Set preloop variables
	usernamedict = {}
	datadict = {}
	numrows = 1
	
	print(tablesize,numrows,tablecutoff[typename],len(Ouserdict))
	#Iterate through dictionary until the cutoff is reached
	for key in Ouserdict:
		if (Ouserdict[key][0] < tablecutoff[typename]) and (tablesize == 0):
			#The current entry is below the cutoff; FOR loop exit condition
			break
		elif (numrows > tablesize) and (tablesize > 0):
			#The top/bottom table has been filled; other FOR loop exit condition
			break
		
		#Get current user info and process it
		
		#First Send API request to Danbooru; response will be a dictionary
		userentry = SubmitRequest('show','users',id=key)
		
		#Separate the users by level if necessary
		if (membertype == 'builder') and (userentry['level'] < builderlevel):
			temp=displaydict.pop(key)
			continue
		elif membertype == 'member' and (userentry['level'] >= builderlevel):
			temp=displaydict.pop(key)
			continue
		
		username = userentry['name']
		
		if (userentry['level'] >= builderlevel):
			usernamedict[key] = (repr(username) + ':[/users/' + repr(key) + ']')
		elif (userentry['level'] < builderlevel):
			usernamedict[key] = ('[u]'+repr(username) + ':[/users/' + repr(key) + '][/u]')
		
		#Don't create a data dictionary for 'top/bottom' tables
		if tablesize == 0 and args.sorttype != 'tagcount':
			if typename == 'upload':
				#With uploads, use the post search user:<USERNAME> metatag
				datadict[key] = repr(repr(Ouserdict[key][0])) + ':[/posts?tags=user%3A' + username + ']'
			elif typename in versionedtypes:
				datadict[key] = repr(repr(Ouserdict[key][0])) + ':[/' + controller + '?' + GetArgUrl('search','updater_id',key) + ']'
			elif typename == 'comment':
				datadict[key] = repr(repr(Ouserdict[key][0])) + ':[/' + controller + '?' + GetArgUrl('search','creator_id',key) + GetArgUrl('group_by','','comment') + ']'
			elif typename in nonversionedtypes:
				datadict[key] = repr(repr(Ouserdict[key][0])) + ':[/' + controller + '?' + GetArgUrl('search','creator_id',key) + ']'
		else:
			#Maybe do something else with datadict here...
			
			#increment to the next entry (For Top/Bottom tables)
			numrows += 1
		
		#Print some feedback
		print(':', end="", flush=True)
	
	print("Writing Data to DText File!")
	membertextstring = "[expand=%s Details - Updated at %s]\r\n" % (membertype.title() + ' ' + (typename.replace('_',' ')).title(),time.asctime((time.gmtime(starttime))))
	membertextstring += constructtable(typename,displaydict,usernamedict,datadict,usertagdict,tablesize,sorttype)
	membertextstring += "\r\n[b]Note:[/b] Cutoff was %d total %s changes; duration was 30 days\r\n[/expand]" % (tablecutoff[typename],(typename.replace('_',' ')).title())
	
	#Print to a temp file first
	with open(workingdirectory + 'temp.txt','wb') as f:
		f.write(membertextstring.encode('UTF'))
	
	#Create directory if it doesn't already exist
	CreateDirectory(dtextfile)
	
	#Then parse it for lines with ' and not " replace ' with "
	with open(workingdirectory + 'temp.txt','rb') as infile, open(dtextfile,'wb') as outfile:
		for line in infile:
			if line.find(b"'") > 0 and line.find(b'"') < 0:
				line = line.replace(b'\'',b'"')
			outfile.write(line)
	
	print("Done!")

#COLUMN FUNCTIONS
def updatepostcolumns(userdict,sorttype):
	if sorttype == '':
		for key in userdict:
			userdict[key] = userdict[key][0:4] + [(userdict[key][4],userdict[key][9])] +\
						[(userdict[key][5],userdict[key][10])] + [(userdict[key][6],userdict[key][11])] +\
						[(userdict[key][7],userdict[key][12])] + [(userdict[key][8],userdict[key][13])] +\
						[userdict[key][14]]
		return userdict
	elif sorttype == 'tagcount':
		for key in userdict:
			userdict[key] = [reduce(lambda x,y:x+y,userdict[key][4:13])]
		return userdict
	return tempdict

def updateuploadcolumns(userdict,sorttype=None):
	tempdict = {}
	if sorttype == '':
		return userdict
	elif sorttype == 'tag':
		for key in userdict:
			if userdict[key][0] < ordercutoff[typename]:
				continue
			tempdict[key] = [(int(100*((userdict[key][8] + userdict[key][9] + userdict[key][10] + userdict[key][11])/ \
							(userdict[key][0]))))/100,userdict[key][0]]	
	
	return tempdict

#HELPER FUNCTIONS

def constructtableheader(typename,sorttype):
	"""Return table header according to type"""
	
	#Sorting being done by Total
	if (typename == 'post') and (sorttype == ''):
		return pretableheader + postcolumns + posttableheader
	if (typename == 'upload') and (sorttype == ''):
		return pretableheader + uploadcolumns + posttableheader
	if (typename == 'pool') and (sorttype == ''):
		return pretableheader + poolcolumns + posttableheader
	if (typename == 'note') and (sorttype == ''):
		return pretableheader + notecolumns + posttableheader
	if (typename == 'artist_commentary') and (sorttype == ''):
		return pretableheader + commentarycolumns + posttableheader
	if (typename == 'artist') and (sorttype == ''):
		return pretableheader + artistcolumns + posttableheader
	if (typename == 'wiki_page') and (sorttype == ''):
		return pretableheader + wikipagecolumns + posttableheader
	if (typename == 'comment') and (sorttype == ''):
		return pretableheader + commentcolumns + posttableheader
	if (typename == 'forum_post') and (sorttype == ''):
		return pretableheader + forumpostcolumns + posttableheader
	if (typename == 'forum_topic') and (sorttype == ''):
		return pretableheader + forumtopiccolumns + posttableheader
	if (typename == 'post_appeal') and (sorttype == ''):
		return pretableheader + postappealcolumns + posttableheader
	if (typename == 'bulk_update_request') and (sorttype == ''):
		return pretableheader + BURcolumns + posttableheader
	if ((typename == 'tag_alias') or (typename == 'tag_implication')) and (sorttype == ''):
		return pretableheader + aliasimplicationcolumns + posttableheader
	
	#Sorting being done by other column
	if (typename == 'upload') and (sorttype == 'tag'):
		return pretableheader + uploadtagcolumns + posttableheader
	
	#Sorting being done on different table
	if (typename == 'post') and (sorttype == 'tagcount'):
		return pretableheader + posttagcountcolumns + posttableheader

def constructtable(typename,ordereddict,usernamedict,datadict,usertagdict,tablesize,sorttype):
	"""Dynamically create the DText Table"""
	
	#Create the DText table header first
	string = constructtableheader(typename,sorttype)
	
	#Start rank at #1
	i = 1
	
	#Iterate through ordered user dictionary
	for key in ordereddict:
		
		#Have we reached the table cutoff yet?
		if ordereddict[key][0] < tablecutoff[typename] and (tablesize == 0):
			#FOR loop exit condition
			break
		elif (i > tablesize) and (tablesize > 0):
			#other FOR loop exit condition
			break
		
		#Add first 2 columns
		string += "[tr]\r\n[th]" + str(i) + \
				"[/th]\r\n[th]" + usernamedict[key]
		
		if tablesize == 0:
			string += "[/th]\r\n[th]" + datadict[key]
		else:
			string += "[/th]\r\n[th]" + str(ordereddict[key][0])
		
		#Then add in the rest
		if sorttype=='tagcount':
			j = 0
			string += "[/th]\r\n[th]" 
			for tag in usertagdict[key]:
				if j >= 10:
					break
				string += '(' + tag + ',' + str(usertagdict[key][tag]) + ') '
				j += 1
		else:
			for val in ordereddict[key]:
				string += "[/th]\r\n[th]" + ((str(val)).replace('(','')).replace(')','')
		#End this row
		string += "[/th]\r\n[/tr]\r\n"
		
		#Increment to next rank
		i += 1
	
	#End this table
	string += "[/tbody]\r\n[/table]"
	
	return string

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="DText table creater")
	parser.add_argument('category',help="post, upload, note, artist_commentary, pool, "
						"artist, wiki_page, forum_topic, forum_post, tag_implication, "
						"tag_alias, bulk_update_request, post_appeal, comment")
	parser.add_argument('-m','--memberlevel',required=False, help="Specify member level",choices=['member','builder'],default='')
	parser.add_argument('-r','--ranking',required=False, help="Specify rank order",choices=['top','bottom'],default='')
	parser.add_argument('-s','--tablesize',required=False,type=int, help="Size of the ranking table (Default: 25)",default=25)
	parser.add_argument('-t','--sorttype',required=False, help="post: ('tag')",choices=['tag','tagcount'],default='')
	args = parser.parse_args()
	
	inputdependencies=[getattr(args,key) is not '' for key in ('ranking','sorttype')]
	if any(inputdependencies) and not all(inputdependencies):
		print("\nError: Both ranking and sorttype must be specified if either is used!")
		sys.exit(-1)
	
	#Call main function
	main(args)
