#REPORT/LOGICAL/USERS.PY

#PYTHON IMPORTS
from types import MethodType

#LOCAL IMPORTS
from misc import GetCallerModule,PrintChar,StaticVars,DebugPrint,MaxStringLength
from danbooru import IDPageLoop,GetTypeDict,GetSearchUrl,PrintChar

#MODULE IMPORTS
from . import reportdata

#Classes

class UserReportData(reportdata.ReportData):
    def __init__(self,*args,iterator):
        super(UserReportData, self).__init__(*args)
        self.iterator = self.UserIterator if iterator == None else MethodType(iterator,self)
        self.keycolumn = GetUserColumn
    
    def UserIterator(self,indict,option,*args):
        yield indict[self.controller.userid]
    
    @classmethod
    def InitializeUserReportData(cls,updatefunc,iterator=None):
        mod = GetCallerModule(2).f_globals
        param = (updatefunc,None,None) + cls.GetParameters(mod)
        return cls(*param,iterator=iterator)

@StaticVars(contributorlist = [])
def GetContributorList():
    def iterator(user,contributorlist):
        contributorlist += [user['id']]
        return 0
    
    if GetContributorList.contributorlist == []:
        print("Building contributor list...")
        IDPageLoop('users',100,iterator,addonlist=[GetSearchUrl('can_upload_free','true')],inputs={'contributorlist':GetContributorList.contributorlist})
        PrintChar('\n')
    return GetContributorList.contributorlist

@StaticVars(useriddict = {})
def GetUserIDDict(useridlist):
    checklist = list(set(useridlist).difference(map(lambda x:x[1]['id'],GetUserIDDict.useriddict.items())))
    DebugPrint("Checklist:",checklist)
    if len(checklist) > 0:
        print("Getting user list...")
        GetUserIDDict.useriddict.update(GetTypeDict('users',checklist))
        PrintChar('\n')
    return GetUserIDDict.useriddict

def GetUserColumn(userdict,**kwargs):
    useriddict = GetUserIDDict(list(userdict.keys()))
    usernames = {}
    for id in useriddict:
        username = MaxStringLength(useriddict[id]['name'],15)
        if (useriddict[id]['level'] >= 32):
            usernames[id] = '"%s":[/users/%d]' % (username,id)
        elif (useriddict[id]['level'] < 32):
            usernames[id] = '[u]"%s":[/users/%d][/u]' % (username,id)
    return usernames
