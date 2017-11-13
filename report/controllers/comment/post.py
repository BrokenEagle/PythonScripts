#REPORT/CONTROLLERS/COMMENT/POST.PY

#LOCAL IMPORTS
import implications
from danbooru import GetPostDict
from misc import TitleRoman,SetPrecision,PrintChar

#MODULE IMPORTS
from ...logical.reportdata import ReportData
from .. import comment

#Functions

def PostIDIterator(indict,*args):
    yield indict['post_id']

def PoststringKeyColumn(indict,**kwargs):
    datacolumn = {}
    if len(indict) > 0:
        print("Building post dict...")
        postdict = GetPostDict(list(indict.keys()))
        PrintChar('\n')
        for postid,post in postdict.items():
            copyrightlist = implications.RemoveParents(post['tag_string_copyright'].split())
            pagename = '(' + ', '.join(map(lambda x:TitleRoman(x.replace('_',' ')),copyrightlist)) + ") uploaded by " + post['uploader_name']
            datacolumn[post['id']] = '"%s":[/posts/%s]' % (pagename,post['id'])
    return datacolumn

def PostMakeTable(indict,*args,**kwargs):
    return dict(sorted(indict.items(),key=lambda x:x[1][0],reverse=True)[slice(0,50)])

def PostDtextTransform(indict,*args,**kwargs):
    tempdict = {}
    for postid in indict:
        total = indict[postid][0]
        tempdict[postid] = [total] 
        tempdict[postid] += list(map(lambda x:"%.2f%%" % SetPrecision(100*x/total,2),indict[postid][1:5]))
        tempdict[postid] += [SetPrecision(indict[postid][5]/total,2)] #avg score
        tempdict[postid] += [indict[postid][6]] #deleted
    return tempdict

#Report variables
reportname = 'post'
dtexttitle = "Comment - Top 50 Posts"
dtextheaders = ['Post','Total','Bump','Update','Pos','Neg','Avg Score','Delete']
transformfuncs = [None,None,None,None,None,None,None]
dtexttransform = PostDtextTransform
maketable = PostMakeTable
csvheaders = ['postid','total','bump','update','pos_count','neg_count','cum_score','delete']
extracolumns = 6
tablecutoffs = [[0]] #50

reporthandler = ReportData.InitializeReportData(comment.UpdateCommentData,PostIDIterator,PoststringKeyColumn)
