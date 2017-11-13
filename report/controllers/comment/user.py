#REPORT/CONTROLLERS/COMMENT/USER.PY

#LOCAL IMPORTS
from danbooru import GetSearchUrl

#MODULE IMPORTS
from ...logical.common import GetTotalColumn,GetIDColumn
from ...logical.users import UserReportData
from .. import comment

#Functions

def BumpColumn(userdict,column,controller,userid,**kwargs):
    return GetIDColumn([controller,userid],userdict,column,addonlist=(comment.urladds+[GetSearchUrl('do_not_bump_post','false')]))

#Report variables
reportname = 'user'
dtexttitle = "Comment Details"
dtextheaders = ['Username','Total','Bump','Update','#Pos','#Neg','Sum Score','Delete']
transformfuncs = [GetTotalColumn,BumpColumn,None,None,None,None,None]
csvheaders = ['userid','total','bump','update','pos_count','neg_count','cum_score','delete']
extracolumns = 6
tablecutoffs = [[100]]

reporthandler = UserReportData.InitializeUserReportData(comment.UpdateCommentData)
