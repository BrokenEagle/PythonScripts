#DANBOORU.PY

#Include functions related to Danbooru here

#PYTHON IMPORTS
import re
import time
from datetime import datetime
from functools import reduce
import argparse
import urllib.parse
import requests
import iso8601

#LOCAL IMPORTS
from misc import DebugPrint,DebugPrintInput,AbortRetryFail,DownloadFile,BlankFunction,\
                PrintChar,RemoveDuplicates,SafePrint
from myglobal import username,apikey,workingdirectory,imagefilepath,booru_domain

#LOCAL GLOBALS

wikilinkregex = re.compile(r'\[\[([^\|\]]+)\|?[^\]]*\]\]')
tagsearchregex = re.compile(r'{{([^}]+)}}')
textileregex1 = re.compile(r'"([^"]+)":\[([^\]]+)\]')
textileregex2 = re.compile(r'"([^"]+)":([^\[]\S+)')
dateregex = re.compile(r"""^([\d]{4}-[\d]{2}-[\d]{2})?        #Date1
                            (?:\.\.)?                        #Non-capturing group for ..
                            (?(1)(?<=\.\.))                    #If Date1 exists, ensure .. exists
                            ([\d]{4}-[\d]{2}-[\d]{2})?$        #Date2""",re.X)
idregex = re.compile(r'^(\d+)?(?:\.\.)?(\d+)?$')
ageregex = re.compile(r"""^([\d]+(?:s|m[io]|h|d|w|y))?        #Age1
                            (?:\.\.)?                        #Non-capturing group for ..
                            (?(1)(?<=\.\.))                    #If Age1 exists, ensure .. exists
                            ([\d]+(?:s|m[io]|h|d|w|y))?$    #Age2""",re.X)
agetypedict = {'s':1,'mi':60,'h':60*60,'d':60*60*24,'w':60*60*24*7,'mo':60*60*24*30,'y':60*60*24*365}

#All of the tags beyond *_request tags
disregardtags = ['tagme','commentary','check_commentary','translated','partially_translated','check_translation','annotated','partially_annotated','check_my_note','check_pixiv_source']

#For building Danbooru URL's and methods on the fly based on the operation type
#Only list, create, show, update, delete, revert, undo and count have been tested
danbooru_ops = {'list':('.json','GET'),'create':('.json','POST'),'show':('/%d.json','GET'),'update':('/%d.json','PUT'),'delete':('/%d.json','DELETE'),'revert':('/%d/revert.json','PUT'),'copy_notes':('/%d/copy_notes.json','PUT'),'banned':('banned.json','GET'),'undelete':('/%d/undelete.json','POST'),'undo':('/%d/undo.json','PUT'),'create_or_update':('/create_or_update.json','PUT'),'count':('counts/posts.json','GET')}
danbooru_methods = {'GET':requests.get,'POST':requests.post,'PUT':requests.put,'DELETE':requests.delete}

#CLASSES

