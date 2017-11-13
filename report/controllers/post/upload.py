#REPORT/CONTROLLERS/POST/UPLOAD.PY

#PYTHON IMPORTS
import statistics
from functools import reduce

#LOCAL IMPORTS
from danbooru import IsUpload,SubmitRequest,GetArgUrl2,JoinArgs,IDPageLoop
from misc import DebugPrint,GetDate,IncDictEntry,SetPrecision,PrintChar

#MODULE IMPORTS
from ...logical import tags
from ...logical.users import GetContributorList,GetUserIDDict,UserReportData
from .. import post

#LOCAL GLOBALS

uploadtaglist = {
    0:[],
    1:['approver:none'],
    2:['status:deleted'],
    3:['parent:any'],
    5:['source:any'],
    6:['rating:s'],
    7:['rating:q'],
    8:['rating:e']}

uploadcategory = {
    10:'general',
    11:'character',
    12:'copyright',
    13:'artist'}

#Functions

def UploadIterator(self,indict,option):
    if IsUpload(indict):
        yield indict[post.userid]

def UpdateUploadData(userid,userdict,postver):
    """Update upload columns for userid"""
    
    taglist = postver['tags'].split()
    postid = postver['post_id']
    
    returnvalue = GetLatestPostData(postid,taglist)
    if isinstance(returnvalue,int):
        return 1
    
    userdict[userid][1] += returnvalue[0]    #mod bypass
    userdict[userid][2] += returnvalue[1]    #deleted
    if postver['parent_id']!=None:
        DebugPrint("Parent")
        userdict[userid][3] += 1
    if postver['parent_id'] != returnvalue[7]:
        DebugPrint("Parent Delta")
        userdict[userid][4] += 1
    if len(postver['source']) != 0:
        DebugPrint("Source")
        userdict[userid][5] += 1
    if postver['rating'] == 's':
        DebugPrint("Safe")
        userdict[userid][6] += 1
    if postver['rating'] == 'q':
        DebugPrint("Questionable")
        userdict[userid][7] += 1
    if postver['rating'] == 'e':
        DebugPrint("Explicit")
        userdict[userid][8] += 1
    if postver['rating'] != returnvalue[6]:
        DebugPrint("Rating Change")
        userdict[userid][9] += 1
    tagtypes = tags.CountTags(taglist)
    DebugPrint("Gen: %d Char: %d Copy: %d Art: %d" % (tagtypes[0],tagtypes[4],tagtypes[3],tagtypes[1]))
    DebugPrint("Tag delta: %d Upscore: %d Downscore: %d" % (returnvalue[8],returnvalue[2],returnvalue[4]))
    userdict[userid][10] += tagtypes[0]                        #general
    userdict[userid][11] += tagtypes[4]                        #character
    userdict[userid][12] += tagtypes[3]                        #copyright
    userdict[userid][13] += tagtypes[1]                        #artist
    userdict[userid][14] += returnvalue[8]                    #tag difference
    userdict[userid][15] += returnvalue[2]                    #up score
    userdict[userid][16] += returnvalue[3]                    #down score

def GetLatestPostData(postid,tagverlist):
    """Compare and contrast the version data with the current post data"""
    
    #Get the lastest post data
    postshow = SubmitRequest('show','posts',id=postid)
    if isinstance(postshow,int):
        return postshow
    
    #First update the Tag dictionary while we have all this good data; This reduces the amount of misses later on
    tags.UpdateTagdictFromPost(postshow)
    
    #Done updating tags.tagdict, now get data from post info
    returnvalue = [0,0,0,0,0,0,0,0,0]
    if (postshow['approver_id']==None) and (not postshow['is_deleted']) and (not postshow['is_pending']):
        DebugPrint("Mod Queue Bypass")
        returnvalue[0] = 1
    elif (postshow['is_deleted']):
        DebugPrint("Deleted")
        returnvalue[1] = 1
    
    returnvalue[2] = postshow['up_score']
    returnvalue[3] = postshow['down_score']
    returnvalue[4] = postshow['score']
    returnvalue[5] = postshow['fav_count']
    returnvalue[6] = postshow['rating']
    returnvalue[7] = postshow['parent_id']
    returnvalue[8] =  len(set(tags.RemoveInvalidTags(tagverlist)).symmetric_difference(tags.RemoveInvalidTags(postshow['tag_string'].split())))
    return returnvalue

