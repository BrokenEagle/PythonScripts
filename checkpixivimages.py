#!/usr/bin/env python3
#CHECKPIXIVIMAGES.PY

#PYTHON IMPORTS
import os
import re
try:
    import requests
except ImportError:
    print("Install requests module: pip install requests --upgrade")
    exit(-1)
from argparse import ArgumentParser

#MY IMPORTS
import pixivapiwrap
from misc import GetDirectoryListing,GetHTTPFilename,GetFilename,CreateDirectory,PutGetRaw,GetBufferChecksum,\
                    LoadInitialValues,PutGetData
from danbooru import SubmitRequest,GetArgUrl2
from myglobal import workingdirectory,datafilepath

#LOCAL GLOBALS

pixivhashfile = workingdirectory + datafilepath + 'pixivimagehashes.txt'

pixividrg = re.compile(r'^(\d+)_p(\d+)(_(?:master|square)1200)?\.(?:jpg|gif|png)$',re.IGNORECASE)
pixivillustrg = re.compile(r'^https?://(?:(?:www|touch)\.)?pixiv\.net/member_illust\.php\?mode=(?:medium|manga|manga_big)&illust_id=(\d+)(?:&page=(\d+))?',re.IGNORECASE)

FOUNDPIXIV = MATCHPIXIV = 1
FOUNDDANBOORU = MATCHDANBOORU = 2

directoryseparator = '\\'

sortdirectories = {
    0:'1-FoundNone\\',
    1:'2-FoundPixiv\\',
    2:'3-FoundDanbooru\\',
    3:'4-FoundBoth\\',
    16:'5-BadName\\'
}

sortsubdirectories = {
    0:'a-MatchNone\\',
    1:'b-MatchPixiv\\',
    2:'c-MatchDanbooru\\',
    3:'d-MatchBoth\\'
}

flatdirectories = {
    0:'A-FoundNone-MatchNone\\',
    2:'B-FoundNone-MatchDanbooru\\',
    4:'C-FoundPixiv-MatchNone\\',
    5:'D-FoundPixiv-MatchPixiv\\',
    6:'E-FoundPixiv-MatchDanbooru\\',
    7:'F-FoundPixiv-MatchBoth\\',
    8:'G-FoundDanbooru-MatchNone\\',
    10:'H-FoundDanbooru-MatchDanbooru\\',
    12:'I-FoundBoth-MatchNone\\',
    13:'J-FoundBoth-MatchPixiv\\',
    14:'K-FoundBoth-MatchDanbooru\\',
    15:'L-FoundBoth-MatchBoth\\',
    16:'Z-BadName\\'
}

#Functions

def movefile(filepath,filename,directory,subdirectory,flatness):
    print("Step 7: Move file")
    print("    Old directory:",filepath + filename)
    if flatness:
        directoryindex = directory if subdirectory == None else (directory << 2) + subdirectory
        print("    New directory:",filepath + flatdirectories[directoryindex] + filename)
        CreateDirectory(filepath + flatdirectories[directoryindex])
        os.rename(filepath + filename,filepath + flatdirectories[directoryindex] + filename)
    elif subdirectory == None:
        print("    New directory:",filepath + sortdirectories[directory] + filename)
        CreateDirectory(filepath + sortdirectories[directory])
        os.rename(filepath + filename,filepath + sortdirectories[directory] + filename)
    else:
        print("    New directory:",filepath + sortdirectories[directory] + sortsubdirectories[subdirectory] + filename)
        CreateDirectory(filepath + sortdirectories[directory] + sortsubdirectories[subdirectory])
        os.rename(filepath + filename,filepath + sortdirectories[directory] + sortsubdirectories[subdirectory] + filename)

def checkdanboorusource(url):
    pagematch = pixivillustrg.match(url)
    if pagematch:
        pixivid = int(pagematch.group(1))
        try:
            pixivpage = int(pagematch.group(2))
        except TypeError:
            pixivpage = None
        return pixivid,pixivpage
    
    filename = GetHTTPFilename(url)
    imagematch = pixividrg.match(filename)
    if imagematch:
        pixivid = int(imagematch.group(1))
        pixivpage = int(imagematch.group(2))
        return pixivid,pixivpage
    
    return None,None

def responsivedownload(checkurl,customheader):
    imagetimeout = 0
    servererror = 0
    while True:
        try:
            resp = requests.get(checkurl,headers=customheader,allow_redirects=False,timeout=30)
        except KeyboardInterrupt:
            exit(0)
        except requests.exceptions.ReadTimeout:
            if imagetimeout > 2:
                print("----Too many timeouts!----")
                return -1
            print("----Download Image Timeout!----")
            imagetimeout += 1
            continue
        except:
            print("----Unexpected exception!----")
            return -1
        if resp.status_code >= 500 and resp.status_code < 600:
            if servererror > 2:
                print("----Too many errors!----")
                return -1
            print("----Server error! Sleeping for 30 seconds...----")
            time.sleep(30)
            servererror += 1
            continue
        elif resp.status_code != 200:
            print("----HTTP Error:",resp.status_code,resp.reason,"----")
            return -1
        return resp

