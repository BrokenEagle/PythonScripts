#IMPLICATIONS.PY

#PYTHON IMPORTS
import os
import time

#MY IMPORTS
from danbooru import SubmitRequest,JoinArgs,GetSearchUrl,GetLimitUrl
from misc import RemoveDuplicates,PutGetData,HasDayPassed,PrintChar
from myglobal import workingdirectory,datafilepath

#LOCAL GLOBALS

max_records = 100
refresh_period = 7
implicationfile = workingdirectory + datafilepath + 'implications.txt'
forwardimplicationdict = {}
reverseimplicationdict = {}

#External functions
def GetTagImplications(tag):
    implicationdata = {}
    if os.path.exists(implicationfile):
        implicationdata = PutGetData(implicationfile,'r')
        if (tag in implicationdata) and not (HasDayPassed(time.time(),implicationdata[tag]['time'],refresh_period)):
            return implicationdata[tag]['implications']
    
    allantecedents = getallantecedents(tag)
    allconsequents = getallconsequents(tag)
    allrelatedtags = getallrelatedtags(tag,allconsequents)
    implicationdata[tag] = {'time':time.time(),'implications':{'antecedents':allantecedents,'consequents':allconsequents,'relatedtags':allrelatedtags}}
    PutGetData(implicationfile,'w',implicationdata)
    
    return implicationdata[tag]['implications']

#Internal functions

def getallconsequents(tag_name):
    global forwardimplicationdict
    PrintChar('.')
    tag_list = []
    if tag_name in forwardimplicationdict:
        consequentlist = forwardimplicationdict[tag_name]
    else:
        urladd = JoinArgs(GetSearchUrl('antecedent_name',tag_name),GetSearchUrl('status','approved'),GetLimitUrl(max_records))
        response = SubmitRequest('list','tag_implications',urladdons = urladd)
        consequentlist = list(map(lambda x:x['consequent_name'],response))
        forwardimplicationdict[tag_name] = consequentlist
    if consequentlist == []:
        return []
    for consequent in consequentlist:
        tag_list += [consequent] + getallconsequents(consequent)
    return RemoveDuplicates(tag_list)

def getallantecedents(tag_name):
    global reverseimplicationdict
    PrintChar('.')
    tag_list = []
    if tag_name in reverseimplicationdict:
        antecedentlist = reverseimplicationdict[tag_name]
    else:
        urladd = JoinArgs(GetSearchUrl('consequent_name',tag_name),GetSearchUrl('status','approved'),GetLimitUrl(max_records))
        response = SubmitRequest('list','tag_implications',urladdons = urladd)
        antecedentlist = list(map(lambda x:x['antecedent_name'],response))
        reverseimplicationdict[tag_name] = antecedentlist
    if antecedentlist == []:
        return []
    for antecedent in antecedentlist:
        tag_list += [antecedent] + getallantecedents(antecedent)
    return RemoveDuplicates(tag_list)

#Fix this so it goes both backwards and forwards
def getallrelatedtags(tag_name,tag_consequents):
    global reverseimplicationdict
    tag_list = []
    tags_seen = tag_consequents + [tag_name]
    for i in range(0,len(tag_consequents)):
        if tag_consequents[i] in reverseimplicationdict:
            antecedentlist = reverseimplicationdict[tag_consequents[i]]
        else:
            urladd = JoinArgs(GetSearchUrl('consequent_name',tag_consequents[i]),GetSearchUrl('status','approved'),GetLimitUrl(max_records))
            response = SubmitRequest('list','tag_implications',urladdons=urladd)
            antecedentlist = list(map(lambda x:x['antecedent_name'],response))
            reverseimplicationdict[tag_consequents[i]] = antecedentlist
        for antecedent in antecedentlist:
            hit = 0
            for k in range(0,len(tags_seen)):
                if antecedent ==  tags_seen[k] and hit == 0:
                    hit = 1
                    #break  #->test this out
            if hit == 0 :
                tag_list += [antecedent] + getallantecedents(antecedent)
                tags_seen += [antecedent]
    return RemoveDuplicates(tag_list)