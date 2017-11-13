#REPORT/LOGICAL/COMMON.PY

#PYTON IMPORTS
from collections import OrderedDict

#LOCAL IMPORTS
from danbooru import JoinArgs,GetSearchUrl

#Functions

def DefaultDtextTransform(userdict,*args,**kwargs):
    return userdict

def DefaultTransform(userdict,column,**kwargs):
    return dict(map(lambda x:(x[0],x[1][column]),userdict.items()))

def GetIDColumn(controller,userdict,column,addonlist=[]):
    idcolumn = {}
    for user in userdict:
        urllink = "/%s?%s" % (controller[0],JoinArgs(GetSearchUrl(controller[1],user),*addonlist))
        idcolumn[user] = '"%s":[%s]' % (repr(userdict[user][column]),urllink)
    return idcolumn

def GetTotalColumn(userdict,column,controller,userid,addonlist,**kwargs):
    return GetIDColumn([controller,userid],userdict,column,addonlist)

def GetCreateColumn(userdict,column,createcontroller,createuserid,addonlist,**kwargs):
    return GetIDColumn([createcontroller,createuserid],userdict,column,addonlist)

def GetRankColumn(userdict,prioruserdict,sortcolumn,reversecolumn):
    userdict = OrderedDict(sorted(userdict.items(),key=lambda x:x[1][sortcolumn],reverse=reversecolumn))
    prioruserdict = OrderedDict(sorted(prioruserdict.items(),key=lambda x:x[1][sortcolumn],reverse=reversecolumn))
    rankdict = {}
    for id in list(userdict.keys()):
        if id not in prioruserdict:
            rankdict[id] = "N/A"
        else:
            rank = list(prioruserdict.keys()).index(id) - list(userdict.keys()).index(id)
            if rank > 0:
                rankdict[id] = "+%d" % rank
            else:
                rankdict[id] = "%d" % rank
    return rankdict