#Main function

def main(args):
    normalpath = args.directory
    if normalpath[-1] != directoryseparator:
        normalpath += directoryseparator
    
    pixivimages = LoadInitialValues(pixivhashfile,{})
    api = pixivapiwrap.PixivAPIWrapper()
    
    for filename in GetDirectoryListing(normalpath):
        print("++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("Checking on",filename)
        
        #Step 1 - Validate the filename
        print("Step 1: Validating filename")
        pixivmatch = pixividrg.match(filename)
        if pixivmatch == None:
            print("Filename does not match Pixiv image scheme!")
            movefile(normalpath,filename,16,None,args.flatdirectories)
            continue
        pixivid = int(pixivmatch.group(1))
        pixivpage = int(pixivmatch.group(2))
        pixivsmall = True if pixivmatch.group(3) else False
        foundon = 0
        matchon = 0
        
        #Step 2 - Check existence on Pixiv
        print("Step 2: Checking existence on Pixiv")
        pixivpost = api.Execute('works',pixivid,processerror=False)
        if not isinstance(pixivpost,int):
            pixivpost = pixivpost[0]
            if pixivpage < pixivpost['page_count']:
                print("    Found on Pixiv!")
                foundon |= FOUNDPIXIV
            else:
                print("    Not found on Pixiv!")
        else:
            print("    Bad Pixiv ID!")
        
        #Step 3 - Check existence on Danbooru
        print("Step 3: Checking existence on Danbooru")
        danboorulist = SubmitRequest('list','posts',urladdons=GetArgUrl2('tags','status:any pixiv:'+str(pixivid)))
        if not isinstance(danboorulist,int) and len(danboorulist) > 0:
            matchingposts = []
            for post in danboorulist:
                danbooruid,danboorupage = checkdanboorusource(post['source'])
                if danbooruid == pixivid and danboorupage == pixivpage:
                    matchingposts += [post['id']]
            if len(matchingposts) > 0:
                print("    Found on Danbooru!")
                foundon |= FOUNDDANBOORU
            else:
                print("    Not found on Danbooru!")
        else:
            print("    Bad Danbooru ID!")
        
        #Step 4 - Open local file and get checksum
        print("Step 4: Get local file checksum")
        buffer = PutGetRaw(normalpath + filename,'rb')
        filechecksum = GetBufferChecksum(buffer)
        
        #Step 5 - Check filematch with Pixiv
        if foundon & FOUNDPIXIV:
            print("Step 5: Get Pixiv image checksum")
            if pixivpage == 0:
                imageurl = pixivpost['image_urls']['large']
            else:
                imageurl = pixivpost['metadata']['pages'][pixivpage]['image_urls']['large']
            pixivchecksum = ''
            if imageurl in pixivimages:
                pixivchecksum = pixivimages[imageurl]
            else:
                response = responsivedownload(imageurl,{ 'Referer': 'https://app-api.pixiv.net/' })
                if not isinstance(response,int):
                    pixivchecksum = GetBufferChecksum(response.content)
                    pixivimages[imageurl] = pixivchecksum
                    PutGetData(pixivhashfile,'w',pixivimages)
                else:
                    print("    Error downloading image!")
            if pixivchecksum == filechecksum:
                matchon |= MATCHPIXIV
                print("    Match on Pixiv!")
            else:
                print("    No Match on Pixiv!")
        
        #Step 6 - Check filematch with Danbooru
        print("Step 6: Get Danbooru image checksum")
        matchingmd5s = list(map(lambda x:x['md5'],danboorulist))
        if filechecksum in matchingmd5s:
            matchon |= MATCHDANBOORU
            print("    Match on Danbooru!")
        else:
            danboorumd5list = SubmitRequest('list','posts',urladdons=GetArgUrl2('tags','status:any md5:'+filechecksum))
            if len(danboorumd5list) > 0:
                matchon |= MATCHDANBOORU
                print("    Match on Danbooru!")
            else:
                print("    No Match on Danbooru!")
        
        movefile(normalpath,filename,foundon,matchon,args.flatdirectories)
    
    print("Done!")

if __name__=='__main__':
    parser = ArgumentParser(description="Organize Pixiv downloads by status")
    parser.add_argument('directory',type=str,help="The directory to process images.")
    parser.add_argument('--flatdirectories',action="store_true",default=False,help="Directory structure will be flat. Default is hierarchical.")
    args = parser.parse_args()
    
    main(args)