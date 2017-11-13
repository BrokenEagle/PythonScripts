#REPORT/LOGICAL/TAGS.PY

#PYTHON IMPORTS
import os
import atexit

#LOCAL IMPORTS
from misc import LoadInitialValues,DebugPrint,FindUnicode,PutGetUnicode,PrintChar
from danbooru import MetatagExists,IsDisregardTag,GetTagCategory
from myglobal import workingdirectory

#LOCAL GLOBALS

tagdictfile = workingdirectory + "tagdict.txt"
tagdict = None
tagtypedict = {'general':0,'character':4,'copyright':3,'artist':1}
revtagtypedict = {0:'general',4:'character',3:'copyright',1:'artist',2:'nonexist'}

#Functions

def GetTagDict():
    global tagdict
    
    if tagdict == None:
        PrintChar('\n')
        tagdict = LoadInitialValues(tagdictfile,{},unicode=True)
        
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

def CountTags(tagstring):
    """Count all the tags for each category"""
    
    tagcount = [0]*5
    tagmiss = 0 #Used only for printing feedback
    tagdict = GetTagDict()
    
    for i in range(0,len(tagstring)):
        
        if MetatagExists(tagstring[i]):
            continue
        
        if IsDisregardTag(tagstring[i]):
            continue
        
        if (tagstring[i] in tagdict):
            tagcount[tagdict[tagstring[i]]] += 1
        else:
            #If unicode is found, then document for later and continue
            if FindUnicode(tagstring[i]) >= 0:
                continue
            
            tagmiss = 1 
            returntag = GetTagCategory(tagstring[i])
            tagdict[tagstring[i]] = returntag
            tagcount[returntag] += 1
            
            #Print some feedback
            DebugPrint(".",end="",flush=True)
    
    #Print some more feedback
    if tagmiss == 1:
        DebugPrint("T",end="",flush=True)
    
    return tagcount

def TagCategory(tagitem):
    tagdict = GetTagDict()
    if tagitem in tagdict:
        return tagdict[tagitem]
    if FindUnicode(tagitem) >= 0:
        return 2
    tagdict[tagitem] = GetTagCategory(tagitem)
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
        categorytags = post['tag_string_'+key].split()
        for tag in categorytags:
            if FindUnicode(tag) < 0:
                tagdict[tag] = tagtypedict[key]