class DanbooruError(Exception):
    """Exception raised for errors with Danbooru.
    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        self.message = message

#EXTERNAL FUNCTIONS

def SubmitRequest(opname,typename,id = None,urladdons = '',senddata = None):
    """Send an API request to Danbooru. The following operations require different positional arguments:
    list: urladdons; show: id; create: senddata; update: id, senddata; delete: id; count: urladdons
    
    Opname and typename are passed in as strings.
    Ex: SubmitRequest('show','posts',id=1234567)
    """
    retry = 0
    tmr_retry = 0
    urlsubmit = GetDanbooruUrl(opname,typename)
    if id != None:
        try:
            urlsubmit = urlsubmit % id
        except TypeError:
            print("Bad arguments! The opname %s does not take an ID argument." % opname)
            return -1
    if urladdons != '':
        urlsubmit = urlsubmit + '?' + urladdons
    httpmethod = danbooru_ops[opname][1]
    connection_retries = server_errors = 0
    while True:
        #Failures occur most often in two places. The first is communicating with Danbooru
        if connection_retries > 2:
            raise DanbooruError("Too many connection errors")
        DebugPrintInput(repr(urlsubmit),repr(senddata),repr(httpmethod))
        try:
            danbooruresp = danbooru_methods[httpmethod](urlsubmit,data=senddata,auth=(username,apikey),headers={'Content-Type':'application/x-www-form-urlencoded'})
        except requests.exceptions.ReadTimeout:
            print("\nSubmitRequest timed out!")
            continue
        except requests.exceptions.ConnectionError:
            print("\nSubmitRequest Connection error! Sleeping 30 seconds...")
            time.sleep(30)
            connection_retries +=1
            continue
        DebugPrint(repr(danbooruresp.text),safe=True)
        DebugPrintInput(danbooruresp.status_code,danbooruresp.reason)
        if danbooruresp.status_code not in [200,201,204]:
            if danbooruresp.status_code in [404,422]:
                return -1
            if danbooruresp.status_code == 429:
                print("\nThrottled!")
                time.sleep(10)
                continue
            elif danbooruresp.status_code >= 500 and danbooruresp.status_code < 600:
                if server_errors > 2:
                    return -2
                print("\nServer error! Sleeping 30 seconds...")
                time.sleep(30)
                server_errors += 1
                continue
            else:
                print("\nServer error!",danbooruresp.status_code,danbooruresp.reason)
                SafePrint(urlsubmit,senddata,httpmethod)
                return -3
        break
    DebugPrint("Before Eval")
    try: 
        data = danbooruresp.json()
    except:
        data = None
    DebugPrint("After Eval")
    return data

def GetCurrFilePath(postdict,size="medium",directory=""):
    """Get filepath for storing server different sized files on local system.
    Input is a post dictionary obtained from Danbooru with either 'list' or 'show'.
    """
    if size == "small":
        return workingdirectory + imagefilepath + directory + postdict["md5"] + '.jpg'
    if size == "medium":
        fileext = postdict["large_file_url"][postdict["large_file_url"].rfind('.'):]
        return workingdirectory + imagefilepath + directory + postdict["md5"] + fileext
    if size == "large":
        return workingdirectory + imagefilepath + directory + postdict["md5"] + '.' + postdict["file_ext"]

def GetServFilePath(postdict,size="medium"):
    """Get serverpath for different sized files
    Input is a post dictionary obtained from Danbooru with either 'list' or 'show'.
    """
    if size=="small":
        return booru_domain + postdict["preview_file_url"]
    if size=="medium":
        return booru_domain + postdict["large_file_url"]
    if size=="large":
        return booru_domain + postdict["file_url"]

def DownloadPostImage(postdict,size="medium",directory=""):
    """Download a post image from Danbooru"""
    localfilepath = GetCurrFilePath(postdict,size,directory)
    serverfilepath = GetServFilePath(postdict,size)
    DebugPrintInput(localfilepath,serverfilepath)
    return DownloadFile(localfilepath,serverfilepath)

def GetPostCount(searchtags):
    """Get the post count given a tag search string"""
    urladd = GetArgUrl2('tags',searchtags)
    return SubmitRequest('count','',urladdons=urladd)['counts']['posts']

def GetTagCount(tagname):
    """Get the post count of all posts that have a tag"""
    urladd = GetSearchUrl('name_matches',tagname)
    taglist = SubmitRequest('list','tags',urladdons=urladd)
    return 0 if taglist == [] else taglist[0]['post_count']

def CheckIQDBUrl(checkurl):
    """Query Danbooru's IQDB server using a URL as the input"""
    return _CheckIQDB(GetArgUrl2('url',checkurl))

def CheckIQDBPost(checkid):
    """Query Danbooru's IQDB server using a post ID as the input"""
    return _CheckIQDB(GetArgUrl2('post_id',checkid))

def _CheckIQDB(urladd):
    IQDBdata = SubmitRequest('list','iqdb_queries',urladdons=urladd)
    if isinstance(IQDBdata,int):
        return IQDBdata
    return list(map(lambda x:x['post']['id'],IQDBdata))

def PostChangeTags(post,tagarray,silence=False):
    """Add a list of tags to a post"""
    addtags = ' '.join(tagarray)
    putdata = EncodeData('post','tag_string',post['tag_string']+' '+addtags)
    SubmitRequest('update','posts',id=post['id'],senddata=putdata)
    if not silence:
        PrintChar('.')

def GetPostDict(postids):
    """Quicker way to get a list of post instances"""
    postiddict = {}
    if len(postids) == 0:
        return postiddict
    for i in range(0,len(postids),100):
        urladdons = JoinArgs(GetArgUrl2('tags','id:'+','.join(map(lambda x:str(x),postids[slice(i,i+100)]))+' status:any'),GetLimitUrl(100))
        postlist = SubmitRequest('list','posts',urladdons=urladdons)
        for post in postlist:
            postiddict[post['id']] = post
        PrintChar('.')
    return postiddict

