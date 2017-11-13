#REPORT/CONTROLLERS/WIKI_PAGE.PY

#LOCAL IMPORTS
from danbooru import ProcessTimestamp,GetSearchUrl,SubmitRequest,IDPageLoop
from misc import DebugPrint,DebugPrintInput,WithinOneSecond

#MODULE IMPORTS
from ..logical.reportcontroller import ReportController
from ..logical.users import UserReportData
from ..logical.common import GetTotalColumn,GetCreateColumn

#Functions

def UpdateWikiPageData(userid,userdict,currversiondata,priorversiondata):
    dirty = 0
    
    #First, check to see if the wiki version is a result of an artist edit
    #Wiki page version does not have the category, but the wiki page does
    wikipage=SubmitRequest('show','wiki_pages',id=currversiondata[lookupid])
    #Was this an artist-type wiki page?
    if wikipage['category_name']==1:
        #Was this the result of an artist edit?
        if WikiArtistChange(currversiondata):
            DebugPrintInput("Art Wiki Change",currversiondata[lookupid])
            #Remove the count of this version from the totals
            userdict[userid][0] -= 1 
            return
    
    if len(priorversiondata)==0:
        DebugPrint("Create")
        userdict[userid][1] += 1
        return
    
    priorversiondata = priorversiondata.pop()
    
    if currversiondata['title'] != priorversiondata['title']:
        DebugPrint("Title")
        dirty = 1
        userdict[userid][2] += 1
    if currversiondata['other_names'] != priorversiondata['other_names']:
        DebugPrint("Original names")
        dirty = 1
        userdict[userid][3] += 1
    if currversiondata['body'] != priorversiondata['body']:
        DebugPrint("Body")
        dirty = 1
        userdict[userid][4] += 1
    if currversiondata['is_deleted'] != priorversiondata['is_deleted']:
        DebugPrint("(Un)delete")
        dirty = 1
        userdict[userid][5] += 1
    if currversiondata['is_locked'] != priorversiondata['is_locked']:
        DebugPrint("Lock event")
        dirty = 1
        #userdict[userid][6] += 1
    if dirty == 0:
        DebugPrint("Other change")
        userdict[userid][6] += 1

def WikiArtistChange(currversiondata):
    def iterator(artistver):
        nonlocal artistedit
        
        artistvertime = ProcessTimestamp(artistver['updated_at'])
        #Is the wiki/artist version timestamps within one second of each other and created by the same user?
        if (WithinOneSecond(wikivertime,artistvertime)) and (wikiupdaterid==artistver['updater_id']):
            artistedit = 1
            return -1
        #Are there no more wiki versions to check related to the artist version
        elif artistvertime < wikivertime:
            return -1
        return 0
    
    wikivertime = ProcessTimestamp(currversiondata['updated_at'])
    wikiupdaterid = currversiondata['updater_id']
    artistedit = 0
    
    urladds = [GetSearchUrl('name',currversiondata['title'])]
    IDPageLoop('artist_versions',10,iterator,urladds)
    return artistedit

#Report variables
reportname = 'wiki_page'
dtexttitle = "Wiki Page Details"
dtextheaders = ['Username','Total','Create','Title','Other Name','Body Edit','(Un) Delete','Other']
csvheaders = ['userid','total','create','title','other_names','body','(un)delete','other']
transformfuncs = [GetTotalColumn,GetCreateColumn,None,None,None,None,None]
extracolumns = 6
tablecutoffs = [[25]]

reporthandler = UserReportData.InitializeUserReportData(UpdateWikiPageData)

#Controller variables
startvalue = 0
querylimit = 10
versioned = True
timestamp = 'updated_at'
userid = 'updater_id'
controller = 'wiki_page_versions'
createuserid = 'creator_id'
createcontroller = 'wiki_pages'
lookupid = 'wiki_page_id'

typehandler = ReportController.InitializeReportController([reporthandler])
