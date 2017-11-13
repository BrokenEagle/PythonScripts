#REPORT/CONTROLLERS/NOTE.PY

#LOCAL IMPORTS
from misc import DebugPrint

#MODULE IMPORTS
from ..logical.reportcontroller import ReportController
from ..logical.users import UserReportData
from ..logical.common import GetTotalColumn,GetCreateColumn

#Functions

def UpdateNoteData(userid,userdict,currversiondata,priorversiondata):
    dirty = 0
    
    if len(priorversiondata)==0:
        DebugPrint("Create")
        userdict[userid][1] += 1
        return
    
    priorversiondata = priorversiondata.pop()
    
    if currversiondata['body'] != priorversiondata['body']:
        DebugPrint("Edit note")
        dirty = 1
        userdict[userid][2] += 1
    if (currversiondata['x'] != priorversiondata['x']) or (currversiondata['y'] != priorversiondata['y']):
        DebugPrint("Move note")
        dirty = 1
        userdict[userid][3] += 1
    if (currversiondata['width'] != priorversiondata['width']) or (currversiondata['height'] != priorversiondata['height']):
        DebugPrint("Resize note")
        dirty = 1
        userdict[userid][4] += 1
    if currversiondata['is_active'] != priorversiondata['is_active']:
        DebugPrint("(Un)Delete note")
        dirty = 1
        userdict[userid][5] += 1
    if dirty == 0:
        DebugPrint("Other")
        userdict[userid][6] += 1

#Report variables
reportname = 'note'
dtexttitle = "Note Details"
dtextheaders = ['Username','Total','Create','Body Edit','Moves','Resize','(Un) Delete','Other']
csvheaders = ['userid','total','create','edit','move','resize','(un)delete','other']
transformfuncs = [GetTotalColumn,GetCreateColumn,None,None,None,None,None]
extracolumns = 6
tablecutoffs = [[250]]

reporthandler = UserReportData.InitializeUserReportData(UpdateNoteData)

#Controller variables
startvalue = 0
querylimit = 25
versioned = True
timestamp = 'updated_at'
userid = 'updater_id'
controller = 'note_versions'
createuserid = 'creator_id'
createcontroller = 'notes'
lookupid = 'note_id'

typehandler = ReportController.InitializeReportController([reporthandler])
