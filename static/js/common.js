// Uffizi - View all of the artwork for Plex sections at once          
// Copyright (C) 2016 Jason Ellis                                      
//                                                                      
// This program is free software: you can redistribute it and/or modify 
// it under the terms of the GNU General Public License as published by 
// the Free Software Foundation, either version 3 of the License, or    
// (at your option) any later version.                                  
//                                                                      
// This program is distributed in the hope that it will be useful,      
// but WITHOUT ANY WARRANTY; without even the implied warranty of       
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        
// GNU General Public License for more details.                         
//                                                                      
// You should have received a copy of the GNU General Public License    
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

function getKey(inputID) {
  var idPos = inputID.search('-') + 1;
  var keyValue = inputID.substr(idPos, inputID.length);
      
  return keyValue;
}

function setDimensions(){
  // Determine what the height of the results DIV should be.  It is the
  // size of the display area minus the heights of the header and the nav
  // bar.
  var resultsHeight = window.innerHeight - 90;
  $('#results').css('height', resultsHeight);
}