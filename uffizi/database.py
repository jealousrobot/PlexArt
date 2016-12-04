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

import sqlite3
import os

import uffizi
from uffizi import *

class Database(object):
    def __init__(self):
        self.conn = sqlite3.connect(DIR_DATA + '/' + DB_STRING)
    
    def startup(self):        
        # Check if the tables exist in the database.  If they don', create it.
        sql = "SELECT COUNT(*) " \
              "  FROM sqlite_master " \
              " WHERE TYPE = 'table' " \
              "   AND NAME = 'TOKEN';"
        
        table_check = self.execute(sql, False)
        
        if table_check[0] == 0:
            sql = "CREATE TABLE `TOKEN` ( " \
	              "  `TOKEN` TEXT NOT NULL UNIQUE, " \
	              "  PRIMARY KEY(`TOKEN`));"
            sql_result = self.execute(sql, False)
            
            sql = "CREATE TABLE `SERVER` ( " \
	              "  `SERVER`         TEXT    NOT NULL, " \
	              "  `PORT`           INTEGER NOT NULL, " \
	              "  `FRIENDLY_NAME`  TEXT    NOT NULL, " \
	              "  PRIMARY KEY(`SERVER`, `PORT`));"
            sql_result = self.execute(sql, False)
        
    def get_token(self):
        sql = "SELECT TOKEN FROM TOKEN"
        sql_result = self.execute(sql, False)
        
        if sql_result is None or sql_result[0] == "":
            return ""
        else:
            return '?X-Plex-Token=' + sql_result[0]
            
    def save_token(self, token):
        # Clear any existing token values (there should only be one).
        sql = "DELETE FROM TOKEN;"
        sql_result = self.execute(sql, False)
        
        # Insert the new token.
        sql = "INSERT INTO TOKEN (TOKEN)" \
              "VALUES ('" + token + "');"
              
        sql_result = self.execute(sql, False)
        self.conn.commit()
        
    def execute(self, sql, return_all):
        sql_result = self.conn.execute(sql)
        
        if return_all:
            return sql_result.fetchall()
        else:
            return sql_result.fetchone()
        