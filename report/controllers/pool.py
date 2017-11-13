#REPORT/CONTROLLERS/POOL.PY

#LOCAL IMPORTS
from danbooru import GetPageUrl,GetSearchUrl,IDPageLoop
from misc import DebugPrint,IsAddItem,IsRemoveItem,GetAddItem,GetRemoveItem,IsOrderChange

#MODULE IMPORTS
from ..logical.reportcontroller import ReportController
from ..logical.users import UserReportData
from ..logical.common import GetTotalColumn,GetCreateColumn

#Functions

def UpdatePoolData(userid,userdict,currversiondata,priorversiondata):
    dirty = 0
    
    if len(priorversiondata)==0:
        DebugPrint("Create")
        userdict[userid][1] += 1
        return
    
    priorversiondata = priorversiondata.pop()
    
    postpoollist = currversiondata['post_ids']
    prepoollist = priorversiondata['post_ids'] #page crossing will cause failure here
    
    if currversiondata['name_changed']:
        DebugPrint("Name change")
        dirty = 1
        userdict[userid][2] += 1
    if currversiondata['description_changed']:
        DebugPrint("Description change")
        dirty = 1
        userdict[userid][3] += 1
    if IsAddItem(prepoollist,postpoollist):
        DebugPrint("Add post")
        dirty = 1
        userdict[userid][4] += 1
        
        obsolete = GetObsoleteAdd(currversiondata,GetAddItem(prepoollist,postpoollist))
        if obsolete > 0:
            DebugPrint("Obsolete Add")
            userdict[userid][5] += 1
    if IsRemoveItem(prepoollist,postpoollist):
        DebugPrint("Remove post")
        dirty = 1
        userdict[userid][6] += 1
        
        obsolete = GetObsoleteRemove(currversiondata,GetRemoveItem(prepoollist,postpoollist))
        if obsolete > 0:
            DebugPrint("Obsolete Remove")
            userdict[userid][7] += obsolete
    if IsOrderChange(prepoollist,postpoollist):
        DebugPrint("Order change")
        dirty = 1
        userdict[userid][8] += 1
    if currversiondata['is_active'] != priorversiondata['is_active']:
        DebugPrint("Active change")
        dirty = 1
        userdict[userid][9] += 1
    if dirty == 0:
        DebugPrint("Other")
        userdict[userid][10] += 1

def GetObsoleteAdd(currversion,postlist):
    startid = [GetPageUrl(currversion['id'],above=True)]
    urladds = [GetSearchUrl('pool_id',currversion['pool_id'])]
    inputdict = {'postlist':[postlist],'obsolete':[0]}
    IDPageLoop('pool_versions',100,GetObsoleteAddIterator,urladds,inputdict,startid,reverselist=True)
    return inputdict['obsolete'][0]

def GetObsoleteAddIterator(poolver,postlist,obsolete):
    poolidlist = poolver['post_ids']
    templist=postlist[0]
    for i in reversed(range(0,len(postlist[0]))):
        if postlist[0][i] not in poolidlist:
            obsolete[0] += 1
            templist.pop(i)
    postlist[0] = templist
    if len(postlist[0]) == 0:
        return -1
    return 0

def GetObsoleteRemove(currversion,postlist):
    startid = [GetPageUrl(currversion['id'],above=True)]
    urladds = [GetSearchUrl('pool_id',currversion['pool_id'])]
    inputdict = {'postlist':[postlist],'obsolete':[0]}
    IDPageLoop('pool_versions',100,GetObsoleteRemoveIterator,urladds,inputdict,startid,reverselist=True)
    return inputdict['obsolete'][0]

def GetObsoleteRemoveIterator(poolver,postlist,obsolete):
    poolidlist = poolver['post_ids']
    templist=postlist[0]
    for i in reversed(range(0,len(postlist[0]))):
        if postlist[0][i] in poolidlist:
            obsolete[0] += 1
            templist.pop(i)
    postlist[0] = templist
    if len(postlist[0]) == 0:
        return -1
    return 0

def pooltransform(userdict,**kwargs):
    datacolumns = {}
    for key in userdict:
        datacolumns[key] = userdict[key][:4] + [str(userdict[key][4])+', ('+str(userdict[key][6])+')'] + [str(userdict[key][5])+', ('+str(userdict[key][7])+')'] +\
                            userdict[key][8:]
    return datacolumns

#Report variables
reportname = 'pool'
dtexttitle = "Pool Details"
dtextheaders = ['Username','Total','Create','Name','Descr','Add/ Rem','Obs Add/ Rem','Order','Active','Other']
csvheaders = ['total','name','descr changed','create','add','remove','obsolete add','obsolete remove','order','active','other']
transformfuncs = [GetTotalColumn,GetCreateColumn,None,None,None,None,None,None,None]
dtexttransform = pooltransform
extracolumns = 10
tablecutoffs = [[40]]

reporthandler = UserReportData.InitializeUserReportData(UpdatePoolData)

#Controller variables
startvalue = 0
querylimit = 10
versioned = True
timestamp = 'updated_at'
userid = 'updater_id'
controller = 'pool_versions'
createuserid = 'creator_id'
createcontroller = 'pools'
lookupid = 'pool_id'

typehandler = ReportController.InitializeReportController([reporthandler])
