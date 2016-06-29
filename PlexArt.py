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
    def section(self, server='localhost', port='32400', key='1', section='<empty>'):        
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
        
        # Get the viewGroup attribute for the root node.  This determines what type
        # of section this is.  Values are:
        #  artist - music sections
        #  movie  - movie sections
        #  show   - TV show sections
        page_type = videos.attrib['viewGroup']
        
        section_template = lookup.get_template('section.html')
        return section_template.render(server=server, port=port, plex_url=plex_url, friendly_name=friendly_name, page_type=page_type, section=section, videos=videos)
    

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
         '/static': {
             'tools.staticdir.on': True,
             'tools.staticdir.dir': './static'
         },
     }
     
    cherrypy.quickstart(PlexArt(), '/', conf)
