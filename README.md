# PlexArt
PlexArt is a Python web app for getting a better view of the artwork used in Plex.  It will show you thumbnails of the posters and background for all of the items in a section.

## Background
Do you like it when all of the posters for your Star Wars movies match, or all of the seasons for your Simpsons collection are in the same style, or the background for all of the Star Trek TV shows share a theme?  Me too!  Only problem, with Plex you have to go into each movie/show to see what's set and to see what's available.  Then there's a bunch of clicking ot get the artwork changed.  I wanted a way to be able to see the posters and background artwork for all items in a section, and thus PlexArt was born.

## Install
Make sure you have Python installed.  This was developed on Python 2.7.10.  It has not yet been tested on other versions so I don't know if it will work or not.

1. Download the project from [here](https://github.com/jealousrobot/PlexArt/archive/master.zip).
2. Move the downloaded folder to where ever you want it on your system.
3. In the terminal, navigate to the folder.
4. Run PlexArt.py with the command `python PlexArt.py`.

You do not need to install PlexArt on the same server that is running the Plex Media Server.

## Using
PlexArt is accessed via your browser.

If using the browser on the same machine that is running PlexArt.py, you can access PlexArt via http://localhost:3700.  

If using a browser on a machine that is not running PlexArt.py, you can access PlexArt via http://<host name>:3700, replacing <host name> with the actual name of the computer running the app.

Once the webpage has loaded you'll be presented with a page where you can enter details on your sever that will allow PlexArt to connect and retrieve data from it.  You'll need to get the URL from your Plex Media Manager page in order to fill in these details.  The address to the Media Manager, may look like the following:
* http://127.0.0.1:32400/web/index.html
* http://localhost:32400/web/index.html
* http://jayne.local:32400/web/index.html
* http://192.168.0.37:32400/web/index.html

We are interested in in the server name/addres and the port number.  The server name/address is the value that appears between the two slashes and the colon.  In the examples above that would be:
* 127.0.0.1
* localhost
* jayne.local
* 192.168.0.37

The port is the numerical value that appears after the colon.  In all four examples above that would be 32400, which is the default port for Plex.

Now that we have these two values, enter them in the appropriate fields on the webpage for Uffizi and press the Submit button.  Once a server is successfully connected to it will appear in a list below the Submit button so you won't need to do it again.

You will now be taken to the sections that are available on the server.  Photo sections are not displayed as they do not have any artwork associated with them.  Pick the one you'd like to view.

The next page will show you thumbnails of the posters and background artwork for all items in that section.  Using the refresh button on the lower right of each item will refresh the artwork for the item.  This is useful for when you update the artwork using the Plex Media Manager.  If the item is a TV show or a music artist a down arrow icon will also appear next to the refresh icon.  Pressing this icon will expand a tray showing the season or album artwork for the item.

## Acknowledgement
This project would not be possible without [PlexPy](https://github.com/drzoidberg33/plexpy).  Having that for a reference was invaluable in creating Uffizi

## License
Uffizi is licensed under GPL v3.0.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

Uffizi uses the following 3rd party packages/scripts:
* [CherryPy](http://www.cherrypy.org/)
* [Mako Templates for Python](http://www.makotemplates.org/)
* [jQuery](https://jquery.com/)
* [jQuery UI](https://jqueryui.com/)
* [jQuery Rotate](http://jqueryrotate.com/)

See their websites for the licenses involved with them.

## Change Log
### 0.1.3.2 Module Load Order Fix
#### New Features
None
#### Bug Fixes
1. 37 - Fixed issue that was cuasing Uffizi to not load on any machine except the dev machine.  This was due to the order in which modules were imported.

### 0.1.3.1 Now with less now since I'm tired of coming up with nows
#### New Features
1. Addition of plexserver.py file which consolidates methods for accessing data from a Plex server to one place.
2. Added commit and close method to database.py.
3. Some code tidying up.
#### Bug Fixes
None

### 0.1.3.0 Now with more Uffizi and less PlexArt
#### New Features
1. Turns out third-party apps can't contain the word "Plex".  PlexArt is now Uffizi.
#### Bug Fixes
None

### 0.1.2.1 Now with masked passwords
#### New Features
None
#### Bug Fixes
1. Changed the password input box to a masked input box.  It was inadvertantly left as a regular text which was used during testing as to make sure passwords were entered correctly to avoid validation failures.

### 0.1.2 Now with Plex.tv token support
#### New Features
None
#### Bug Fixes
1. Added support for using plex.tv tokens.  Tokens were made mandatory by Plex for accessing a server in PMS version 1.0+.