#TAGGARDEN.PY

#PYTHON IMPORTS
import os
import sys
import time
import msvcrt
import threading
from argparse import ArgumentParser
from collections import OrderedDict

#MY IMPORTS
from misc import TurnDebugOn,StaticVars,PrintChar,RemoveDuplicates,PutGetData,LoadInitialValues,DebugPrint,DebugPrintInput
from danbooru import SubmitRequest,IDPageLoop,DownloadPostImageIteration,GetPostCount,GetArgUrl2,GetCurrFilePath,\
                    DownloadPostImage,PostChangeTags
from myglobal import workingdirectory,datafilepath,imagefilepath

try:
    from keyoutput import AltTab
    regainfocus = True
except ImportError:
    regainfocus = False

try:
    from terminalsize import get_terminal_size
    resizeterminal = True
except ImportError:
    resizeterminal = False

try:
    from implications import GetTagImplications
    useimplications = True
except ImportError:
    useimplications = False

#LOCAL GLOBALS

#Variables
#Adjust these console variables manually if the terminalsize module is not used
consolewidth = 80
consoleheight = 25

#Constants
menuconfigfile = workingdirectory + datafilepath + 'taggarden-config.txt'
seenlistfile = workingdirectory + datafilepath + 'taggarden-seenlist.txt'
bannerstring = "Post (%d/%d): <post #%d>"
delayalt = 1.5        #time to wait before pressing Alt
releasealt = 0.2    #time to wait before releasing Alt
numbertab = 1        #times to press Tab key
ESCAPEKEY = b'\x1b'
BACKSPACE = b'\x08'
ENTERKEY = b'\r'
ESCAPEBYTE = b'\xe0'
FUNCTIONBYTE = b'\x00'

#Main execution functions

@StaticVars(downloadfile = False,debug = False,simulate = False,singlethread = False,backwardsarray = [])
def taggardenpostiteration(post,currpos):
    """Main program iterator"""
    global seenlist
    
    DebugPrintInput("Seenlist:",seenlist)
    
    if (seenlist != None) and (post['id'] in seenlist):
        seenlist.remove(post['id'])
        currpos[0] += 1
        return 0
    
    #Download the file if needed then get the local path
    if taggardenpostiteration.downloadfile:
        DownloadPostImage(post,directory='taggarden\\')
    currfile = GetCurrFilePath(post,directory='taggarden\\')
    DebugPrint("Image filepath:",currfile)
    
    #Start the downloaded file with its default viewer
    if os.path.exists(currfile):
        temp = os.startfile(currfile)
    else:
        print("Error: image does not exist!")
        print("Filepath:", currfile)
        print("Exiting...")
        exit(-1)
    
    if regainfocus:
        #Configurable Alt Tab: gets back screen focus
        AltTab(delayalt,releasealt,numbertab)
    
    #Get user input for tagging
    tagsadded = executemainmenu(post,currpos)
    
    #Now update the post
    if not taggardenpostiteration.simulate and (len(tagsadded) > 0):
        if taggardenpostiteration.singlethread:
            print("\nUpdating tags...",end="")
            PostChangeTags(post,tagsadded)
        else:
            print("\nStarting multitask tag thread...")
            update_thread = threading.Thread(target=PostChangeTags, args=(post,tagsadded,True))
            update_thread.start()
    
    if seenlist != None:
        PutGetData(seenlistfile,'w',taggardenpostiteration.backwardsarray)
    
    currpos[0] += 1
    return 0

