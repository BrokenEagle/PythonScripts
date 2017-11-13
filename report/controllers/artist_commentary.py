#REPORT/CONTROLLERS/ARTIST_COMMENTARY.PY

#LOCAL IMPORTS
from misc import DebugPrint

#MODULE IMPORTS
from ..logical.reportcontroller import ReportController
from ..logical.users import UserReportData
from ..logical.common import GetTotalColumn,GetCreateColumn

#Functions

def UpdateArtistCommentaryData(userid,userdict,currversiondata,priorversiondata):
    dirty = 0
    
    if len(priorversiondata)==0:
        DebugPrint("Create")
        userdict[userid][1] += 1
        return
    
    priorversiondata = priorversiondata.pop()
    
    if currversiondata['original_title'] != priorversiondata['original_title']:
        DebugPrint("Orig Title")
        dirty = 1
        userdict[userid][2] += 1
    if currversiondata['original_description'] != priorversiondata['original_description']:
        DebugPrint("Orig Descr")
        dirty = 1
        userdict[userid][3] += 1
    if currversiondata['translated_title'] != priorversiondata['translated_title']:
        DebugPrint("Trans Title")
        dirty = 1
        userdict[userid][4] += 1
    if currversiondata['translated_description'] != priorversiondata['translated_description']:
        DebugPrint("Trans Descr")
        dirty = 1
        userdict[userid][5] += 1
    if dirty == 0:
        DebugPrint("Other")
        userdict[userid][6] += 1

#Report variables
reportname = 'artist_commentary'
dtexttitle = "Artist Commentary Details"
dtextheaders = ['Username','Total','Create','Orig Title','Orig Descr','Trans Title','Trans Descr','Other']
csvheaders = ['userid','total','create','orig title','orig descr','trans title','trans descr','other']
transformfuncs = [GetTotalColumn,GetCreateColumn,None,None,None,None,None]
extracolumns = 6
tablecutoffs = [[100]]

reporthandler = UserReportData.InitializeUserReportData(UpdateArtistCommentaryData)

#Controller variables
startvalue = 0
querylimit = 25
versioned = True
timestamp = 'updated_at'
userid = 'updater_id'
controller = 'artist_commentary_versions'
createuserid = 'creator_id'
createcontroller = 'artist_commentaries'
lookupid = 'post_id'

typehandler = ReportController.InitializeReportController([reporthandler])
