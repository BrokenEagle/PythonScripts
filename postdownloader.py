#POSTDOWNLOADER.PY

#PYTHON IMPORTS
import re
import os
import sys
import argparse

#MY IMPORTS
from misc import TurnDebugOn,CreateDirectory
from danbooru import SubmitRequest,JoinArgs,GetArgUrl2,GetCurrFilePath,GetServFilePath,DownloadPostFile

#LOCAL GLOBALS

pagelimit = 100

#LOCAL FUNCTIONS

def main(args):
	#TurnDebugOn('danbooru')
	
	#Get pagecount for download request
	urladd = JoinArgs(GetArgUrl2('tags',args.tags))
	countrequest = SubmitRequest('count','',urladdons=urladd)
	totalpages = ((countrequest['counts']['posts']-1)//pagelimit) + 1
	
	for x in range(0,totalpages):
		#Start in reverse order like taggardening.py
		urladd = JoinArgs(GetArgUrl2('tags',args.tags),GetArgUrl2('page',totalpages-x))
		postlist = SubmitRequest('list','posts',urladdons=urladd)
		
		for y in range(0,len(postlist)):
			#Download from server to local
			DownloadPostFile(postlist[y])
			
			#Are we downloading all child/parent posts?
			if args.related and (postlist[y]['has_visible_children'] or postlist[y]['parent_id'] != None):
				totaldownloaded = len(getrelatedposts(postlist[y],[postlist[y]['id']]))
				print("(R%d)" % totaldownloaded,end="",flush=True)
			
			#print some feedback
			if (y%10)==0:
				print(y, end="", flush=True)
			else:
				print('.', end="", flush=True)
		
		print(':', end="", flush=True)

	input("Press any key to exit")

def getrelatedposts(postdict,alreadydownloaded):
	"""Recursively download all child and parent posts"""
	
	#Download any parent posts
	if (postdict['parent_id'] != None) and (postdict['parent_id'] not in alreadydownloaded):
		parentdict = SubmitRequest('show','posts',id=postdict['parent_id'])
		DownloadPostFile(parentdict)
		alreadydownloaded += [parentdict['id']]
		alreadydownloaded = getrelatedposts(parentdict,alreadydownloaded)
	
	#Download any child posts
	if postdict['has_visible_children']:
		childdict = SubmitRequest('list','posts',urladdons="&tags=parent:%d" % postdict['id'])
		for i in range(0,len(childdict)):
			if childdict[i]['id'] not in alreadydownloaded:
				DownloadPostFile(childdict[i])
				alreadydownloaded += [childdict[i]['id']]
				alreadydownloaded = getrelatedposts(childdict[i],alreadydownloaded)
	
	return alreadydownloaded

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Download Images From Danbooru")
	parser.add_argument('tags',help="Danbooru Tag Query String")
	parser.add_argument('--related', help="Download related images",action="store_true",default=False)
	args = parser.parse_args()
	
	main(args)