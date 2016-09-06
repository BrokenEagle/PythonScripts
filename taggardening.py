#TAGGARDENING.PY

#PYTHON IMPORTS
import re
import os
import sys
import time
import msvcrt
import argparse
from subprocess import Popen, CREATE_NEW_CONSOLE

#MY IMPORTS
from misc import TurnDebugOn
from danbooru import SubmitRequest,JoinArgs,GetArgUrl2,GetCurrFilePath,EncodeData,IDStringInput,DateStringInput
from keyoutput import AltTab

#LOCAL GLOBALS
displaystring="Page (%d/%d): #%d/%d\n[%s]Small [%s]Medium [%s]Large [%s]Huge [%s]Gigantic \n[%s]Flat Chest [%s]Remove"
breastsimpstr = ['backboob', 'bouncing_breasts', 'breast_rest', 'breasts_on_head', 'carried_breast_rest', 'breasts_apart', 'breasts_outside', 'breast_squeeze', 'bursting_breasts', 'cleavage', 'cum_on_breasts', 'floating_breasts', 'gigantic_breasts', 'hanging_breasts', 'huge_breasts', 'large_breasts', 'medium_breasts', 'perky_breasts', 'sagging_breasts', 'sideboob', 'small_breasts', 'unaligned_breasts', 'underboob']
searchtags = 'breasts -small_breasts -medium_breasts -large_breasts -huge_breasts -gigantic_breasts'
pagelimit = 100

def setbreastimplications(tag_str):
	"""Set array according to found breasts implications"""
	array = [0]*len(breastsimpstr)
	for i in range(0,len(array)):
		if tag_str.find(breastsimpstr[i]) > 0:
			array[i]=1
	return array

def printbreastimplications(array):
	"""Print all found breasts implications"""
	for i in range(0,len(array)):
		if array[i]==1:
			print("* " + breastsimpstr[i])

def removebreastimplications(array):
	"""Return tags to remove all breasts implications"""
	tag_array = []
	for i in range(0,len(array)):
		if array[i]==1:
			tag_array = [' -' + breastsimpstr[i]]
	return tag_array

def setmenutuple(array):
	"""Dynamically build menu tuple"""
	menu = ()
	for i in range(0,len(array)):
		if array[i]: menu += ('x',)
		else: menu += (' ',)
	return menu

def getuserkeypresses(postid,tag_string,*pageinfo):
	"""Display a menu and get user input"""
	
	breastsarray = [0] * 7
	flatchest = False
	
	if tag_string.find('flat_chest')>=0:
		breastsarray[5] = 1
		flatchest = True
	
	redraw = True
	
	while True:
		
		if redraw:
			temp = os.system('cls')
			print(displaystring % (pageinfo+setmenutuple(breastsarray)))
			print("Breast Implications: (%d)" % postid)
			breastimplications = setbreastimplications(tag_string)
			printbreastimplications(breastimplications)	
		
		redraw = True
		keypress = msvcrt.getch()
		if keypress == b'\r':
			break
		if keypress == b'\x1b':
			sys.exit()
		if keypress.lower() == b'1':
			breastsarray[0] = breastsarray[0] ^ 1
			breastsarray[6] = 0
		elif keypress.lower() == b'2':
			breastsarray[1] = breastsarray[1] ^ 1
			breastsarray[6] = 0
		elif keypress.lower() == b'3':
			breastsarray[2] = breastsarray[2] ^ 1
			breastsarray[6] = 0
		elif keypress.lower() == b'4':
			breastsarray[3] = breastsarray[3] ^ 1
			breastsarray[6] = 0
		elif keypress.lower() == b'5':
			breastsarray[4] = breastsarray[4] ^ 1
			breastsarray[6] = 0
		elif keypress.lower() == b'f':
			breastsarray[5] = breastsarray[5] ^ 1
		elif keypress.lower() == b'r':
			breastsarray = [0]*5 + [breastsarray[5]] + [1]
		else:
			redraw = False
	
	tagsadded = []
	if breastsarray[6]:
		tagsadded += ["-breasts"]
		tagsadded += removebreastimplications(breastimplications)
	else:
		if breastsarray[0]:
			tagsadded += ["small_breasts"]
		if breastsarray[1]:
			tagsadded += ["medium_breasts"]
		if breastsarray[2]:
			tagsadded += ["large_breasts"]
		if breastsarray[3]:
			tagsadded += ["huge_breasts"]
		if breastsarray[4]:
			tagsadded += ["gigantic_breasts"]
	
	if flatchest and not breastsarray[5]:
		tagsadded += ["-flat_chest"]
	if not flatchest and breastsarray[5]:
		tagsadded += ["flat_chest"]
	
	print("\nAdding Tags:\n")	
	print(tagsadded)
	
	return tagsadded


def main(args):
	global searchtags
	#TurnDebugOn('danbooru')
	
	if args.date != None:
		searchtags += " date:" + args.date
	else:
		searchtags += " id:" + args.id
	
	#Start downloader in new console so images can be downloaded in the background
	p = Popen([sys.executable,'postdownloader.py',searchtags],creationflags=CREATE_NEW_CONSOLE)
	
	#Get the page count for tagging
	tagsurl = GetArgUrl2('tags',searchtags)
	urladd = JoinArgs(tagsurl)
	countrequest = SubmitRequest('count','',urladdons=urladd)
	totalpages = ((countrequest['counts']['posts']-1)//pagelimit) + 1
	
	for x in range(0,totalpages):
		#Start in reverse order since adding/removing tags will affect post queries
		urladd = JoinArgs(tagsurl,GetArgUrl2('page',totalpages-x))
		postlist = SubmitRequest('list','posts',urladdons=urladd)
		
		for y in range(0,len(postlist)):
			
			#Check to see that postdownloader.py has already downloaded the file
			currfile = GetCurrFilePath(postlist[y])
			print("Checking file",currfile)
			while not os.path.exists(currfile):
					print('.', end="", flush=True)
					time.sleep(1)
			
			#Sleep again, to give the OS time to fully write the file
			time.sleep(1)
			
			#Start the downloaded file with its default viewer
			temp = os.startfile(currfile)
			
			#Configurable Alt Tab: gets back screen focus
			AltTab(1,0.1) 
			
			#Get user input for tagging
			pageinfo = (totalpages - x,totalpages,y+1,len(postlist))
			tagsadded = getuserkeypresses(postlist[y]["id"],postlist[y]["tag_string"],*pageinfo)
			
			#Now update the post
			putdata = EncodeData('post','tag_string',postlist[y]["tag_string"] + ' ' + ' '.join(tagsadded))
			response = SubmitRequest('update','posts',id=postlist[y]["id"],senddata=putdata)
	
	print("Done!")

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Tag Images From Danbooru")
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('-d','--date',type=DateStringInput,help="Date of images to tag",)
	group.add_argument('-i','--id',type=IDStringInput,help="ID's of images to tag")
	args = parser.parse_args()
	
	main(args)