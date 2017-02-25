# Uffizi - View all of the artwork for Plex sections at once
# Copyright (C) 2016  Jason Ellis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import urllib2, os, sys, string, urllib, httplib, getopt
import sqlite3, webbrowser

# Ensure lib added to path, before any other imports
# Thank you PlexPy for this!
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib/"))

import cherrypy
import mako

from mako.template import Template
from mako.lookup import TemplateLookup

import uffizi
from uffizi import *
from uffizi.api import *
from uffizi.database import *
from uffizi.plexserver import *

def launch_browser(get_token):
    if get_token:
        url = "http://localhost:3700/sign_in?redirect=home"
    else:
        url = "http://localhost:3700"
        
    webbrowser.open(url)

class Uffizi(object):
    
    def __init__(self):
        # Check if the data directory exists.  Create it if it doesn't.
        if not os.path.exists(uffizi.DIR_DATA):
            os.mkdir(uffizi.DIR_DATA)
            
        # Setup the database.
        db = Database()
        db.startup()
        
        # Set the plex.tv token to the global value uffizi.plex_token.  If no
        # token is found, set the flag that will cause the sign in page to be
        # displayed.
        uffizi.plex_token = db.get_stored_token()
        db.close()
    
        if uffizi.plex_token is None:
            uffizi.plex_token = ""
    
        if uffizi.plex_token == "":
            self.refresh_token = True
        else:
            self.refresh_token = False
                            
    def __refresh_servers(self):
        
        db = Database()
        
        # Get a list of servers from plex.tv
        try:
            devices = ET.ElementTree(file=
                        urllib2.urlopen("https://plex.tv/api/resources?" + \
                                        uffizi.PLEX_TOKEN_PARM + \
                                        uffizi.plex_token)).getroot()
        except:
            raise cherrypy.HTTPRedirect("error?error=PLEX_TV_UNREACHABLE")
        
        # Loop through the results from plex.tv and delete the data that 
        # Uffizi doesn't need.
        for device in devices:
            if device.get('product') == "Plex Media Server":
                server_name = device.get("name")
                platform = device.get("platform")
                owned = device.get("owned")
                
                db.delete_server(server_name)
                db.insert_server(server_name, platform, 'plex.tv')
                                
                # If the device is marked as "owned" add it to the list.
                if owned == "1":                
                    for connection in device:
                        if connection.get("local") == "1":
                            address = connection.get("address")
                            port = connection.get("port")
                            
                            # Check if the address/port combo can be connected 
                            # to.
                            if PlexServer.get_server_status(address, port)[0:1] in ('1', '2'):
                                valid = "Y"
                            else:
                                valid = "N"
                                
                            db.insert_server_addr(server_name
                                                 ,address
                                                 ,port
                                                 ,valid)
        db.commit()
        db.close()
                    
    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("home")
        
    @cherrypy.expose
    def error(self, error=""):
        # Get the error text to display from the MSG_TXT dictionary.
        errort_txt = uffizi.MSG_TXT[error]
        
        error_template = lookup.get_template("error.html")
        return error_template.render(error=errort_txt)
        
    @cherrypy.expose
    def sign_in(self, redirect, reason=""):
        if reason is None or reason == "":
            message = ""
        else:
            message = uffizi.MSG_TXT[reason]
            
        # The redirect parameter is the URL the user will be sent to after
        # successfully getting a token from plex.tv.
        sign_in_template = lookup.get_template("sign_in.html")
        return sign_in_template.render(redirect=redirect, reason=message)
        
    @cherrypy.expose
    def home(self, error=""):
        # Check if the database has plex servers stored in it.
        db = Database()
        servers = db.get_servers()
        
        if servers is None or len(servers) == 0:
            # No servers were found.  Get the list of servers from plex.tv.
            self.__refresh_servers()
            # Servers have been saved to the database, now get the list of
            # servers.
            servers = db.get_servers()
            
        db.close()
        
        home_template = lookup.get_template("home.html")
        return home_template.render(servers=servers)
        
    @cherrypy.expose
    def settings(self):
        settings_template = lookup.get_template("settings.html")
        return settings_template.render()
        
    @cherrypy.expose
    def server_edit(self, server):
        ps = PlexServer(server)
                    
        server_template = lookup.get_template("server_edit.html")
        return server_template.render(ps=ps)
        
    @cherrypy.expose
    def server(self, server):
        ps = PlexServer(server)
        
        if ps.simple_status == "down":
            raise cherrypy.HTTPRedirect("error?error=SERVER_UNREACHABLE")
        else:
            server_template = lookup.get_template("server.html")
            return server_template.render(server=server, videos=ps.get_sections())
        
    @cherrypy.expose
    def section(self, server="localhost", key="1", section="<empty>"):  
        ps = PlexServer(server)
        
        if ps.simple_status == "down":
            raise cherrypy.HTTPRedirect("error?error=SERVER_UNREACHABLE")
        else:
            cookieSet = cherrypy.response.cookie
            
            # Retrieve the cookie for the display mode (thumbs or list).
            cookie_display_mode = "displayMode-" + str(server) + "-" + str(key)
            cookie_display_mode = urllib2.quote(cookie_display_mode)
            
            # Use cookies to save the values of the URL parameters.  This seems 
            # easier than trying to deconstruct the URL query string in javascript.
            cookieSet["address"] = ps.address
            cookieSet["port"] = ps.port
            cookieSet["key"] = key
            cookieSet["section"] = section
    
            try:
                cookie = cherrypy.request.cookie
                display_mode = cookie[cookie_display_mode].value
            except KeyError:
                display_mode = "thumbs"
                cookieSet[cookie_display_mode] = display_mode
            
            # Get the items that are in this section.
            videos = ps.get_section_items(key)
            
            # This will be a dictionary that will hold the other dictionaries listed
            # below.  This will be the dictionary that will be handed off to the page
            # template.
            list_dict = {}
            
            # Build dictionaries that will hold the genres, collections, and 
            # playlist info.  For each dictionary, the key of the dictionary is the
            # key for the video and the value is a list that contains each of the 
            # genre/collection/playlists the video belongs to.  For playlists, if 
            # the item in the playlist is an episode/song, the entire show/artist 
            # is considered part of the playlist
            genre_dict = {}
            coll_dict = {}
            pl_dict = {}
            
            for video in videos:        
                rating_key = video.get("ratingKey")
                genre_dict[rating_key] = ["loading..."]
                coll_dict[rating_key] = ["loading..."]
                    
            # Get the list of playlists
            playlists = ps.get_playlists()
            
            # Loop through each playlist and get the individual items in the list.
            for playlist in playlists:
                playlist_title = playlist.get("title")
                playlist_key = playlist.get("key")
                
                # Get the individual items that make up the playlist.
                playlist_items = ps.get_playlist_items(playlist_key)
                
                # Loop through each item in the playlist.
                for video in playlist_items:
                    rating_key = video.get("ratingKey")
                    playlist_gp_key = video.get("grandparentRatingKey")
                    
                    # Check if the grandparent key is populated.  If it is, 
                    # this item is an episode or song.  In that case, we use
                    # the grandparent key as that is the TV show or artist that
                    # this item belongs to.
                    if not playlist_gp_key:
                        key_to_use = rating_key
                    else:
                        key_to_use = playlist_gp_key
                    
                    # Determine if this video has been added to the dictionay.
                    if pl_dict.has_key(key_to_use):
                        # Determine if this playlist has been added to the list
                        # that makes up the value portion of the dictionary 
                        # item.  This is needed since the playlist can contain 
                        # multiple episodes/songs from the same show/artist and
                        # the playlist only needs to be added once to the show/
                        # artist.
                        if pl_dict[key_to_use].count(playlist_title) == 0:
                            pl_dict[key_to_use].append(playlist_title)
                    else:
                        pl_dict[key_to_use] = [playlist_title]
            
            # Create the dictionary of dictionaries.
            list_dict = {"genre" : genre_dict, "collection" : coll_dict, "playlist" : pl_dict}
                            
            # Get the viewGroup attribute for the root node.  This determines what type
            # of section this is.  Values are:
            #  artist - music sections
            #  movie  - movie sections
            #  show   - TV show sections
            page_type = videos.attrib["viewGroup"]
            
            cookieSet["section_type"] = page_type
            
            section_template = lookup.get_template("section.html")
            return section_template.render(server=server
                                          ,page_type=page_type
                                          ,section=section
                                          ,videos=videos
                                          ,display_mode=display_mode
                                          ,lists=list_dict)  

    @cherrypy.expose
    def refresh_servers_redirect(self):
        self.__refresh_servers()
        raise cherrypy.HTTPRedirect("home")
        #raise cherrypy.HTTPRedirect("error?error=REFRESH_SERVERS")
        
