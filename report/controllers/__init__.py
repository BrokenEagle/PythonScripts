#REPORT/CONTROLLERS module

#LOCAL IMPORTS
from misc import GetCallerModule,GetDirectoryListing,GetSubdirectoryListing,GetFileNameOnly,GetDirectory

#Initialization

controllersdir = GetDirectory(__file__)
filemodules = list(map(lambda x:GetFileNameOnly(x),GetDirectoryListing(controllersdir)))
dirmodules = list(set(GetSubdirectoryListing(controllersdir)).difference(['__pycache__']))
validtypes = filemodules + dirmodules
