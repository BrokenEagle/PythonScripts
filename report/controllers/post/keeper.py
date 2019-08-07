#REPORT/CONTROLLERS/POST/KEEPER.PY

#PYTHON IMPORTS
import json

#LOCAL IMPORTS
from danbooru import IsUpload,SubmitRequest

#MODULE IMPORTS
from ...logical.users import UserReportData
from ...logical.posts import GetPost,PreloadPosts
from .. import post

#LOCAL GLOBALS

#Functions

def KeeperIterator(self,indict,option):
    if IsUpload(indict):
        yield indict[post.userid]

def UpdateKeeperData(userid,userdict,postver):
    """Update upload columns for userid"""
    
    '''
    keepervalue = GetKeeperData(postver['post_id'])
    if isinstance(keepervalue,int):
        return 1
    '''
    post = GetPost(postver['post_id'])
    if isinstance(post,int):
        #print("Returned int",postver['post_id'])
        return
    if post == None or post['keeper_data'] == None:
        #print("Returned none",postver['post_id'])
        return
    if isinstance(post['keeper_data'],dict):
        keeperid = post['keeper_data']['uid']
    elif isinstance(post['keeper_data'],str):
        try:
            keeperid = json.loads(post['keeper_data'])['uid']
        except:
            print("Error data check",post)
            exit(0)
    
    if userid != keeperid:
        userdict[userid][1] += 1
        if keeperid in userdict:
            userdict[keeperid][2] += 1
        else:
            userdict[keeperid] = [0,0,1]

'''
def GetKeeperData(postid):
    """Get the current keeper ID"""
    
    #Get the lastest post data
    postshow = SubmitRequest('show','posts',id=postid)
    if isinstance(postshow,int):
        return postshow
    
    return [postshow['keeper_data']['uid']]
'''

def KeeperPreprocess(postverlist):
    postver_postids = list(map(lambda x:x['post_id'],postverlist))
    PreloadPosts(postver_postids)

reportname = 'keeper'
dtexttitle = "Keeper Details"
footertext = "lost/gotten uploads"
dtextheaders = ['Username','Uploads','Lost','Gotten']
csvheaders = ['userid','uploads','lost','gotten']
transformfuncs = [None,None,None]
dtexttransform = None
maketable = None
extracolumns = 2
tablecutoffs = [[5],[5]] #50
sortcolumns = [1,2]
reversecolumns = [[True],[True]]
preprocess = KeeperPreprocess

reporthandler = UserReportData.InitializeUserReportData(UpdateKeeperData,KeeperIterator)
