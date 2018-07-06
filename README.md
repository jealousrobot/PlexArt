# Uffizi
Uffizi is a Python web app for getting a better view of the artwork used in Plex.  It will show you thumbnails of the posters and background for all of the items in a section.

## Background
I was setting up a new server and was in the process of updating the artwork for each TV show, movie, etc. to the images that I liked.  One of the things I like to do is make sure that the artwork for a set matches, i.e. all of the seasons for a TV show are the same or all of the backgrounds for a movie trilogy are similar.  I was finding it annoying to have to bounce back and forth between different media items to see if they matched, and thought it would be great if I could see all of the background artwork at once.  Nothing that I was aware of did that, so I built Uffizi.

While Uffizi was created to fill a need, I also did it so that I could learn Python, and brush up on some CSS, HTML, and Javascript.  **NOTE** I'm no expert at Python or web stuff.  Use Uffizi at your own risk.

## Install
Make sure you have Python installed.  This was developed on Python 2.7.10.  It has not yet been tested on other versions so I don't know if it will work or not.

1. Download the project from [here](https://github.com/jealousrobot/Uffizi/archive/master.zip).
2. Move the downloaded folder to where ever you want it on your system.
3. In the terminal, navigate to the folder.
4. Run Uffizi.py with the command `python Uffizi.py`.  You can use `python Uffizi.py --help` for a full list of options when starting Uffizi.

You do not need to install Uffizi on the same server that is running the Plex Media Server.

## Using
Uffizi is accessed via your browser.

If using the browser on the same machine that is running Uffizi.py, you can access Uffizi via http://localhost:3700.  Uffizi will launch a browser when it is first launched.

If using a browser on a machine that is not running Uffizi.py, you can access Uffizi via http://<host name>:3700, replacing <host name> with the actual name of the computer running the app.

If this is the first time running Uffizi, you will be prompted for your plex.tv credentials.  In order for Uffizi to access your server, it requires a token from plex.tv.  Uffizi does not store your login credentials.  Just the token that is provided by plex.tv (this is similar to other tools like PlexPy).

### Adding Servers
Once it has a token, Uffizi will get a list of servers you've registered at plex.tv and will display them on the Uffizi home page.  

You can also manually enter a server for any unclaimed Plex servers on your network.  To manually enter a server you'll need to get the URL from your Plex Media Manager page.  The address to the Media Manager, may look like the following:
* http://127.0.0.1:32400/web/index.html
* http://localhost:32400/web/index.html
* http://myplexserver.local:32400/web/index.html
* http://192.168.0.37:32400/web/index.html

We are interested in in the server name/address and the port number.  The server name/address is the value that appears between the two slashes and the colon.  In the examples above that would be:
* 127.0.0.1
* localhost
* jayne.local
* 192.168.0.37

The port is the numerical value that appears after the colon.  In all four examples above that would be 32400, which is the default port for Plex.

Now that we have these two values, click the "+" button in the upper right corner of the Uffizi homepage.  This will display a window where the server details can be entered.  Enter the server and port in the appropriate fields press the Submit button.  Once a server is successfully connected to you will be taken to the server's page showing the sections available in the server.

### Viewing Sections on a Server
To view the sections available on a server, click on the server's image or name on the Uffizi home page.  This will take you to the server's page where the list of sections on the server are displayed.  Photo sections are not displayed as they do not have any artwork associated with them.  

### Viewing Artwork in a Section
Click on one of the sections in a server and you will be taken to a page that will show you thumbnails of the posters and background artwork for all items in that section.  Using the refresh button on the lower right of each item will refresh the artwork for the item.  This is useful for when you update the artwork using the Plex Media Manager.  If the item is a TV show or a music artist a down arrow icon will also appear next to the refresh icon.  Pressing this icon will expand a tray showing the season or album artwork for the item.

## Acknowledgement
This project would not be possible without [Tautulli](https://github.com/Tautulli/Tautulli).  Having that for a reference was invaluable in creating Uffizi

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
### 0.2.2
#### New Features
1. Reworked body.html to make it reliant on a custom XML dataset instead of using the XML as delivered from the Plex API.  This should make the page easier to expand in the future. (27)
2. Added logging using the Python loggin module.  Launch Uffizi with the -d switch to make use of this. (43)
3. Created a new details page for an item.  Clicking on the name of an item will now take you to a page for just that item.  For now the page just shows what can be seen in the list view, but future enhancements will bring more details. (20).
#### Bug Fixes
1. Choosing to save an image will now save the image in an image format, not text. (51)
2. List or thumbnail mode will be remembered using the back button or refresh. (50)
3. When refreshing an item, "none" will be displayed when the item doesn't contain anything in that field.  For example, "none" will be displayed in the Collections field if the item doesn't belong to any collections. (49)
4. Refreshing a TV show will no longer show duplicates in the Playlist field. (48)
5. Fixed typos in the README.MD file. (23)


### 0.2.1 
#### New Features
1. Issue tracking has moved to GitHub.  All referenced issue numbers from this release forward relate to issues on GitHub. (16)
#### Bug Fixes
1. Fixed missing image for a Plex cloud server. (15)

### 0.2.0 Server Enhancement Edition
#### New Features
1. When you sign in for the first time, Uffizi will now fetch a list of servers from plex.tv avoiding the need to manually add servers.  This will only work on servers that you have claimed.  An unclaimed server on your network will still need to be entered manually (9).
2. Uffizi will now check if a server is online when you visit the Uffizi homepage.  If the server is offline you will not be able to visit it.  Online servers have a green checkmark next to the server name.  Offline servers have a red "x".  (13)
3. Some server details can now be edited. (22)
4. Data need by Uffizi is now stored in a database instead of text file. (25)
5. Servers on the homepage are now represented by graphics showing the OS of the server and a title bar instead of a button.  This makes the homepage visually look similar to the server and section pages. (35)
6. When starting Uffizi, if a token is needed, the browser will launch with the sign-in page displayed. (38)
7. Added command line switches to be used when starting Uffizi.  Enter "python Uffizi.py --help" for a full list. (39)
8. Add button on the homepage to refresh servers from plex.tv. (43)
9. Removed the form on the home page for adding a server.  Adding a server manually can now be done by using the "+" button in the toolbar on the homepage. (48)
10. Updated README.md file with new instructions for using Uffizi based on the changes for how servers are now populated from plex.tv and the moving of the manual form to the toolbar.
11. Created new page for displaying error messages. (49)
#### Bug Fixes
1. Fixed issue where the scrollbar background area would show up even if there was no scrollbar. (33)
2. Fixed issue where the scrollbar wasn't showing up on the home page. (34)
3. In a music section, fixed issue where the TV thumbnail was shown on missing artwork instead of the music thumbnail. (40)
4. Removed references to PlexArt in the README.md file. (46)

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
1. Changed the password input box to a masked input box.  It was inadvertently left as a regular text which was used during testing as to make sure passwords were entered correctly to avoid validation failures.

### 0.1.2 Now with Plex.tv token support
#### New Features
None
#### Bug Fixes
1. Added support for using plex.tv tokens.  Tokens were made mandatory by Plex for accessing a server in PMS version 1.0+.