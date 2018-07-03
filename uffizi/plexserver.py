# Uffizi - View all of the artwork for Plex sections at once
# Copyright (C) 2016 Jason Ellis
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
import urllib, urllib2, httplib
import logging

from socket import error as socket_error

from uffizi import *
from uffizi.database import *
from uffizi.exceptions import *

import cherrypy

logger = logging.getLogger('uffizi.plexserver')
    
class PlexServer(object):
    def __init__(self, server="", address="", port=""):
        self.server = server
        self.address = address
        self.port = port
        self.connections = None
        self.platform = ""
        self.name = ""
        self.source = ""
            
        if server == "":
            self.status = PlexServer.get_server_status(self.address, self.port)
        
            try:
                serverXML = self.get_xml()
                self.server = serverXML.attrib["friendlyName"]
                self.platform = serverXML.attrib["platform"]
            except:
                self.server = "<unknown>"
                self.platform = "<unknown>"
        else:
            db = Database()
            server_exists = db.server_exists(server)
            
            if server_exists:
                self.__set_attributes()
                
                self.connections = db.get_server_addr(server, 'all')
                
                server_addr = PlexServer.get_server_addr(server)
                
                if server_addr:
                    self.address = server_addr['address']
                    self.port = server_addr['port']
                    self.status = server_addr['status']
                else:
                    self.address = "0.0.0.0"
                    self.port = "32400"
                    self.status = '900'
            
                db.close()
            else:
                raise uffiziInvalidServer(server)
                
        if self.status[0:1] in ('1', '2'):
            self.simple_status = 'up'
        else:
            self.simple_status = 'down'
        
        self.name = self.server
            
    def __set_attributes(self):
        db = Database()
        server_attributes = db.get_attributes(self.server)
        self.platform = server_attributes[1]
        self.source = server_attributes[2]
        db.close()
                
    @staticmethod
    def get_plex_url(address, port, path="", parms={}, include_token=True):
        # Check if the path starts with a slash.  If it doesn't append it.
        if path[0:1] == "/" and path != "" and path is not None:
            formatted_path = path
        else:
            formatted_path = "/" + path
            
        # Check to make sure the path doesn't contain a question mark at the end of
        # it.  If there are pararameters for the URL, the question mark will be 
        # handled when evaluating the parms variable.
        if formatted_path[-1:] == "?":
            formatted_path = formatted_path[:-1]
            
        formatted_parms = ""
        if parms:
            formatted_parms = "?"
            
            for key, value in parms.iteritems():
                if formatted_parms != "?":
                    formatted_parms += "&"
                
                formatted_parms += "{0}={1}".format(key, value)
            
        url = "http://{0}:{1}{2}{3}".format(address
                                           ,port
                                           ,formatted_path
                                           ,formatted_parms)
        
        if include_token:
            # Check if formatted_parms contains a question mark, if it does, append
            # the token to the existing paramters.
            if formatted_parms[0:1] == "?":
                url += "&"
            else:
                url += "?"
                
            url +=  uffizi.PLEX_TOKEN_PARM + uffizi.plex_token
            
        logger.debug("PlexServer.get_plex_url : {}".format(url))
        return url
            
    @staticmethod
    def get_server_addr(server=""):
        """Find an address/port combination for the provided server."""
        
        server_found = False
        server_details = {}
        
        db = Database()
        
        modes = ['always', 'valid', 'invalid']
        
        for mode in modes:
            server_found = False
                 
            connections = db.get_server_addr(server, mode)
            for connection in connections:
                address = connection[0]
                port = connection[1]
                                
                status = PlexServer.get_server_status(address, port)
                
                server_details = {'address':address, 
                                  'port':port, 
                                  'status':status}
                
                # If a server was found with the "always" flag check, it will be
                # used.  If the server being tested returned a status starting 
                # with a 1 or a 2, the server is online and it can be used.
                if mode == 'always' or status[0:1] in ('1', '2'):
                    server_found = True
                    break              
                
            # A server was found, no need to try the other modes.
            if server_found:
                break
        
        db.close()
                            
        return server_details
        
    @staticmethod
    def get_server_status(address, port):
        try:
            parms = "/library?{0}{1}".format(uffizi.PLEX_TOKEN_PARM, uffizi.plex_token)
        
            conn = httplib.HTTPConnection(address, int(port), timeout=5)
            conn.request("HEAD", parms)
            
            server_status = str(conn.getresponse().status)
        except:
            server_status = '900'
            
        return server_status                
        
    def get_url(self, path="", parms={}, include_token=True):
        return PlexServer.get_plex_url(self.address, self.port, path, parms, include_token)
        
    def get_xml(self, path=""):
        logger.debug("path : {}".format(path))
        url = self.get_url(path)
        
        logger.debug("url : {}".format(url))
        
        try:
            root = ET.ElementTree(file=urllib2.urlopen(url)).getroot()
        except urllib2.HTTPError as err:
           if str(err.code)[0:1] == "4":
               #redirect_url = urllib.quote_plus(cherrypy.url(qs=cherrypy.request.query_string))
               #raise cherrypy.HTTPRedirect("sign_in?reason=EXPIRED_TOKEN&redirect={0}".format(redirect_url))
               raise uffiziExpiredToken()
           else:
               raise
        except:
            raise
        
        return root
          
    def get_sections(self):
        return self.get_xml("/library/sections")
        
    def get_section_items(self, key):
        section_path = "/library/sections/{0}/all".format(key)
        
        return self.get_xml(section_path)
        
    def get_playlists(self):
        return self.get_xml("/playlists")
        
    def get_playlist_items(self, key):
        return self.get_xml(key)
        
    def add_server(self, source):
        db = Database()
        
        if db.server_exists(self.name):
            db.update_server(self.name, self.platform, source)
        else:
            db.insert_server(self.name, self.platform, source)
            
        if db.server_addr_exists(self.name, self.address, self.port):
            db.update_server_addr(self.name, self.address, self.port, "Y", "")
        else:
            db.insert_server_addr(self.name, self.address, self.port, "Y")
            
        db.commit()
        db.close()

    def delete_server(self):
        db = Database()
        db.delete_server()
        db.commit()
        db.close()
        
    def update_server_addr(self, address, port, valid, always):
        logger.debug("address : ".format(address))
        logger.debug("port : ".format(port))
        logger.debug("valid : ".format(valid))
        logger.debug("always : ".format(always))
        
        db = Database()
        db.update_server_addr(self.server, address, port, valid, always);
        db.commit()
        db.close()