#REPORT/CONTROLLERS/FORUM_TOPIC.PY

#LOCAL IMPORTS
from misc import DebugPrint

#MODULE IMPORTS
from ..logical.reportcontroller import ReportController
from ..logical.users import UserReportData

#Functions

def UpdateForumTopicData(userid,userdict,typeentry):
    userdict[userid][1] += typeentry['response_count']    #total replies
    DebugPrint("User",userid,"Current replies",userdict[userid][1])

#Report variables
reportname = 'forum_topic'
dtexttitle = "Forum Topic Details"
dtextheaders = ['Username','Total','Replies']
csvheaders = ['userid','total','response_count']
transformfuncs = [None,None]
extracolumns = 1
tablecutoffs = [[4]]

reporthandler = UserReportData.InitializeUserReportData(UpdateForumTopicData)

#Controller variables
startvalue = 1000000
querylimit = 10
versioned = False
timestamp = 'created_at'
userid = 'creator_id'
controller = 'forum_topics'

typehandler = ReportController.InitializeReportController([reporthandler])
