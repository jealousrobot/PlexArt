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

import logging
from logging import handlers

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
        uffizi.plex_token = db.get_token()
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
        
    def __get_sort_values(self, in_title, in_sort_title):
        if in_sort_title:
            sort_title = in_sort_title
        else:
            sort_title = in_title
            
        sort_letter = sort_title[0:1]
        if sort_letter in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            sort_letter = "#"
        else:
            sort_letter = sort_letter.upper()
            
        return {'sort_title':sort_title, 'sort_letter':sort_letter}
                    
    def __build_xml(self, ps, videos):
        items = ET.Element("items")                    
        items.set("pageType", "show")
        
        # The vidoes object can contain the details for a single video, or the
        # listing of a section.  When it's the listing of a section, extra data
        # about each video needs to be fetched.  When it's a single video the
        # needed data is already in the video XML.  The section listing can be
        # determined by the fact that the MediaContainer tag contains the "art" 
        # attribute.
        if videos.get('art'):
            fetch_additional = True
        else:
            fetch_additional = False
        
        for video in videos:
            # Loop through each video in the XML from Plex and add it to the
            # custom XML.
            child = ET.SubElement(items, "item",
                                 {"key":video.get("ratingKey")
                                 ,"title":video.get("title")
                                 ,"type":video.get("type")
                                 })                 
                               
            if video.get("titleSort"):
                sort_title = video.get("titleSort")
            else:
                sort_title = video.get("title")
                
            sort_letter = sort_title[0:1]
            if sort_letter in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                sort_letter = "#"
            else:
                sort_letter = sort_letter.upper()
            
                
            child.set("sortTitle", sort_title)
            child.set("sortLetter", sort_letter)
                
            if video.get("childCount"):
                child.set("childCount", video.get("childCount"))
            else:
                child.set('childCount', "0")
            
            if video.get("art"):
                child.set("art", video.get("art"))
                
            if video.get("thumb"):
                child.set("thumb", video.get("thumb"))
                                    
            # Get XML on the show in order to get the collection and genre info.
            # If the XML being built is for a details page, then the info for
            # collections and genres is already included in the videos object.
            # This object contains a "Location" element, which isn't present in
            # the XML for the non-details page.  Only proceed with getting the
            # additional data if the "Location" element isn't present.
            if fetch_additional:
                logger.debug('here')
                show = ps.get_video(video.get("ratingKey"))
            else:
                logger.debug('there')
                show = video
            
            lists = ET.SubElement(child, "lists")
            for g in show.iter("Genre"):
                list_item = ET.SubElement(lists, "list_item",
                                         {"key":g.get("id")
                                         ,"title":g.get("tag")
                                         ,"filter":g.get("filter")
                                         ,"type":"genre"
                                         })
                                 
            for c in show.iter("Collection"):
                list_item = ET.SubElement(lists, "list_item",
                                          {"key":c.get("id")
                                          ,"title":c.get("tag")
                                          ,"filter":c.get("filter")
                                          ,'type':'collection'
                                          })
            
            # If the childCount is greater than zero there are seasons or albums
            # associated with this item.  Fetch them and add them to the XML.
            if int(child.get('childCount')) > 0:
                seasons_element = ET.SubElement(child, "seasons")
                
                seasons = ps.get_video_children(video.get("ratingKey"))
                
                for season in seasons:
                    logger.debug('Key : {0}'.format(season.get('ratingKey')))
                    logger.debug('Title : {0}'.format(season.get('title')))
                    logger.debug('Thumb : {0}'.format(season.get('thumb')))
                    logger.debug('Art : {0}'.format(season.get('art')))
                    
                    if season.get('ratingKey'):
                        season_element = ET.SubElement(seasons_element, 'season',
                                                      {'key':season.get('ratingKey')
                                                      ,'title':season.get('title')
                                                      ,'thumb':season.get('thumb')
                                                      ,'art':season.get('art')
                                                      })
                        
        # Get the list of playlists
        plex_playlists = ps.get_playlists()
        
        # Loop through each playlist and get the individual items in the list.
        for plex_playlist in plex_playlists:
            playlist_title = plex_playlist.get("title")
            playlist_key = plex_playlist.get("key")
            playlist_rating_key = plex_playlist.get("ratingKey")
                            
            # Get the individual items that make up the playlist.
            plex_playlist_items = ps.get_playlist_items(playlist_key)
            
            # Loop through each item in the playlist.
            for pl_video in plex_playlist_items:
                rating_key = pl_video.get("ratingKey")
                gp_rating_key = pl_video.get("grandparentRatingKey")
                
                # Check if the grandparent key is populated.  If it is, 
                # this item is an episode or song.  In that case, we use
                # the grandparent key as that is the TV show or artist that
                # this item belongs to.
                if not gp_rating_key:
                    key_for_item = rating_key
                else:
                    key_for_item = gp_rating_key
                                        
                # Loop through the items XML looking for the video that's in 
                # the playlist.  If found, add the playlist to the playlist 
                # tags in the XML for the video.
                for i in items:
                    # See if this particular item is the one that's in the 
                    # playlist
                    if i.get("key") == key_for_item:
                        # Determine if the playlist has been added to the
                        # lists XML for the item.
                        found = False
                        
                        ## Loop through the list items for this video
                        for li in i.iter("list_item"):
                            if li.get("key") == playlist_rating_key:
                                found = True
                            
                        if not found:
                            for l in i.iter("lists"):
                                list_item = ET.SubElement(l, "list_item",
                                                        {"key":playlist_rating_key
                                                        ,"title":playlist_title
                                                        ,'type':'playlist'
                                                        ,'filter':playlist_key
                                                        })
        return items
        
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
        
        items = ET.Element('items')
        items.set('pageType', 'server')
        
        sections = ps.get_sections()
        
        for section in sections:
            child = ET.SubElement(items, 'item',
                                 {'key':section.get('key')
                                 ,'title':section.get('title')
                                 ,'type':section.get('type')
                                 })
                                 
            sort_values = self.__get_sort_values(section.get('title'), section.get('sortTitle'))
            child.set('sortTitle', sort_values['sort_title'])
            child.set('sortLetter', sort_values['sort_letter'])
            
            if section.get('art'):
                child.set('art', section.get('art'))
                
            if section.get('thumb'):
                child.set('thumb', section.get('thumb'))
            
        logger.debug(ET.tostring(items))
        
        server_template = lookup.get_template("server.html")
        return server_template.render(server=server, items=items)
        
    @cherrypy.expose
    def section(self, server="localhost", key="1", section="<empty>"):
        ps = PlexServer(server)
        
        if ps.simple_status == "down":
            raise cherrypy.HTTPRedirect("error?error=SERVER_UNREACHABLE")

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
        cookieSet["server"] = server

        try:
            cookie = cherrypy.request.cookie
            display_mode = cookie[cookie_display_mode].value
        except KeyError:
            display_mode = "thumbs"
            cookieSet[cookie_display_mode] = display_mode
        
        # Get the items that are in this section.
        videos = ps.get_section_items(key)
                                                      
        logger.debug('begin')
        items = self.__build_xml(ps, videos)
        logger.debug('end')
                        
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
                                      ,key=key
                                      ,items=items
                                      ,display_mode=display_mode)

    @cherrypy.expose
    def refresh_servers_redirect(self):
        self.__refresh_servers()
        raise cherrypy.HTTPRedirect("home")
        
    @cherrypy.expose
    def details(self, server, key):
        ps = PlexServer(server)
        
        if ps.simple_status == "down":
            raise cherrypy.HTTPRedirect("error?error=SERVER_UNREACHABLE")
            
        cookieSet = cherrypy.response.cookie
        
        # Retrieve the cookie for the display mode (thumbs or list).
        cookie_display_mode = "displayMode-" + str(server) + "-" + str(key)
        cookie_display_mode = urllib2.quote(cookie_display_mode)
        
        # Use cookies to save the values of the URL parameters.  This seems 
        # easier than trying to deconstruct the URL query string in javascript.
        cookieSet["address"] = ps.address
        cookieSet["port"] = ps.port
        cookieSet["key"] = key
        cookieSet["section"] = ''
        cookieSet["server"] = server
        cookieSet[cookie_display_mode] = "list"

        # Get XML for the show.
        videos = ps.get_video(key)
        
        section_title = videos.get('librarySectionTitle')
        section_key = videos.get('librarySectionID')
        
        for video in videos:
            video_title = video.get('title')
            page_type = 'details_{0}'.format(video.get('type'))
            # The guid has the info needed to get data from the scraper website.
            guid = video.get('guid')
            
        logger.debug('page_type : {0}'.format(page_type))
            
        # Check the guid to see if it's for thetvdb.
        if guid.find('thetvdb') > 0:
            # Extract the key for the video from the guid
            str_start = guid.find('//') + 2
            str_end = guid.find('?')
            thetvdb_key = guid[str_start:str_end]
            logger.debug('The tv db : {0}'.format(thetvdb_key))
        
        items = self.__build_xml(ps, videos)
        
        logger.debug(ET.tostring(items))
        
        detail_template = lookup.get_template('details.html')
        return detail_template.render(server=server
                                     ,key=key
                                     ,page_type=page_type
                                     ,section_key=section_key
                                     ,section_title=section_title
                                     ,video_title=video_title
                                     ,items=items)
                                     
        
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
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
        
    # Set up logging
    logger = logging.getLogger('uffizi')
    logger.setLevel(log_level)
    
    # Create console handler to write messages to the command line.
    logger_console = logging.StreamHandler()
    logger_console.setLevel(log_level)
    
    # Create file handler to write message to the log file.
    if not os.path.exists(os.path.join(os.path.dirname(__file__), "logs")):
        os.makedirs(os.path.join(os.path.dirname(__file__), "logs"))
        
    filename = os.path.join(os.path.dirname(__file__), "logs", LOG_FILE)
    logger_file = handlers.TimedRotatingFileHandler(filename=filename, when="D", backupCount=10)
    logger_file.setLevel(log_level)
    
    # Set the format for the log messages
    formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s] %(message)s', datefmt="%Y/%m/%d %I:%M:%S %p")
    
    # Set the format for the console and file handlers.
    logger_console.setFormatter(formatter)
    logger_file.setFormatter(formatter)
    
    # Add the handlers to the logger.
    logger.addHandler(logger_console)
    logger.addHandler(logger_file)
        
    logger.info("Command line options")
    logger.info("  debug : %s", uffizi.arg_debug)
    logger.info("  nolanuch : %s", uffizi.arg_nolaunch)
    
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
    