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

import httplib, urllib, base64

class PlexToken(object):
    def get_token:
        #return '?X-Plex-Token=axsexNa7zxJAyDyWiquS'
        
        username = "jealous37"
        password = "xje41416"
        base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
        txdata = ""
        
        headers={'Authorization': "Basic %s" % base64string,
                        'X-Plex-Client-Identifier': "PlexArt",
                        'X-Plex-Product': "PlexArt 123",
                        'X-Plex-Version': "1.2"}
        
        conn = httplib.HTTPSConnection("plex.tv")
        conn.request("POST","/users/sign_in.json",txdata,headers)
        response = conn.getresponse()
        print response.status, response.reason
        data = response.read()
        print str(data)
        conn.close()