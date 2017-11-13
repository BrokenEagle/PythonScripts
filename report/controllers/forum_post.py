#REPORT/CONTROLLERS/FORUM_POST.PY

#LOCAL IMPORTS
from danbooru import ProcessTimestamp
from misc import DebugPrint

#MODULE IMPORTS
from ..logical.reportcontroller import ReportController
from ..logical.users import UserReportData
from ..logical.common import GetTotalColumn

#Functions

def UpdateForumPostData(userid,userdict,typeentry):
    if ProcessTimestamp(typeentry['created_at']) != (ProcessTimestamp(typeentry['updated_at'])):
        DebugPrint("Forum update")
        userdict[userid][1] += 1

#Report variables
reportname = 'forum_post'
dtexttitle = "Forum Post Details"
dtextheaders = ['Username','Total','Updates']
csvheaders = ['userid','total','update']
transformfuncs = [GetTotalColumn,None]
extracolumns = 1
tablecutoffs = [[25]]

reporthandler = UserReportData.InitializeUserReportData(UpdateForumPostData)

#Controller variables
startvalue = 0
querylimit = 10
versioned = False
timestamp = 'created_at'
userid = 'creator_id'
controller = 'forum_posts'

typehandler = ReportController.InitializeReportController([reporthandler])