def TagSearchColumn(userdict,column,**kwargs):
    useriddict = GetUserIDDict(userdict.keys())
    taglist = uploadtaglist[column]
    tagcolumn = {}
    for user in userdict:
        urllink = "/posts?%s" % (GetArgUrl2('tags',' '.join(['user:'+useriddict[user]['name']] + taglist)))
        tagcolumn[user] = '"%s":[%s]' % (repr(userdict[user][column]),urllink)
    return tagcolumn

def RelatedTagColumn(userdict,column,starttime,endtime,**kwargs):
    useriddict = GetUserIDDict(userdict.keys())
    category = uploadcategory[column]
    tagcolumn = {}
    startdate = GetDate(starttime)
    enddate = GetDate(endtime)
    for user in userdict:
        urllink = "/related_tag?%s" % (JoinArgs(GetArgUrl2('query',' '.join(['user:'+useriddict[user]['name']] +\
                    ['date:%s..%s'%(enddate,startdate)])),GetArgUrl2('category',category)))
        tagcolumn[user] = '"%s":[%s]' % (repr(userdict[user][column]),urllink)
    return tagcolumn

def UploadTransform(userdict,starttime,endtime):
    useriddict = GetUserIDDict(userdict.keys())
    datacolumns = {}
    print("Transforming upload table...")
    for key in userdict:
        scoredict,favdict,score = GetFavScore(useriddict[key]['name'],starttime,endtime)
        scorelist = reduce(lambda x,y:x+y,map(lambda x:[x[0]]*x[1],scoredict.items()))
        favlist = reduce(lambda x,y:x+y,map(lambda x:[x[0]]*x[1],favdict.items()))
        scoremean = SetPrecision(statistics.mean(scorelist),2)
        favmean = SetPrecision(statistics.mean(favlist),2)
        scorestdev = SetPrecision(statistics.stdev(scorelist),2)
        favstdev = SetPrecision(statistics.stdev(favlist),2)
        datacolumns[key] = userdict[key][:15] + [str(score[0])+', ('+str(score[1])+')',scoremean,scorestdev,favmean,favstdev]
    PrintChar('\n')
    return datacolumns

def UploadMemberType(userdict,option):
    contributorlist = GetContributorList()
    if option == 'member':
        return {k: v for k, v in userdict.items() if k not in contributorlist}
    elif option == 'contributor':
        return {k: v for k, v in userdict.items() if k in contributorlist}

def GetFavScore(username,starttime,endtime):
    scoredict = {}
    favdict = {}
    score = [0,0]
    
    def iterator(post):
        nonlocal scoredict,favdict,score
        
        IncDictEntry(scoredict,post['score'])
        IncDictEntry(favdict,post['fav_count'])
        score[0] += post['up_score']
        score[1] += post['down_score']
        return 0
    
    startdate = GetDate(starttime)
    enddate = GetDate(endtime)
    urladds = [GetArgUrl2('tags',' '.join(['user:'+username,'date:%s..%s'%(enddate,startdate)]))]
    
    PrintChar('F')
    IDPageLoop('posts',200,iterator,urladds)
    return scoredict,favdict,score

reportname = 'upload'
dtexttitle = "Upload Details"
footertext = "uploads"
dtextheaders = ['Username','Total','Que Byp','Del','Par','Par Δ','Src','S','Q','E','Rate Δ','Gen Tag','Char Tag','Copy Tag','Art Tag','Tag Δ','Sum Score','Mean Score','Stdev Score','Mean Favs','Stdev Favs']
csvheaders = ['userid','total','modbypass','deleted','parent','parent delta','source','safe','questionable','explicit','rating delta','gentag','chartag','copytag','arttag','tag delta','upvotes','downvotes']
transformfuncs = [TagSearchColumn,TagSearchColumn,TagSearchColumn,TagSearchColumn,None,TagSearchColumn,TagSearchColumn,TagSearchColumn,TagSearchColumn,None,RelatedTagColumn,RelatedTagColumn,RelatedTagColumn,RelatedTagColumn,None,None,None,None,None,None]
dtexttransform = UploadTransform
maketable = UploadMemberType
extracolumns = 16
tablecutoffs = [[100,200]]
reversecolumns = [[True,True]]
tableoptions = ['member','contributor']

reporthandler = UserReportData.InitializeUserReportData(UpdateUploadData,UploadIterator)
