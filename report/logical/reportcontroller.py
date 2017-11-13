#REPORT/LOGICAL/REPORTCONTROLLER.PY

#PYTHON IMPORTS
import importlib

#LOCAL IMPORTS
from misc import GetCallerModule,GetDirectory,GetFileNameOnly,GetDirectoryListing
from danbooru import FormatStartID,IDPageLoop,SubmitRequest,JoinArgs,GetSearchUrl,GetPageUrl,GetLimitUrl

#Classes

class ReportController:
    controllervars = ['controllername','controller','startvalue','querylimit','urladds','timestamp','userid',
        'lookupid','createuserid','createcontroller','versioned']
    defaultvalues = {
        'controllername': None,
        'urladds': [],
        'lookupid': None,
        'createcontroller': None,
        'createuserid': None
        }
    
    def __init__(self,reporthandlers,controllername,controller,startvalue,querylimit,urladds,timestamp,userid,
            lookupid,createuserid,createcontroller,versioned):
        self.reporthandlers = reporthandlers
        for handler in reporthandlers:
            handler.SetController(self)
        self.controllername = controllername
        self.controller = controller
        self.startvalue = startvalue
        self.querylimit = querylimit
        self.urladds = urladds
        self.timestamp = timestamp
        self.userid = userid
        self.lookupid = lookupid
        self.createuserid = createuserid
        self.createcontroller = createcontroller
        self.versioned = versioned
        self.footertext = controller.replace('_versions','').replace('_',' ') + ' changes' if versioned else controller.replace('_',' ')
    
    def StartLoop(self,iterator,postprocess,inputdata,startid):
        if startid == 0:
            startid = FormatStartID(self.startvalue)
        else:
            startid = FormatStartID(startid)
        lastid = IDPageLoop(self.controller,self.querylimit,iterator,self.urladds,inputdata,startid,postprocess)
        return lastid
    
    def GetPriorVersion(self,currversiondata):
        urladd = JoinArgs(GetSearchUrl(self.lookupid,currversiondata[self.lookupid]),GetPageUrl(currversiondata['id']),GetLimitUrl(1))
        return SubmitRequest('list',self.controller,urladdons=urladd)
    
    @staticmethod
    def InitializeReportController(reporthandlers):
        mod = GetCallerModule(2).f_globals
        param = (reporthandlers,) + ReportController.GetParameters(mod)
        return ReportController(*param)
    
    @staticmethod
    def GetParameters(module):
        param = ()
        for var in ReportController.controllervars:
            if var in module:
                param += (module[var],)
            elif var in ReportController.defaultvalues:
                param += (ReportController.defaultvalues[var],)
            else:
                raise NameError("Controller module not set up correctly!")
        return param
    
    @staticmethod
    def GetPackageReportHandlers(filepath,package):
        controllersdir = GetDirectory(filepath)
        filemodules = list(set(map(lambda x:GetFileNameOnly(x),GetDirectoryListing(controllersdir))).difference(['__init__']))
        reporthandlers = []
        for file in filemodules:
            reporthandlers += [importlib.import_module('.'+file,package).reporthandler]
        return reporthandlers