# Configure CherryPy so that the webserver is visible on the LAN, not just the
# local machine.
cherrypy.config.update({"server.socket_host": "0.0.0.0",
                        "server.socket_port": 3700,
                       })

lookup = TemplateLookup(directories=["html"])

if __name__ == "__main__":
        
    # Get the command line switches/arguments.
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd", ["help","debug","nolaunch"])
    except getopt.GetoptError:
        # If there's an error getting the switches/arguments display the proper
        # format for launching Uffizi
        print "Uffizi.py [-d|--debug] [--nolaunch]"
        sys.exit(2)
        
    # Loop through each switch/argument pair and handle them.
    for opt, arg in opts:
        # Help switch - Display the format for the Uffizi command line and the 
        # supported switches.
        if opt in ('-h', '--help'):
            print "Uffizi.py [-d|--debug] [--nolaunch]"
            print "-d, --debug : Debug mode"
            print "--nolaunch  : Do not launch the web browser when Uffizi is started."
            print "              Ignored when a token is needed from plex.tv."
            sys.exit()
        elif opt in ("-d", "--debug"):
            uffizi.arg_debug = True
        elif opt == "--nolaunch":
            uffizi.arg_nolaunch = True
            
    if uffizi.arg_debug:
        print "UFFIZI COMMAND LINE OPTIONS"
        print " debug    : ", uffizi.arg_debug
        print " nolaunch : ", uffizi.arg_nolaunch
    
    # Configure settings for cherrypy.
    conf = {
         "/": {
             "tools.sessions.on": True,
             "tools.staticdir.root": os.path.abspath(os.getcwd())
         },
         "/playlist": {
             "request.dispatch": cherrypy.dispatch.MethodDispatcher(),
             "tools.response_headers.on": True,
             "tools.response_headers.headers": [("Content-Type", "text/plain")],
         },
         "/image": {
             "request.dispatch": cherrypy.dispatch.MethodDispatcher(),
             "tools.response_headers.on": True,
             "tools.response_headers.headers": [("Content-Type", "text/plain")],
         },
         "/metadata": {
             "request.dispatch": cherrypy.dispatch.MethodDispatcher(),
             "tools.response_headers.on": True,
             "tools.response_headers.headers": [("Content-Type", "text/plain")],
         },
         "/token": {
             "request.dispatch": cherrypy.dispatch.MethodDispatcher(),
             "tools.response_headers.on": True,
             "tools.response_headers.headers": [("Content-Type", "text/plain")],
         },
         "/server_status": {
             "request.dispatch": cherrypy.dispatch.MethodDispatcher(),
             "tools.response_headers.on": True,
             "tools.response_headers.headers": [("Content-Type", "text/plain")],
         },
         "/add_server": {
             "request.dispatch": cherrypy.dispatch.MethodDispatcher(),
             "tools.response_headers.on": True,
             "tools.response_headers.headers": [("Content-Type", "text/plain")],
         },
         "/refresh_servers": {
             "request.dispatch": cherrypy.dispatch.MethodDispatcher(),
             "tools.response_headers.on": True,
             "tools.response_headers.headers": [("Content-Type", "text/plain")],
         },
         "/get_server_details": {
             "request.dispatch": cherrypy.dispatch.MethodDispatcher(),
             "tools.response_headers.on": True,
             "tools.response_headers.headers": [("Content-Type", "text/plain")],
         },
         "/edit_server_details": {
             "request.dispatch": cherrypy.dispatch.MethodDispatcher(),
             "tools.response_headers.on": True,
             "tools.response_headers.headers": [("Content-Type", "text/plain")],
         },
         "/static": {
             "tools.staticdir.on": True,
             "tools.staticdir.dir": "./static"
         },
    }
    webapp = Uffizi()
    webapp.playlist = GetPlaylists()
    webapp.image = GetImage()
    webapp.metadata = GetMetaData()
    webapp.token = GetPlexToken()
    webapp.server_status = GetServerStatus()
    webapp.add_server = AddServer()
    webapp.refresh_servers = RefreshServers()
    webapp.get_server_details = GetServerDetails()
    webapp.edit_server_details = EditServerDetails()
    
    #cherrypy.quickstart(webapp, "/", conf)
    cherrypy.tree.mount(webapp, '/', conf)

    # Start up cherrypy.  If a Plex token is needed, the sign in page will be 
    # shown.  If a token is not needed, and the nolaunch switch is not set, the
    # home page will be shown.  If the nolaunch switch is set, cherrypy will 
    # launch, but the user will not be redirected to a web browser.  If a token
    # is needed the nolaunch switch is ignored.
    if webapp.refresh_token or not uffizi.arg_nolaunch:
        cherrypy.engine.start_with_callback(launch_browser(webapp.refresh_token))
    else:
        cherrypy.engine.start()
        
    cherrypy.engine.block()
    