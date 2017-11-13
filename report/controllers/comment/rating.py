#REPORT/CONTROLLERS/COMMENT/CATEGORY.PY

#LOCAL IMPORTS
from danbooru import GetArgUrl2,SubmitRequest,MetatagExists,IsDisregardTag,IDPageLoop
from misc import StaticVars,GetDate,SetPrecision,IncDictEntry

#MODULE IMPORTS
from ...logical.reportdata import ReportData
from ...logical.posts import GetPost,GetPostCount,ratingdict
from .. import comment

#Functions

def RatingIterator(indict,option):
    post = GetPost(indict['post_id'])
    yield ratingdict[post['rating']]

def RatingDtextTransform(indict,starttime,endtime):
    datacolumns = {}
    
    for rating in indict:
        posts = GetPostCount('rating:'+rating,starttime,endtime)
        if posts > 0:
            datacolumns[rating] = [SetPrecision(indict[rating][0]/posts,2),posts] + indict[rating]
    return datacolumns

def RatingColumnTransform(indict,**kwargs):
    datacolumn = {}
    for rating in indict:
        datacolumn[rating] = '{{rating:%s}}' % rating
    return datacolumn

reportname = 'rating'
dtexttitle = "Comment - Top 10 Tags - Rating"
dtextheaders = ['Rating','Tags/ Post','Posts','Comments','Bump','Update','#Pos','#Neg','Sum Score','Delete']
transformfuncs = [None,None,None,None,None,None,None,None,None]
dtexttransform = RatingDtextTransform
csvheaders = ['rating','total','bump','update','pos_count','neg_count','cum_score','delete']
extracolumns = 6
tablecutoffs = [[0]] #50

reporthandler = ReportData.InitializeReportData(comment.UpdateCommentData,RatingIterator,RatingColumnTransform)

