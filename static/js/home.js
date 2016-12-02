// PlexArt - View all of the artwork for Plex sections at once             
// Copyright (C) 2016  Jason Ellis                                         
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

function buildMetaDataURL(server, port, path) {
    return '/metadata?server=' + server + '&port=' + port + '&path=' + path
  }

function validateForm() {
  
  var serverName = document.forms['getServer']['serverName'].value;
  var serverPort = document.forms['getServer']['serverPort'].value;
  
  $('#serverError').css('visibility', 'hidden');
    
  if (serverName == null || serverName == '') {
    $('#serverNameDiv').effect("shake");
    $('#errorText').html('Server Name is required');
    $('#serverError').css('visibility', 'visible');
    $('#serverName').focus();
    return false;
  } 
  
  if (serverPort == null || serverPort == '') {
    $('#serverPortDiv').effect("shake");
    $('#errorText').html('Server Port is required');
    $('#serverError').css('visibility', 'visible');
    $('#serverPort').focus();
    return false;
  }
  
  var plexURL = 'http://' + serverName + ':' + serverPort + '/library/'
  
  // Validate that the server and port combination leads to Plex.
  $.ajax({
      type: 'GET',
      dataType: 'xml',
      url: buildMetaDataURL(serverName, serverPort, '/library/'),
      async: false,
      error: errorResponse,
      success: successResponse
  }); 
  
  function successResponse(xml) {
    $(xml).find('MediaContainer').each(function()
    {
      // Check just to make sure that the XML that came back has a Plex related
      // tag.  If so, go to the server page, otherwise show an error.
      if ($(this).attr('title1') == 'Plex Library') {
        $(location).attr('href', '/server?server=' + serverName + '&port=' + serverPort)
      }
      else {
        $('#serverInputs').effect('shake');
        $('#errorText').html('This is not a valid Plex server and port combination.');
        $('#serverError').css('visibility', 'visible');
        return false;
      }
    });
  }
  
  function errorResponse() {
    $('#serverInputs').effect('shake');
    $('#errorText').html('This is not a valid Plex server and port combination: ');
    $('#serverError').css('visibility', 'visible');
    return false;
  }
}

function checkSubmit(keyPress)
{
   if(keyPress && keyPress.keyCode == 13)
   {
      validateForm();
   }
}