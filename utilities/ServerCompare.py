# Uffizi - View all of the artwork for Plex sections at once
# Copyright (C) 2018 Jason Ellis
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

"""
This script provides a means to compare the media files of one server 
with another 

This script is used to compare the files contained on one server with 
another.  It works based on the file system, not what is in PMS.  Data
for a server is loaded either by reading the file system directly or by
importing in a file that contains a list of files.  This script can be 
used to generate the import file.

The driving force for creating this script was the need to keep a remote
server up to date with a local server.  The remote server is not 
reachable except by physical means.  This script can be used to generate
a list of files on the remote server, compared to a list of files on the
local server and then the necessary files copied to a portable drive to
be loaded onto the remote server the next time it's visited.

To compare two servers with ServerCompare reading the file system
directly:
1. Choose option 2 to load files from the file system of the source
   system.  The computer that the this script is being run from needs
   access to the file system of the source Plex install.
2. Provide the path to the directory that contains the files that need
   to be loaded.
3. Provide the portion of the path that should be stripped from the 
   files.  This is neccessary if the files that are to be compared are
   contained with different paths on each server.  Take for example
   the following servers:
     Source server path: /Users/user1/media/movies
     Target server path: /Users/user2/media/movies
     
   If the movies Alien exists on both servers with the following path:
     Source server: /Users/user1/media/movies/Alien/Alien.mp4
     Target server: /Users/user2/media/movies/Alien/Alien.mp4
     
   Comparing these two paths would result in the script stating that the
   file needs to be copied from the source server to the target server
   and the file from the target server needing to be removed since it's 
   not on the source server.  This is due to the paths not matching.
   
   By removing part of the path from the file that leaves a string with
   just the values that are the same, in this case, 
   "media/movies/Alien/Alien.mp4", the compare will yield that this file
   already exists on the target server.
4. Repeat steps 2 and 3 until all folders that contain files that need 
   to be compared are loaded.  The script will drill down in to sub-
   folders so it's only neccessary to provide top level folders, i.e.
   the path to the movie directory and the path to the TV show 
   directory.
   
   Press <enter> once all paths have been loaded.  A blank path will
   end this process.
5. Choose option 4 to load files from the file system of the target
   system.  The computer that the this script is being run from needs
   access to the file system of the target Plex install.
6. Follow steps 2-4 for the target system.
7. Choose option 7 to compare the files.  This will create three files:
     target_add.txt - The list of files from the source system that need
       to be added to the target system.
     target_del.txt - The list of files from the target system that need
       to be deleted because they are not found on the source system.
     target_upd.txt - The list of files from the source system that are
       found on the target system but the file sizes are different 
       indicating that the file has changed on the source.
       
   The files are located in the output directory which is contained in 
   the same directory as this script.
       
To generate an output file that contains a list of files from a server:
1. Follow steps 1 through 3 above to load up the files from the file 
   system.
2. Choose option 5 and provide the name of the output file.  Only the
   name of the file should be entered.  No path information should be 
   entered.  The file will be created in the output directory which is
   contained in the same directory as this script.
   
   If files have already been loaded for the target server, option 6 can
   be used to output a file.
   
To compare servers using data from an input file:
1. Choose option 1 to load files for the source server or option 3 to 
   load files for the target server.
2. Load files from the file system using the steps above or from another
   file.
3. Choose option 7 to compare the files.
   
Clear source and target data:
Options 8 and 9 can be used to clear the files that have been loaded.  
Usefule to avoid restarting the script if a mistake is made in loading 
the files.

"""

import os
import logging
from platform import system as system_name


