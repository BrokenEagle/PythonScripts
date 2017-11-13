#REPORT/CONTROLLERS/COMMENT module

#LOCAL IMPORTS
from danbooru import GetArgUrl2,ProcessTimestamp
from misc import DebugPrint,DebugPrintInput

#MODULE IMPORTS
from ...logical.reportcontroller import ReportController

#Common functions

def UpdateCommentData(key,indict,typeentry):
    if typeentry['do_not_bump_post'] == False:
        DebugPrint("Comment bump")
        indict[key][1] += 1
    if ProcessTimestamp(typeentry['created_at']) != (ProcessTimestamp(typeentry['updated_at'])):
        DebugPrint("Comment update")
        indict[key][2] += 1
    if typeentry['score'] > 0:
        DebugPrint("Positive comm")
        indict[key][3] += 1
    if typeentry['score'] < 0:
        DebugPrint("Negative comm")
        indict[key][4] += 1
    indict[key][5] += typeentry['score']    #cumulative score
    DebugPrintInput("Key",key,"Current score",indict[key][5])
    if typeentry['is_deleted'] == True:
        DebugPrint("Comment delete")
        indict[key][6] += 1

#Report variables
reporthandlers = ReportController.GetPackageReportHandlers(__file__,__package__)

#Controller variables
controllername = 'comment'
startvalue = 0
querylimit = 50
urladds = [GetArgUrl2('group_by','comment')]
versioned = False
timestamp = 'created_at'
userid = 'creator_id'
controller = 'comments'

typehandler = ReportController.InitializeReportController(reporthandlers)

