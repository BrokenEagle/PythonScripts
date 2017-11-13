#REPORT/CONTROLLERS/FORUM_TOPIC.PY

#LOCAL IMPORTS
from misc import DebugPrint

#MODULE IMPORTS
from ..logical.reportcontroller import ReportController
from ..logical.users import UserReportData

#Functions

def UpdateTagAliasData(userid,userdict,typeentry):
    if typeentry['status']=='active':
        DebugPrint("Approved")
        userdict[userid][1] += 1

#Report variables
reportname = 'tag_implication'
dtexttitle = "Tag Implication Details"
dtextheaders = ['Username','Total','Approved']
csvheaders = ['userid','total','approved']
transformfuncs = [None,None]
extracolumns = 2
tablecutoffs = [[2]]

reporthandler = UserReportData.InitializeUserReportData(UpdateTagAliasData)

#Controller variables
startvalue = 1000000
querylimit = 10
versioned = False
timestamp = 'created_at'
userid = 'creator_id'
controller = 'tag_implications'

typehandler = ReportController.InitializeReportController([reporthandler])
