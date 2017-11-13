#REPORT/CONTROLLERS/USER_FEEDBACK.PY

#LOCAL IMPORTS
from danbooru import GetSearchUrl
from misc import DebugPrint

#MODULE IMPORTS
from ..logical.reportcontroller import ReportController
from ..logical.users import UserReportData
from ..logical.common import GetTotalColumn,GetIDColumn

#Functions

def UpdateUserFeedbackData(userid,userdict,typeentry):
    if typeentry['category']=='positive':
        DebugPrint("Positive")
        userdict[userid][1] += 1
    elif typeentry['category']=='neutral':
        DebugPrint("Neutral")
        userdict[userid][2] += 1
    elif typeentry['category']=='negative':
        DebugPrint("Negative")
        userdict[userid][3] += 1

def PositiveFeedbackColumn(userdict,column,controller,userid,**kwargs):
    return GetIDColumn([controller,userid],userdict,column,addonlist=[GetSearchUrl('category','positive')])

def NeutralFeedbackColumn(userdict,column,controller,userid,**kwargs):
    return GetIDColumn([controller,userid],userdict,column,addonlist=[GetSearchUrl('category','neutral')])

def NegativeFeedbackColumn(userdict,column,controller,userid,**kwargs):
    return GetIDColumn([controller,userid],userdict,column,addonlist=[GetSearchUrl('category','negative')])

#Report variables
reportname = 'user_feedback'
dtexttitle = "User Feedback Details"
dtextheaders = ['Username','Total','Positive','Neutral','Negative']
csvheaders = ['userid','total','positive','neutral','negative']
transformfuncs = [GetTotalColumn,PositiveFeedbackColumn,NeutralFeedbackColumn,NegativeFeedbackColumn]
extracolumns = 3
tablecutoffs = [[2]]

reporthandler = UserReportData.InitializeUserReportData(UpdateUserFeedbackData)

#Controller variables
startvalue = 0
querylimit = 10
versioned = False
timestamp = 'created_at'
userid = 'creator_id'
controller = 'user_feedbacks'

typehandler = ReportController.InitializeReportController([reporthandler])
