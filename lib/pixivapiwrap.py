#PIXIVAPIWRAP.PY

#PYTHON IMPORTS
import os
import sys
try:
    from pixivpy3 import PixivAPI
except ImportError:
    print("Install PixivPy module: pip install pixivpy --upgrade")
    exit(-1)

#LOCAL IMPORTS
from misc import GetCurrentTime,AbortRetryFail,PutGetData
from myglobal import pixivusername,pixivpassword,workingdirectory,datafilepath

#LOCAL GLOBALS

savetokenfile = workingdirectory + datafilepath + "pixivapiwrap.txt"

#CLASSES

class PixivAPIWrapper(PixivAPI):
    logontime = 0
    timeout = 0
    _USERNAME = pixivusername
    _PASSWORD = pixivpassword
    _REQUESTS_KWARGS = {'timeout':10}
    
    def __init__(self):
        super(PixivAPIWrapper, self).__init__(**self._REQUESTS_KWARGS)
        if self.__CheckSavedCredentials():
            print("Authenticating with Pixiv...")
            self.WrapLogin()
    
    def WrapLogin(self):
        self.logontime = GetCurrentTime()
        token = self.login(self._USERNAME,self._PASSWORD)
        self.timeout = token['response']['expires_in']
        PutGetData(savetokenfile,'w',[self.logontime, self.timeout, self.access_token, self.user_id, self.refresh_token])
    
    def Execute(self,funcname,*args,responseonly=True,processerror=True,**kwargs):
        self.__CheckTimeout()
        
        try:
            func = getattr(self,funcname)
        except AttributeError:
            print("Invalid function name:",funcname)
            return -1
        
        while True:
            try:
                response = func(*args,**kwargs)
            except:
                if AbortRetryFail(sys.exc_info()[0],sys.exc_info()[1]): continue
                else: return -1
            if response == None:
                break
            if response['status'] != 'success':
                if processerror and AbortRetryFail(response): continue
                else: return -1
            if responseonly:
                return response['response']
            else:
                return response
    
    def __CheckTimeout(self):
        if (GetCurrentTime() - self.logontime) > self.timeout:
            print("Reauthenticating with Pixiv...")
            self.WrapLogin()
    
    def __CheckSavedCredentials(self):
        if os.path.exists(savetokenfile):
            print("Loading cached credentials")
            self.logontime, self.timeout, self.access_token, self.user_id, self.refresh_token = PutGetData(savetokenfile,'r')
            self.__CheckTimeout()
            return False
        return True
