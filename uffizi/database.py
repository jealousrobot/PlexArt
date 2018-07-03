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
import urllib2

import logging

import uffizi
from uffizi import *

logger = logging.getLogger('Uffizi.database')

class Database(object):
    def __init__(self):
        self.conn = sqlite3.connect(uffizi.DIR_DATA + '/' + uffizi.DB_STRING)
        
    def __execute(self, sql, parms=(), return_all=False):
        sql_result = self.conn.execute(sql, parms)
        
        if return_all:
            return sql_result.fetchall()
        else:
            return sql_result.fetchone()
    
    def startup(self):
        # Check if the tables exist in the database.  If they don', create it.
        sql = "SELECT COUNT(*) " \
              "  FROM sqlite_master " \
              " WHERE TYPE = 'table' " \
              "   AND NAME = 'TOKEN';"
        
        table_check = self.__execute(sql, (), False)
        
        if table_check[0] == 0:
            sql = "CREATE TABLE `TOKEN` ( " \
	              "  `TOKEN` TEXT NOT NULL UNIQUE, " \
	              "  PRIMARY KEY(`TOKEN`));"
            sql_result = self.__execute(sql, (), False)
            
            sql = "CREATE TABLE `SERVER` ( " \
                  "  `SERVER_NAME` TEXT NOT NULL, " \
                  "  `PLATFORM`    TEXT, " \
                  "  `SOURCE`      TEXT, " \
                  "  PRIMARY KEY(`SERVER_NAME`));"
            
            sql_result = self.__execute(sql, (), False)
            
            sql = "CREATE TABLE `SERVER_ADDR` ( " \
                  "  `SERVER_NAME` TEXT NOT NULL, " \
                  "  `ADDRESS`     TEXT NOT NULL, " \
                  "  `PORT`        TEXT NOT NULL, " \
                  "  `VALID`       TEXT, " \
                  "  `ALWAYS_USE`  TEXT, " \
                  "  PRIMARY KEY(`SERVER_NAME`,`ADDRESS`,`PORT`));"
                  
            sql_result = self.__execute(sql, (), False)
        
    def get_stored_token(self):
        sql = "SELECT TOKEN FROM TOKEN"
        sql_result = self.__execute(sql, (), False)
        
        if sql_result is None or sql_result[0] == "":
            return ""
        else:
            return sql_result[0]
            
    def save_token(self, token):
        # Clear any existing token values (there should only be one).
        sql = "DELETE FROM TOKEN;"
        sql_result = self.__execute(sql, (), False)
        
        # Insert the new token.
        parms = (token,)
        sql = "INSERT INTO TOKEN (TOKEN)" \
              "VALUES (?)"
              
        sql_result = self.__execute(sql, parms,  False)
        self.conn.commit()
                    
    def commit(self):
        self.conn.commit()
            
    def close(self):
        self.conn.close()
        
    def server_exists(self, server_name):
        parms = (server_name,)
        
        sql = "SELECT COUNT(*) " \
              "  FROM SERVER " \
              " WHERE SERVER_NAME = ?" 
        
        row_count = self.__execute(sql, parms, False)
        
        if row_count[0] > 0:
            return True
        else:
            return False
            
    def server_addr_exists(self, server_name, address, port):
        parms = (server_name, address, port)
        
        sql = "SELECT COUNT(*) " \
              "  FROM SERVER_ADDR " \
              " WHERE SERVER_NAME = ? " \
              "   AND ADDRESS = ? " \
              "   AND PORT = ?" 
        
        row_count = self.__execute(sql, parms, False)
        
        if row_count[0] > 0:
            return True
        else:
            return False
        
    def insert_server(self, server_name, platform, source):
        parms = (server_name, platform, source)
        
        sql = "INSERT INTO SERVER " \
              "  (SERVER_NAME, PLATFORM, SOURCE) " \
              "VALUES " \
              "  (?,?,?)"
              
        self.__execute(sql, parms, False)
        
    def insert_server_addr(self, server_name, address, port, valid):
        parms = (server_name, address, port, valid)
        
        sql = "INSERT INTO SERVER_ADDR " \
              "  (SERVER_NAME, ADDRESS, PORT, VALID, ALWAYS_USE) " \
              "VALUES " \
              "  (?, ?, ?, ?, '')"
              
        self.__execute(sql, parms, False)
        
    def update_server(self, server_name, platform):
        parms = (platform, server_name)
        
        sql = "UPDATE SERVER " \
              "   SET PLATFORM = ? " \
              " WHERE SERVER_NAME = ?"
              
        self.__execute(sql, parms, False)
        
    def update_server_addr(self, server_name, address, port, valid, always):
        parms = (valid, always, server_name, address, port)
        
        logger.debug('parms', parms)
        
        sql = "UPDATE SERVER_ADDR " \
              "   SET VALID = ? " \
              "     , ALWAYS_USE = ? " \
              " WHERE SERVER_NAME = ? " \
              "   AND ADDRESS = ? " \
              "   AND PORT = ? "
              
        self.__execute(sql, parms, False)
              
    def get_servers(self):
        
        logger.info("Getting servers")
        
        sql = "SELECT SERVER_NAME " \
              "     , PLATFORM " \
              "  FROM SERVER " \
              " ORDER BY 1;"
              
        return self.__execute(sql, (), True)
        
    def get_server_addr(self, server, mode="all"):
        # Valid mode options:
        #   all - return all address/ports for a server
        #   valid - return only identified valid address/port combinations
        #   invalid - Return only invalid address/port combinations
        #   always - Return only those addresses marked to always use
        
        parms = (server,)
        
        sql = "SELECT ADDRESS " \
              "     , PORT " \
              "     , VALID " \
              "     , ALWAYS_USE " \
              "  FROM SERVER_ADDR " \
              " WHERE SERVER_NAME = ? "
        
        if mode == "valid":
            sql += "AND VALID = 'Y'"
        elif mode == "invalid":
            sql += "AND VALID = 'N'"
        elif mode == "always":
            sql += "AND ALWAYS_USE = 'Y'"
            
        sql += " ORDER BY 1 DESC, 2"
        
        server_details = self.__execute(sql, parms, True)
        
        return server_details
        
    def update_valid_server_add(self, server, address, port, valid):
        parms = (server, address, port, valid)
        
        sql = "UPDATE SERVER_ADDR " \
              "   SET VALID = ? " \
              " WHERE SERVER_NAME = ?" \
              "   AND ADDRESSS    = ?" \
              "   AND PORT        = ?"
              
        retval = self.__execute(sql, parms, False)
        
    def delete_server(self, server):
        parms = (server,)
        
        sql = "DELETE FROM SERVER_ADDR" \
              " WHERE SERVER_NAME = ? "
        retval = self.__execute(sql, parms)
        
        sql = "DELETE FROM SERVER" \
              " WHERE SERVER_NAME = ?"
        retval = self.__execute(sql, parms)
        
    def get_attributes(self, server):
        parms = (server,)
        
        sql = "SELECT * " \
              "  FROM SERVER " \
              " WHERE SERVER_NAME = ?"
              
        return self.__execute(sql, parms, False)