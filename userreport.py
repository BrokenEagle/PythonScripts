#USERREPORT.PY

#PYTHON IMPORTS
import uuid
import time
import importlib
from argparse import ArgumentParser

#LOCAL IMPORTS
import report
from misc import LoadInitialValues,PutGetUnicode,StaticVars,DaysToSeconds,SecondsToDays,HasDayPassed,AddDays,\
                TouchFile,PrintChar,DebugPrintInput,TurnDebugOn,GetDate,DebugPrint,GetDirectory
from danbooru import ProcessTimestamp,DateStringInput,TimestampInput
from myglobal import workingdirectory,datafilepath,csvfilepath,jsonfilepath,dtextfilepath

#LOCAL GLOBALS

watchdogfile = workingdirectory + "watchdog.txt"
globalcurrentid = 0
globallastid = 0

#Main functions

def main(args):
    """Main function; 
    args: Instance of argparse.Namespace
    """
    if(args.category) not in report.validtypes:
        print("Invalid category")
        return -1
    
    if args.debug:
        TurnDebugOn()
    
    if args.debuglib:
        for mod in args.debuglib.split():
            TurnDebugOn(mod)
    
    InitializeGlobals(args)
    
    if not args.nocheck:
        print("Checking local report completion...")
        startid,userdict = CheckUserFiles(True)
        PrintChar('\n')
        if startid >= 0:
            print("Starting main loop...")
            lastid = globalhandler.StartLoop(UserReportIteration,UserReportPostprocess,UserReportPreprocess,{'userdict':userdict},startid)
            PrintChar('\n')
    
    if args.output:
        OutputProducts(args)
    print("Done!")

def OutputProducts(args):
    global globaldate
    
    print("\nLoading data for reports...")
    globaldate = args.date
    SetCurrentPeriod()
    print("Loading current dicts...")
    userdict = LoadDicts(globalendtime)
    
    if args.prior:
        print("Loading prior dicts...")
        globalpriortime = globalendtime - DaysToSeconds(args.prior)
        priordict = LoadDicts(globalpriortime)
    else:
        globalpriortime = 0
        priordict = {}
    
    for handler in globalhandler.reporthandlers:
        reportdict = userdict[handler.reportname] if handler.reportname in userdict else {}
        previousdict = priordict[handler.reportname] if handler.reportname in priordict else {}
        if handler.reporttype == 'csv':
            handler.OutputCSV(workingdirectory + csvfilepath,reportdict)
        elif handler.reporttype == 'json':
            handler.OutputJSON(workingdirectory + jsonfilepath,reportdict)
        handler.OutputDText(workingdirectory + dtextfilepath,reportdict,globalstarttime,globalendtime,previousdict,globalpriortime)

#Misc functions

def InitializeGlobals(args):
    global globalhandler,typefilename,globalstarttime,globalendtime,globaldate,globalreports,globaldebug,globalcategory
    
    if args.debug:
        TurnDebugOn('report.'+args.category)
        globaldebug = True
    else:
        globaldebug = False
    
    globalcategory = args.category
    
    globaldate = args.date
    globalstarttime = ProcessTimestamp("%sT00:00:00.000Z"%args.date)
    globalendtime = globalstarttime - DaysToSeconds(args.days)
    
    typefilename = '%suserdict.txt' % args.category
    mod = importlib.import_module('report.controllers.'+args.category)
    globalhandler = mod.typehandler
    
    allhandlers = list(map(lambda x:x.reportname,globalhandler.reporthandlers))
    if args.reports:
        runreports = list(set(allhandlers).intersection([args.reports]))
        DebugPrint("All report handlers:",allhandlers)
        if len(runreports) == 0:
            print("Invalid report selection!")
            exit(-1)
        globalreports = runreports
    else:
        globalreports = allhandlers
    DebugPrint("Global:",globalreports)
    globalhandler.reporthandlers = list(filter(lambda x:x.reportname in globalreports,globalhandler.reporthandlers))
    
    SetCurrentPeriod()

