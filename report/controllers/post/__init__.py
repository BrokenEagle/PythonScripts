#REPORT/CONTROLLERS/POST module

#MODULE IMPORTS
from ...logical.reportcontroller import ReportController

#Report variables
reporthandlers = ReportController.GetPackageReportHandlers(__file__,__package__)

#Controller variables
controllername = "post"
startvalue = 0
querylimit = 150
urladds = []
versioned = False
timestamp = 'updated_at'
userid = 'updater_id'
controller = 'post_versions'
createuserid = 'creator_id'
createcontroller = 'posts'
lookupid = 'post_id'

typehandler = ReportController.InitializeReportController(reporthandlers)
