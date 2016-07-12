# PlexArt - View all of the artwork for Plex sections at once
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
import urllib2
import os
import sys

DB_STRING = 'plexarts.db'
SERVER_FILE = 'servers.xml'

# Ensure lib added to path, before any other imports
# Thank you PlexPy for this!
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib/'))

import cherrypy
import mako

from mako.template import Template
from mako.lookup import TemplateLookup

class PlexArtAPI(object):
    exposed = True  
    
    @cherrypy.tools.accept(media='text/plain')
    def GET(self, server, port, rating_key):
        playlist_out = ''
        
        playlistURL = 'http://' + server + ':' + port + '/playlists'
        
        playlistsXML = ET.ElementTree(file=urllib2.urlopen(playlistURL))
        playlists = playlistsXML.getroot()
        
        for playlist in playlists:
            playlist_title = playlist.get('title')
            playlist_key = playlist.get('key')
            
            specificPlaylistURL = 'http://' + server + ':' + port + playlist_key 
            #specificPlaylistURL = 'http://melody.local:32400/playlists/73508/items'
            
            playlist_items_xml = ET.ElementTree(file=urllib2.urlopen(specificPlaylistURL))
            playlist_items = playlist_items_xml.getroot()  
            
            for video in playlist_items:
                playlist_rating_key = video.get('ratingKey')
                playlist_gp_key = video.get('grandparentRatingKey')
                
                # Check if the grandparent key is populated.  If it is, 
                # this item is an episode or song.  In that case, we use
                # the grandparent key as that is the TV show or artist that
                # this item belongs to.
                if not playlist_gp_key:
                    key_to_use = playlist_rating_key
                else:
                    key_to_use = playlist_gp_key
                    
                if key_to_use == rating_key:
                    if playlist_out:
                        playlist_out += ' / ' + playlist_title
                    else:
                        playlist_out = playlist_title
                
        return playlist_out

