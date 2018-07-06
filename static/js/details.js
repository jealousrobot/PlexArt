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

// Set the dimensions of items that can change depending on the size of the 
// browser window.
function setDimensionsSection() {
  var seasonTop;
  var elementID;
  var seasonID;
  var stopRowCheck = 0
  var totalWidth;
  
  // Determine what the height of the results DIV should be.  It is the
  // size of the display area minus the heights of the header and the nav
  // bar.
  var resultsHeight = window.innerHeight - 90;
  $('#results').css('height', resultsHeight);
  
  // Set the width of the drawer that shows seasons/albums.
  if (gSectionType == 'details_show' || gSectionType == 'details_artist') {
    $('.seasons').css('width', '100%'); 
  }
}

function showSeasons() {
  var seasons = document.getElementsByClassName('seasons'); 
       
  // Loop through the list detail elements.
  for (i=0; i<seasons.length; i++) {  
    var elementID = getKey(seasons[i].id); 
    
    // Get the XML for the seasons for the TV Show
    $.ajax({
      type: 'GET',
      dataType: 'xml',
      url: buildMetaDataURL('/library/metadata/' + elementID + '/children'),
      success: parseSeasonXML
    });
    
    function parseSeasonXML(xml) {
      var result = '';
      
      $(xml).find('Directory').each(function()
      {
        // Skip the first record
        if ($(this).attr('parentRatingKey') == elementID) {
          result += '<div class="' + div_name + '">';
          result += '    <div class="season">';
          result += '        <div class="season_img"><img id="seasonImage-' + $(this).attr('ratingKey') + '" class="' + elementID + '" src="/image?server=' + gServer + '&path=' + $(this).attr('thumb') + '&type=thumb' + '" width="100" height="' + img_height + '"></div>';
          result += '        <div class="season_title">' + $(this).attr('title') + '</div>';
          result += '    </div>';
          result += '</div>';
        }
      });
      
      $('#season-' + elementID).html(result);
    }
  }   
}

$(document).ready(function(){
  
  if (gSectionType == 'details_show') {
    div_name = 'season_block_tv';
    img_height = '150';
  }
  else {
    div_name = 'season_block_music';
    img_height = '100'
  }
  
  setDimensionsSection();
  
  // Populate the thumbnail images for the seasons.
  showSeasons();
  
});