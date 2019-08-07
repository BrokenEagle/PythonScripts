#REPORT/CONTROLLERS/ARTIST.PY

#LOCAL IMPORTS
from danbooru import ProcessTimestamp,GetSearchUrl,SubmitRequest,IDPageLoop
from misc import DebugPrint,DebugPrintInput,WithinOneSecond

#MODULE IMPORTS
from ..logical.reportcontroller import ReportController
from ..logical.users import UserReportData
from ..logical.common import GetTotalColumn,GetCreateColumn

#Functions

def UpdateArtistData(userid,userdict,currversiondata,priorversiondata):
    dirty = 0
    
    if len(priorversiondata)==0:
        DebugPrint("Create")
        userdict[userid][1] += 1
        return
    
    priorversiondata = priorversiondata.pop()
    
    if currversiondata['name'] != priorversiondata['name']:
        DebugPrint("Name")
        dirty = 1
        userdict[userid][2] += 1
    if len(set(currversiondata['other_names']).symmetric_difference(priorversiondata['other_names'])):
        DebugPrint("Other Name")
        dirty = 1
        userdict[userid][3] += 1
    if len(set(currversiondata['urls']).symmetric_difference(priorversiondata['urls'])):
        DebugPrint("URL")
        dirty = 1
        userdict[userid][4] += 1
    if currversiondata['group_name'] != priorversiondata['group_name']:
        DebugPrint("Group")
        dirty = 1
        userdict[userid][5] += 1
    if currversiondata['is_active'] != priorversiondata['is_active']:
        DebugPrint("(Un)Delete")
        dirty = 1
        userdict[userid][6] += 1
    
    #Done getting all the information from the version info
    #Now let's search for a corresponding wiki page
    
    urladd = GetSearchUrl('title',currversiondata['name'])
    artistwiki = SubmitRequest('list','wiki_pages',urladdons=urladd)
    
    if len(artistwiki)==1: 
        #Found an exact match; otherwise there is no wiki page
        
        artistwiki = artistwiki.pop()
        if ArtistWikiChange(currversiondata,artistwiki):
            DebugPrintInput("Wiki",userid,artistwiki['id'],currversiondata['artist_id'])
            dirty=1
            userdict[userid][7] += 1
    
    if dirty == 0:
        DebugPrint("Other")
        userdict[userid][8] += 1

def ArtistWikiChange(currversiondata,artistwiki):
    def iterator(wikipagever):
        nonlocal wikiedit
        
        wikivertime = ProcessTimestamp(wikipagever['updated_at'])
        #Is the wiki/artist version timestamps within one second of each other and created by the same user?
        if (WithinOneSecond(artistvertime,wikivertime)) and (artistupdaterid==wikipagever['updater_id']):
            wikiedit = 1
            return -1
        #Are there no more wiki versions to check related to the artist version
        elif wikivertime < artistvertime:
            return -1
        return 0
    
    artistvertime = ProcessTimestamp(currversiondata['updated_at'])
    artistupdaterid = currversiondata['updater_id']
    wikiedit = 0
    
    urladds = [GetSearchUrl('wiki_page_id',artistwiki['id'])]
    IDPageLoop('wiki_page_versions',10,iterator,urladds)
    return wikiedit

#Artist variables
reportname = 'artist'
dtexttitle = "Artist Details"
dtextheaders = ['Username','Total','Create','Name','Other Name','URL','Group','(Un) Delete','Wiki','Other']
csvheaders = ['userid','total','create','name','other_name','url','group','(un)delete','wiki','other']
transformfuncs = [GetTotalColumn,GetCreateColumn,None,None,None,None,None,None,None]
extracolumns = 8
tablecutoffs = [[40]]

reporthandler = UserReportData.InitializeUserReportData(UpdateArtistData)

#Controller variables
startvalue = 0
querylimit = 10
versioned = True
timestamp = 'updated_at'
userid = 'updater_id'
controller = 'artist_versions'
createuserid = 'creator_id'
createcontroller = 'artists'
lookupid = 'artist_id'

typehandler = ReportController.InitializeReportController([reporthandler])
