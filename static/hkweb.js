// This file is part of Heapkeeper.
//
// Heapkeeper is free software: you can redistribute it and/or modify it
// under the terms of the GNU General Public License as published by the Free
// Software Foundation, either version 3 of the License, or (at your option) any
// later version.
//
// Heapkeeper is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
// FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
// more details.
//
// You should have received a copy of the GNU General Public License along with
// Heapkeeper.  If not, see <http://www.gnu.org/licenses/>.

// Copyright (C) 2010 Csaba Hoch


///// Types /////

// - postId: a string which contains a heap id and a post index, separated with
//   a '-' sign. Example: 'myheap-11'
// - postIdStr: a string which is very similar to postId, but uses '/' as a
//   separator. Internally Heapkeeper's JavaScript code uses PostId, because he
//   '/' character has a special meaning in JQuery, but externally Heapkeeper
//   uses postIdStr.

function postIdToPostIdStr(postId) {
    return postId.replace('-', '/');
}

function postIdStrToPostId(postId) {
    return postId.replace('/', '-');
}


///// AJAX /////

function ajaxQuery(url, args, callback) {
    // Performs an AJAX query using JSON texts and calls the callback function
    // with the result.
    //
    // - url(str) -- The URL to be sent to the server.
    // - args(object) -- `args` will be converted to a JSON text and sent to the
    //   server.
    // - callback (fun(result)) -- Function to be called after we received the
    //   result. The server is expected to send a JSON text that will be
    //   converted to the `result` object.

    $.ajax({
        url: url,
        dataType: 'json',
        data: {'args': JSON.stringify(args)},
        type: 'post',
        success: callback
    });
}


///// Scrolling /////

// Code copied from Peter-Paul Koch:
// http://www.quirksmode.org/js/findpos.html
function ObjectPosition(obj) {
    var curleft = 0;
    var curtop = 0;
    if (obj.offsetParent) {
        do {
            curleft += obj.offsetLeft;
            curtop += obj.offsetTop;
        } while (obj = obj.offsetParent);
    }
    return [curleft, curtop];
}

// Code copied from Michael Khalili:
// http://www.michaelapproved.com/articles/scroll-to-object-without-leaving-page
function ScrollTo(obj) {
    var objpos = ObjectPosition(obj);
    scroll(0,objpos[1]);
    window.scrollTo(0, objpos[1]);
}

function ScrollToId(id) {
    ScrollTo(document.getElementById(id))
}


///// Post body visibility /////

function getPostIds() {
    // Returns an array that contains all post ids present on the page.
    //
    // Returns: [str]

    return $('.post-body-container').map(function(index) {
        return $(this).attr('id').replace(/post-body-container-/, '');
    });
}

function isPostBodyVisible(postId) {
    // Returns whether the post body is visible.
    //
    // Argument:
    //
    // - postId (PostId)

    return ($('#post-body-container-' + postId).css('display') != 'none');
}

function hidePostBody(postId) {
    // Hides a post body and shows the "Show body" button.
    //
    // Argument:
    //
    // - postId (postId)

    $('#post-body-container-' + postId).hide('fast');

    // Showing the "Show body" button. `show('fast')` would not be good instead
    // of `animate`, because that would set the style.display to 'block', but
    // we need it to be ''.
    $('#post-body-show-button-' + postId).animate(
        {opacity: 'show' }, 'fast');
}

function showPostBody(postId) {
    // Shows a post body and hides the "Show body" button.
    //
    // Argument:
    //
    // - postId (PostId)

    $('#post-body-container-' + postId).show('fast');

    $('#post-body-show-button-' + postId).animate(
        {opacity: 'hide' }, 'fast');
}

// High level funtions

function togglePostBodyVisibility(postId) {
    // Toggles the visibility of a post's body.
    //
    // Argument:
    //
    // - postId (str)

    if (isPostBodyVisible(postId)) {
        hidePostBody(postId);
    } else {
        showPostBody(postId);
    }
}

function hideAllPostBodies() {
    // Turns off the visibility for all visible post bodies.

    getPostIds().each(function(index) {
        hidePostBody(this);
    });
}

function showAllPostBodies() {
    // Turns on the visibility for all hidden post bodies.

    getPostIds().each(function(index) {
        showPostBody(this);
    });
}


///// Post body editing /////

function getRawPostBodyRequest(postId, callback) {
    // Gets the raw body of the given post and executes a callback function with
    // it.
    //
    // Arguments:
    //
    // - postId (PostId)
    // - callback (fun(rawPostBody: str))

    var postIdStr = postIdToPostIdStr(postId);
    $.get("/raw-post-bodies/" + postIdStr, {}, callback);
}

function setPostBodyRequest(postId, newPostBodyText, callback) {
    // Sets the body of the given post in a raw format.
    //
    // Arguments:
    //
    // - postId (PostId)
    // - callback (fun(result)) -- Function to be called after we set the post
    //   body. `result` is the information returned by the server.

    ajaxQuery(
        "/set-post-body/" + postIdToPostIdStr(postId),
        {'new_body_text': newPostBodyText},
        callback);
}

function editPostBody(postId) {
    // Lets the user edit the post of a post.
    //
    // The post-body-content box is replaced with a textarea that contains
    // the post body.
    //
    // Argument:
    //
    // - postId (PostId)

    getRawPostBodyRequest(postId, function(postBodyText) {
        var postBodyContainer = $('#post-body-container-' + postId);
        var postBodyContentNode = $('.post-body-content', postBodyContainer);

        // Replacing the post-body-content box with a textarea
        postBodyContentNode.after(
            '<textarea id="post-body-textarea-' + postId + '"' +
            ' rows="10" cols="80">' +
            '</textarea>').remove();

        // Adding the text to the textarea
        var textArea = $('textarea', postBodyContainer);
        textArea.attr('class', 'post-body-content');
        textArea.val(postBodyText);
        textArea.focus();

        // Changing the "Edit" button to "Save"
        var editButton = $('#post-body-edit-button-' + postId);
        editButton.html('Save');
        editButton.unbind('click');
        editButton.bind('click', function() { savePostBody(postId); });
     });
}

function savePostBody(postId) {
    // Saves the contents of the post's textarea as the new post body.
    //
    // The textarea is replaced with the post-body-content box that contains
    // the new body.
    //
    // Argument:
    //
    // - postId (PostId)

    var postBodyContainer = $('#post-body-container-' + postId);
    var textArea = $('textarea', postBodyContainer);
    var newPostBodyText = textArea.val();

    setPostBodyRequest(postId, newPostBodyText, function(result) {

        if (result.error) {
            window.alert('Error occured:\n' + result.error);
            return;
        }

        // Replacing the textArea with the received post-body-container
        // box
        textArea.replaceWith(result.new_body_html);

        // Changing the "Save" button to "Edit"
        var editButton = $('#post-body-edit-button-' + postId);
        editButton.html('Edit');
        editButton.unbind('click');
        editButton.bind('click', function() { editPostBody(postId); });
     });
}
