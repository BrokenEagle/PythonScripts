1. Original Environment Details

    a. Operating System -    Windows 7
    b. Script Language -     Python 3.5

2. Library Files

    a. myglobal.py -        Global variables for customizing script environment
    b. misc.py -            Functions that are universally applicable to any script
    c. danbooru.py -        Functions specifically to help communicate with Danbooru
    d. dtext.py -           Functions that help create DText tables
    e. implications.py -    Gets the current sets of implications for a tag.
    f. keyoutput.py -       Allows for key output to be programmatically be sent to the system
    g. terminalsize.py -    Gets the current size of the console

3. Application Files

    a. userreport.py -  Collects data for the preceding month for various categories
        (Currently being reworked)
    
    b. toptags.py -     Collects data for the preceding month on top taggers
        (Currently being reworked)
    
    c. taggarden.py -   Interactive tagging for Danbooru

4. Other Files

    a. tagdict.txt -    Contains 60K+ tag entries; Will drastically reduce the amount
                        of tag misses as compared to starting a brand new tag dictionary.

5. Setup

    a. Adjust settings in myglobal.py
    
        username:           Your Danbooru username
        apikey:             Your Danbooru apikey; found on Danbooru user profile under API Key.
        workingdirectory:   Base directory where the scripts can write files.
        datafilepath:       Directory in workingdirectory where the data gets saved
                            periodically in a text file.
        csvfilepath:        Directory in workingdirectory where the CSV file gets saved.
        dtextfilepath:      Directory in workingdirectory where the text file with the DText 
                            table gets saved.
        imagefilepath:      Directory in workingdirectory where images from Danbooru will
                            be downloaded to.
    
    b. Move the tagdict.txt into the "workingdirectory" (this step is only for userreport.py)

6. Usage Notes

a. userreport.py

    Some of the reports take quite a while to fully generate. The 'uploads' report takes
    the longest at around 2-3 hours to complete.  The other reports noted for lengthy
    collection times are: post, note, artist_commentary, in the order of collection time
    length.

    The program supplies some feedback, notably a ':' whenever it sends a request to
    Danbooru for a new list.  It'll print a number once a day has been fully collected,
    and the number reflects how many days have been collected so far.

b. taggarden.py

    The program uses the systems native file opener, which for the system of development
    was IrfanView for JPG/PNG, Internet Explorer for GIF, and Media Player Classic for WEBM.
    
    With implications.py, the program will show all tags related by implications, and present
    them for removal as needed.
    
    With keyoutput.py, the program sends an Alt+Tab (which is configurable) to the system to
    gain back focus after opening up the file. 
    
    With terminalsize.py, the console window can be resized and adjusted on the fly using F5.
    
    Use the -h or --listhotkeys command line arguments for more program information.
    
    Program use involved having the console window on the right of the screen and the file
    opener on the left side.
