#REPORT/LOGICAL/TAGS.PY

#PYTHON IMPORTS
import os
import atexit

#LOCAL IMPORTS
from misc import LoadInitialValues,DebugPrint,FindUnicode,PutGetUnicode,PrintChar,StaticVars
from danbooru import MetatagExists,GetTagCategory
from myglobal import workingdirectory

#LOCAL GLOBALS

tagdictfile = workingdirectory + "tagdict.txt"
tagdict = None
tagtypedict = {'general':0,'character':4,'copyright':3,'artist':1,'nonexist':2,'meta':5}
revtagtypedict = {0:'general',4:'character',3:'copyright',1:'artist',2:'nonexist',5:'meta'}

#Functions

def GetTagDict():
    global tagdict
    
    if tagdict == None:
        PrintChar('\n')
        tagdict = LoadInitialValues(tagdictfile,{})
        
        @atexit.register
        def savetagfile():
            print("Saving",tagdictfile)
            #Try writing to null first so that we don't clobber the actual tag file upon write error
            try:
                PutGetUnicode(os.devnull,'w',tagdict)
            except UnicodeEncodeError:
                print("Error saving",tagdictfile)
                return
            PutGetUnicode(tagdictfile,'w',tagdict)
    
    return tagdict

def CountTags(taglist):
    """Count all the tags for each category"""
    
    tagcount = [0] * 6
    TagCategory.tagmiss = False
    for i in range(0,len(taglist)):
        if MetatagExists(taglist[i]):
            continue
        returntag = TagCategory(taglist[i])
        tagcount[returntag] += 1
    #Print some more feedback
    if TagCategory.tagmiss:
        DebugPrint("T",end="",flush=True)
    return tagcount

@StaticVars(tagmiss = False)
def TagCategory(tagitem):
    tagdict = GetTagDict()
    if tagitem in tagdict:
        return tagdict[tagitem]
    if FindUnicode(tagitem) >= 0:
        return 2
    TagCategory.tagmiss = True
    tagdict[tagitem] = GetTagCategory(tagitem)
    DebugPrint(".",end="",flush=True)
    return tagdict[tagitem]

def RevTagCategory(tagitem):
    return revtagtypedict[TagCategory(tagitem)]

def RemoveInvalidTags(taglist):
    templist = taglist.copy()
    for i in reversed(range(0,len(taglist))):
        if MetatagExists(taglist[i]) or IsDisregardTag(taglist[i]):
            del templist[i]
    return templist

def UpdateTagdictFromPost(post):
    tagdict = GetTagDict()
    for key in tagtypedict:
        tagstringkey = 'tag_string_' + key
        if tagstringkey not in post:
            continue
        categorytags = post[tagstringkey].split()
        for tag in categorytags:
            if FindUnicode(tag) < 0:
                tagdict[tag] = tagtypedict[key]

def IsDisregardTag(tagitem):
    return TagCategory(tagitem) == tagtypedict['meta']
