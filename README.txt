1. Original Environment Details

    a. Operating System -    Windows 7 / Ubuntu 16
    b. Script Language -     Python 3.5

2. Library Files

    a. myglobal.py -        Global variables for customizing script environment.
    b. misc.py -            Functions that are universally applicable to any script.
    c. danbooru.py -        Functions specifically to help communicate with Danbooru.
    d. dtext.py -           Functions that help create DText tables.
    e. implications.py -    Gets the current sets of implications for a tag.
    f. keyoutput.py -       Allows for key output to be programmatically be sent to the system.
    g. terminalsize.py -    Gets the current size of the console.
    h. pixivapiwrap.py -    Wrapper for PixivPy. Manages error conditions, performs common
                            data operations, and keeps the user logged in.

3. Application Files

    a. taggarden.py -       Interactive tagging for Danbooru
    
    b. checkpixivimages.py - Organizes a collection of images downloaded from Pixiv.
    
    c. watchdog.py          Monitors a Python program and restarts as needed

4. Other Files

    a.  Installation files

        Installs packages and required modules, and sets environment variables.

        - INSTALL.windows - Rename to a .bat file and run.
        - INSTALL.linux - Rename to a .sh file, set execution permission, and run.

5. Setup

    a. Run installation files. Refer to section 4 above.

    b. Adjust settings in myglobal.py

        username:           Your Danbooru username.
        apikey:             Your Danbooru apikey; found on Danbooru user profile under API Key.
        pixivusername:      Your Pixiv username.
        pixivpassword:      Your Pixiv password.
        workingdirectory:   Base directory where the scripts can write files.
        datafilepath:       Directory in workingdirectory where the data gets saved
                            periodically in a text file.
        csvfilepath:        Directory in workingdirectory where the CSV file gets saved.
        dtextfilepath:      Directory in workingdirectory where the text file with the DText 
                            table gets saved.
        imagefilepath:      Directory in workingdirectory where images from Danbooru will
                            be downloaded to.

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

    The program uses the systems native file opener, which for Windows was IrfanView for JPG/PNG,
    Internet Explorer for GIF, and Media Player Classic for WEBM.  For Linux, Geeqie was used
    for JPG/PNG/GIF.  The execution parameters for Geeqie was "geeqie -r %F" in its .desktop file.
    The default application for a MIME type can be set in the ~/.config/mimeapps.list. See
    https://wiki.archlinux.org/index.php/default_applications for more information.
    
    With implications.py, the program will show all tags related by implications, and present
    them for removal as needed.
    
    With keyoutput.py, the program sends an Alt+Tab (which is configurable) to the system to
    gain back focus after opening up the file (Windows Only). 
    
    With terminalsize.py, the console window can be resized and adjusted on the fly using F5.
    
    Use the -h or --listhotkeys command line arguments for more program information.
    
    Program use involved having the console window on the right of the screen and the file
    opener on the left side.

  c. checkpixivimages.py

    The program organizes images downloaded from Pixiv based on their status on Pixiv and
    Danbooru.  This includes whether the image name is properly formatted, whether the image
    exists on Danbooru and/or Pixiv, and whether the image is an MD5 match with Danbooru
    and/or Pixiv.

  d. watchdog.py

    Have a global variable "watchdogfile" in the monitored application that points to a file.
    Have the application continue to write to or touch that file in the main execution loop to
    establish its heartbeat. Adjust the parameters on the watchdog application as necessary to
    restart the application when a lockup has been detected.