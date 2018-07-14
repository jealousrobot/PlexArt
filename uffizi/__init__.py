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

# Constants
DIR_DATA = "data"
DB_STRING = "uffizi.db"
SERVER_FILE = "servers.xml"
UFFIZI_VERSION = "0.2.2"
PLEX_TOKEN_PARM = "X-Plex-Token="
LOG_FILE = "uffizi.log"

# Messages
MSG_TXT = {"ERR_MISSING_DB": "Cannot find database file.  Restart Uffizi from "
                             "the command line.",
           "SERVER_UNREACHABLE": "Cannot reach the requested server.  Check to "
                                 "make sure the server is online.",
           "EXPIRED_TOKEN": "It appears as if the plex.tv token Uffizi was "
                            "using has expired.  Please sign in again in order "
                            "to get a new token.",
           "PLEX_TV_UNREACHABLE": "Cannot reach plex.tv.  Try adding the "
                                  "server manually.",
           "SERVER_INVALID": "Server '{0}' does not exist in Uffizi.",
           "INVALID_SOURCE": "Source {} is not a valid source. Valid values are {}"}
                                 
# Globals
arg_debug = False
arg_nolaunch = False

plex_token = ''

        
def nvl(val, when_null):
    return val or when_null
