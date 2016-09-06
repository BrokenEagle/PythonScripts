1. Original Environment Details

	a. Operating System -	Windows 7
	b. Script Language - 	Python 3.5

2. Library Files

	a. myglobal.py - 	Global variables for customizing script environment
	b. misc.py 	 	Functions that are universally applicable to any script
	c. danbooru.py - 	Functions specifically to help communicate with Danbooru

3. Application Files

	a. userreport.py -	Collects data for the preceding month for various categories
				End product is a CSV file.
	
	b. dtexttable.py - 	Create a Danbooru DText table from the data collected by userreport.py
				End product is a TXT file.

	c. taggardening.py - 	Interactive tagging on Danbooru for a given Date or ID range
	
	d. postdownloader.py -	Download all medium-sized images from Danbooru for a given tag search query
		

4. Other Files

	a. tagdict.txt - 	Contains 60K+ tag entries; Will drastically reduce the amount of tag
				misses as compared to starting a brand new tag dictionary.

5. Setup

	a. Adjust settings in myglobal.py
	
		username: 		Your Danbooru username
		apikey: 		Your Danbooru apikey; found on Danbooru user profile under API Key.
		workingdirectory: 	Base directory where the scripts can write files.
		datafilepath: 		Directory in workingdirectory where the data gets saved periodically
					in a text file.
		csvfilepath: 		Directory in workingdirectory where the CSV file gets saved.
		dtextfilepath: 		Directory in workingdirectory where the text file with the DText 
					table get saved.
		imagefilepath: 		Directory in workingdirectory where images from Danbooru will be 
					downloaded to.
	
	b. Move the tagdict.txt into the "workingdirectory"

6. Usage Notes

a. userreport.py

	Some of the reports take quite a while to fully generate. The 'uploads' report takes the longest
	at around 2-3 hours to complete.  The other reports noted for lengthy collection times are:
	post, note, artist_commentary, in the order of collection time length.

	The program supplies some feedback, notably a ':' whenever it sends a request to Danbooru for
	a new list.  It'll print a number once a day has been fully collected, and the number reflects
	how many days have been collected so far.

b. taggardening.py

	The program uses the systems native file opener, which for the system of development was IrfanView for JPG/PNG, 
	Internet Explorer for GIF, and Media Player Classic for WEBM.
	
	The program sends an Alt+Tab (which is configurable) to the system to gain back focus after opening up the file.
	
	The current hotkeys are 1-5, 'r', 'x', Enter, and Escape.
	
	Use involved having the console window on the right of the screen and the file opener on the left side.
