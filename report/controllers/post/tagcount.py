#REPORT/CONTROLLERS/POST/TAGCOUNT.py

#PYTHON IMPORTS
from collections import Counter

#LOCAL IMPORTS
from danbooru import IsUpload,IsTagAdd,IsTagRemove,MetatagExists

#MODULE IMPORTS
from ...logical import tags
from ...logical.users import UserReportData

def TagcountIterator(self,indict,option):
    if (option == 'upload' and IsUpload(indict)) or (option == 'post' and (IsTagAdd(indict) or IsTagRemove(indict))):
        yield indict[self.controller.userid]

def PopulateAllTagDicts(userid,userdict,postver):
    PopulateUserTagDict(userid,userdict,postver['added_tags'])
    PopulateUserTagDict(userid,userdict,postver['removed_tags'])

def PopulateUserTagDict(userid,usertagdict,taglist):
    for tag in taglist:
        if MetatagExists(tag):
            continue
        category = tags.TagCategory(tag)
        if userid not in usertagdict: 
            usertagdict[userid]={0:{},1:{},2:{},3:{},4:{},5:{}}
        usertagdict[userid][category][tag] = (usertagdict[userid][category][tag] + 1) if (tag in usertagdict[userid][category]) else 1

#JSON functions
def WritePostJSONFiles(userdict):
    allusertagdict = {}
    for key in subkeys:
        usertagdict = userdict[key]
        yield key + 'user' , CreateUserJSONFile(usertagdict)
        yield key + 'site' , CreateSiteJSONFile(usertagdict)
        allusertagdict = UserReportData.AddJSONDicts(allusertagdict,usertagdict)
    yield 'alluser' , CreateUserJSONFile(allusertagdict)
    yield 'allsite' , CreateSiteJSONFile(usertagdict)

jsontagtypedict = {0:'gentags',4:'chartags',3:'copytags',1:'arttags',2:'emptytags',5:'metatags'}
def CreateUserJSONFile(usertagdict):
    usertags = []
    for user in usertagdict:
        useritem = {'id':user}
        for category in usertagdict[user]:
            useritem[jsontagtypedict[category]] = usertagdict[user][category]
        usertags += [useritem]
    return usertags

def CreateSiteJSONFile(usertagdict):
    sitetags = {'gentags':{},'arttags':{},'emptytags':{},'copytags':{},'chartags':{},'metatags':{}}
    for user in usertagdict:
        for category in usertagdict[user]:
            for tag in usertagdict[user][category]:
                sitetags[jsontagtypedict[category]][tag] = (sitetags[jsontagtypedict[category]][tag] + usertagdict[user][category][tag]) if (tag in sitetags[jsontagtypedict[category]]) else (usertagdict[user][category][tag])
    return sitetags

#Dtext functions
def CreateTagcountTable(userdict,option):
    usertagdict = userdict[option]
    usertagtotals = {}
    alltags = {}
    for user in usertagdict:
        usertagtotals[user] = 0
        alltags[user] = Counter()
        for category in usertagdict[user]:
            alltags[user] += Counter(usertagdict[user][category])
            for tag in usertagdict[user][category]:
                usertagtotals[user] += usertagdict[user][category][tag]
    
    outputdict = {}
    for user in alltags:
        tempstr = ""
        for tagitem in alltags[user].most_common(10):
            tempstr += "([[%s]],%d) " % tagitem
        outputdict[user] = [usertagtotals[user],tempstr]
    
    return outputdict

reportname = 'tagcount'
dtexttitle = "Tag Count Details"
footertext = 'tag changes'
dtextheaders = ['Username','Total','Tags']
transformfuncs = [None,None]
maketable = CreateTagcountTable
csvheaders = []
extracolumns = 0
tablecutoffs = [[1000,5000]] #1000
reversecolumns = [[True,True]]
tableoptions = ['post','upload']
subkeys = ['post','upload']
reporttype = 'json'
jsoniterator = WritePostJSONFiles

reporthandler = UserReportData.InitializeUserReportData(PopulateAllTagDicts,iterator=TagcountIterator)
