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

var currentModal = "";

function buildMetaDataURL(server, port, path) {
    return '/metadata?server=' + server + '&port=' + port + '&path=' + path
}
  
function showEditServer(server) {
  var server_tbl = "";
  var valid_check, always_check;
  var server_port;
  
  $.ajax({
    type: 'GET',
    datatype: 'xml',
    url: '/get_server_details?server=' + server,
    success: function(xml){
      $('#xserverName').html($(xml).filter(":first").attr('name'));
      $('#xplatformName').html($(xml).filter(":first").attr('platform') + " (" + $(xml).filter(":first").attr('source') + ')');
      
      server_tbl = '<div class="sd_header">';
      server_tbl += '<div class="sd_cell_1 bold">Address</div>';
      server_tbl += '<div class="sd_cell_2 bold">Port</div>';
      server_tbl += '<div class="sd_cell_3 bold">Valid</div>';
      server_tbl += '<div class="sd_cell_4 bold">Always Use</div>';
      server_tbl += '</div>';
      
      $(xml).find('address').each(function(){
        server_tbl += '<div class="sd_row">';
        server_tbl += '<span class="sd_cell_1">' + $(this).attr('address') + '</span>';
        server_tbl += '<span class="sd_cell_2">' + $(this).attr('port') + "</span>";
        
        server_port = $(this).attr('address') + '-' + $(this).attr('port');
        server_port = $(this).attr('port');
        
        if ($(this).attr('valid') == 'Y')
          valid_check = 'checked';
        else
          valid_check = '';
          
        if ($(this).attr('always_use') == 'Y')
          always_check = 'checked';
        else
          always_check = '';
          
        server_tbl += '<span class="sd_cell_3"><input type="checkbox" name="valid" value="Y" ' + valid_check + '></span>';
        server_tbl += '<span class="sd_cell_4"><input type="radio" class="au" name="always_use" value="Y" ' + always_check + '></span>';
        server_tbl += '</div>\n';
      });
      $("#editServerInputs").html(server_tbl);
      $("#progressbar_modal").hide()
      $("#edit_modal").show(); 
    },
  });
}

function saveServerEdit() {
  var i = 0;
  var address, port, valid, always, parms;
  var row = 0;
  
  parms = 'server=' + $('#xserverName').text();
  
  $(".sd_row").each(function(index) {
    row++;
    i = 0;
    $(this).children('span').each(function() {
      i++;
      
      switch(i) {
        case 1:
          address = this.innerText;
          break;
        case 2:
          port = this.innerText;
        case 3:
          $(this).children('input').each(function() {
            if (this.checked)
              valid = "Y";
            else
              valid = "N";
          });
          break;
        case 4:
          $(this).children('input').each(function() {
            if (this.checked)
              always = "Y";
            else
              always = "N";
          });
          break;
      };
    });
    
    parms += "&row" + row + '=' + address + ',' + port + ',' + valid + ',' + always;
  });

  $.ajax({
    type: 'GET',
    dataType: 'text',
    url: '/edit_server_details?' + parms,
    success: function(){
      $('#edit_modal').fadeOut(); 
    },
    error: function() {
      alert('error');
    },
  });
}
  
function refreshServers() {
  $("#progressbar_modal").show();
  $.ajax({
    type: 'GET',
    dataType: 'text',
    url: '/refresh_servers',
    success: refreshServersSuccess}); 
}

function refreshServersSuccess() {
  $("#progressbar_modal").hide();
  window.open("home", "_self");
}

function addServer() {
  $('#serverError').css('visibility', 'hidden');
  currentModal = "#add_modal";
  $("#add_modal").fadeIn();
}

function validateForm() {
  
  var serverAddress = document.forms['getServer']['serverName'].value;
  var serverPort = document.forms['getServer']['serverPort'].value;
  
  $('#serverError').css('visibility', 'hidden');
    
  if (serverAddress == null || serverAddress == '') {
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
  
  // Validate that the server and port combination leads to Plex.
  $.ajax({
      type: 'GET',
      dataType: 'xml',
      url: 'add_server?address=' + serverAddress + '&port=' + serverPort,
      async: false,
      error: errorResponse,
      success: successResponse
  }); 
  
  function successResponse(xml) {
    
    $(xml).find("server").each(function() {
        //elementID = $(this).find('name').text();
        //server_status = $(this).find('status').text();
        elementID = $(this).attr('name');
        server_status = $(this).attr('status');
        
        if (server_status == 'up') {
          $("#add_modal").fadeOut();
          $(location).attr('href', '/server?server=' + elementID)
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

function openServer(item) {
  var server, img_src;
  
  server = getKey($(item).attr("id"));
  
  img_src = $('#status-' + server).attr('src');
  
  if (img_src != '/static/images/server_down.png')  
    window.open("server?server=" + server, "_self");
    
  server = "";
}

function closeModal(inElement) {
    var dashPos = inElement.search('-');
    var modalDiv = "#" + inElement.substr(0, dashPos);
    
    $(modalDiv).fadeOut(); 
}

$(window).resize(function(){
  // If the window is resized, reset the widths of the 
  // seasons DIVs.
  setDimensions();
});

$(document).ready(function(){
  
  $("#editServerInputs").on("click", ".au", function(){
    always_use = this;
    
    //$(".au").each(function(index) {
    //  if (this != always_use){
    //    //$(this).attr('checked','false');
    //    var elem_name = $(this).attr('name');
    //    var what = 'input:checkbox[name=' + elem_name + ']';
    //    $(what).attr('checked',false);
    //    //$(this).removeAttr('checked');
    //  }
    //});
  });
  
  $('.modal_close').click(function() {
    closeModal($(this).attr("id"));
  });
  
  $('.modal_cancel').click(function() {
    closeModal($(this).attr("id"));
  });
    
    
  $(".item_image").click(function(){
    openServer(this);
  });
  
  $(".item_title2").click(function(){
    openServer(this);
  });
  
  setDimensions();
  
  // Determine if the servers are online.
  var servers = document.getElementsByClassName('server_icon'); 
  for (i=0; i<servers.length; i++) {  
    var elementID = getKey(servers[i].id);
    
    $.ajax({
      type: 'GET',
      dataType: 'xml',
      url: '/server_status?server=' + elementID,
      success: changeImage
    });
     
    function changeImage(xml) {
      $(xml).find("server").each(function() {
        //elementID = $(this).find('name').text();
        elementID = $(this).attr('name')
        status_id = '#status-' + elementID;
        image_id = '#image-' + elementID;
        title2_id = '#title2-' + elementID;
        
        //server_status = $(this).find('status').text();
        server_status = $(this).attr('status')
                
        $(status_id).attr('src', '/static/images/server_' + server_status + '.png');
        
        if (server_status == 'up') {
          cursor_class = 'pointer';
        }
        else {
          cursor_class = 'arrow'
        }
        
        $(image_id).addClass(cursor_class);
        $(title2_id).addClass(cursor_class);
      });
    }
  }
})

$(function() {
  $("#progressbar").progressbar({
    value: false
  });
});