#LOOP CONSTRUCTS

def IDPageLoop(type,limit,iteration,addonlist=[],inputs={},firstloop=[],postprocess=BlankFunction,reverselist=False):
    """Standard loop using 'ID' pages to iterate
    'firstloop' is for types that require the pageID to sort properly, e.g. forum topics,
    or for continuing from the last saved location, such as in the case of a crash
    """
    currentid = -1
    urladd = JoinArgs(GetLimitUrl(limit),*firstloop,*addonlist)
    while True:
        typelist = SubmitRequest('list',type,urladdons=urladd)
        if isinstance(typelist,int):
            return typelist
        if len(typelist) == 0:
            postprocess(typelist,**inputs)
            return currentid
        if reverselist:
            iteratelist = reversed(typelist)
        else:
            iteratelist = typelist
        for item in iteratelist:
            currentid = item['id']
            if iteration(item,**inputs) < 0:
                postprocess(typelist,**inputs)
                return currentid
        if len(typelist) < limit:
            postprocess(typelist,**inputs)
            return currentid
        postprocess(typelist,**inputs)
        if reverselist:
            urladd = JoinArgs(GetLimitUrl(limit),GetPageUrl(currentid,above=True),*addonlist)
        else:
            urladd = JoinArgs(GetLimitUrl(limit),GetPageUrl(currentid),*addonlist)
        PrintChar(':')

def NumPageLoop(type,limit,iteration,addonlist=[],inputs={},page=1,postprocess=BlankFunction):
    """Standard loop using page numbers to iterate"""
    idseen = []
    while True:
        urladd = JoinArgs(GetLimitUrl(limit),GetPageNumUrl(page),*addonlist)
        typelist = SubmitRequest('list',type,urladdons=urladd)
        if isinstance(typelist,int):
            return typelist
        if len(typelist) == 0:
            postprocess(typelist,**inputs)
            return page
        idlist = []
        for item in typelist:
            if item['id'] in idseen:
                continue
            idlist += [item['id']]
            if iteration(item,**inputs) < 0:
                postprocess(typelist,**inputs)
                return page
        postprocess(typelist,**inputs)
        idseen = idlist; page += 1
        PrintChar(':')

def IDListLoop(type,limit,idlist,iteration,inputs={},postprocess=BlankFunction):
    """Standard loop iterating through a list of IDs"""
    counter = 1
    for num in idlist.copy():
        item = SubmitRequest('show',type,id=num)
        if isinstance(item,int) or len(item) == 0:
            print("%s #%d not found!" % (type.title(),num))
            idlist.remove(num)
            postprocess([],**inputs)
            continue
        ret = iteration(item,**inputs)
        if ret < 0:
            postprocess([],**inputs)
            return
        elif ret > 0:
            continue
        if (counter % limit) == 0:
            postprocess([],**inputs)
            PrintChar(':')
        counter += 1
    postprocess([],**inputs)

#LOOP HELPERS

def FormatStartID(startid,above=False):
    return [GetPageUrl(startid,above)] if (startid != 0 or above==True) else []

#LOOP ITERABLES

def GetTypeDict(type,idlist,limit=1):
    """Get a list of type instances"""
    
    typeiddict = {}
    IDListLoop(type,limit,idlist,GetTypeIteration,inputs={'typeiddict':typeiddict})
    return typeiddict

def GetTypeIteration(type,typeiddict):
    typeiddict[type['id']] = type
    return 0

def GetContributorList():
    """Get the current list of contributors"""
    
    contributorlist = []
    IDPageLoop('users',100,GetContributorListIteration,addonlist=[GetSearchUrl('can_upload_free','true')],inputs={'contributorlist':contributorlist})
    return contributorlist

def GetContributorIteration(user,contributorlist):
    contributorlist += [user['id']]
    return 0

def DownloadPostImageIteration(post,related=False,size="medium",directory="",lastid=0):
    """To be called with loop construct to download images"""
    if lastid >= post['id']:
        return -1
    
    #Download post image from server to local
    DownloadPostImage(post,size,directory)
    
    #Are we downloading all child/parent posts?
    if related and (HasChild(post) or HasParent(post)):
        PrintChar('(')
        DownloadRelatedPostImages(post,[post['id']],size,directory)
        PrintChar(')')
    
    #Print some feedback
    PrintChar('.')
    return 0

