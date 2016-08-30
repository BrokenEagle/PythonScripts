#DTEXTTABLE.PY
"""Primary use is to take the data collected by userreport.py and create a DText table"""

#PYTHON IMPORTS
import os
import sys
import time
from collections import OrderedDict

#LOCAL IMPORTS
from misc import PutGetData,CreateDirectory
from myglobal import workingdirectory,datafilepath,dtextfilepath
from danbooru import SubmitRequest,GetArgUrl
from userreport import userdictfile,versionedtypes,nonversionedtypes,validtypes

#MODULE GLOBAL VARIABLES
builderlevel = 32
adminlevel = 50

dtextfile = workingdirectory + dtextfilepath + '%sdtexttable.txt'

ordercutoff = {'pool':0,'note':0,'artist_commentary':0,'artist':0,'wiki_page':0,'post':0,'upload':50,'comment':0,'forum_post':0,'forum_topic':0,'post_appeal':0,'bulk_update_request':0,'tag_alias':0,'tag_implication':0}
membercutoff = {'pool':40,'note':250,'artist_commentary':50,'artist':40,'wiki_page':25,'post':500,'upload':100,'comment':100,'forum_post':25,'forum_topic':4,'post_appeal':2,'bulk_update_request':2,'tag_alias':2,'tag_implication':2}
buildercutoff = {'pool':40,'note':250,'artist_commentary':50,'artist':40,'wiki_page':25,'post':500,'upload':250,'comment':100,'forum_post':25,'forum_topic':4,'post_appeal':2,'bulk_update_request':2,'tag_alias':2,'tag_implication':2}
tablecutoff = {}

pretableheader = "[table]\r\n[thead]\r\n[tr]\r\n[th]Rank[/th]\r\n" + \
				"[th]Username[/th]\r\n[th]Total[/th]\r\n"
posttableheader = "[/tr]\r\n[/thead]\r\n[tbody]\r\n"

postcolumns = "[th]Uploads[/th]\r\n[th]Adds[/th]\r\n[th]Removes[/th]\r\n" + \
				"[th]Parent[/th]\r\n[th]Rating[/th]\r\n" + \
				"[th]Source[/th]\r\n[th]Other[/th]\r\n"
uploadcolumns = "[th]Queue Bypass[/th]\r\n[th]Deleted[/th]\r\n[th]Parent[/th]\r\n[th]Source[/th]\r\n" + \
				"[th]S[/th]\r\n[th]Q[/th]\r\n[th]E[/th]\r\n[th]GenTag[/th]\r\n[th]CharTag[/th]\r\n" + \
				"[th]CopyTag[/th]\r\n[th]ArtTag[/th]\r\n[th]Tag Error[/th]\r\n[th]Removes[/th]\r\n"
poolcolumns = "[th]Creates[/th]\r\n[th]Adds[/th]\r\n[th]Removes[/th]\r\n" + \
				"[th]Orders[/th]\r\n[th]Other[/th]\r\n"
notecolumns = "[th]Creates[/th]\r\n[th]Body Edits[/th]\r\n[th]Moves[/th]\r\n" + \
				"[th]Resizes[/th]\r\n[th]Deletes[/th]\r\n" + \
				"[th]Undeletes[/th]\r\n[th]Other[/th]\r\n"
commentarycolumns = "[th]Creates[/th]\r\n[th]Orig Title[/th]\r\n[th]Orig Descr[/th]\r\n" + \
				"[th]Trans Title[/th]\r\n[th]Trans Descr[/th]\r\n" + \
				"[th]Other[/th]\r\n"
artistcolumns = "[th]Creates[/th]\r\n[th]Name[/th]\r\n[th]Other Names[/th]\r\n" + \
				"[th]URL[/th]\r\n[th]Group[/th]\r\n" + \
				"[th]Deletes[/th]\r\n[th]Undeletes[/th]\r\n" + \
				"[th]Wiki[/th]\r\n[th]Other[/th]\r\n"
wikipagecolumns = "[th]Creates[/th]\r\n[th]Title[/th]\r\n[th]Other Names[/th]\r\n" + \
				"[th]Body Edits[/th]\r\n[th]Other[/th]\r\n"
