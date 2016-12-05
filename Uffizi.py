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
import urllib2, os, sys, string, urllib
import sqlite3

import uffizi
from uffizi import *
from uffizi.api import *
from uffizi.database import *
from uffizi.plexserver import *

# Ensure lib added to path, before any other imports
# Thank you PlexPy for this!
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib/"))

import cherrypy
import mako

from mako.template import Template
from mako.lookup import TemplateLookup

class Uffizi(object):
    
    def __init__(self):
        
        found = True
        
        # Check if the servers.xml file exists.  This file holds the list of 
        # previously visited servers.
        if os.path.exists(SERVER_FILE):
            try:
                self.servers_XML = ET.ElementTree(file=SERVER_FILE)
                self.servers = self.servers_XML.getroot()
            except ET.ParseError:
                found = False
        else:
            found = False
            
        if not found:
            # Create the file with the root node.
            self.servers = ET.Element("servers")
            self.servers_XML = ET.ElementTree(self.servers)
            self.servers_XML.write(SERVER_FILE)
        
        # Check if the data directory exists.
        if not os.path.exists(DIR_DATA):
            os.mkdir(DIR_DATA)
            
        # Setup the database.
        db = Database()
        db.startup()
        
        # Check for a Plex token.  If one is not found, the user will be
        # asked to log in to plex.tv when they first visit Uffizi.
        self.plex_token = db.get_stored_token()
                
    def check_token(self, server, port):
        get_token = False
        
        # Refresh the token.  
        db = Database()
        self.plex_token = db.get_stored_token()
        db.close()
        
        # If the token is empty, then have it refreshed.
        if self.plex_token is None or self.plex_token == "":
            get_token = True
        else:
            # Token is populated, but make sure that it's still a valid token.
            try:
                # If server and port are both 'x', check_token is being called
                # when Uffizi is started for the very first time.  No need to
                # check if the token is valid against a server, since there is 
                # no known server and the token was just fetched.
                if server != "x" and port != "x":
                    library_xml = ET.ElementTree(file=urllib2.urlopen(self.__build_url(server, port), "/library"))
            except:
                get_token = True
        
        # One of the validations failed.  Send the user to the sign in page to
        # get a new token.
        if get_token:
            redirect_url = urllib.quote_plus(cherrypy.url(qs=cherrypy.request.query_string))
            raise cherrypy.HTTPRedirect("sign_in?redirect=" + redirect_url)
                    
    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("home")
        
    @cherrypy.expose
    def sign_in(self, redirect):
        sign_in_template = lookup.get_template("sign_in.html")
        return sign_in_template.render(redirect=redirect)
        
    @cherrypy.expose
    def home(self):
        if self.plex_token is None or self.plex_token == "":
            self.check_token("x", "x")
        
        home_template = lookup.get_template("home.html")
        return home_template.render(servers=self.servers)
        
    @cherrypy.expose
    def server(self, server="localhost", port="32400"):
        self.check_token(server, port)   
        
        ps = PlexServer(server, port)
        
        #Get the friendly name of the server.
        friendly_name = ps.get_friendly_name()
        
        #Get the list of sections.
        library = ET.ElementTree(file=urllib2.urlopen(ps.get_url("/library/sections")))
        
        videos = library.getroot()
        
        # Determine if the server is saved in the XML file        
        found = False
        for instance in self.servers: 
            # instance[0] accesses the server tag and [1] the port tag.
            if server == instance[0].text and port == instance[1].text:
                # Check if the friendly name of the server has been updated
                # since the last time the server was visited by Uffizi.  If so
                # update the XML with the new value.
                if friendly_name != instance[2].text:
                    instance[2].text = friendly_name
                    self.servers_XML.write(SERVER_FILE)
                
                found = True
                break
        
        # If not found, add the server to the XML.
        if not found:
            # Build the <server> element.
            server_elem = ET.Element("server")
            address_elem = ET.SubElement(server_elem, "address")
            address_elem.text = server
            port_elem = ET.SubElement(server_elem, "port")
            port_elem.text = port
            friendly_elem = ET.SubElement(server_elem, "friendlyName")
            friendly_elem.text = friendly_name
            
            # Add the new element to the existing set.
            self.servers.append(server_elem)
            
            # Write the changes to the file.
            
            # When ElementTree writes out XML it's all in one line.  That's ugly
            # and hard to read.  Convert the XML to a string, pretty it up, and
            # then write to a file.
            xml_string = ET.tostring(self.servers, "utf-8")
            xml_format = minidom.parseString(xml_string)
            
            xml_file = open(SERVER_FILE, "w")
            xml_file.write(xml_format.toprettyxml(indent="  "))
                
            xml_file.close()
            
        server_template = lookup.get_template("server.html")
        return server_template.render(server=server, port=port, friendly_name=friendly_name, videos=videos)
        
    @cherrypy.expose
    def section(self, server="localhost", port="32400", key="1", section="<empty>"):  
        self.check_token(server, port)        
        
        ps = PlexServer(server, port)
        
        cookieSet = cherrypy.response.cookie
        
        # Retrieve the cookie for the display mode (thumbs or list).
        cookie_display_mode = "displayMode-" + str(server) + "-" + str(key)
        cookie_display_mode = urllib2.quote(cookie_display_mode)
        
        # Use cookies to save the values of the URL parameters.  This seems 
        # easier than trying to deconstruct the URL query string in javascript.
        cookieSet["server"] = server
        cookieSet["port"] = port
        cookieSet["key"] = key
        cookieSet["section"] = section

        try:
            cookie = cherrypy.request.cookie
            display_mode = cookie[cookie_display_mode].value
        except KeyError:
            display_mode = "thumbs"
            cookieSet[cookie_display_mode] = display_mode
        
        #Get the friendly name of the server.
        friendly_name = ps.get_friendly_name()
        
        # Build the URL to the XML that returns all of the videos in the section.
        section_path = "/library/sections/" + key + "/all"
        
        # Get the XML for the section
        library = ET.ElementTree(file=urllib2.urlopen(ps.get_url(section_path)))
        videos = library.getroot()
        
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
        
        # The commented out code loads the dictionaries for the genres and
        # collections.  Since it needs to get the XML for each video it's
        # sloooooooow.  I'm keeping it here for reference only.  Getting 
        # this info is now done through AJAX calls in javascript once the
        # page loads.
        #for video in videos:
        #    rating_key = video.get('ratingKey')
        #    
        #    # Get the XML for the video.  While the XML for the video from
        #    # the section has a lot of info, it only has the first three
        #    # genres or collections.  We need to get the XML for the video
        #    # to get all of the items.
        #    video_xml_path = plex_url + '/library/metadata/' + rating_key
        #    video_xml = ET.ElementTree(file=urllib2.urlopen(video_xml_path))
        #    video_xml_root = video_xml.getroot()
        #    
        #    for genre in video_xml_root.iter('Genre'):
        #        if genre_dict.has_key(rating_key):
        #            genre_dict[rating_key].append(genre.get('tag'))
        #        else:
        #            genre_dict[rating_key] = [genre.get('tag')]
        #            
        #    for collection in video_xml_root.iter('Collection'):
        #        if coll_dict.has_key(rating_key):
        #            coll_dict[rating_key].append(collection.get('tag'))
        #        else:
        #            coll_dict[rating_key] = [collection.get('tag')]   
        for video in videos:        
            rating_key = video.get("ratingKey")
            genre_dict[rating_key] = ["loading..."]
            coll_dict[rating_key] = ["loading..."]
                
        # Get the list of playlists
        playlists_XML = ET.ElementTree(file=urllib2.urlopen(ps.get_url("/playlists")))
        playlists = playlists_XML.getroot()
        
        # Loop through each playlist and get the individual items in the
        # list.
        for playlist in playlists:
            playlist_title = playlist.get("title")
            playlist_key = playlist.get("key")
            
            # Get the individual items that make up the playlist.
            playlist_items_xml = ET.ElementTree(file=urllib2.urlopen(ps.get_url(playlist_key)))
            playlist_items = playlist_items_xml.getroot()
            
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
        
        list_dict = {"genre" : genre_dict, "collection" : coll_dict, "playlist" : pl_dict}
                        
        # Get the viewGroup attribute for the root node.  This determines what type
        # of section this is.  Values are:
        #  artist - music sections
        #  movie  - movie sections
        #  show   - TV show sections
        page_type = videos.attrib["viewGroup"]
        
        cookieSet["section_type"] = page_type
        
        section_template = lookup.get_template("section.html")
        return section_template.render(server=server, port=port, friendly_name=friendly_name, page_type=page_type, section=section, videos=videos, display_mode=display_mode, lists=list_dict)
    

# Configure CherryPy so that the webserver is visible on the LAN, not just the
# local machine.
cherrypy.config.update({"server.socket_host": "0.0.0.0",
                        "server.socket_port": 3700,
                       })

lookup = TemplateLookup(directories=["html"])

if __name__ == "__main__":
    
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
    
    cherrypy.quickstart(webapp, "/", conf)