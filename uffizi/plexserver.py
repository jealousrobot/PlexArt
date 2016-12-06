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
import urllib2

from uffizi import *
from uffizi.database import *

class PlexServer(object):
    
    def __init__(self, server, port):
        self.server_url = "http://" + server + ":" + port
        
    def get_url(self, path="", parms=""):
        # Get the Plex token
        db = Database()
        
        # Check if the path starts with a slash.  If it doesn't append it.
        #if path[0:] == "/" and path != "" and path is not None:
        #    formatted_path = path
        #else:
        #    formatted_path = "/" + path
        formatted_path = path
            
        # If parms is populated append the Plex token to the end of the provided
        # parms.
        if path.find("?") > 0:
            formatted_parms = parms + "&"
        else:
            formatted_parms = "?"
            
        url = self.server_url + formatted_path + formatted_parms + PLEX_TOKEN_PARM + db.get_stored_token()
        db.close()
            
        #return self.__set_plex_url(server_name, port) + path + '?' + PLEX_TOKEN_PARM + self.plex_token
        return url
      
    def get_image(self, path):
        #url = 'http://' + server + ':' + port + path + '?' + PLEX_TOKEN_PARM + plex_token
        return self.get_url(path)
      
    def get_friendly_name(self):
        library = ET.ElementTree(file=urllib2.urlopen(self.get_url()))
        serverXML = library.getroot()
        friendly_name = serverXML.attrib["friendlyName"]
    
        return friendly_name 
    