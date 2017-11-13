#REPORT/CONTROLLERS/POST/TRANSLATE.PY

#MODULE IMPORTS
from ...logical.users import UserReportData

#Functions

def UpdateTranslateData(userid,userdict,postver):
    """Update translate columns for user ID"""
    
    taglist = postver['added_tags']
    addtranslated = 1 if 'translated' in taglist else 0
    addcheck = 1 if 'check_translation' in taglist else 0
    addpartial = 1 if 'partially_translated' in taglist else 0
    addcommentary = 1 if 'commentary' in taglist else 0
    addcheckcomm = 1 if 'check_commentary' in taglist else 0
    
    taglist = postver['removed_tags']
    subtranslated = 1 if 'translated' in taglist else 0
    subcheck = 1 if 'check_translation' in taglist else 0
    subpartial = 1 if 'partially_translated' in taglist else 0
    subtransreq = 1 if 'translation_request' in taglist else 0
    subcommentary = 1 if 'commentary' in taglist else 0
    subcheckcomm = 1 if 'check_commentary' in taglist else 0
    subcommreq = 1 if 'commentary_request' in taglist else 0
    
    total = \
        addtranslated + subtranslated + addcheck + subcheck + addpartial + subpartial + subtransreq +\
        addcommentary + subcommentary + addcheckcomm + subcheckcomm + subcommreq
    
    if total == 0:
        return 1
    
    userdict[userid][0] += total - 1        #Subtract the 1 added by ReportData class
    userdict[userid][1] += addtranslated
    userdict[userid][2] += subtranslated
    userdict[userid][3] += addcheck
    userdict[userid][4] += subcheck
    userdict[userid][5] += addpartial
    userdict[userid][6] += subpartial
    userdict[userid][7] += subtransreq
    userdict[userid][8] += addcommentary
    userdict[userid][9] += subcommentary
    userdict[userid][10] += addcheckcomm
    userdict[userid][11] += subcheckcomm
    userdict[userid][12] += subcommreq

def TranslateTransform(userdict,**kwargs):
    datacolumns = {}
    for user in userdict:
        datacolumns[user] = \
            [userdict[user][0],"%d, (%d)" % (userdict[user][1],userdict[user][2]),"%d, (%d)" % (userdict[user][3],userdict[user][4]),
            "%d, (%d)" % (userdict[user][5],userdict[user][6]),"(%d)" % userdict[user][7],"%d, (%d)" % (userdict[user][8],userdict[user][9]),\
            "%d, (%d)" % (userdict[user][10],userdict[user][11]),"(%d)" % userdict[user][12]]
    return datacolumns

reportname = 'translate'
dtexttitle = "Translate Details"
footertext = "translation tags"
dtextheaders = ['username','Total','Trans','Check','Part','Trans Req','Comm','Check Comm','Comm Req']
csvheaders = ['userid','total','+translated','-translated','+check','-check','+partial','-partial','-transrequest','+commentary','-commentary','+checkcomm','-checkcomm','-commrequest']
transformfuncs = [None,None,None,None,None,None,None,None]
dtexttransform = TranslateTransform
extracolumns = 12
tablecutoffs = [[100]]

reporthandler = UserReportData.InitializeUserReportData(UpdateTranslateData)
