#REPORT/CONTROLLERS/POST/TAGGING.PY

#LOCAL IMPORTS
from danbooru import IsUpload
from misc import DebugPrint,SetPrecision

#MODULE IMPORTS
from ...logical import tags
from ...logical.users import UserReportData
from .. import post

#Functions

def ToptagIterator(self,indict,options):
    if IsUpload(indict):
        yield indict[post.userid]

def UpdateToptagData(userid,userdict,postver):
    """Update requests columns for user ID"""
    
    if not IsUpload(postver):
        DebugPrint("Not upload")
        return 1
    
    tagtypes = tags.CountTags(postver['tags'].split())
    
    userdict[userid][1] += tagtypes[0] + tagtypes[1] + tagtypes[3] + tagtypes[4]


def ToptagTable(userdict,option,*args,**kwargs):
    datacolumns = {}
    for key in userdict:
        datacolumns[key] = [SetPrecision(userdict[key][1]/userdict[key][0],2)] + userdict[key]
    
    if option == 'top':
        reverselist = True
    elif option == 'bottom':
        reverselist = False
    return dict(sorted(datacolumns.items(),key=lambda x:x[1][0],reverse=reverselist)[slice(0,25)])

reportname = 'tagging'
dtexttitle = "Uploader Tagging"
footertext = "uploads"
dtextheaders = ['Username','Tags/Upload','Uploads','Tags']
transformfuncs = [None,None,None]
maketable = ToptagTable
csvheaders = ['userid','uploads','tags']
extracolumns = 1
tablecutoffs = [[0,0]]
cutoffcolumn = (50,0)
reversecolumns = [[True,False]]
tableoptions = ['top','bottom']

reporthandler = UserReportData.InitializeUserReportData(UpdateToptagData,ToptagIterator)