class PlexArt(object):
    
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
            self.servers = ET.Element('servers')
            self.servers_XML = ET.ElementTree(self.servers)
            self.servers_XML.write(SERVER_FILE)
        
    @staticmethod
    def __set_plex_url(server_name, port):
      return 'http://' + server_name + ':' + port
      
    @staticmethod
    def __get_friendly_name(server_xml_root):
        friendly_name = server_xml_root.attrib['friendlyName']
        return friendly_name 
    
    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect('home')
        
    @cherrypy.expose
    def home(self):
        home_template = lookup.get_template("home.html")
        return home_template.render(servers=self.servers)
        
    @cherrypy.expose
    def server(self, server='localhost', port='32400'):
        plex_url = self.__set_plex_url(server, port) 
        
        #Get the friendly name of the server.
        library = ET.ElementTree(file=urllib2.urlopen(plex_url))
        serverXML = library.getroot()
        friendly_name = self.__get_friendly_name(serverXML)
        
        #Get the list of sections.
        library = ET.ElementTree(file=urllib2.urlopen('%s/library/sections/' % plex_url))
        
        videos = library.getroot()
        
        # Determine if the server is saved in the XML file        
        found = False
        for instance in self.servers: 
            # instance[0] accesses the server tag and [1] the port tag.
            if server == instance[0].text and port == instance[1].text:
                # Check if the friendly name of the server has been updated
                # since the last time the server was visited by PlexArt.  If so
                # update the XML with the new value.
                if friendly_name != instance[2].text:
                    instance[2].text = friendly_name
                    self.servers_XML.write(SERVER_FILE)
                
                found = True
                break
        
        # If not found, add the server to the XML.
        if not found:
            # Build the <server> element.
            server_elem = ET.Element('server')
            address_elem = ET.SubElement(server_elem, 'address')
            address_elem.text = server
            port_elem = ET.SubElement(server_elem, 'port')
            port_elem.text = port
            friendly_elem = ET.SubElement(server_elem, 'friendlyName')
            friendly_elem.text = friendly_name
            
            # Add the new element to the existing set.
            self.servers.append(server_elem)
            
            # Write the changes to the file.
            
            # When ElementTree writes out XML it's all in one line.  That's ugly
            # and hard to read.  Convert the XML to a string, pretty it up, and
            # then write to a file.
            xml_string = ET.tostring(self.servers, 'utf-8')
            xml_format = minidom.parseString(xml_string)
            
            xml_file = open(SERVER_FILE, 'w')
            xml_file.write(xml_format.toprettyxml(indent="  "))
                
            xml_file.close()
            
        server_template = lookup.get_template("server.html")
        return server_template.render(server=server, port=port, plex_url=plex_url, friendly_name=friendly_name, videos=videos)
        
    @cherrypy.expose
    def section(self, server='localhost', port='32400', key='1', section='<empty>', display_mode='thumbs'):        
        # Set the base URL for the server.
        plex_url = self.__set_plex_url(server, port)
        
        #Get the friendly name of the server.
        library = ET.ElementTree(file=urllib2.urlopen(plex_url))
        serverXML = library.getroot()
        friendly_name = self.__get_friendly_name(serverXML)
        
        # Build the URL to the XML that returns all of the videos in the section.
        plex_xml_path = plex_url + '/library/sections/' + key + '/all'
        
        # Get the XML for the section
        library = ET.ElementTree(file=urllib2.urlopen(plex_xml_path))
        videos = library.getroot()
        
        list_dict = {}
        
        # If the display mode is list, buid dictionaries that will hold the 
        # genres, collections, and playlist info.  For each dictionary, the
        # key of the dictionary is the key for the video and the value is a 
        # list that contains each of the genre/collection/playlists the 
        # video belongs to.  For playlists, if the item in the playlist is an
        # an episode/song, the entire show/artist is considered part of the 
        # playlist.
        if display_mode == 'list':
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
                rating_key = video.get('ratingKey')
                genre_dict[rating_key] = ['loading...']
                coll_dict[rating_key] = ['loading...']
                    
            # Get the list of playlists
            playlists_XML = ET.ElementTree(file=urllib2.urlopen('%s/playlists' % plex_url))
            playlists = playlists_XML.getroot()
            
            # Loop through each playlist and get the individual items in the
            # list.
            for playlist in playlists:
                playlist_title = playlist.get('title')
                playlist_key = playlist.get('key')
                
                # Get the individual items that make up the playlist.
                playlist_items_xml = ET.ElementTree(file=urllib2.urlopen(plex_url + playlist_key))
                playlist_items = playlist_items_xml.getroot()
                
                # Loop through each item in the playlist.
                for video in playlist_items:
                    rating_key = video.get('ratingKey')
                    playlist_gp_key = video.get('grandparentRatingKey')
                    
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
            
            list_dict = {'genre' : genre_dict, 'collection' : coll_dict, 'playlist' : pl_dict}
                        
        # Get the viewGroup attribute for the root node.  This determines what type
        # of section this is.  Values are:
        #  artist - music sections
        #  movie  - movie sections
        #  show   - TV show sections
        page_type = videos.attrib['viewGroup']
        
        section_template = lookup.get_template('section.html')
        return section_template.render(server=server, port=port, plex_url=plex_url, friendly_name=friendly_name, page_type=page_type, section=section, videos=videos, display_mode=display_mode, lists=list_dict)
    

# Configure CherryPy so that the webserver is visible on the LAN, not just the
# local machine.
cherrypy.config.update({'server.socket_host': '0.0.0.0',
                        'server.socket_port': 3700,
                       })

lookup = TemplateLookup(directories=['html'])

if __name__ == '__main__':
    conf = {
         '/': {
             'tools.sessions.on': True,
             'tools.staticdir.root': os.path.abspath(os.getcwd())
         },
         '/playlist': {
             'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
             'tools.response_headers.on': True,
             'tools.response_headers.headers': [('Content-Type', 'text/plain')],
         },
         '/static': {
             'tools.staticdir.on': True,
             'tools.staticdir.dir': './static'
         },
    }
    webapp = PlexArt()
    webapp.playlist = PlexArtAPI() 
    #cherrypy.quickstart(PlexArt(), '/', conf)
    cherrypy.quickstart(webapp, '/', conf)