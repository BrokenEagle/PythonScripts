#REPORT/CONTROLLERS/POST/EDIT.PY

#LOCAL IMPORTS
from danbooru import IsParentChange,IsRatingChange,IsSourceChange,IsUpload
from misc import DebugPrint

#MODULE IMPORTS
from ...logical import tags
from ...logical.users import UserReportData
from ...logical.common import GetTotalColumn
from .. import post

#Functions

def PostIterator(self,indict,option):
    if not IsUpload(indict):
        yield indict[post.userid]

def UpdatePostData(userid,userdict,postver):
    """Update post columns for userid"""
    
    postid = postver['post_id']
    dirty = 0
    if IsParentChange(postver):
        DebugPrint("Parent Change")
        dirty = 1
        userdict[userid][1] += 1
    if IsRatingChange(postver):
        DebugPrint("Rating Change")
        dirty = 1
        userdict[userid][2] += 1
    if IsSourceChange(postver):
        DebugPrint("Source")
        dirty = 1
        userdict[userid][3] += 1
    
    tagtypes = tags.CountTags(postver['added_tags'])
    userdict[userid][4] += tagtypes[0]                        #general
    userdict[userid][5] += tagtypes[4]                        #character
    userdict[userid][6] += tagtypes[3]                        #copyright
    userdict[userid][7] += tagtypes[1]                        #artist
    userdict[userid][8] += len(tags.RemoveInvalidTags(postver['obsolete_added_tags'].split()))
    if any(tagtypes):
        DebugPrint("Tag Add")
        dirty = 1
    
    tagtypes = tags.CountTags(postver['removed_tags'])
    userdict[userid][9] += tagtypes[0]                        #general
    userdict[userid][10] += tagtypes[4]                        #character
    userdict[userid][11] += tagtypes[3]                        #copyright
    userdict[userid][12] += tagtypes[1]                        #artist
    userdict[userid][13] += len(tags.RemoveInvalidTags(postver['obsolete_removed_tags'].split()))
    if any(tagtypes):
        DebugPrint("Tag Remove")
        dirty = 1
    
    if dirty == 0:
        DebugPrint("Other")
        userdict[userid][14] += 1

def PostTransform(userdict,**kwargs):
    datacolumns = {}
    for key in userdict:
        datacolumns[key] = userdict[key][:4] + [str(userdict[key][4])+', ('+str(userdict[key][9])+')'] +\
                    [str(userdict[key][5])+', ('+str(userdict[key][10])+')'] + [str(userdict[key][6])+', ('+str(userdict[key][11])+')'] +\
                    [str(userdict[key][7])+', ('+str(userdict[key][12])+')'] + [str(userdict[key][8])+', ('+str(userdict[key][13])+')'] +\
                    [userdict[key][14]]
    return datacolumns

#Report variables
reportname = 'edit'
dtexttitle = "Post Edit Details"
footertext = "post changes"
dtextheaders = ['Username','Total','Par','Rate','Src','Gen Tag','Char Tag','Copy Tag','Art Tag','Obs Tag','Other']
csvheaders = ['userid','total','parent','rating','source','+gentag','+chartag','+copytag','+arttag','+obsoletetag','-gentag','-chartag','-copytag','-arttag','-obsoletetag','other']
transformfuncs = [GetTotalColumn,None,None,None,None,None,None,None,None,None]
dtexttransform = PostTransform
extracolumns = 14
tablecutoffs = [[500]]

reporthandler = UserReportData.InitializeUserReportData(UpdatePostData,PostIterator)