def LoadDicts(endtime):
    outdict = {}
    while True:
        if endtime > globaldatechange:
            if not globaldebug:
                PrintChar('\n')
            return outdict
        startid,firstid,lastid,finished,tempdict,uniqueid = LoadInitialValues(userdictfile,[0,0,0,[],{},""],unicode=True,silence=not globaldebug)
        if startid >= 0:
            print("Error! %s not processed yet..." % globaldate)
            exit(-1)
        for handler in globalhandler.reporthandlers:
            outdict[handler.reportname] = outdict[handler.reportname] if (handler.reportname in outdict) else {}
            outdict[handler.reportname] = handler.AddJSONDicts(outdict[handler.reportname],tempdict[handler.reportname])
        ChangeDatePeriod()
        SetCurrentPeriod()
        if not globaldebug:
            PrintChar('+')

def PrintStateInfo(place,indict):
    if not globaldebug:
        return
    
    printparams = (
        "\nState #" + str(place),
        globaldate,
        globalcurrentid,
        globalfirstid,
        globallastid,
        UserReportIteration.skipid,
        list(map(lambda x:len(x),indict.values())),
        globaluniqueid)
    print(*printparams)
    input()

#Date change functions

def CheckUserFiles(beginning=False):
    global globalfirstid,globallastid,globalfinished,globaluniqueid,globalmissingreports
    
    while True:
        oldlastid = globallastid
        startid,globalfirstid,globallastid,globalfinished,tempdict,globaluniqueid = LoadInitialValues(userdictfile,[0,0,0,[],{},""],unicode=True,silence=not globaldebug)
        
        globalmissingreports = list(set(globalreports).difference(globalfinished))
        
        for report in list(set(globalreports).difference(tempdict.keys())):
            tempdict[report] = {}
        
        PrintStateInfo(1,tempdict)
        if len(globalmissingreports) > 0:
            if globaluniqueid == "":
                globaluniqueid = uuid.uuid4().hex
            if startid < 0:
                startid = globalfirstid
                DebugPrint("Restart id:",startid)
            
            if startid == 0:
                if beginning and oldlastid == 0:
                    startid = CheckPriorDay()
                    beginning = False
                else:
                    startid = oldlastid
                
                if startid != 0:
                    DebugPrint("Prior startid:",startid)
            
            if startid >= 0:
                DebugPrint("Missing:",globalmissingreports)
                return startid,tempdict
        
        ChangeDatePeriod()
        SetCurrentPeriod()
        if globalendtime > globaldatechange:
            DebugPrint("End of data retrieval...")
            return -1,-1
        if not globaldebug:
            #Print some feedback for those huge files
            PrintChar('+')
        
        #Send a heartbeat for long-loading files
        TouchFile(watchdogfile)

def CheckPriorDay():
    return LoadInitialValues(workingdirectory + datafilepath + AddDays(globaldate,1) + '\\' + typefilename,[0,0,0,[],{},""],unicode=True,silence=not globaldebug)[2]

def SetCurrentPeriod():
    global userdictfile,globaldatechange
    userdictfile = workingdirectory + datafilepath + globaldate + '\\' + typefilename
    globaldatechange = ProcessTimestamp("%sT00:00:00.000Z"%globaldate) - DaysToSeconds(1)

def ChangeDatePeriod():
    global globaldate
    globaldate = AddDays(globaldate,-1)

#Loop functions

