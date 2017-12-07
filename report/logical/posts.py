#REPORT/LOGICAL/POSTS.PY

#LOCAL IMPORTS
from danbooru import SubmitRequest,IDPageLoop,ProcessTimestamp,GetArgUrl2,MetatagExists
from misc import StaticVars,GetDate,HasDayPassed,DaysToSeconds,SecondsToDays,PrintChar,IncDictEntry
from .tags import IsDisregardTag

#LOCAL GLOBALS

ratingdict = {'s':'safe','q':'questionable','e':'explicit'}

#Functions

@StaticVars(postiddict={})
def GetPost(postid):
    if postid not in GetPost.postiddict:
        post = SubmitRequest('show','posts',id=postid)
        GetPost.postiddict[postid] = post
    return GetPost.postiddict[postid]

@StaticVars(postdatedict={})
def GetPostsByDate(starttime,endtime):
    startdate = GetDate(starttime)
    enddate = GetDate(endtime)
    index = '%s..%s'%(enddate,startdate)
    if index not in GetPostsByDate.postdatedict:
        print("Building post list:",index)
        
        def loadpost(post):
            nonlocal postdatelist
            
            postdatelist.append(post)
            return 0
        
        def loaddate(postlist):
            nonlocal currentday
            
            currenttime = ProcessTimestamp(postlist[-1]['created_at'])
            if HasDayPassed(starttime-currenttime,DaysToSeconds(currentday)):
                currentday = int(SecondsToDays(starttime-currenttime))
                PrintChar(currentday)
        
        urladds = [GetArgUrl2('tags','date:'+index+' status:any')]
        postdatelist = []
        currentday = 0
        IDPageLoop('posts',200,loadpost,urladds,postprocess=loaddate)
        GetPostsByDate.postdatedict[index] = postdatelist
        PrintChar('\n')
    return GetPostsByDate.postdatedict[index]

@StaticVars(postcountdict={})
def GetPostCount(tag,starttime,endtime):
    if GetPostCount.postcountdict == {}:
        postlist = GetPostsByDate(starttime,endtime)
        for post in postlist:
            for tag in post['tag_string'].split():
                if MetatagExists(tag) or IsDisregardTag(tag):
                    continue
                IncDictEntry(GetPostCount.postcountdict,tag)
            IncDictEntry(GetPostCount.postcountdict,'rating:'+ratingdict[post['rating']])
    return GetPostCount.postcountdict[tag] if tag in GetPostCount.postcountdict else 0
