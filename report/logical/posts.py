#REPORT/LOGICAL/POSTS.PY

#LOCAL IMPORTS
from danbooru import SubmitRequest,IDPageLoop,ProcessTimestamp,GetArgUrl2,MetatagExists,GetPostDict
from misc import StaticVars,GetDate,HasDayPassed,DaysToSeconds,SecondsToDays,PrintChar,IncDictEntry
from .tags import IsDisregardTag,GetTagDict

#LOCAL GLOBALS

ratingdict = {'s':'safe','q':'questionable','e':'explicit'}

#Functions

@StaticVars(postiddict={})
def GetPost(postid):
    if postid not in GetPost.postiddict:
        post = SubmitRequest('show','posts',id=postid)
        GetPost.postiddict[postid] = post
    return GetPost.postiddict[postid]

def PreloadPosts(postid_list):
    get_postids = list(set(postid_list).difference(GetPost.postiddict.keys()))
    adds_postiddict = GetPostDict(get_postids,True)
    GetPost.postiddict.update(adds_postiddict)

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
def GetPostCount(checktag,starttime,endtime):
    if GetPostCount.postcountdict == {}:
        #Preload tag dict
        if not MetatagExists(checktag):
            tagdict = GetTagDict()
        postlist = GetPostsByDate(starttime,endtime)
        for post in postlist:
            for tag in post['tag_string'].split():
                if MetatagExists(tag) or IsDisregardTag(tag):
                    continue
                IncDictEntry(GetPostCount.postcountdict,tag)
            IncDictEntry(GetPostCount.postcountdict,'rating:'+ratingdict[post['rating']])
    print("GetPostCount:",checktag,GetPostCount.postcountdict[checktag] if checktag in GetPostCount.postcountdict else 0)
    return GetPostCount.postcountdict[checktag] if checktag in GetPostCount.postcountdict else 0
