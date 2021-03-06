#!/usr/bin/env python3
#WATCHDOG.PY

#PYTHON IMPORTS
import re
import os
import sys
import time
import importlib
import subprocess
from argparse import ArgumentParser

#LOCAL IMPORTS
from misc import GetFilename,GetCurrentTime,TurnDebugOn,DebugPrint,TouchFile

#LOCAL GLOBALS

watchdogfile = ""
pythonfileregex = re.compile(r'^(.*)\.py$')

#Helper functions

def StartProcess(commandline):
    TouchFile(watchdogfile)
    return subprocess.Popen([sys.executable]+commandline,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

def GetWatchdogInfo(program):
    global watchdogfile
    
    print("Getting module watchdog info")
    filename = GetFilename(program)
    match = pythonfileregex.match(filename)
    if not match:
        print(filename, "has an invalid Python extension")
        exit(-1)
    modulename = match.group(1)
    try:
        pythonmod = importlib.import_module(modulename)
        watchdogfile = pythonmod.watchdogfile
    except ImportError:
        print("Unable to import",filename)
        exit(-1)
    except AttributeError:
        print("Module",modulename,"does not have value 'watchdogfile'")
        exit(-1)

#Main function

def main(args):
    if args.debug:
        TurnDebugOn()
    commandline = args.program.split()
    startup = 1
    
    GetWatchdogInfo(commandline[0])
    
    print("Starting up",commandline[0])
    print("Pressing Ctrl-C will exit the program at the next available opportunity")
    p = StartProcess(commandline)
    while True:
        try:
            DebugPrint("Polling interval:",args.pollinginterval,"Startup period:",args.startupwait)
            p.wait(timeout=args.pollinginterval if startup==0 else args.startupwait)
            errorcode = p.returncode if (p.returncode < (1<<31)) else (p.returncode - (1<<32))
            DebugPrint("\nProgram returned",errorcode)
            if not errorcode:
                break
            if errorcode == -999:
                print("\a\a\a\a\aFatal error... exiting")
                exit(-1)
            print("\nRestarting",commandline[0],"with system exception in",args.exceptionwait,"seconds")
            time.sleep(args.exceptionwait)
            print("Starting up",commandline)
            p = StartProcess(commandline)
            startup = 1
            continue
        except KeyboardInterrupt:
            print("Exiting program")
            p.kill()
            exit(-1)
        except subprocess.TimeoutExpired:
            modifiedtime = os.path.getmtime(watchdogfile)
            currenttime = GetCurrentTime()
            DebugPrint("\nLast status update:",currenttime - modifiedtime, "Timeout period:",args.timeoutwait)
            if (currenttime - modifiedtime) > args.timeoutwait:
                print("\nRestarting deadlocked",commandline)
                p.kill()
                p = StartProcess(commandline)
                startup = 1
                continue
        startup = 0

if __name__ == '__main__':
    parser = ArgumentParser(description="Monitors other long-running python scripts for a heartbeat")
    parser.add_argument('-p','--pollinginterval',required=False,type=int, help="Interval for checking program status (Default: 30 sec)",default=30)
    parser.add_argument('-e','--exceptionwait',required=False,type=int, help="Wait time after program exception before restarting (Default: 300 sec)",default=300)
    parser.add_argument('-t','--timeoutwait',required=False,type=int, help="Wait time after program lockup before restarting (Default: 60 sec)",default=60)
    parser.add_argument('-s','--startupwait',required=False,type=int, help="Wait time after program starts before watchdog monitors (Default: 60 sec)",default=60)
    parser.add_argument('-d','--debug',action="store_true",default=False,required=False)
    parser.add_argument('program',help="Program and program arguments of monitored script enclosed in quotations \"\"")
    args = parser.parse_args()
    
    main(args)