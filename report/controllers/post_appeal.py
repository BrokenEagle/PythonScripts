#REPORT/CONTROLLERS/POST_REPLACEMENT.PY

#LOCAL IMPORTS
from danbooru import GetSearchUrl
from misc import DebugPrint

#MODULE IMPORTS
from ..logical.reportcontroller import ReportController
from ..logical.users import UserReportData
from ..logical.common import GetTotalColumn,GetIDColumn

#Functions

def UpdatePostAppealData(userid,userdict,typeentry):
    if typeentry['is_resolved']==True:
        DebugPrint("Successful")
        userdict[userid][1] += 1

def ResolvedColumn(userdict,column,controller,userid,**kwargs):
    return GetIDColumn([controller,userid],userdict,column,addonlist=[GetSearchUrl('is_resolved','true')])

#Report variables
reportname = 'post_appeal'
dtexttitle = "Post Appeal Details"
dtextheaders = ['Username','Total','Successful']
csvheaders = ['userid','total','successful']
transformfuncs = [GetTotalColumn,ResolvedColumn]
extracolumns = 1
tablecutoffs = [[2]]

reporthandler = UserReportData.InitializeUserReportData(UpdatePostAppealData)

#Controller variables
startvalue = 0
querylimit = 10
versioned = False
timestamp = 'created_at'
userid = 'creator_id'
controller = 'post_appeals'

typehandler = ReportController.InitializeReportController([reporthandler])
