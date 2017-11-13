#REPORT/CONTROLLERS/POST/REQUEST.PY

#MODULE IMPORTS
from ...logical.users import UserReportData

#LOCAL GLOBALS

otherrequests = ['annotation_request', 'flower_request', 'weapon_request', 'food_request', 'collaboration_request', 'style_request', 'vehicle_request', 'medium_request', 'bird_request', 'instrument_request', 'cosplay_request', 'costume_request', 'animal_request', 'song_request', 'fish_request', 'plant_request', 'gesture_request', 'object_request', 'underwear_request', 'location_request', 'guitar_request', 'emblem_request', 'model_request', 'reverse_translation_request']

#Functions

def UpdateRequestData(userid,userdict,postver):
	"""Update requests columns for user ID"""
	
	taglist = postver['added_tags']
	
	if 'tagme' in taglist:
		addtagme = 1
	else:
		addtagme = 0
	
	if 'artist_request' in taglist:
		addartist = 1
	else:
		addartist = 0
	
	if 'copyright_request' in taglist:
		addcopyright = 1
	else:
		addcopyright = 0
	
	if 'character_request' in taglist:
		addcharacter = 1
	else:
		addcharacter = 0
	
	if 'source_request' in taglist:
		addsource = 1
	else:
		addsource = 0
	
	if len(set(otherrequests).intersection(taglist)) > 0:
		addother = len(set(otherrequests).intersection(taglist))
	else:
		addother = 0
	
	taglist = postver['removed_tags']
	
	if 'tagme' in taglist:
		subtagme = 1
	else:
		subtagme = 0
	
	if 'artist_request' in taglist:
		subartist = 1
	else:
		subartist = 0
	
	if 'copyright_request' in taglist:
		subcopyright = 1
	else:
		subcopyright = 0
	
	if 'character_request' in taglist:
		subcharacter = 1
	else:
		subcharacter = 0
	
	if 'source_request' in taglist:
		subsource = 1
	else:
		subsource = 0
	
	if len(set(otherrequests).intersection(taglist)) > 0:
		subother = len(set(otherrequests).intersection(taglist))
	else:
		subother = 0
	
	addtags = addtagme + addartist + addcopyright + addcharacter + addsource + addother
	subtags = subtagme + subartist + subcopyright + subcharacter + subsource + subother
	
	if (addtags+subtags) == 0:
		return 1
	
	userdict[userid][0] += addtags - 1		#Subtract the 1 added by ReportData class
	userdict[userid][1] += subtags
	userdict[userid][2] += addtagme
	userdict[userid][3] += subtagme
	userdict[userid][4] += addartist
	userdict[userid][5] += subartist
	userdict[userid][6] += addcopyright
	userdict[userid][7] += subcopyright
	userdict[userid][8] += addcharacter
	userdict[userid][9] += subcharacter
	userdict[userid][10] += addsource
	userdict[userid][11] += subsource
	userdict[userid][12] += addother
	userdict[userid][13] += subother

def RequestTransform(userdict,**kwargs):
	datacolumns = {}
	for user in userdict:
		datacolumns[user] = userdict[user][0:2] +\
			["%d, (%d)" % (userdict[user][2],userdict[user][3]),"%d, (%d)" % (userdict[user][4],userdict[user][5]),\
			"%d, (%d)" % (userdict[user][6],userdict[user][7]),"%d, (%d)" % (userdict[user][8],userdict[user][9]),\
			"%d, (%d)" % (userdict[user][10],userdict[user][11]),"%d, (%d)" % (userdict[user][12],userdict[user][13])]
	return datacolumns

#Report variables
reportname = 'request'
dtexttitle = "Request Details"
footertext = "request tags"
dtextheaders = ['Username','Add Total','Sub Total','Tagme','Art','Copy','Char','Src','Other']
transformfuncs = [None,None,None,None,None,None,None,None]
dtexttransform = RequestTransform
csvheaders = ['userid','addtags','subtags','+tagme','-tagme','+artreq','-artreq','+copyreq','-copyreq','+charreq','-charreq','+sourcereq','-sourcereq','+otherreq','-otherreq']
extracolumns = 13
tablecutoffs = [[50],[50]] #50
sortcolumns = [0,1]
reversecolumns = [[True],[True]]

reporthandler = UserReportData.InitializeUserReportData(UpdateRequestData)
