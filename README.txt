-------------------------------------
   Ace of Spades Server Browser
       By Jonathan Mackenzie
               2011
-------------------------------------

~~~~~~~~~~Contents~~~~~~~~~~~~~~~~~~~

A. Running
B. Building
C. Todo

*********Running*********************

1. Extract the contents of this archive into a 
   folder on your computer

2. Run 'AoS-ServerBrowser.exe' from the dist subfolder

3. Click on a server to attempt to join it!

4. Enjoy the grey sea!

*********Building********************

Source is available in the src folder.
If you want to edit the script you'll need
python and pygtk installed.
If you want to distribute your own build,
you'll need to install cxfreeze, then from the
source folder, run:
cxfreeze AoS-ServerBrowser.py --target-dir dist --base Win32GUI --icon diamonds.ico

********Todo*************************

1. Make it work with Wine on GNU/Linux and Mac OS X

2. Functionality to switch between skin packs
