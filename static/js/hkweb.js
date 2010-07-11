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


///// Communication with the server: HTML queries and AJAX /////

function gotoURL(url, args) {
    // Goes to the specified URL; the query parameters will be created from
    // `args`.
    //
    // - url(str) -- The URL to load. If empty string, the current URL (with
    //   'args' as query parameters) will be loaded.
    // - args(object) -- `args` will be converted to a JSON text and sent to
    //   the server as query parameters.

    // `query_url` will look like this:
    //
    //     <url>?<key1>=<value1>&<key2>=<value2>&...
    //
    // where:
    // - all keys are escaped
    // - all values are converted to JSON and then escaped
    data = [url + '?'];
    var first = true;
    $.each(args, function(key, value) {
        if (first) {
            first = false;
        } else {
            data.push('&');
        }
        data.push(escape(key) + '=' + escape(JSON.stringify(value)));
    });
    query_url = data.join('');

    $(location).attr('href', query_url);
}

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

    data = {};
    $.each(args, function(key, value) {
        data[key] = JSON.stringify(value);
    });

    $.ajax({
        url: url,
        dataType: 'json',
        data: data,
        type: 'post',
        success: callback
    });
}


///// Basic DOM stuff /////

function setButtonVisibility(button, visibility) {
    // Sets the visibility of a button.
    //
    // When the button has to be hidden, it is not animated, but when it
    // appears, it is.
    //
    // Arguments:
    //
    // - button(JQuery)
    // - visibility(str) -- Either 'show' or 'hide'.

    if (visibility == 'show') {
        button.animate({opacity: visibility}, 'fast');
    } else {
        button.hide();
    }
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

function getRootPostId() {
    // Returns the root of the thread that is displayed.
    //
    // Returns: str

    return location.href.replace(/^.*\/([^\/]+)\/([^\/]+)$/, '$1-$2');
}

function hidePostBody(postId) {
    // Hides a post body and shows the "Show body" button.
    //
    // Argument:
    //
    // - postId (postId)

    $('#post-body-container-' + postId).hide('fast');
    setButtonVisibility($('#post-body-show-button-' + postId), 'show');
}

function showPostBody(postId) {
    // Shows a post body and hides the "Show body" button.
    //
    // Argument:
    //
    // - postId (PostId)

    $('#post-body-container-' + postId).show('fast');
    setButtonVisibility($('#post-body-show-button-' + postId), 'hide');
}

// High level funtions

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

// Keys: post ids that are being edited.
// Values: mode of editing: either 'body' if the body is edited or 'raw' if the
// raw post text is edited.
var editState = {}

function getRawPostRequest(postId, mode, callback) {
    // Gets the raw body of the given post and executes a callback function with
    // it.
    //
    // Arguments:
    //
    // - postId (PostId)
    // - mode(str) -- Either 'body' or 'raw'.
    // - callback (fun(rawPostBody: str))

    var postIdStr = postIdToPostIdStr(postId);
    if (mode == 'body') {
        $.get("/raw-post-bodies/" + postIdStr, {}, callback);
    } else if (mode == 'raw') {
        $.get("/raw-post-text/" + postIdStr, {}, callback);
    }
}

function setPostContentRequest(postId, newPostText, mode, callback) {
    // Sets the body of the given post in a raw format.
    //
    // Arguments:
    //
    // - postId (PostId)
    // - newPostText(str)
    // - mode(str) -- Either 'body' or 'raw'.
    // - callback (fun(result)) -- Function to be called after we set the post
    //   body. `result` is the information returned by the server.

    if (mode == 'body') {
        ajaxQuery(
            "/set-post-body/" + postIdToPostIdStr(postId),
            {'new_body_text': newPostText},
            callback);
    } else if (mode == 'raw') {
        ajaxQuery(
            "/set-raw-post/" + postIdToPostIdStr(postId),
            {'new_post_text': newPostText},
            callback);
    }
}

function getPostBodyRequest(postId, callback) {
    // Gets the body of the given post.
    //
    // Arguments:
    //
    // - postId (PostId)
    // - callback (fun(result)) -- Function to be called with the post body.
    //   `result` is the information returned by the server.

    ajaxQuery(
        "/get-post-body/" + postIdToPostIdStr(postId),
        {},
        callback);
}

function editPostStarted(postId) {
    // Should be called when editing the post body has been started.
    //
    // - postId (PostId)

    setButtonVisibility($('#post-body-edit-button-' + postId), 'hide');
    setButtonVisibility($('#post-raw-edit-button-' + postId), 'hide');
    setButtonVisibility($('#post-body-save-button-' + postId), 'show');
    setButtonVisibility($('#post-body-cancel-button-' + postId), 'show');

    var postBodyContainer = $('#post-body-container-' + postId);
    var textArea = $('textarea', postBodyContainer);

    // Save the post body for shift-enter
    textArea.bind('keypress', function(e) {
        if (e.which == 13 && e.shiftKey) {
            e.preventDefault();
            savePost(postId);
        }
    });
}

function editPostFinished(postId) {
    // Should be called when editing the post body has been finished.
    //
    // - postId (PostId)

    setButtonVisibility($('#post-body-edit-button-' + postId), 'show');
    setButtonVisibility($('#post-raw-edit-button-' + postId), 'show');
    setButtonVisibility($('#post-body-save-button-' + postId), 'hide');
    setButtonVisibility($('#post-body-cancel-button-' + postId), 'hide');

    delete editState[postId]
}

function editPost(postId, mode) {
    // Lets the user edit the body of a post.
    //
    // The post-body-content box is replaced with a textarea that contains
    // the post body.
    //
    // Argument:
    //
    // - postId (PostId)
    // - mode(str) -- Either 'body' or 'raw'.

    getRawPostRequest(postId, mode, function(postText) {
        var postBodyContainer = $('#post-body-container-' + postId);
        var postBodyContentNode = $('.post-body-content', postBodyContainer);

        editState[postId] = mode

        // Replacing the post-body-content box with a textarea
        postBodyContentNode.after(
            '<textarea id="post-body-textarea-' + postId + '"' +
            ' rows="10" cols="80">' +
            '</textarea>').remove();

        // Adding the text to the textarea
        var textArea = $('textarea', postBodyContainer);
        textArea.attr('class', 'post-body-content');
        textArea.val(postText);
        textArea.focus();

        editPostStarted(postId);
     });
}

function savePost(postId) {
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
    var newPostText = textArea.val();
    var mode = editState[postId]

    setPostContentRequest(postId, newPostText, mode, function(result) {

        if (result.error) {
            window.alert('Error occured:\n' + result.error);
            return;
        }

        if (mode == 'body') {
            // Replacing the textArea with the received post-body-container
            // box
            textArea.replaceWith(result.new_body_html);
        } else if (mode == 'raw') {
            var postSummary = $('#post-summary-' + postId);
            postSummary.replaceWith(result.new_post_summary);
            addEventHandlersToPostSummary(postId);
            if (result.major_change) {
                window.alert(
                    'A major change was made on the post that may have ' +
                    'affected the thread structure. To see the most current ' +
                    'thread structure, please reload the page.');
            }
        }

        editPostFinished(postId);
     });
}

function cancelEditPost(postId) {
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

    getPostBodyRequest(postId, function(result) {

        if (result.error) {
            window.alert('Error occured:\n' + result.error);
            return;
        }

        // Replacing the textArea with the received post-body-container
        // box
        textArea.replaceWith(result.body_html);

        editPostFinished(postId);
     });
}

function confirmExit() {
    // Asks confirmation before leaving the page if there are any post being
    // edited.

    var needToConfirm = false;
    var postIdsStr = '';
    var separator = '';

    $.each(editState, function(postId, state) {

        postIdsStr = postIdsStr + separator + postIdToPostIdStr(postId);

        // This is the first postId
        if (!needToConfirm) {
            separator = ', ';
            needToConfirm = true;
        }
    });

    if (needToConfirm) {
        return 'You have attempted to leave this page, but there are posts ' +
               'being edited: ' + postIdsStr;
    }
}

///// Adding new buttons /////

function addGlobalButton(buttonText, buttonId, eventHandler) {
    // Adds the specified kind of button to global buttons.
    //
    // Arguments:
    //
    // - buttonText (str) -- The text of the button.
    // - buttonId (str) -- The button's HTML id.
    // - eventHandler(function(postId)) -- Functions that will be called when
    //   the button is clicked on.

    var globalButtons = $('.global-buttons');
    globalButtons.append(
        '<span class="button global-button" id="' + buttonId + '">' +
        buttonText +
        '</span>');
    $('#' + buttonId).bind('click', function() {
        eventHandler();
    });
}

function addBodyButtons(buttonText, buttonName, eventHandler) {
    // Adds the specified kind of button to each post body container.
    //
    // Arguments:
    //
    // - buttonText (str) -- The text of the button.
    // - buttonName (str) -- The button's HTML id will be
    //   buttonName + '-' + postId
    // - eventHandler(function(postId)) -- Functions that will be called when
    //   the button is clicked on.

    getPostIds().each(function(index) {
        var postId = this;
        var postBodyContainer = $('#post-body-container-' + postId);
        var postBodyButtons = $('.post-body-buttons', postBodyContainer);
        var buttonId = buttonName + '-' + postId;
        postBodyButtons.append(
            '<span class="button post-body-button" ' +
            'id="' + buttonId + '">' +
            buttonText +
            '</span>');
        $('#' + buttonId).bind('click', function() {
            eventHandler(postId);
        });
    });
}

///// Adding event handlers /////

function addEventHandlersToPostSummary(postId) {
    // Adds the necessary event handlers to the nodes inside a post summary.
    //
    // Argument:
    //
    // - postId(PostId)

    $('#post-body-hide-button-' + postId).bind('click', function() {
        hidePostBody(postId);
    });

    $('#post-body-show-button-' + postId).bind('click', function() {
        showPostBody(postId);
    });

    $('#post-body-edit-button-' + postId).bind('click', function() {
        editPost(postId, 'body');
    });

    $('#post-raw-edit-button-' + postId).bind('click', function() {
        editPost(postId, 'raw');
    });

    $('#post-body-save-button-' + postId).bind('click', function() {
        savePost(postId);
    });

    $('#post-body-cancel-button-' + postId).bind('click', function() {
        cancelEditPost(postId);
    });
}

$(document).ready(function() {

    $('#hide-all-post-bodies').bind('click', function() {
        hideAllPostBodies();
    });

    $('#show-all-post-bodies').bind('click', function() {
        showAllPostBodies();
    });

    // Adding the event handlers to the nodes inside post summaries
    getPostIds().each(function(index) {
        var postId = this;
        addEventHandlersToPostSummary(postId);
    });

    window.onbeforeunload = confirmExit;
});