def executemainmenu(post,currpos):
    """Display a menu and get user input"""
    
    #Create function variables
    tag_string = post['tag_string']
    postid = post['id']
    menulen = len(menuitems)
    tagarray = [0] * menulen
    removearray = [0] * 4
    redraw = True
    displaytagstring = False
    manualtags = []
    
    #Set array to initial values
    tagarray = list(map(lambda x:1 if tag_string.find(x) >= 0 else 0,menutags))
    DebugPrint("Tagarrays:",tagarray,removearray)
    DebugPrintInput("Tag string:",tag_string,safe=True)  #There could potentiall be unicode tags
    
    while True:
        if redraw:
            temp = os.system('cls')
            printconsole.linepos = 0
            printconsole(bannerstring % (tuple(currpos)+(postid,)))
            printconsolewrap(menubanner % setmenutuple(tagarray,removearray))
            if useimplications:
                printtagimplications(tag_string)
            addedtags = manualtags + gettagsadded(tag_string,tagarray,removearray)
            if len(addedtags) > 0:
                printlistitems(addedtags,"\nAdded tags:",'\n ',1)
                #printconsole("\nAdded tags:")
                #for tag in addedtags:
                #    printconsole(' '+tag)
            if displaytagstring:
                printconsole("\nTag string:")
                printconsolewrap(tag_string)
            DebugPrint("\nLinepos:",printconsole.linepos)
            DebugPrint("\nTagarrays:",tagarray,removearray)
        redraw = True
        keypress = msvcrt.getch()
        if keypress == ENTERKEY:
            break
        if keypress == ESCAPEKEY:
            sys.exit(0)
        if keypress == BACKSPACE:
            if len(taggardenpostiteration.backwardsarray) == 0:
                redraw = False
                continue
            try:
                backpostid = taggardenpostiteration.backwardsarray[taggardenpostiteration.backwardsarray.index(postid)-1]
            except ValueError:
                backpostid = taggardenpostiteration.backwardsarray[-1]
            DebugPrintInput("Backwards info:",postid,backpostid,taggardenpostiteration.backwardsarray)
            backpost = SubmitRequest('show','posts',id=backpostid)
            currpos[0] -= 1
            taggardenpostiteration(backpost,currpos)
            currfile = GetCurrFilePath(post,directory="taggarden\\")
            os.startfile(currfile)
            if regainfocus:
                AltTab(delayalt,releasealt,numbertab)
        elif keypress == FUNCTIONBYTE:
            functionkey = msvcrt.getch()
            if functionkey == b'?':
                updateconsolesize()
            else:
                redraw = False
        elif keypress in menukeys:
            pos = menukeys.index(keypress.lower())
            tagarray[pos] ^= 1
        elif keypress.lower() == ESCAPEBYTE:
            escapecode = msvcrt.getch()
            if escapecode == 'S':
                tagarray = [0] * menulen
                removearray = [0] * 4
        elif keypress.lower() == b'a':
            removearray[0] ^= 1
        elif keypress.lower() == b'c':
            removearray[1] ^= 1
        elif keypress.lower() == b'r':
            removearray[2] ^= 1
        elif keypress.lower() == b'x':
            removearray[3] ^= 1
        elif keypress.lower() == b'f':
            currfile = GetCurrFilePath(post,"large",directory="taggarden\\")
            if os.path.exists(currfile):
                os.remove(currfile)
            DownloadPostImage(post,"large",directory="taggarden\\")
            temp = os.startfile(currfile)
            if regainfocus:
                AltTab(delayalt,releasealt,numbertab)
        elif keypress.lower() == b'm':
            keyinput = input("\nEnter manual tags:\n\n")
            manualtags = keyinput.split()
        elif keypress.lower() == b't':
            displaytagstring ^= True
        elif keypress.lower() == b'o':
            os.startfile("http://danbooru.donmai.us/posts/%d" % postid)
            redraw = False
        elif keypress.lower() == b'?':
            listhotkeys()
            print("\nPress any key to continue...",flush=True,end="")
            getch()
        else:
            redraw = False
    
    tagsadded = manualtags + gettagsadded(tag_string,tagarray,removearray)
    
    if postid not in taggardenpostiteration.backwardsarray:
        taggardenpostiteration.backwardsarray.append(postid)
    
    DebugPrint("\nAdding Tags:\n",tagsadded)
    DebugPrintInput("\nPost array:\n",taggardenpostiteration.backwardsarray)
    return tagsadded

