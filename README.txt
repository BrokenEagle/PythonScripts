1. Environment Details
	a. Operating System
		Windows 7
	b. Programming Language
		Python 3.5

2. Library Files
	a. myglobal.py - Global variables for customizing script environment
	b. misc.py - Functions that are universally applicable to any script
	c. danbooru.py - Functions specifically to help communicate with Danbooru

3. Application Files
	a. userreport.py -	Collects data for the preceding month for various categories
				End product is a CSV file.
		USAGE: 
		userreport.py categoryname [new]
			
		Options:
		categoryname:	post,upload,note,artist_commentary,pool,artist,wiki_page,
				forum_topic,forum_post,tag_implication,tag_alias,
				bulk_update_request,post_appeal,comment
			
		new (optional): Creates a new report, overwriting any existing report.
								
				Data collection can be stopped partway through and resumed in
				the same location by excluding this input.  Useful in case an
				exception gets thrown at any point in the process.
	
	b. dtexttable.py (coming) - Create a Danbooru DText table from the data collected by userreport.py

4. Other Files
	a. tagdict.txt: Contains 60K+ tag entries; Will drastically reduce the amount of tag
			misses as compared to starting a brand new tag dictionary.

5. Setup
	a. Adjust settings in myglobal.py
		username: Your Danbooru username
		apikey: Your Danbooru apikey; found on Danbooru user profile under API Key.
		workingdirectory: Base directory where the scripts can write files.
		datafilepath: Directory in workingdirectory where the data gets saved periodically in a text file.
		csvfilepath: Directory in workingdirectory where the CSV file gets saved.
		dtextfilepath: Directory in workingdirectory where the text file with the DText table get saved.
		imagefilepath: Directory in workingdirectory where images from Danbooru will be downloaded to.
	
	b. Move the tagdict.txt into the "workingdirectory"

6. Usage Notes

Some of the reports take quite a while to fully generate. The 'uploads' report takes the longest
at around 2-3 hours to complete.  The other reports noted for lengthy collection times are:
post, note, artist_commentary, in the order of collection time length.

The program supplies some feedback, notably a ':' whenever it sends a request to Danbooru for
a new list.  It'll print a number once a day has been fully collected, and the number reflects
how many days have been collected so far.
