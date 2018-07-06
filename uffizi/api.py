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
import urllib, urllib2
import base64, httplib
from httplib import HTTPConnection
import uuid
import logging
import cherrypy
import uffizi
from uffizi import *
from uffizi.database import *
from uffizi.plexserver import *

logger = logging.getLogger('uffizi.api')

class GetPlaylists(object):
    exposed = True  
    
    @cherrypy.tools.accept(media="text/plain")
    def GET(self, server, rating_key):
        
        ps = PlexServer(server)
        
        playlist_out = ""
        
        playlists = ps.get_playlists()
        
        for playlist in playlists:
            playlist_title = playlist.get("title")
            playlist_key = playlist.get("key")
            
            playlist_items = ps.get_playlist_items(playlist_key)
            
            for video in playlist_items:
                playlist_rating_key = video.get("ratingKey")
                playlist_gp_key = video.get("grandparentRatingKey")
                
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
                        playlist_out += " / " + playlist_title
                    else:
                        playlist_out = playlist_title
                
        return playlist_out

class GetImage(object):
    exposed = True
    
    @cherrypy.tools.accept(media="text/plain")
    def GET(self, server, path, type, width="", height=""):
        logger.debug('NOW IN GetImage')
        
        ps = PlexServer(server)
        
        try:
            if path == "None":
                raise
            if width == "" and height == "" and path != "None":
                logger.debug('GetImage.GET : 1')
                # Get the URL to the image
                url = ps.get_url(path)
                cherrypy.response.headers['Content-Type'] = 'image/png'
                image = urllib2.urlopen(url)
            else:
                logger.debug('GetImage.GET : 2')
                # Get the URL for the image escaped and without the plex token.  
                url_escaped = urllib.quote_plus(ps.get_url(path, {}, False))
                
                parms = {'url':url_escaped, 'width':width, 'height':height}
                
                # It looks like that if the server hasn't been "claimed", then 
                # using this API fails.  In this scenario, try getting the non
                # resized version.
                try:
                    url = ps.get_url("/photo/:/transcode", parms)
                    cherrypy.response.headers['Content-Type'] = 'image/png'
                    image = urllib2.urlopen(url)
                except:
                    url = ps.get_url(path)
                    cherrypy.response.headers['Content-Type'] = 'image/png'
                    image = urllib2.urlopen(url)
        except:
            logger.debug('GetImage.GET : 3')
            if type == "background":
                imageName = "emptyBackground"
            elif type == "thumb":
                imageName = "emptyTVThumb"
            else:
                imageName = "emptyMusicThumb"
                
            cherrypy.response.headers['Content-Type'] = 'image/png'
            image = urllib2.urlopen("http://localhost:3700/static/images/" + imageName + ".png")
        
        return image

class GetMetaData(object):
    exposed = True
        
    @cherrypy.tools.accept(media="text/plain")
    def GET(self, server, path):

        ps = PlexServer(server)
        url = ps.get_url(path)
        
        results = urllib2.urlopen(url)
        
        return results
        
class GetPlexToken(object):
    exposed = True
    
    @cherrypy.tools.accept(media="text/plain")
    def GET(self, username, password):
        found = 'Not Found'
        
        base64string = base64.encodestring("%s:%s" % (username, password)).replace("\n", "")
        txdata = ""
        client_id = uuid.uuid4()
        
        headers={"Content-Type": "application/xml; charset=utf-8",
                 "Authorization": "Basic %s" % base64string,
                 "X-Plex-Client-Identifier": client_id,
                 "X-Plex-Product": "Uffizi",
                 "X-Plex-Version": UFFIZI_VERSION,
                 "X-Plex-Device-Name": "Uffizi"
                 }
                 
        found = 'Found'
                
        conn = httplib.HTTPSConnection("plex.tv")
        conn.request("POST","/users/sign_in.xml", txdata, headers)
        response = conn.getresponse()
        
        data = response.read()

        usr_xml = ET.fromstring(data)
        uffizi.plex_token = usr_xml.get("authenticationToken")
        
        # Save the token to the database
        db = Database()
        db.save_token(uffizi.plex_token)
        db.close()

        conn.close()
                
        return found
        
class GetServerStatus(object):
    exposed = True
    
    @cherrypy.tools.accept(media="text/plain")
    def GET(self, server):
        ps = PlexServer(server)
        
        root = ET.Element("server")
        root = ET.Element("server", name=server, status=ps.simple_status)
        
        return ET.tostring(root)
        
class AddServer(object):
    exposed = True
    
    @cherrypy.tools.accept(media="text/plain")
    def GET(self, address, port):
        ps = PlexServer(address=address, port=port)
        
        root = ET.Element("server", name=ps.name, status=ps.simple_status)
        
        if ps.name == "<unknown>":
            error = ET.SubElement(root, "error", error_code="UNKNOWN_SERVER", error_text="Unable to locate plex server")
        else:
            ps.add_server('manual')


        return ET.tostring(root)
        
class RefreshServers(object):
    exposed = True
    
    @cherrypy.tools.accept(media="text/plain")
    def GET(self):
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
        
        return 'success'
        
class GetServerDetails (object):
    exposed = True
    
    @cherrypy.tools.accept(media="text/plain")
    def GET(self, server):
        
        ps = PlexServer(server)
        
        root = ET.Element("server", name=ps.name, platform=ps.platform, source=ps.source)
        
        for connection in ps.connections:
            address = ET.SubElement(root, "address", address=connection[0], port=connection[1], valid=connection[2], always_use=nvl(connection[3],""))
        
        return ET.tostring(root)
        
class EditServerDetails (object):
    exposed = True
    
    @cherrypy.tools.accept(media="text/plan")
    def GET(self, server, **kwargs):
        logger.debug('server', server)
        logger.debug('parms', kwargs)
        
        for key, value in kwargs.iteritems():
            parms = value.split(',')
            
            ps = PlexServer(server)
            ps.update_server_addr(parms[0], parms[1], parms[2], parms[3])
        
        return 'success'