def setupmenus():
    """Query user input for menu configuration"""
    
    setupmenudict = LoadInitialValues(menuconfigfile,["",{}])[1]
    while True:
        setupmenuarray = []
        hotkey = 1
        while True:
            print("\nHotkey #%d" % hotkey)
            tag_name = input("Enter tag name (or Enter to finish): ").lower().strip().replace(' ','_')
            if len(tag_name) == 0:
                break
            header = getnameinput("Enter short name for %s: " % tag_name).strip().replace(' ','_')
            setupmenuarray.append((tag_name,{'header':header,'hotkey':str(hotkey)}))
            if hotkey == 0:
                print("No more hotkeys!!")
                break
            hotkey += 1
            if hotkey >= 10:
                hotkey = 0
        
        menu_name = getnameinput("\nEnter a name for this menu configuration: ").lower()
        setupmenudict[menu_name] = setupmenuarray
        if getyninput("\nContinue adding more more menus (y/n)? "):
            continue
        break
    print("\nSetting \"%s\" as default menu configuration." % menu_name)
    print("Writing menu configuration...")
    PutGetData(menuconfigfile,'w',[menu_name,setupmenudict])

def deletepostiteration(post):
    """Loop iterator to delete posts"""
    
    currfile = GetCurrFilePath(post,directory="taggarden\\")
    if os.path.exists(currfile):
        os.remove(currfile)
        PrintChar('.')
    else:
        PrintChar('+')
    return 0

#Tag array functions

def gettagsadded(tag_str,tagarray,removearray):
    tagsadded = []
    if any(removearray) and useimplications:
        tagsadded += removetagimplications(tag_str,removearray)
    
    for i in range(0,len(menutags)):
        found = 1 if tag_str.find(menutags[i])>=0 else 0
        if found != tagarray[i]:
            tagsadded += [menutags[i]] if found==0 else ['-'+menutags[i]]
    return tagsadded

def removetagimplications(tag_str,removearray):
    """Create list of tag removals for implications"""
    
    removelist = []
    taglist = tag_str.split()
    for tag in implicationdict:
        if tag in taglist:
            removelist += list(set(taglist).intersection(implicationdict[tag]['antecedents'])) if removearray[0] else []
            removelist += list(set(taglist).intersection(implicationdict[tag]['consequents'])) if removearray[1] else []
        else:
            removelist += list(set(taglist).intersection(implicationdict[tag]['consequents']).difference(menutags)) if removearray[3] else []
        removelist += list(set(taglist).intersection(implicationdict[tag]['relatedtags']).difference(menutags)) if removearray[2] else []
    return list(map(lambda x:'-'+x,RemoveDuplicates(removelist)))

#Menu functions

def checkmenus():
    """Load and check the menu configuration info"""
    
    defaultmenu,setupmenudict = LoadInitialValues(menuconfigfile,["",{}])
    if len(setupmenudict) == 0:
        print("No menus installed!\nRun \"--setupmenus\" from the command line.")
        exit(-1)
    return defaultmenu,setupmenudict

def setupmenuglobals(defaultmenu,setupmenudict):
    global menuitems,menutags,menubanner,menukeys
    
    menuitems = OrderedDict(setupmenudict[defaultmenu])
    menutags = list(menuitems.keys())
    menubanner =getmenubanner(menuitems)
    menukeys = list(map(lambda x:x[1]['hotkey'].encode('ascii'),menuitems.items()))

def getmenubanner(menudict):
    return ' '.join(list(map(lambda x:"%s.[%%s]%s"%(x[1]['hotkey'],x[1]['header']),menudict.items()))) + (" [%s]Remove" if useimplications else "")

def setmenutuple(menuarray,removearray):
    """Build menu tuple for printing"""
    
    menu = ()
    for i in range(0,len(menuarray)):
        if menuarray[i]: menu += ('x',)
        else: menu += ('_',)
    
    if useimplications:
        removestr = ""
        for i in range(0,len(removearray)):
            if removearray[i]:removestr += ['A','C','R','X'][i]
        if removestr == "": removestr = "_"
        menu += (removestr,)
    
    return menu

#Input functions

def getnameinput(query):
    while True:
        keyinput = input(query)
        if len(keyinput) == 0:
            print("No name entered!")
            continue
        break
    return keyinput

def getyninput(query):
    while True:
        keyinput = input(query)
        if keyinput.lower() == 'y':
            return True
        elif keyinput.lower() == 'n':
            return False

#Print functions