class ServerCompare(object):
    """
    This class is used to compare the files from two Plex systems to 
    determine which files need to be added, deleted, or updated on the
    target system.
    
    Attributes:
        result: A message indicating the result of the most recent 
            action.
        source_populated: A true/false indicator identifying if files
            have been loaded to the source dictionary.
        target_populated: A true/false indicator identifying if files
            have been loaded to the target dictionary.
    """

    SOURCE = "SOURCE"
    TARGET = "TARGET"

    # List of valid extensions to include
    __IGNORE_FILES = ("Thumbs.db", ".DS_Store")

    def __init__(self, log_level="INFO"):
        self.__source = {}
        self.__target = {}
        self.__result = ""
        
        self.__source_source = []
        self.__target_source = []

        # Ensure the output directory exists
        self.__output_path = os.path.join(
            os.path.dirname(
                os.path.realpath(__file__)), "output")
        if not os.path.exists(self.__output_path):
            os.makedirs("output")

    @property
    def result(self):
        return self.__result

    @property
    def source_populated(self):
        return self.__is_populated(self.__source)

    @property
    def target_populated(self):
        return self.__is_populated(self.__target)

    def __is_populated(self, dict_to_test):
        """
        Identifies if the provided dictionary is populated.
        
        Args:
            dict_to_test: The dictionary to test.  Should be either
                self.__source or self.__target.
                
        Returns:
            True if the dictionary is populated.
            False if the dictionary is empty.
        """
        if dict_to_test:
            return True
        else:
            return False

    def __load_file(self, description):
        """
        Loads a file into a dictionary for later comparison.
        
        Args:
            description: A string value that denotes which dictionary
                should be loaded, source or target.  The values
                self.SOURCE or self.TARGET should be used when calling
                the method.
                
        Returns:
            None
        """

        while True:
            try:
                file_path = input("Path to {} file: ".format(description)).strip()
                if file_path:
                    file_load = open(file_path, "r")
                break
            except IsADirectoryError:
                print("ERROR - Directory specified instead of a file.")
            except FileNotFoundError:
                print("ERROR - Cannot find file.  Check path and try again.")

        if file_path:
            # dictionary = {}
            
            getattr(self, "_ServerCompare__{}_source".format(description.lower())).append(file_path)

            row_count = 0
            lines = file_load.readlines()
            for line in lines:
                row_count += 1

                parts = line.rstrip("\n")
                parts = parts.split("|")
                # dictionary[parts[0]] = (int(parts[1]), parts[2])
                getattr(self, "_ServerCompare__{}".format(description.lower()))[parts[0]] = (int(parts[1]), parts[2])

            file_load.close()

            # if description == self.SOURCE:
            #    self.__source = dictionary
            # else:
            #    self.__target = dictionary

            self.__result = "{} file loaded from:\n    {}".format(description,
                                                                  file_path)
        else:
            self.__result = "No {} file loaded".format(description)

    def load_file_source(self):
        self.__load_file(self.SOURCE)

    def load_file_target(self):
        self.__load_file(self.TARGET)

    def __write_file(self, description):
        """
        Writes the contents of a dictionary to a file.  The name of the
        file is provided by the user.
        
        Args:
            description: A string value that denotes which dictionary
                should be used, source or target.  The values
                self.SOURCE or self.TARGET should be used when calling
                the method.
                
        Returns:
            None
        """

        if ((description == self.SOURCE and not self.__source) or
                (description == self.TARGET and not self.__target)):
            self.__result = "ERROR - Cannot write file no {} provided".format(description)
        else:
            if description == self.SOURCE:
                dictionary = self.__source
            else:
                dictionary = self.__target

            while True:
                try:
                    output_file_name = input("Name of output file: ")

                    output_file_path = os.path.join(self.__output_path,
                                                    output_file_name)

                    output_file = open(output_file_path, "w")
                    
                    sorter = []
                    for key, item in dictionary.items():
                        sorter.append(key)
                        
                    sorter.sort()

                    #for key, item in dictionary.items():
                    #    output_file.write("{}|{}|{}{}".format(key,
                    #                                          item[0],
                    #                                          item[1],
                    #                                          os.linesep))
                    
                    for item in sorter:
                        output_file.write("{}|{}|{}{}".format(item,
                                                              dictionary[item][0],
                                                              dictionary[item][1],
                                                              os.linesep))

                    output_file.close()

                    self.__result = "{} written to file:\n    {}".format(description,
                                                                         output_file_path)

                    break

                except FileNotFoundError:
                    print("ERROR - Invalid file name provided")

    def write_file_source(self):
        self.__write_file(self.SOURCE)

    def write_file_target(self):
        self.__write_file(self.TARGET)

    def __load_directory(self, load_path, strip_path, description):
        """
        Loads files from the provided path into the dictionary specified by
        the description parameter.
        
        Args:
            load_path: A string for the path to the directory that is to be 
                read.
            strip_path: Any portion of the path should be removed.  This is
                needed in case the files aren't located within the same path
                on either system.  Without this, all files would come back as
                different.
                
        Returns:
            Dictionary containing the list of files found in the provided 
            path.
        """

        output = {}

        if strip_path[:-1] not in ("/", "\\"):
            strip_path = os.path.join(strip_path, "~").strip("~")

        # Iterate through each file and subdirectory in the provided path.
        for path, subdirs, files in os.walk(load_path):
            for filename in files:
                full_file_name = os.path.join(path, filename)

                if filename not in self.__IGNORE_FILES:
                    file_size = os.path.getsize(full_file_name)
                    compare_file_name = full_file_name.replace(strip_path, "")

                    # output[compare_file_name] = (file_size, full_file_name)
                    getattr(self, "_ServerCompare__{}".format(description.lower()))[compare_file_name] = (
                    file_size, full_file_name)

        getattr(self, "_ServerCompare__{}".format(description.lower())).update(output)

    def __load_path(self, description):
        """
        Accepts input from the user in the form of file paths which are 
        then traversed to load files into one of the dictionaries.
        
        Args:
            description: A string value that denotes which dictionary
                should be loaded, source or target.  The values
                self.SOURCE or self.TARGET should be used when calling
                the method.
                
        Returns:
            None
        """
        load_path = "x"

        # Ask the user for paths to process.  Keep asking until the user enters
        # an empty path.
        while load_path:
            load_path = input("Path to load files from (enter nothing to finish): ")
            load_path = load_path.strip()
            load_path = load_path.replace("\ ", " ")

            if load_path:
                getattr(self, "_ServerCompare__{}_source".format(description.lower())).append(load_path)
                
                # Determine if any portion of the path should be removed.  This 
                # is needed in case the files aren't located within the same 
                # path on either system.  Without this, all files would come 
                # back as different.
                strip_path = input("Portion of path to remove: ").strip()

                self.__load_directory(load_path, strip_path, description)

        self.__result = "Completed loading {} from file system".format(description)

    def load_path_source(self):
        self.__load_path(self.SOURCE)

    def load_path_target(self):
        self.__load_path(self.TARGET)

    def __load_list(self, description):
        """
        Reads a list of paths from a file and loads the files from paths
        into the dictionary for later comparison.  This method allows for an
        easier way of loading files from the file system from multiple 
        directories.  
        
        Format for the file should be one line contains the path to load and
        the next line should contain the path to strip from the files.  Repeat
        for each path to load.
        
        Args:
            description: A string value that denotes which dictionary
                should be loaded, source or target.  The values
                self.SOURCE or self.TARGET should be used when calling
                the method.
                
        Returns:
            None
        """

        while True:
            try:
                file_path = input("Path to the list file for {}:".format(description)).strip()
                if file_path:
                    file_load = open(file_path, "r")
                break
            except IsADirectoryError:
                print("ERROR - Directory specified instead of a file.")
            except FileNotFoundError:
                print("ERROR - Cannot find file.  Check path and try again.")

        if file_path:
            lines = file_load.readlines()
            for line in lines:
                parts = line.rstrip("\n")
                parts = parts.split("|")
                
                getattr(self, "_ServerCompare__{}_source".format(description.lower())).append(parts[0])

                self.__load_directory(parts[0], parts[1], description)

            file_load.close()

            self.__result = "{} dirctory list loaded from {}".format(description,
                                                                     file_path)
        else:
            self.__result = "No {} list file loaded.".format(description)

    def load_list_source(self):
        self.__load_list(self.SOURCE)

    def load_list_target(self):
        self.__load_list(self.TARGET)

    def __clear_dictionary(self, description):
        """
        Clears the dictionary indicated by the description parameter.
        
        Args:
            description: A string value that denotes which dictionary
                should be cleared, source or target.  The values
                self.SOURCE or self.TARGET should be used when calling
                the method.
                
        Returns:
            None
        """
        if description == self.SOURCE:
            self.__source = {}
        else:
            self.__target = {}

        self.__result = "{} cleared".format(description)

    def clear_source(self):
        self.__clear_dictionary(self.SOURCE)

    def clear_target(self):
        self.__clear_dictionary(self.TARGET)

    def compare(self):
        """
        Compares the source and target dictionaries.
        
        Compare the dictionaries to get a list of files that need to be 
        added, deleted, or updated on the target system.  Files are 
        output to the output directory contained in the same directory
        as this file.  Files created:
            target_add.txt - Files to be added to the target system.
            target_del.txt - Files to be deleted from the target system.
            target_upd.txt - Files to be updated on the target system 
                because the file sizes are different from the source
                system.
        """
        if self.__source and self.__target:
            add_file_path = os.path.join(self.__output_path, "target_add.txt")
            del_file_path = os.path.join(self.__output_path, "target_del.txt")
            upd_file_path = os.path.join(self.__output_path, "target_upd.txt")

            add_file = open(add_file_path, "w")
            del_file = open(del_file_path, "w")
            upd_file = open(upd_file_path, "w")
            
            add_list = []
            del_list = []
            upd_list = []

            for key, item in self.__source.items():
                if key in self.__target:
                    if item[0] != self.__target[key][0]:
                        upd_list.append(item[1])
                else:
                    add_list.append(item[1])

            for key, item in self.__target.items():
                if key not in self.__source:
                    del_list.append(item[1])
                    
            add_list.sort()
            del_list.sort()
            upd_list.sort()
                        
            for item in add_list:
                add_file.write("{}\n".format(item))
                
            for item in del_list:
                del_file.write("{}\n".format(item))
                
            for item in upd_list:
                upd_file.write("{}\n".format(item))

            add_file.close()
            del_file.close()
            upd_file.close()

            self.__result = ("Comparison complete.  See files:\n"
                             "    {}\n"
                             "    {}\n"
                             "    {}").format(add_file_path,
                                              del_file_path,
                                              upd_file_path)

        elif not self.__source and not self.__target:
            self.__result = "ERROR - Cannot compare - no SOURCE or TARGET provided"

        elif not self.__source:
            self.__result = "ERROR - Cannot compare - no SOURCE provided"

        elif not self.__target:
            self.__result = "ERROR - Cannot compare - no TARGET provided"

    def copy_files(self):
        """
        Copies files that were identified as needing to be added or updated 
        on the target system to an external drive.
        
        Requies that the compare process be run prior to being used.
        """
        self.__result = "**** NOT READY YET ****"
        
    def source_status(self):
        """
        Provides details on the information loaded in the source dictionary.
        
        Args:
            None
            
        Returns:
            TODO
        """
        
        


