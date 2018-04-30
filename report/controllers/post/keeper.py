#REPORT/CONTROLLERS/POST/KEEPER.PY

#PYTHON IMPORTS

#LOCAL IMPORTS
from danbooru import IsUpload,SubmitRequest

#MODULE IMPORTS
from ...logical.users import UserReportData
from .. import post

#LOCAL GLOBALS

#Functions

def KeeperIterator(self,indict,option):
    if IsUpload(indict):
        yield indict[post.userid]

def UpdateKeeperData(userid,userdict,postver):
    """Update upload columns for userid"""
    
    keepervalue = GetKeeperData(postid)
    if isinstance(keepervalue,int):
        return 1
    
    keeperid = keepervalue[0]
    
    if userid != keeperid:
        userdict[userid][1] += 1
        if keeperid in userdict:
            userdict[keeperid][2] += 1
        else:
            userdict[keeperid] = [0,0,1]

def GetKeeperData(postid):
    """Get the current keeper ID"""
    
    #Get the lastest post data
    postshow = SubmitRequest('show','posts',id=postid)
    if isinstance(postshow,int):
        return postshow
    
    return [postshow['keeper_data']['uid']]

reportname = 'keeper'
dtexttitle = "Keeper Details"
footertext = "uploads"
dtextheaders = ['Username','Total','Lost','Gotten']
csvheaders = ['userid','total','lost','gotten']
transformfuncs = [None,None]
dtexttransform = None
maketable = None
extracolumns = 2
tablecutoffs = [[50]]

reporthandler = UserReportData.InitializeUserReportData(UpdateKeeperData,KeeperIterator)
