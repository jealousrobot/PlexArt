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

$(document).ready(function(){
    
    function getKey(inputID) {
        var idPos = inputID.search('-') + 1;
        var keyValue = inputID.substr(idPos, inputID.length);
        
        return keyValue;
    }
    
    function getMetaValue(metaName) {
        return document.getElementById(metaName).getAttribute('content'); 
    }
    
    function positionDrawer(seasonID) {
        // Determine how far to the left the seasons DIV needs to
        // be moved.  As loaded, the DIV is lined up on the left 
        // with the video thumbnail.
        
        var videoLeft;
        var seasonLeft;
        var firstLeft;
        var i;
        
        // Get the ID associated with the video block of the season.
        var videoID = 'block-' + getKey(seasonID);
        
        // Get all of the video blocks.                    
        var videoBlocks = document.getElementsByClassName('video_block'); 
        
        // Loop through the video blocks to get to the block defined in
        // videoID.
        for (i=0; i<videoBlocks.length; i++) {
            
            // Save the value of the first block.  This is needed 
            // for calculating the left offset of the season block.
            if (i == 0) {
                firstLeft = videoBlocks[i].offsetLeft;
            }
            
            // If the current block is the video block we are after
            // derive the value to shift the season block.
            if (videoBlocks[i].id == videoID) {
                // If the offsetLeft of the current video block is
                // the same as the first block, then this block is
                // in the first column and the season block is already 
                // where it needs to be.
                if (videoBlocks[i].offsetLeft != firstLeft) {
                    seasonLeft = (videoBlocks[i].offsetLeft - firstLeft) * -1;
                    $(seasonID).css('left',seasonLeft);
                }
                else
                    $(seasonID).css('left', 0);
                // We found what we are looking for.  No need to
                // continue looping.
                break;
            }
        }    
    }
    
    // Set the width of the seasons DIV elements.
    function setDimensions() {
        
        var seasonTop;
        var elementID;
        var seasonID;
        var stopRowCheck = 0
        
        // Determine what the height of the results DIV should be.  It is the
        // size of the display area minus the heights of the header and the nav
        // bar.
        var resultsHeight = window.innerHeight - 90;
        $('#results').css('height', resultsHeight);
        
        var section_type = getMetaValue('metaSectionType');
        
        // Set the width of the drawer that shows seasons/albums.
        if (section_type == 'show' || section_type == 'artist')
        {
            // Loop through the video blocks until finding one on a different
            // row.  This will tell us how many images are on a row, which in
            // in turn can be used to determine how wide to make the drawer.
            var videoBlocks = document.getElementsByClassName('video_block'); 
            var upperLeftTop;
            var upperLeftLeft;
            var upperRightLeft;
            var totalWidth;
            for (var i=0; i<videoBlocks.length; i++) {
                if (i == 0) {
                    // Set the values for the upper left most block.
                    upperLeftTop = videoBlocks[i].offsetTop;
                    upperLeftLeft = videoBlocks[i].offsetLeft;
                }
                else {
                    // If the offsetTop value changes then this block is on
                    // the next line.  The width can now be calculated
                    if (upperLeftTop != videoBlocks[i].offsetTop) {
                        // Width of the shelf is the position of the left 
                        // side of the last image on the row minus the left 
                        // position of the first image in the row.  Add to 
                        //that the width of the video block.
                        totalWidth = upperRightLeft - upperLeftLeft + videoBlocks[i].offsetWidth;
                        // Update the width property in the CSS of the seasons DIV.
                        $('.seasons').css('width', totalWidth);
                        
                        // Set the number of columns.
                        document.getElementById('metaCols').getAttribute('content', i-1);
                        
                        // Exit the loop as we now know what the width of the 
                        // drawer should be.
                        break;
                    }
                    else {
                        upperRightLeft = videoBlocks[i].offsetLeft;
                    }
                }                      
            } 
            
            $('.seasons').css('width', totalWidth); 
            
            // Determine if there is an open drawer.  If so, reposition as it's
            // now probably no longer aligned to the left edge of the display
            // area.  
            var drawerID = getMetaValue('metaSlider');
        
            if (drawerID != null) {
                positionDrawer(drawerID);
            }
        }
    }
    
    function rotateImage(sliderID, direction) {
      var elementID = getKey(sliderID);
      var drawerID = "#drawer-" + elementID;
      var deg = '';
      
      if (direction == 'down')
        $(drawerID).rotate({animateTo:180})
      else 
       $(drawerID).rotate({animateTo:0})
    }
    
    function showSeasons(elementName) {
        
        var metaSetValue;
        
        var plex_url = getMetaValue('metaPlexUrl');
        
        // Get the content of the meta tag metaSlider, which contains the 
        // currently open season block.
        var slider = getMetaValue('metaSlider');
        
        if (slider != null) {
            $(slider).slideUp('slow');
            
            // Rotate the icon of the open drawer
            rotateImage(slider, 'up');
        }
        
        // Based on the element that was clicked, and provided in the 
        // elementName input paraemter, build the ID value of the DIV for the
        // drawer.
        var elementID = getKey(elementName); 
        var seasonID = '#season-' + elementID;
        
        // Get the XML for the seasons for the TV Show
        $.ajax({
            type: 'GET',
            dataType: 'xml',
            url: plex_url + '/library/metadata/' + elementID + '/children',
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
                    result += '        <div class="season_img"><img id="seasonImage-' + $(this).attr('ratingKey') + '" class="' + elementID + '" src="' + plex_url + $(this).attr('thumb') + '" width="100" height="' + img_height + '"></div>';
                    result += '        <div class="season_title">' + $(this).attr('title') + '</div>';
                    result += '    </div>';
                    result += '</div>';
                }
            });
            
            $(seasonID).html(result);
        }   
        
        positionDrawer(seasonID);                 
                                                
        // Toggle the DIV holding the season images.
        if (seasonID != slider) {
            $(seasonID).slideDown('slow');
            metaSetValue = seasonID;
            rotateImage(seasonID, 'down');
        }
        else {
            metaSetValue = "x";
        }
        
        document.getElementById('metaSlider').setAttribute('content', metaSetValue);
    }
    
    function refreshVideo(elementName) {
      var plexURL = getMetaValue('metaPlexUrl');
      var sectionType = getMetaValue('metaSectionType');
      
      var elementID = getKey(elementName);
      var thumbID = '#thumb-' + elementID;
      var artID = '#art-' + elementID;
      var seasonID = '#season-' + elementID;
      
      // Rotate the refresh button one time.
      $('#refresh-' + elementID).rotate({
        duration:3000,
        angle: 0,
        animateTo:360
      });
      
      // Continually rotate the refresh button.  The intent being that it would
      // rotate until the refresh was complete.  Could not figure out how to do 
      // it with the async AJAX calls.
      //var angle = 0;
      //var spinRefresh = setInterval(function(){
       //             angle+=3;
      //              $('#refresh-' + elementID).rotate(angle);
      //            },50);
          
      // All of the seasons have the same class assigned to them.  The class is
      // named after the key of the show/artist.  Fade out all of the 
      // seasons/albums at once using the class.
      $('.' + elementID).fadeTo('slow', .1);
      
      // Fade out the old images.  Refreshed image will be faded in later.
      $(thumbID).fadeTo('slow', .1);
      $(artID).fadeTo('slow', .1, refreshImages);
      
      function refreshImages() {
        // Get the XML for the video.  This contains the paths to the thumb and 
        // artwork.
        $.ajax({
            type: 'GET',
            dataType: 'xml',
            url: plexURL + '/library/metadata/' + elementID,
            success: reloadImage
        });
        
        // Function that proceses once the AJAX call has completed.
        function reloadImage(xml) {
          var thumb = '';
          var art = '';
          var sectionElement = '';
          
          // Based on the type of section, set the element to look for in the
          // XML.
          if (sectionType == 'show' || sectionType == 'artist')
            sectionElement = 'Directory';
          else
            sectionElement = 'Video';
          
          // Build the URL for the image.
          $(xml).find(sectionElement).each(function()
          {
            thumb = plexURL + $(this).attr('thumb');
            art = plexURL + $(this).attr('art');
          });
                    
          // Refresh the seasons if a TV show or music
          if (sectionType == 'show' || sectionType == 'artist') {
            // Get the XML for the seasons for the TV Show
            $.ajax({
                type: 'GET',
                dataType: 'xml',
                url: plexURL + '/library/metadata/' + elementID + '/children',
                success: parseSeasonXML
            });
            
            function parseSeasonXML(xml) {
                var seasonImagePath = '';
                var seasonImageID = '';
                
                $(xml).find('Directory').each(function()
                {
                    // Skip the first record
                    if ($(this).attr('parentRatingKey') == elementID) {
                        seasonImageID = '#seasonImage-' + $(this).attr('ratingKey');
                        seasonImagePath = plexURL + $(this).attr('thumb') + 'x';
                        $(seasonImageID).attr("src", seasonImagePath);
                    }
                });
                
                // Fade the seasons/album back.
                $('.' + elementID).fadeTo('slow', 1);
                
                // Update the source to the new image and fade it back in.
                $(thumbID).attr('src', thumb);
                $(thumbID).fadeTo('slow', 1);
                $(artID).attr('src', art);
                $(artID).fadeTo('slow', 1);
            }
          }
          else {
            // Update the source to the new image and fade it back in.
            $(thumbID).attr('src', thumb);
            $(thumbID).fadeTo('slow', 1);
            $(artID).attr('src', art);
            $(artID).fadeTo('slow', 1);
          }
           
            // Stop the refresh button from spinning.  Doesn't work.
            //clearInterval(spinRefresh);
            //$('#refresh-' + elementID).rotate({
             // angle: 0,
             // animateTo:0
            //});
        }
      }
    }
        
    $(".video_img").click(function(){
      //showSeasons($(this).attr("id"));
      var seasonID = '#season-' + getKey($(this).attr('id'));
      positionDrawer(seasonID);
    });
    
    $(".video_title").click(function(){
      //var elementID = getKey($(this).attr("id"));
      //var seasonID = '#season-' + elementID;
      //$(seasonID).slideDown('slow');
    });
    
    $(".video_drawer").click(function(){
        showSeasons($(this).attr("id"));
    });
    
    $(".seasons").click(function(){
        showSeasons($(this).attr("id"));
    });
    
    $(".video_refresh").click(function(){
      refreshVideo($(this).attr("id"));
    });
    
    $(window).resize(function(){
        // If the window is resized, reset the widths of the 
        // seasons DIVs.
        setDimensions();
    });
    
    // Get the section type from the meta tag.
    var section_type = getMetaValue('metaSectionType');
    
    // Calling set_dimensions here will set the width for all of the 
    // season DIVs after the page has loaded.
    setDimensions();
    
    if (section_type == 'show') {
        div_name = 'season_block_tv';
        img_height = '150';
    }
    else {
        div_name = 'season_block_music';
        img_height = '100'
    }
});