def DownloadRelatedPostImages(post,alreadydownloaded,size,directory):
    """Recursively download all child and parent images"""
    #Download any parent posts
    if HasParent(post) and (post['parent_id'] not in alreadydownloaded):
        parent = SubmitRequest('show','posts',id=post['parent_id'])
        DownloadPostImage(parent,size,directory)
        PrintChar('.')
        alreadydownloaded += [parent['id']]
        alreadydownloaded = DownloadRelatedPostImages(parent,alreadydownloaded,size,directory)
    #Download any child posts
    if HasChild(post):
        urladd = JoinArgs(GetArgUrl2('tags',"parent:%d" % post['id']))
        childlist = SubmitRequest('list','posts',urladdons=urladd)
        for child in childlist:
            if child['id'] not in alreadydownloaded:
                DownloadPostImage(child,size,directory)
                PrintChar('.')
                alreadydownloaded += [child['id']]
                alreadydownloaded = DownloadRelatedPostImages(child,alreadydownloaded,size,directory)
    return alreadydownloaded

#EXTERNAL HELPER FUNCTIONS

def JoinArgs(*args):
    """Take multiple URL arguments of form "name=val" and concatenate them together"""
    string = ''
    for arg in args:
        if len(arg) > 0:
            string += arg + '&'
    return string[:-1]

def GetArgUrl(typename,keyname,data):
    """Parameters are for URL arguments as such: typename[keyname]=data or typename=data
    E.g. notes[post_id]=1234, would be EncodeData('notes','post_id',1234)
    """
    if keyname == '':
        return urllib.parse.urlencode(eval("{'%s':%s}" % (typename,repr(data))))
    else:
        return urllib.parse.urlencode(eval("{'%s[%s]':%s}" % (typename,keyname,repr(data))))

def GetArgUrl2(typename,data):
    return GetArgUrl(typename,'',data)

def GetArgUrl3(typename,keyname,data):
    return GetArgUrl(typename,keyname,data)

def GetPageUrl(id,above=False):
    """Get the page argument for all ID's below the parameter 'id'"""
    if above:
        return GetArgUrl2('page','a'+str(id))
    else:
        return GetArgUrl2('page','b'+str(id))

def GetLimitUrl(limit):
    return GetArgUrl2('limit',limit)

def GetPageNumUrl(pagenum):
    return GetArgUrl2('page',pagenum)

def GetSearchUrl(keyname,data):
    return GetArgUrl3('search',keyname,data)

def EncodeData(typename,keyname,data):
    """Encode data for the senddata parameter of SubmitRequest."""
    return (GetArgUrl(typename,keyname,data)).encode('UTF')

def JoinData(*args):
    """Take multiple POST arguments of form "name=val" and concatenate them together"""
    bytes = b''
    for arg in args:
        bytes += arg + b'&'
    return bytes[:-1]

def ProcessTimestamp(timestring):
    """Get seconds from the Epoch for Danbooru's timestamps"""
    return iso8601.parse_date(timestring).timestamp()

def CreateTimestamp(epochtime):
    """Convert seconds from the Epoch to Danbooru's timestamps"""
    return time.strftime("%Y-%m-%dT%H:%M:%S.",time.gmtime(epochtime)) + str(int((epochtime % 1) * 1000)) + 'Z'

def DateStringInput(string):
    match = dateregex.match(string)
    if match == None:
        raise argparse.ArgumentTypeError("Date input must be of format 'YYYY-MM-DD'")
    if (match.group(1) == None) and (match.group(2) == None):
        raise argparse.ArgumentTypeError("At least one date must be included")
    if (match.group(1) != None) and (match.group(2) != None):
        if time.strptime(match.group(1),'%Y-%m-%d') > time.strptime(match.group(2),'%Y-%m-%d'):
            raise argparse.ArgumentTypeError("1st date must be before 2nd date")
    return match.group()

def TimestampInput(string):
    try:
        stringlist = string.split('..')
        timelist = [0,0]
        for i in range(0,len(stringlist)):
            timelist[i] = ProcessTimestamp(stringlist[i])
    except:
        raise argparse.ArgumentTypeError("Invalid timestamp input'")
    return timelist

def IDStringInput(string):
    match = idregex.match(string)
    if match == None:
        raise argparse.ArgumentTypeError("ID input must be of format 'Start#..End#'")
    start = int(match.group(1))
    end = int(match.group(2))
    if start > end:
        raise argparse.ArgumentTypeError("Start ID must be less than End ID")
    return match.group()