def clear_screen():
    """
    Clears the terminal screen.
    """

    # The clear screen command is different depending on the OS.  Examine
    # the OS name and set the command appropriately.
    if system_name().lower() == "windows":
        command = "cls"
    else:
        command = "clear"

    os.system(command)


if __name__ == '__main__' and __package__ is None:

    server_comp = ServerCompare()

    action = ""

    menu = {}

    menu_count = 1
    menu[str(menu_count)] = ("load_file_source", "Load SOURCE from file")
    menu_count += 1
    menu[str(menu_count)] = ("load_path_source", "Load SOURCE from file system")
    menu_count += 1
    menu[str(menu_count)] = ("load_list_source", "Load SOURCE from folder list")
    menu_count += 1
    menu[str(menu_count)] = ("load_file_target", "Load TARGET from file")
    menu_count += 1
    menu[str(menu_count)] = ("load_path_target", "Load TARGET from file system")
    menu_count += 1
    menu[str(menu_count)] = ("load_list_target", "Load TARGET from folder list")
    menu_count += 1
    menu[str(menu_count)] = ("write_file_source", "Write SOURCE to file")
    menu_count += 1
    menu[str(menu_count)] = ("write_file_target", "Write TARGET to file")
    menu_count += 1
    menu[str(menu_count)] = ("compare", "Compare")
    menu_count += 1
    menu[str(menu_count)] = ("clear_source", "Clear SOURCE")
    menu_count += 1
    menu[str(menu_count)] = ("clear_target", "Clear TARGET")
    menu_count += 1
    menu[str(menu_count)] = ("copy_files", "Copy files to folder")

    menu["X"] = ("", "Exit")

    while action != "X":

        clear_screen()

        if action:
            print("Result from last command:")
            print("  {}".format(server_comp.result))
            print("")

        print("Status:")
        print("  SOURCE : {}".format("Loaded" if server_comp.source_populated
                                     else "Emtpy"))
        print("  TARGET : {}".format("Loaded" if server_comp.target_populated
                                     else "Empty"))
        print("")

        # Get input from the user
        print("Action:")
        for menu_key, menu_item in menu.items():
            print("  {} - {}".format(menu_key, menu_item[1]))

        action = input("Choose action: ")

        action = action.upper()

        result = ""

        if action == "X":
            break
        elif action in menu:
            getattr(server_comp, menu[action][0])()
        else:
            input("Invalid selection (press <enter> to continue)")
            action = ""

# The following code could be used one day to allow the script to load files
# directly from PMS.

# Check if Uffizi is running.
# **** Not sure if having Uffizi running will be needed, but this will figure it
# **** out if it is.
# process_name= "Uffizi.py" # change this to the name of your process

# tmp = os.popen("ps -Af").read()

# if process_name not in tmp[:]:
#    print("The process is not running. Let's restart.")
# else:
#    print("The process is running.")



# TO DO
# 1. Add more information about the state of the source and target dictionaries
# 2. Add a progress bar and more info to loading files