def printconsolewrap(text):
    outputsegments = []
    while True:
        if len(text) < consolewidth:
            break
        breakpos = text[:consolewidth].rfind(' ')
        printconsole(text[:breakpos])
        text = text[breakpos+1:]
    printconsole(text)

@StaticVars(linepos = 0)
def printconsole(text):
    if printconsole.linepos < consoleheight:
        if printconsole.linepos == consoleheight-1:
            #This allows us to print on the very last line
            print(text,end='',flush=True)
        else:
            print(text)
    printconsole.linepos += 1 + text.count('\n')

def printtagimplications(tag_str):
    antecedents = []
    consequents = []
    relatedtags = []
    allconsequents = []
    taglist = tag_str.split()
    for tag in implicationdict:
        if tag in taglist:
            antecedents += list(map(lambda x:"* %s -> %s"%(x,tag),set(taglist).intersection(implicationdict[tag]['antecedents'])))
            consequents += list(map(lambda x:"* %s -> %s"%(tag,x),set(taglist).intersection(implicationdict[tag]['consequents'])))
        else:
            allconsequents += list(set(taglist).intersection(implicationdict[tag]['consequents']).difference(menutags))
        relatedtags += list(set(taglist).intersection(implicationdict[tag]['relatedtags']).difference(menutags))
    
    printlistitems(antecedents,"\nA. Implication antecedents:",'\n')
    printlistitems(consequents,"\nC. Implication consequents:",'\n')
    printlistitems(relatedtags,"\nR. Implication related tags:",', ',2)
    printlistitems(allconsequents,"\nX. All related consequents:",', ',2)

def printlistitems(itemlist,title,joiner,spaces=0):
    itemlist = RemoveDuplicates(itemlist)
    if len(itemlist) > 0:
        printconsole(title)
        printconsole(' '*spaces + joiner.join(itemlist))

def printmenus():
    defaultmenu,setupmenudict = checkmenus()
    for menu in setupmenudict:
        print("\n\"%s\" menu:\n" % menu)
        print(getmenubanner(OrderedDict(setupmenudict[menu])).replace('%s',' '))
    print("\nDefault menu is %s." % defaultmenu)

def listhotkeys():
    print("List of program hotkeys:\n")
    print("      0 - 9: Toggle tags on or off")
    print("        Del: Quick remove of all tags")
    print("      Enter: Submit tag changes")
    print("        Esc: Exit program")
    print("  Backspace: Goto previous post")
    print("         F5: Refresh screen")
    print("          F: Download and display fullsize image")
    print("          O: Open image post on Danbooru")
    print("          T: Toggle tag string on or off")
    print("          M: Add list of tags (separated by spaces)")
    print("          A: Remove all tag antecedents")
    print("          C: Remove all tag consequents")
    print("          R: Remove all related tags")
    print("          X: Remove all related consequents")
    print("          ?: Print this help page")

#Helper functions

def updateconsolesize():
    global consoleheight,consolewidth
    if resizeterminal:
        consolewidth,consoleheight = get_terminal_size()

#Main function

