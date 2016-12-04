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

function validateForm() {
  
  var user = document.forms['signIn']['username'].value;
  var pw = document.forms['signIn']['password'].value;
  
  $('#serverError').css('visibility', 'hidden');
    
  if (user == null || user == '') {
    $('#serverNameDiv').effect("shake");
    $('#errorText').html('Plex.tv Username is required');
    $('#serverError').css('visibility', 'visible');
    $('#serverName').focus();
    return false;
  } 
  
  if (pw == null || pw == '') {
    $('#serverPortDiv').effect("shake");
    $('#errorText').html('Plex.tv Password is required');
    $('#serverError').css('visibility', 'visible');
    $('#serverPort').focus();
    return false;
  }
    
  
  // Get the token
  $.ajax({
    type: 'GET',
    dataType: 'text',
    url: '/token?username=' + user + '&password=' + pw,
    success: function(xml) {
      // Token was successfully retrieved.  
      
      // The browser will be redirected.  The URL to use is a parameter to the
      // current page.  Get the parm.
      var URLCurrent = window.location.href;
      var URLParms = URLCurrent.split("?");
      var URLRedirect = decodeURIComponent(URLParms[1].split("=")[1]);

      window.location.href = URLRedirect
    },
    error: function (xml) {
      // Token was not retrieved.  Show an error to the user.
      $('#serverInputs').effect('shake');
      $('#errorText').html('Could not retrieve Plex.tv token');
      $('#serverError').css('visibility', 'visible');
      return false;
    }
  });
} 

function checkSubmit(keyPress)
{
   if(keyPress && keyPress.keyCode == 13)
   {
      validateForm();
   }
}