@StaticVars(startedyet=False, skipid=-1)
def UserReportIteration(item,userdict,**kwargs):
    global globalfirstid,globalcurrentid
    
    globalcurrentid = item['id']
    
    if UserReportIteration.skipid > 0:
        if UserReportIteration.skipid < item['id']:
            PrintChar('.')
            return 0
        else:
            DebugPrintInput("Caught up to",item['id'])
            UserReportIteration.skipid = -1
    
    timestamp = item[globalhandler.timestamp]
    userid = item[globalhandler.userid]
    
    currenttime = ProcessTimestamp(timestamp)
    if globalstarttime < currenttime:
        return 0
    elif UserReportIteration.startedyet == False:
        UserReportIteration.startedyet = True
        if globalfirstid == 0:
            globalfirstid = item['id']+1
        PrintChar('S')
    
    while globaldatechange > currenttime:
        DebugPrintInput("\nChangeover:",globalfirstid,item['id']+1,globalreports)
        PrintStateInfo(2,userdict)
        PutGetUnicode(userdictfile,'w',[-1,globalfirstid,item['id']+1,list(set(globalreports).union(globalfinished)),userdict,globaluniqueid])
        ChangeDatePeriod()
        SetCurrentPeriod()
        #First exit condition (Last day was processed)
        if globalendtime > globaldatechange:
            DebugPrint("\nExit UserReportIteration #1")
            UserReportPostprocess.savereport = False
            return -1
        
        UserReportIteration.skipid,tempdict = CheckUserFiles()
        
        #Second exit condition (Last day was already processed)
        if isinstance(tempdict,int):
            DebugPrint("\nExit UserReportIteration #2")
            UserReportPostprocess.savereport = False
            return -1
        
        userdict.clear()
        for key in tempdict:
            userdict[key] = tempdict[key]
        if globalfirstid == 0:
            globalfirstid = item['id'] + 1
        if UserReportIteration.skipid > 0 and UserReportIteration.skipid  < item['id']:
            return 0
    
    for handler in globalhandler.reporthandlers:
        if handler.reportname in globalmissingreports:
            handler.UpdateData(userid,userdict,item)
    return 0

def UserReportPreprocess(typelist,**kwargs):
    #if UserReportIteration.startedyet:
    if True:
        for handler in globalhandler.reporthandlers:
            if handler.reportname in globalmissingreports and handler.preprocess != None:
                handler.preprocess(typelist)

@StaticVars(currentday = 0,savereport = True)
def UserReportPostprocess(typelist,userdict,**kwargs):
    if UserReportPostprocess.savereport:
        PrintStateInfo(3, userdict)
        PutGetUnicode(userdictfile,'w',[typelist[-1]['id'],globalfirstid,globallastid,globalfinished,userdict,globaluniqueid])
    
    #Send a heartbeat
    TouchFile(watchdogfile)
    
    #Print some extra screen feedback so we know where we're at
    currenttime = ProcessTimestamp(typelist[-1][globalhandler.timestamp])
    if HasDayPassed(globalstarttime-currenttime,DaysToSeconds(UserReportPostprocess.currentday)):
        UserReportPostprocess.currentday = int(SecondsToDays(globalstarttime-currenttime))
        PrintChar(UserReportPostprocess.currentday)

if __name__ =='__main__':
    parser = ArgumentParser(description="Generate a Danbooru User Report")
    parser.add_argument('category',help="post, upload, note, artist_commentary, pool, "
                        "artist, wiki_page, forum_topic, forum_post, tag_implication, "
                        "tag_alias, bulk_update_request, post_appeal, comment, user_feedback, "
                        "post_replacement")
    parser.add_argument('--days',type=int,help="Days for the report",default=1)
    parser.add_argument('--prior',type=int,help="Prior days to compare to")
    parser.add_argument('--reports',type=str,help="Individual reports to run")
    parser.add_argument('--output',required=False,action="store_true",help="Select to output report products")
    parser.add_argument('--nocheck',required=False,action="store_true",help="Don't chek the reports for completion")
    timegroup = parser.add_mutually_exclusive_group(required=True)
    timegroup.add_argument('-d','--date',type=DateStringInput,help="Date to start the report")
    timegroup.add_argument('-t','--timestamp',type=TimestampInput,help="Timestamp ranges for the report")
    parser.add_argument('--debug',required=False,action="store_true",help="Show additional debug details.")
    parser.add_argument('--debuglib',required=False,help="Show additional debug details for other libraries.")
    
    args = parser.parse_args()
    
    main(args)