def main(args):
    global searchtags,implicationdict,seenlist
    
    if args.debug:
        TurnDebugOn()
    
    if args.debuglib:
        for mod in args.debuglib.split():
            TurnDebugOn(mod)
    
    if args.listhotkeys:
        listhotkeys()
        return 0
    
    if args.setupmenus:
        setupmenus()
        return 0
    
    if args.printmenus:
        printmenus()
        return 0
    
    searchtags = args.tags
    
    if args.download:
        if len(args.tags) == 0:
            print("Error: No tags specified!\n\"--download\" requires that \"--tags\" be used.")
            exit(-1)
        IDPageLoop('posts',100,DownloadPostImageIteration,addonlist=[GetArgUrl2('tags',searchtags)],inputs={'directory':'taggarden\\'})
        return 0
    
    if args.delete:
        if len(args.tags) == 0:
            deletedirectory = workingdirectory + imagefilepath + 'taggarden\\'
            deletefilelist =  [os.path.join(deletedirectory,fn) for fn in next(os.walk(deletedirectory))[2]]
            for deletefile in deletefilelist:
                os.remove(deletefile)
                PrintChar('.')
        else:
            IDPageLoop('posts',100,deletepostiteration,addonlist=[GetArgUrl2('tags',searchtags)])
        return 0
    
    if not args.nodownload:
        taggardenpostiteration.downloadfile = True
    
    if args.simulate:
        taggardenpostiteration.simulate = True
    
    if args.saveprogress:
        seenlist = []
    elif args.restoreprogress:
        seenlist = LoadInitialValues(seenlistfile,None)
        taggardenpostiteration.backwardsarray += seenlist if seenlist != None else []
    else:
        seenlist = None
    
    defaultmenu,setupmenudict = checkmenus()
    if args.defaultmenu != None:
        if args.defaultmenu.lower() not in setupmenudict:
            print("Invalid menu selection!")
            print("Available choices:",', '.join(setupmenudict.keys()))
            exit(-1)
        defaultmenu = args.defaultmenu
        print("\nSetting \"%s\" as default menu configuration." % defaultmenu)
        print("Writing menu configuration...")
        PutGetData(menuconfigfile,'w',[defaultmenu,setupmenudict])
    
    if resizeterminal:
        updateconsolesize()
    else:
        print("\"terminal.py\" missing! Setting console to constant width and height.")
        if current_os == "Windows":
            os.system("mode con: cols=%d lines=%d" % (consolewidth,consoleheight))
        elif current_os == "Linux":
            os.system("stty cols %d" % consolewidth)
            os.system("stty rows %d" % consoleheight)
    
    setupmenuglobals(defaultmenu,setupmenudict)
    implicationdict = {}
    if useimplications:
        print("\nGetting implications:\n")
        for tag in menutags:
            print("Querying %s..." % tag)
            implicationdict[tag] = GetTagImplications(tag)
    
    #Get the total count for tagging
    print("\nGetting total post count:\n")
    loopinput = {}
    loopinput['currpos'] = [1,GetPostCount(args.tags)]
    print("%d posts found" % loopinput['currpos'][1])
    
    #Execute main loop
    IDPageLoop('posts',100,taggardenpostiteration,addonlist=[GetArgUrl2('tags',searchtags)],inputs=loopinput)
    print("Done!")

if __name__ == '__main__':
    parser = ArgumentParser(description="Tag Images From Danbooru")
    funcgroup = parser.add_mutually_exclusive_group(required=False)
    funcgroup.add_argument('--nodownload',required=False,action="store_true",default=False,help="Don't download images. Will error on image not found.")
    funcgroup.add_argument('--download',required=False,action="store_true",default=False,help="Download all images ahead of time. Use with --tags.")
    funcgroup.add_argument('--delete',required=False,action="store_true",default=False,help="Delete downloaded images. Can be used with --tags.")
    funcgroup.add_argument('--setupmenus',required=False,action="store_true",default=False,help="Setup configuration info for tag menus.")
    funcgroup.add_argument('--printmenus',required=False,action="store_true",default=False,help="Print out all currently available menus.")
    funcgroup.add_argument('--listhotkeys',required=False,action="store_true",default=False,help="Print out all available program hotkeys.")
    parser.add_argument('--tags',required=False,default='',help="Search string as used on Danbooru. Surround with quotes when more than one tag is used.")
    parser.add_argument('--defaultmenu',required=False,help="Change the default tag menu used.")
    parser.add_argument('--debug',required=False,action="store_true",help="Show additional debug details.")
    parser.add_argument('--debuglib',required=False,help="Show additional debug details for other libraries.")
    parser.add_argument('--simulate',required=False,action="store_true",default=False,help="Run the program without pushing any tag edits.")
    parser.add_argument('--singlethread',required=False,action="store_true",default=False,help="Will not send tag edits via multi-threading.")
    progressgroup = parser.add_mutually_exclusive_group(required=False)
    progressgroup.add_argument('--saveprogress',required=False,action="store_true",default=False,help="Start recording the posts that have already been edited.")
    progressgroup.add_argument('--restoreprogress',required=False,action="store_true",default=False,help="Restart tagging using the progress saved by --saveprogress.")
    args = parser.parse_args()
    
    main(args)