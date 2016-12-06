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
import base64, httplib
from httplib import HTTPConnection
import uuid
import cherrypy
import uffizi
from uffizi import *
from uffizi.database import *
from uffizi.plexserver import *

class GetPlaylists(object):
    exposed = True  
    
    @cherrypy.tools.accept(media="text/plain")
    def GET(self, server, port, rating_key):
        #db = Database()
        #plex_token = db.get_stored_token()
        #db.close()
        
        ps = PlexServer(server, port)
        
        playlist_out = ""
        
        #playlistURL = "http://" + server + ":" + port + "/playlists" + plex_token
        playlistURL = ps.get_url("/playlists")
        
        playlistsXML = ET.ElementTree(file=urllib2.urlopen(playlistURL))
        playlists = playlistsXML.getroot()
        
        for playlist in playlists:
            playlist_title = playlist.get("title")
            playlist_key = playlist.get("key")
            
            #specificPlaylistURL = "http://" + server + ":" + port + playlist_key + plex_token
            specificPlaylistURL = ps.get_url(playlist_key)
            
            playlist_items_xml = ET.ElementTree(file=urllib2.urlopen(specificPlaylistURL))
            playlist_items = playlist_items_xml.getroot()  
            
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
    def GET(self, server, port, path, type):
        
        #url = "http://" + server + ":" + port + path + "?" + PLEX_TOKEN_PARM + plex_token
        ps = PlexServer(server, port)
        url = ps.get_image(path)
        
        try:
            image = urllib2.urlopen(url)
        except:
            if type == "background":
                imageName = "emptyBackground"
            elif type == "thumb":
                imageName = "emptyTVThumb"
            else:
                imageName = "emptyMusicThumb"
                
            image = urllib2.urlopen("http://localhost:3700/static/images/" + imageName + ".png")
        
        return image

class GetMetaData(object):
    exposed = True
        
    @cherrypy.tools.accept(media="text/plain")
    def GET(self, server, port, path):
        #db = Database()
        #plex_token = db.get_stored_token()
        
        #url = "http://" + server + ":" + port + path + "?" + PLEX_TOKEN_PARM + plex_token
        ps = PlexServer(server, port)
        url = ps.get_url(path)
        
        print '*********', url
        
        results = urllib2.urlopen(url)
        
        return results
        
class GetPlexToken(object):
    exposed = True
    
    @cherrypy.tools.accept(media="text/plain")
    def GET(self, username, password):
        found = "Fail"
        
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
                 
        found = "worked"
                
        conn = httplib.HTTPSConnection("plex.tv")
        conn.request("POST","/users/sign_in.xml",txdata,headers)
        response = conn.getresponse()
        
        data = response.read()

        usr_xml = ET.fromstring(data)
        plex_token = usr_xml.get("authenticationToken")
        found = "Token retrieved : " + plex_token
        
        db = Database()
        db.save_token(plex_token)
        db.close()

        conn.close()
        
        return found        
        