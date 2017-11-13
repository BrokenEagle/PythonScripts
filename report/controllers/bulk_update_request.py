#REPORT/CONTROLLERS/BULK_UPDATE_REQUEST.PY

#LOCAL IMPORTS
from misc import DebugPrint

#MODULE IMPORTS
from ..logical.reportcontroller import ReportController
from ..logical.users import UserReportData

#Functions

def UpdateBulkUpdateRequestData(userid,userdict,typeentry):
    if typeentry['status']=='approved':
        DebugPrint("Approved")
        userdict[userid][1] += 1
    elif typeentry['status']=='rejected':
        DebugPrint("Rejected")
        userdict[userid][2] += 1

#Report variables
reportname = 'bulk_update_request'
dtexttitle = "Bulk Update Request Details"
dtextheaders = ['Username','Total','Approved','Rejected']
csvheaders = ['userid','total','approved','rejected']
transformfuncs = [None,None,None]
extracolumns = 2
tablecutoffs = [[2]]

reporthandler = UserReportData.InitializeUserReportData(UpdateBulkUpdateRequestData)

#Controller variables
startvalue = 1000000
querylimit = 10
versioned = False
timestamp = 'created_at'
userid = 'user_id'
controller = 'bulk_update_requests'

typehandler = ReportController.InitializeReportController([reporthandler])