commentcolumns = "[th]Updates[/th]\n[th]Bumps[/th]\n" + \
				"[th]# with Pos Score[/th]\n[th]# with Neg Score[/th]\n" + \
				"[th]Cumulative Score[/th]\n[th]Deletes[/th]\n"
forumpostcolumns = "[th]Updates[/th]\n"
forumtopiccolumns = "[th]Replies[/th]\n"
postappealcolumns = "[th]Successful[/th]\n"
aliasimplicationcolumns = "[th]Approved[/th]\n"
BURcolumns = "[th]Approved[/th]\n[th]Rejected[/th]\n"

#MAIN FUNCTION

def main(argv,argc):
	"""Main function; 
	argv[1] = typename
	"""
	global userdictfile,dtextfile,tablecutoff
	
	#TurnDebugOn('danbooru')	#uncomment this line to see debugging in danbooru module
	
	if(argv[1]) not in validtypes:
		print("Invalid category")
		return -1
	
	#Are we splitting the tables or not?
	if 'builder' in argv:
		tablecutoff = buildercutoff
		tabletype = 'builder'
	elif 'member' in argv:
		tablecutoff = membercutoff
		tabletype = 'member'
	else:
		tablecutoff = buildercutoff
		tabletype = ''
	
	#Are we doing a Top/Bottom XX table?
	if any('top' in x for x in argv):
		subarg = (''.join(s for s in argv if "top" in s))[3:]
		if subarg.isdigit():
			ordertable = "top"
			tablesize = int(subarg)
		else:
			print("Invalid top argument")
			return -1
	elif any('bottom' in x for x in argv):
		subarg = (''.join(s for s in argv if "bottom" in s))[6:]
		if subarg.isdigit():
			ordertable = "bottom"
			tablesize = int(subarg)
		else:
			print("Invalid bottom argument")
			return -1
	else:
		ordertable = ''
	
	#Are we doing a Top/Bottom table?
	if ordertable != '':
		#The only case being handled right now, though more could be added
		if typename == 'upload' and 'tag' in argv:
			sorttype = 'tag'
			for key in userdict:
				if userdict[key][0] < ordercutoff[typename]:
					continue
				tempdict[key] = [(int(100*((userdict[key][8] + userdict[key][9] + userdict[key][10] + userdict[key][11])/ \
								(userdict[key][0]))))/100,userdict[key][0]]
			userdict = tempdict
		#any nondefined cases goes here
		else:
			print("Sort type not set")
			return -1
	else:
		sorttype = ''
	
	#Set variables according to the current type
	typename = argv[1]
	userdictfile = userdictfile % typename
	dtextfile = dtextfile % (typename+tabletype+ordertable+sorttype)
	
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
	
	endid,startid,starttime,userdict = PutGetData(userdictfile,'r')
	
	#Sort the user dictionary by the Total column
	if ordertable == 'bottom':
		Ouserdict = OrderedDict(sorted(userdict.items(), key=lambda x:x[1], reverse=False))
	else:
		Ouserdict = OrderedDict(sorted(userdict.items(), key=lambda x:x[1], reverse=True))
	
	#Get a copy that we can manipulate for displaying
	displaydict = Ouserdict.copy()
	
	#Set preloop variables
	usernamedict = {}
	datadict = {}
	numrows = 1
	#Iterate through dictionary until the cutoff is reached
	for key in Ouserdict:
		if (Ouserdict[key][0] < tablecutoff[typename]) and (ordertable == ''):
			#The current entry is below the cutoff; FOR loop exit condition
			break
		elif (numrows > tablesize) and (ordertable != ''):
			#The top/bottom table has been filled; other FOR loop exit condition
			break
		
		#Get current user info and process it
		
		#First Send API request to Danbooru; response will be a dictionary
		userentry = SubmitRequest('show','users',id=key)
		
		#Separate the users by level if necessary
		if (tabletype == 'builder') and (userentry['level'] < builderlevel):
			temp=displaydict.pop(key)
			continue
		elif tabletype == 'member' and (userentry['level'] >= builderlevel):
			temp=displaydict.pop(key)
			continue
		
		username = userentry['name']
		
		if (userentry['level'] >= builderlevel):
			usernamedict[key] = (repr(username) + ':[/users/' + repr(key) + ']')
		elif (userentry['level'] < builderlevel):
			usernamedict[key] = ('[u]'+repr(username) + ':[/users/' + repr(key) + '][/u]')
		
		#With uploads, user the post search user:<USERNAME> metatag
		if typename == 'upload':
			datadict[key] = repr(repr(Ouserdict[key][0])) + ':[/posts?tags=user%3A' + username + ']'
		elif typename in versionedtypes:
			datadict[key] = repr(repr(Ouserdict[key][0])) + ':[/' + controller + '?' + GetArgUrl('search','updater_id',key) + ']'
		elif typename == 'comment':
			datadict[key] = repr(repr(Ouserdict[key][0])) + ':[/' + controller + '?' + GetArgUrl('search','creator_id',key) + GetArgUrl('group_by','','comment') + ']'
		elif typename in nonversionedtypes:
			datadict[key] = repr(repr(Ouserdict[key][0])) + ':[/' + controller + '?' + GetArgUrl('search','creator_id',key) + ']'
		
		#Print some feedback
		print(':', end="", flush=True)
	
	print("Writing Data to DText File!")
	membertextstring = "[expand=%s Details - Updated at %s]\r\n" % (tabletype.title() + ' ' + (typename.replace('_',' ')).title(),time.asctime((time.gmtime(starttime))))
	membertextstring += constructtable(typename,displaydict,usernamedict,datadict)
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

