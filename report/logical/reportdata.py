#REPORT/LOGICAL/REPORTDATA.PY

#PYTHON IMPORTS
import csv
import json
from collections import OrderedDict

#LOCAL IMPORTS
from dtext import CreateArray,ConstructTable,WriteDtextFile
from misc import CreateOpen,MinimumCutoffDict,SetPrecision,SecondsToDays,GetCallerModule,\
                 DebugPrint,DebugPrintInput
from danbooru import CreateTimestamp

#MODULE IMPORTS
from .common import DefaultTransform,DefaultDtextTransform,GetRankColumn

#Classes

class ReportData:
    reportvars = [
        'reportname','dtexttitle','dtextheaders','csvheaders','extracolumns','tablecutoffs','sortcolumns',
        'reversecolumns','transformfuncs','maketable','dtexttransform','tableoptions','reporttype','subkeys',
        'jsoniterator','footertext','cutoffcolumn']
    defaultvalues = {
        'sortcolumns': [0],
        'reporttype': 'csv',
        'dtexttransform': None,
        'maketable': None,
        'reversecolumns': [[True]],
        'tableoptions': [None],
        'subkeys': [],
        'jsoniterator': None,
        'footertext': None,
        'cutoffcolumn': None
        }
    
    def __init__(self,updatefunc,iterator,keycolumn,reportname,dtexttitle,dtextheaders,csvheaders,extracolumns,
            tablecutoffs,sortcolumns,reversecolumns,transformfuncs,maketable,dtexttransform,tableoptions,
            reporttype,subkeys,jsoniterator,footertext,cutoffcolumn):
        self.reportname = reportname
        self.dtexttitle = dtexttitle
        self.dtextheaders = dtextheaders
        self.csvheaders = csvheaders
        self.columns = extracolumns
        self.cutoffs = tablecutoffs
        self.sortcolumns = sortcolumns
        self.reversecolumns = reversecolumns
        self.updatefunc = updatefunc
        self.transformfuncs = []
        for func in transformfuncs:
            self.transformfuncs += [DefaultTransform] if func == None else [func]
        self.dtexttransform = DefaultDtextTransform if dtexttransform == None else dtexttransform
        self.maketable = DefaultDtextTransform if maketable == None else maketable
        self.tableoptions = tableoptions
        self.reporttype = reporttype
        self.iterator = iterator
        self.keycolumn = keycolumn
        self.subkeys = subkeys
        self.jsoniterator = jsoniterator
        self.footertext = footertext
        self.cutoffcolumn = cutoffcolumn
    
    def SetController(self,controller):
        self.controller = controller
    
    def ReportFilename(self):
        return (self.controller.controllername if self.controller.controllername != None else "") + self.reportname
    
    def GetFooterText(self):
        if self.footertext == None:
            return self.controller.footertext
        else:
            return self.footertext
    
    def GetCutoff(self,cutoff):
        if self.cutoffcolumn:
            return self.cutoffcolumn[0]
        else:
            return cutoff
    
    def UpdateData(self,userid,userdict,typeentry):
        reportdict = userdict[self.reportname] = userdict[self.reportname] if (self.reportname in userdict) else {}
        if len(self.subkeys) > 0:
            for option in self.subkeys:
                reportdict[option] = reportdict[option] if option in reportdict else {}
                self.UpdateItemData(reportdict[option],typeentry,option)
        else:
            self.UpdateItemData(reportdict,typeentry)
    
    def UpdateItemData(self,reportdict,typeentry,option=None):
        for key in self.iterator(typeentry,option):
            if key == None:
                continue
            self.AddDataEntry(key,reportdict)
            if self.controller.versioned:
                removeentry = self.updatefunc(key,reportdict,typeentry,self.controller.GetPriorVersion(typeentry))
            elif not self.controller.versioned:
                removeentry = self.updatefunc(key,reportdict,typeentry)
            if removeentry:
                DebugPrint("Removing entry")
                self.RemoveDataEntry(key,reportdict)
    
    def AddDataEntry(self,userid,reportdict):
        if self.reporttype == 'json':
            return
        if userid not in reportdict: 
            reportdict[userid] = [1] + [0] * self.columns
        else: 
            reportdict[userid][0] += 1
    
    def RemoveDataEntry(self,userid,reportdict):
        if self.reporttype == 'json':
            return
        reportdict[userid][0] -= 1
        if reportdict[userid][0] == 0:
            del reportdict[userid]
    
    def OutputCSV(self,directory,userdict):
        if len(self.subkeys) > 0:
            for option in self.subkeys:
                reportdict = userdict[option]
                filename = directory + self.ReportFilename() + '_%s.csv' % option
                self.WriteCSV(filename,self.csvheaders,reportdict)
        else:
            filename = directory + self.ReportFilename() + '.csv'
            self.WriteCSV(filename,self.csvheaders,userdict)
    
    @staticmethod
    def WriteCSV(filename,csvheaders,userdict):
        print("Writing", filename)
        with CreateOpen(filename,'w',newline='') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(csvheaders)
            for key in userdict:
                writer.writerow([key]+userdict[key])
    
    def OutputJSON(self,directory,userdict):
        for fileaddon,usertagdict in self.jsoniterator(userdict):
            filename = directory + fileaddon + self.ReportFilename() + '.json'
            self.WriteJSON(filename,usertagdict)
    
    @staticmethod
    def WriteJSON(filename,usertagdict):
        print("Writing",filename)
        with CreateOpen(filename, 'w') as outfile:
            json.dump(usertagdict, outfile)
    
    def OutputDText(self,directory,userdict,starttime,endtime,priordict={},priortime=0):
        for i in range(0,len(self.sortcolumns)):
            for j in range(0,len(self.tableoptions)):
                fileaddons = ""
                dtextstring = ("[expand=%s" % self.dtexttitle)
                if len(self.sortcolumns) > 1:
                    fileaddons += '_%d'%i
                    dtextstring += " (Ordered by %s)" % self.dtextheaders[self.sortcolumns[i]+1]
                if len(self.tableoptions) > 1:
                    fileaddons += '_%s' % self.tableoptions[j]
                    dtextstring += " - %s" % self.tableoptions[j].title()
                dtextstring += ("]\r\n[tn]Updated at %s[/tn]\r\n" % CreateTimestamp(starttime))
                dtextstring += self.CreateTable(userdict,starttime,endtime,self.cutoffs[i][j],self.sortcolumns[i],self.tableoptions[j],self.reversecolumns[i][j],priordict)
                dtextstring += "[tn][b]Note:[/b] cutoff was %d total %s; duration was %.2f days" %\
                            (self.GetCutoff(self.cutoffs[i][j]),self.GetFooterText(),SetPrecision(SecondsToDays(starttime-endtime),2))
                if priordict != {}:
                    dtextstring += "; prior duration was %.2f days" % (SetPrecision(SecondsToDays(endtime-priortime),2))
                dtextstring += "[/tn]\r\n[/expand]\r\n\r\n"
                filename = directory + 'dtext' + self.ReportFilename() + fileaddons + '.txt'
                print("Writing", filename)
                WriteDtextFile(filename,dtextstring)
    
    def CreateTable(self,indict,starttime,endtime,cutoff,sortcolumn,option,reversecolumn,priordict):
        tablecolumns = []
        if self.cutoffcolumn:
            indict = MinimumCutoffDict(indict,self.cutoffcolumn[0],self.cutoffcolumn[1])
        indict = self.maketable(indict,option)
        if priordict != {}:
            if self.cutoffcolumn:
                priordict = MinimumCutoffDict(priordict,self.cutoffcolumn[0],self.cutoffcolumn[1])
            priordict = self.maketable(priordict,option)
            DebugPrintInput("Priordict:",priordict.keys())
            tablecolumns += [GetRankColumn(indict,priordict,sortcolumn,reversecolumn)]
            DebugPrintInput("Tableprior:",tablecolumns)
            dtextheaders = ['Rank Diff']
        else:
            dtextheaders = []
        indict = MinimumCutoffDict(indict,cutoff,sortcolumn)
        DebugPrintInput("Indict:",indict.keys())
        indict = self.dtexttransform(indict,starttime=starttime,endtime=endtime)
        indict = OrderedDict(sorted(indict.items(), key=lambda x:x[1][sortcolumn], reverse=reversecolumn))
        tablecolumns += [self.keycolumn(indict)]
        dtextheaders += [self.dtextheaders[0]]
        if priordict != {}:
            tablecolumns += [DefaultTransform(priordict,sortcolumn)]
            dtextheaders += ['Prior']
        dtextheaders += self.dtextheaders[1:]
        for i in range(0,len(self.transformfuncs)):
            ctrl = self.controller
            tablecolumns += [
                self.transformfuncs[i](
                    indict,i,controller=ctrl.controller,userid=ctrl.userid,createcontroller=ctrl.createcontroller,\
                    createuserid=ctrl.createuserid,addonlist=self.controller.urladds,\
                    starttime=starttime,endtime=endtime)
                ]
        DebugPrintInput(tablecolumns,safe=True)
        tablelist = CreateArray(indict.keys(),*tablecolumns)
        DebugPrintInput(tablelist,safe=True)
        return ConstructTable(dtextheaders,tablelist)
    
    @classmethod
    def InitializeReportData(cls,updatefunc,iterator,keycolumn):
        mod = GetCallerModule(2).f_globals
        param = (updatefunc,iterator,keycolumn) + cls.GetParameters(mod)
        return cls(*param)
    
    @classmethod
    def GetParameters(cls,module):
        param = ()
        for var in cls.reportvars:
            if var in module:
                param += (module[var],)
            elif var in cls.defaultvalues:
                param += (cls.defaultvalues[var],)
            else:
                raise NameError("Report module not set up correctly!")
        return param
    
    @classmethod
    def AddJSONDicts(cls,indict1,indict2):
        similarkeys = list(set(indict1.keys()).intersection(indict2.keys()))
        dict1keys = list(set(indict1.keys()).difference(indict2.keys()))
        dict2keys = list(set(indict2.keys()).difference(indict1.keys()))
        tempdict = {}
        for key in similarkeys:
            if isinstance(indict1[key],dict):
                tempdict[key] = cls.AddJSONDicts(indict1[key],indict2[key])
            elif isinstance(indict1[key],list):
                tempdict[key] = []
                for i in range(0,len(indict1[key])):
                    tempdict[key] += [indict1[key][i] + indict2[key][i]]
            else:
                tempdict[key] = indict1[key] + indict2[key]
        for key in dict1keys:
            tempdict[key] = indict1[key]
        for key in dict2keys:
            tempdict[key] = indict2[key]
        return tempdict
