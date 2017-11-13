#REPORT/CONTROLLERS/COMMENT/TAGS.PY

#PYTHON IMPORTS
from collections import Counter

#LOCAL IMPORTS
from danbooru import MetatagExists,IsDisregardTag
from misc import SetPrecision

#MODULE IMPORTS
from ...logical.reportdata import ReportData
from ...logical.posts import GetPost,GetPostCount
from .. import comment

#Functions

def CategoryIterator(indict,option):
    post = GetPost(indict['post_id'])
    for tag in post['tag_string_'+option].split():
        if MetatagExists(tag) or IsDisregardTag(tag):
            continue
        yield tag

def TagCategoryFilter(indict,option):
    return indict[option]

def TagDtextTransform(indict,starttime,endtime):
    datacolumns = {}
    for tag in indict:
        posts = GetPostCount(tag,starttime,endtime)
        if posts > 0:
            datacolumns[tag] = [SetPrecision(indict[tag][0]/posts,2),posts] + indict[tag]
    return dict(Counter(datacolumns).most_common(10))

def TagColumnTransform(indict,**kwargs):
    datacolumn = {}
    for tag in indict:
        datacolumn[tag] = '[[%s]]' % tag
    return datacolumn

#Report variables
reportname = 'tags'
dtexttitle = "Comment - Top 10 Tags"
dtextheaders = ['Tag Name','Tags/ Post','Posts','Comments','Bump','Update','#Pos','#Neg','Sum Score','Delete']
transformfuncs = [None,None,None,None,None,None,None,None,None]
dtexttransform = TagDtextTransform
maketable = TagCategoryFilter
csvheaders = ['tagname','total','bump','update','pos_count','neg_count','cum_score','delete']
extracolumns = 6
tablecutoffs = [[25,25,25,25]] #50
reversecolumns = [[True,True,True,True]]
tableoptions = ['copyright','character','artist','general']
subkeys = ['copyright','character','artist','general']

reporthandler = ReportData.InitializeReportData(comment.UpdateCommentData,CategoryIterator,TagColumnTransform)

