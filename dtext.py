#DTEXT.PY

#Include functions used to format with dtext here

#PYTHON IMPORTS

#LOCAL IMPORTS
from misc import CreateOpen
from myglobal import workingdirectory

__all__ = ['WriteDtextFile','ConstructTable']

#EXTERNAL FUNCTIONS

#Python formats lines differently based on whether the line has a " or not
#So first write the file to a temporary location, then process it line by line
def WriteDtextFile(dtextfile,dtextstring):
	"""Input is a filepath and DText string"""
	
	with CreateOpen(workingdirectory + 'temp.txt','wb') as f:
		f.write(dtextstring.encode('UTF'))
	
	with open(workingdirectory + 'temp.txt','rb') as infile, CreateOpen(dtextfile,'wb') as outfile:
		for line in infile:
			if line.find(b"'") > 0 and line.find(b'"') < 0:
				line = line.replace(b'\'',b'"')
			outfile.write(line)

def ConstructTable(columnlist,datalist,isrank=True):
	"""Construct a Dtext table from a column list and 2D datalist"""
	
	tablehead = ''
	if isrank:
		tablehead += AddTableHeader("Rank")
	for column in columnlist:
		tablehead += AddTableHeader(column)
	tablehead = AddTableHead(AddTableRow(tablehead))
	tablebody = ""
	for i in range(0,len(datalist)):
		tempstr = ''
		if isrank:
			tempstr += AddTableHeader(i+1)
		for j in range(0,len(datalist[i])):
			tempstr += AddTableData(datalist[i][j])
		tablebody += AddTableRow(tempstr)
	tablebody = AddTableBody(tablebody)
	return AddTable(tablehead+tablebody)

#HELPER FUNCTIONS

def AddTable(input):
	return '[table]\r\n' + input + '[/table]\r\n'

def AddTableHead(input):
	return '[thead]\r\n' + input + '[/thead]\r\n'

def AddTableBody(input):
	return '[tbody]\r\n' + input + '[/tbody]\r\n'

def AddTableRow(input):
	return '[tr]\r\n' + input + '[/tr]\r\n'

def AddTableHeader(input):
	return '[th]' + str(input) + '[/th]\r\n'

def AddTableData(input):
	return '[td]' + str(input) + '[/td]\r\n'