#HELPER FUNCTIONS

def constructtableheader(typename):
	"""Return table header according to type"""
	if typename == 'post':
		return pretableheader + postcolumns + posttableheader
	if typename == 'upload':
		return pretableheader + uploadcolumns + posttableheader
	if typename == 'pool':
		return pretableheader + poolcolumns + posttableheader
	if typename == 'note':
		return pretableheader + notecolumns + posttableheader
	if typename == 'artist_commentary':
		return pretableheader + commentarycolumns + posttableheader
	if typename == 'artist':
		return pretableheader + artistcolumns + posttableheader
	if typename == 'wiki_page':
		return pretableheader + wikipagecolumns + posttableheader
	if typename == 'comment':
		return pretableheader + commentcolumns + posttableheader
	if typename == 'forum_post':
		return pretableheader + forumpostcolumns + posttableheader
	if typename == 'forum_topic':
		return pretableheader + forumtopiccolumns + posttableheader
	if typename == 'post_flag':
		return pretableheader + postflagcolumns + posttableheader
	if typename == 'post_appeal':
		return pretableheader + postappealcolumns + posttableheader
	if typename == 'bulk_update_request':
		return pretableheader + BURcolumns + posttableheader
	if (typename == 'tag_alias') or (typename == 'tag_implication'):
		return pretableheader + aliasimplicationcolumns + posttableheader

def constructtable(typename,ordereddict,usernamedict,datadict):
	"""Dynamically create the DText Table"""
	
	#Create the DText table header first
	string = constructtableheader(typename)
	
	#Start rank at #1
	i = 1
	
	#Iterate through ordered user dictionary
	for key in ordereddict:
		
		#Have we reached the table cutoff yet?
		if ordereddict[key][0] < tablecutoff[typename]:
			#FOR loop exit condition
			break
		
		#Add first 3 columns
		string += "[tr]\r\n[th]" + str(i) + \
				"[/th]\r\n[th]" + usernamedict[key] + \
				"[/th]\r\n[th]" + datadict[key]
		
		#Then add in the rest
		for j in range(1,len(ordereddict[key])):
			string += "[/th]\r\n[th]" + str(ordereddict[key][j])
		
		#End this row
		string += "[/th]\r\n[/tr]\r\n"
		
		#Increment to next rank
		i += 1
	
	#End this table
	string += "[/tbody]\r\n[/table]"
	
	return string

if __name__ == '__main__':
	#Arguments from command-line
	if (len(sys.argv) < 2):
		print("Invalid input")
		sys.exit(-1)
	
	#Call main function
	main(sys.argv,len(sys.argv))
