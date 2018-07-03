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

import logging

import uffizi
from uffizi import *

logger = logging.getLogger('uffizi.exceptions')

class uffiziInvalidServer(Exception):
    def __init__(self, server):
        self.server = server
        self.msg = MSG_TEXT["SERVER_INVALID"].format(server)
        
        Exception.__init__(self, self.msg)
        
class uffiziExpiredToken(Exception):
    def __init__(self):
        self.msg = MSG_TEXT["EXPIRED_TOKEN"]