def AgeStringInput(string):
    match = ageregex.match(string)
    if match == None:
        raise argparse.ArgumentTypeError("Age input must be of format 'Start..End'\nValid qualifiers are 's','mi','h','d','w','mo','y'")
    if (match.group(1) == None) and (match.group(2) == None):
        raise argparse.ArgumentTypeError("At least one age specifier must be used")
    if (match.group(1) != None) and (match.group(2) != None):
        if (int(re.search(r'[\d]+',match.group(1)).group()) * agetypedict[re.search(r'[^\d]+',match.group(1)).group()]) > (int(re.search(r'[\d]+',match.group(2)).group()) * agetypedict[re.search(r'[^\d]+',match.group(2)).group()]):
            raise argparse.ArgumentTypeError("Start specifier must be less than end specifier")
    return match.group()

#POST SPECIFIC FUNCTIONS

def IsUpload(postver):
    return (len(postver['unchanged_tags']) == 0) and (len(postver['added_tags']) > 0)

def HasChild(postver):
    return postver['has_visible_children']

def HasParent(postver):
    return (postver['parent_id'] != None)

def HasRelated(postver):
    return (HasParent(postver) or HasChild(postver))

def IsTagAdd(postver):
    if (len(postver['unchanged_tags']) > 0) and (len(postver['added_tags']) > 0):
        return (len(postver['added_tags'])) > MetatagCount(' '.join(postver['added_tags']))
    return False

def IsTagRemove(postver):
    if (len(postver['unchanged_tags']) > 0) and (len(postver['removed_tags']) > 0):
        return (len(postver['removed_tags'])) > MetatagCount(' '.join(postver['removed_tags']))
    return False

def MetatagExists(string):
    return (ParentExists(string) or SourceExists(string) or RatingExists(string))

def ParentExists(string):
    return ((string.find("parent:")) >= 0)

def SourceExists(string):
    return ((string.find("source:")) >= 0)

def RatingExists(string):
    return ((string.find("rating:")) >= 0)

def IsParentChange(postver):
    return (ParentExists(' '.join(postver['added_tags'])) or ParentExists(' '.join(postver['removed_tags']))) and not IsUpload(postver)

def IsRatingChange(postver):
    return RatingExists(' '.join(postver['added_tags'])) and RatingExists(' '.join(postver['removed_tags']))

def IsSourceChange(postver):
    return (SourceExists(' '.join(postver['added_tags'])) or SourceExists(' '.join(postver['removed_tags']))) and not IsUpload(postver)

def MetatagCount(string):
    return ParentCount(string) + SourceCount(string) + RatingCount(string)

def ParentCount(string):
    return 1 if ParentExists(string) else 0

def RatingCount(string):
    return 1 if RatingExists(string) else 0

def SourceCount(string):
    return 1 if SourceExists(string) else 0

#TAG SPECIFIC FUNCTIONS

def GetTagCategory(tagname,hideempty = "yes"):
    """Query danbooru for the category of a tag"""
    #Send tag query to Danbooru
    urladd = JoinArgs(GetSearchUrl('name',tagname),GetSearchUrl("hide_empty",hideempty))
    taglist = SubmitRequest('list','tags',urladdons = urladd)
    #If the length of the list is one, then we found an exact match
    if len(taglist) == 1:
        return taglist[0]['category']
    #Otherwise the tag doesn't exist or it's empty
    DebugPrint("Empty Tag",tagname)
    #Return a nonexistant tag category enumeration for internal use only
    return 2

def IsDisregardTag(tagname):
    return True if (tagname in disregardtags) or (tagname[-8:]=='_request') else False

#DTEXT HELPER FUNCTIONS

def GetWikiLinks(string):
    return RemoveDuplicates(list(map(lambda x:x.lower().replace(' ','_'),wikilinkregex.findall(string))))

def GetTextileLinks(string):
    return RemoveDuplicates(list(map(lambda x:x[1],textileregex1.findall(string)))+list(map(lambda x:x[1],textileregex2.findall(string))))

def GetTagSearches(string):
    tagsearches = list(map(lambda x:x.split(),tagsearchregex.findall(string)))
    return RemoveDuplicates(reduce(lambda x,y:x+y,tagsearches)) if len(tagsearches) > 0 else []

#INTERNAL HELPER FUNCTIONS

def GetDanbooruUrl(opname,typename):
    """Build Danbooru URL on the fly"""
    return (booru_domain + '/' + typename + danbooru_ops[opname][0])