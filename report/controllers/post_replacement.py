#REPORT/CONTROLLERS/POST_REPLACEMENT.PY

#MODULE IMPORTS
from ..logical.reportcontroller import ReportController
from ..logical.users import UserReportData
from ..logical.common import GetTotalColumn

#Functions

def UpdatePostReplacementData(userid,userdict,typeentry):
    pass

#Report variables
reportname = 'post_replacement'
dtexttitle = "Post Replacement Details"
dtextheaders = ['Username','Total']
csvheaders = ['userid','total']
transformfuncs = [GetTotalColumn]
extracolumns = 0
tablecutoffs = [[10]]

reporthandler = UserReportData.InitializeUserReportData(UpdatePostReplacementData)

#Controller variables
startvalue = 0
querylimit = 10
versioned = False
timestamp = 'created_at'
userid = 'creator_id'
controller = 'post_replacements'

typehandler = ReportController.InitializeReportController([reporthandler])
