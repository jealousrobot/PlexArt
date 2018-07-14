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

import logging

import uffizi
# from uffizi import *

logger = logging.getLogger('Uffizi.database')

PARM_RETURN_ALL = True
PARM_RETURN_ONE = False


class Database(object):
    """Methods for interacting the the Uffizi database."""
    
    
    def __init__(self, database_path=""):
        """ Start connection to the SQLite database.
        
        Args:
            database_path (str): The file name, including the full path, to the 
                SQLite database file.  If not provided, the default value
                stored in package level variables DIR_DATA and DB_STRING will 
                be used.  The only time this should be used is when using
                the class in a test script.
                
        Returns:
            None
        """
                
        if database_path:
            self.conn = sqlite3.connect(database_path)
        else:
            self.conn = sqlite3.connect(os.path.join(uffizi.DIR_DATA, 
                                                     uffizi.DB_STRING))
        
    def __execute(self, sql, parms=(), return_all=False):
        """Execute a SQL statement.
        
        Args:
            sql (str): The SQL to be executed.
            parms (tuple): The parameters to be passed to the SQL statement.
            return_all (bool): Whether or not all rows from the result set should be
                returned or just one.  True will return all rows.  False will
                return only one.
                
        Returns:
            If the return_all parameter is false, one row of data from the SQL
            statement provided in the sql parameter.
            
            If the return_all parameter is true, all rows of data from the SQL
            statement provided in the sql parameter.
        """
        
        sql_result = self.conn.execute(sql, parms)
        
        if return_all:
            return sql_result.fetchall()
        else:
            return sql_result.fetchone()
    
    def startup(self):
        """Steps to execute each time the database is started.
        
        At this time, the method only performs one action, which is to ensure
        that the tables exist in the database.  If they don't, they will be
        created. 
        
        In the future, if any steps need to be done when the database is 
        started, they should be added here.
        
        Args:
            None
            
        Returns:
            None
        """  
        
        # Check if the tables exist in the database.  If they don't, create it.
        sql = "SELECT COUNT(*) " \
              "  FROM sqlite_master " \
              " WHERE TYPE = 'table' " \
              "   AND NAME = 'TOKEN';"
        
        table_check = self.__execute(sql, (), PARM_RETURN_ONE)
        
        if table_check[0] == 0:
            sql = "CREATE TABLE `TOKEN` ( " \
                  "  `TOKEN` TEXT NOT NULL UNIQUE, " \
                  "  PRIMARY KEY(`TOKEN`));"
            self.__execute(sql, (), PARM_RETURN_ONE)
            
            sql = "CREATE TABLE `SERVER` ( " \
                  "  `SERVER_NAME` TEXT NOT NULL, " \
                  "  `PLATFORM`    TEXT, " \
                  "  `SOURCE`      TEXT, " \
                  "  PRIMARY KEY(`SERVER_NAME`));"
            
            self.__execute(sql, (), PARM_RETURN_ONE)
            
            sql = "CREATE TABLE `SERVER_ADDR` ( " \
                  "  `SERVER_NAME` TEXT NOT NULL, " \
                  "  `ADDRESS`     TEXT NOT NULL, " \
                  "  `PORT`        TEXT NOT NULL, " \
                  "  `VALID`       TEXT, " \
                  "  `ALWAYS_USE`  TEXT, " \
                  "  PRIMARY KEY(`SERVER_NAME`,`ADDRESS`,`PORT`));"
                  
            self.__execute(sql, (), PARM_RETURN_ONE)
        
    def get_token(self):
        """Retrieve the Plex token.
        
        Plex requires a token in order to use the API.  This method will 
        retrieve the token that has been saved in teh database.
        
        Args:
            None
            
        Returns:
            The token for Uffizi to use to interact with the Plext API.
        """
        
        sql = "SELECT TOKEN FROM TOKEN"
        sql_result = self.__execute(sql, (), PARM_RETURN_ONE)
        
        if sql_result is None or sql_result[0] == "":
            return ""
        else:
            return sql_result[0]
            
    def save_token(self, token):
        """Save a Plex token to the database.
        
        Args:
            token (str): The value that needs to be saved to the database.
            
        Returns:
            None
        """
        
        # Clear any existing token values (there should only be one).
        sql = "DELETE FROM TOKEN;"
        self.__execute(sql, (), PARM_RETURN_ONE)
        
        # Insert the new token.
        parms = (token,)
        sql = "INSERT INTO TOKEN (TOKEN)" \
              "VALUES (?)"
              
        self.__execute(sql, parms,  PARM_RETURN_ONE)
        self.conn.commit()
                    
    def commit(self):
        self.conn.commit()
            
    def close(self):
        self.conn.close()
        
    def server_exists(self, server_name):
        """Determines if a server record exists in the table SERVER.
        
        Based on the name of the server provided in the server_name parameter, 
        determines if a record exists in the SERVER table with that name.
        
        Args:
            server_name (str): The name of the server to lookup.
            
        Returns:
            True if the server exists in the SERVER table.
            False if the server doesn't exist in the SERVER table.
        """
        
        parms = (server_name,)
        
        sql = "SELECT COUNT(*) " \
              "  FROM SERVER " \
              " WHERE SERVER_NAME = ?" 
        
        row_count = self.__execute(sql, parms, PARM_RETURN_ONE)
        
        if row_count[0] > 0:
            return True
        else:
            return False
            
    def server_addr_exists(self, server_name, address, port):
        """Determines if a server address record exists in the tabe SERVER_ADDR.
        
        Based ont the name, IP address, and port number provided in the input 
        parameters, determines if a record exists in the SERVER_ADDR table with
        those values. 
        
        Args:
            server_name (str): The name of the server to lookup.
            address (str): The IP address to lookup.
            port (str): The port number to lookup.
            
        Returns:
            True if a record is found in the SERVER_ADDR table.
            False if a record is not fund in the SERVER_ADDR table.
        """
        
        parms = (server_name, address, port)
        
        sql = "SELECT COUNT(*) " \
              "  FROM SERVER_ADDR " \
              " WHERE SERVER_NAME = ? " \
              "   AND ADDRESS = ? " \
              "   AND PORT = ?" 
        
        row_count = self.__execute(sql, parms, PARM_RETURN_ONE)
        
        if row_count[0] > 0:
            return True
        else:
            return False
        
    def insert_server(self, server_name, platform, source):
        """Inserts a record into the SERVER table.
        
        Args:
            server_name (str): The name of the server.
            platform (str): The OS platform used by the server.
            source (str): The source of the information.
            
        Returns:
            None
        """
        
        parms = (server_name, platform, source)
        
        sql = "INSERT INTO SERVER " \
              "  (SERVER_NAME, PLATFORM, SOURCE) " \
              "VALUES " \
              "  (?,?,?)"
              
        self.__execute(sql, parms, PARM_RETURN_ONE)
        
    def insert_server_addr(self, server_name, address, port, valid):
        """Inserts a record into the SERVER_ADDR table.
        
        Args:
            server_name (str): The name of the server.
            address (str): The IP address for the server.
            port (str): The port for the server.
            valid (str): True/false value on whether or not the server can be
                reached.
                
        Returns:
            None
        """
        parms = (server_name, address, port, valid)
        
        sql = "INSERT INTO SERVER_ADDR " \
              "  (SERVER_NAME, ADDRESS, PORT, VALID, ALWAYS_USE) " \
              "VALUES " \
              "  (?, ?, ?, ?, '')"
              
        self.__execute(sql, parms, PARM_RETURN_ONE)
        
    def update_server(self, server_name, platform):
        """Update the platform value for a record in the SERVER table.
        
        Args:
            server_name (str): The name of the server to update.
            platfomr (str): The new value for the platform column.
            
        Returns:
            None
        """
        
        parms = (platform, server_name)
        
        sql = "UPDATE SERVER " \
              "   SET PLATFORM = ? " \
              " WHERE SERVER_NAME = ?"
              
        self.__execute(sql, parms, PARM_RETURN_ONE)
        
    def update_server_addr(self, server_name, address, port, valid, always):
        """Update the VALID and ALWAYS_USE columns for a record in the 
           SERVER_ADDR table.
           
        Args:
            server_name (str): The name of the server to update.
            address (str): The IP address of the server to update.
            port (str): The port of the server to update.
            valid (str): The new value for the VALID column.
            always (str): The new value for the ALWAYS_USER column.
        
        Returns:
            None
        """
        
        parms = (valid, always, server_name, address, port)
        
        logger.debug('parms', parms)
        
        sql = "UPDATE SERVER_ADDR " \
              "   SET VALID = ? " \
              "     , ALWAYS_USE = ? " \
              " WHERE SERVER_NAME = ? " \
              "   AND ADDRESS = ? " \
              "   AND PORT = ? "
              
        self.__execute(sql, parms, PARM_RETURN_ONE)
              
    def get_servers(self):
        """Returns the SERVER_NAME and PLATFORM for all servers in the SERVER
        table.
        
        Args:
            None
            
        Returns:
            A list of tuples for each record in the SERVER table. The tupple
            contains the following elements:  
                SERVER_NAME, PLATFORM
        """
        
        logger.info("Getting servers")
        
        sql = "SELECT SERVER_NAME " \
              "     , PLATFORM " \
              "  FROM SERVER " \
              " ORDER BY 1;"
              
        return self.__execute(sql, (), PARM_RETURN_ALL)
        
    def get_server_addr(self, server, mode="all"):
        """Returns the SERVER_ADDR records for a server.
        
        Args:
            server (str): The name of the server to get data for.
            mode (str): Determines which records to return.  Valid values are:
                all - return all address/ports for a server
                valid - return only identified valid address/port combinations
                invalid - Return only invalid address/port combinations
                always - Return only those addresses marked to always use
                
        Returns:
            A list of tuples for each record from the SERVER_ADDR table. The 
            tuple contains the following elements:
                ADDRESS, PORT, VALID, ALWAYS_USE
        """
        
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
        
        server_details = self.__execute(sql, parms, PARM_RETURN_ALL)
        
        return server_details
        
    #def update_valid_server_add(self, server, address, port, valid):
    #    parms = (server, address, port, valid)
    #    
    #    sql = "UPDATE SERVER_ADDR " \
    #          "   SET VALID = ? " \
    #          " WHERE SERVER_NAME = ?" \
    #          "   AND ADDRESSS    = ?" \
    #          "   AND PORT        = ?"
    #          
    #    retval = self.__execute(sql, parms, False)
        
    def delete_server(self, server):
        """Delete a server from the database.
        
        Will delete all records from SERVER and SERVER_ADDR tables for the 
        provided server.
        
        Args:
            server (str): The name of the server to delete.
            
        Returns:
            None
        """
        
        parms = (server,)
        
        sql = "DELETE FROM SERVER_ADDR" \
              " WHERE SERVER_NAME = ? "
        self.__execute(sql, parms)
        
        sql = "DELETE FROM SERVER" \
              " WHERE SERVER_NAME = ?"
        self.__execute(sql, parms)
        
    # def get_attributes(self, server):
    #    parms = (server,)
    #    
    #    sql = "SELECT * " \
    #          "  FROM SERVER " \
    #          " WHERE SERVER_NAME = ?"
    #          
    #    return self.__execute(sql, parms, PARM_RETURN_ONE)
