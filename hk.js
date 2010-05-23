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


///// Scrolling functions /////

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


///// Post body visibility functions /////

// Low level functions

function getPostBodyFromContainer(postBodyContainer) {
    // Returns the post body of the given post body container.
    //
    // Argument:
    //
    // - postBodyContainer (node)

//    return postBodyContainer.childNodes[1];

    for (var i = 0; i < postBodyContainer.childNodes.length; i++) {
        var childNode = postBodyContainer.childNodes[i];
        if (childNode.tagName == 'DIV' &&
            childNode.getAttribute('class') == 'body') {
            return childNode;
        }
    }
}

function getPostBodyStubFromContainer(postBodyContainer) {
    // Returns the post body of the given post body container.
    //
    // Argument:
    //
    // - postBodyContainer (node)

    for (var i = 0; i < postBodyContainer.childNodes.length; i++) {
        var childNode = postBodyContainer.childNodes[i];
        if (childNode.tagName == 'DIV' &&
            childNode.getAttribute('class') == 'postbody-stub') {
            return childNode;
        }
    }
}

function getPostBodyContainers() {
    // Returns an array that contains all post body containers, i.e. "span"
    // tags with an id that starts with "post-body-container".
    //
    // Returns: Array(node)

    var containers = new Array();
    var spans = document.getElementsByTagName('span');

    for (var i=0; i<spans.length; i++) {
        if (/^post-body-container/.test(spans[i].getAttribute('id'))) {
            containers.push(spans[i]);
        }
    }
    return containers;
}

function isPostBodyVisible(postBodyContainer) {
    // Returns whether the post body is visible.
    //
    // Argument:
    //
    // - postBodyContainer (node)

    var postBody = getPostBodyFromContainer(postBodyContainer);

    return (postBody.style.display != 'none');
}

function hidePostBody(postBodyContainer) {
    // Turns off the visibility of the given post body. Should be called only
    // when the visibility is turned on.
    //
    // Argument:
    //
    // - postBodyContainer (node)

    var postBody = getPostBodyFromContainer(postBodyContainer);
    var postBodyStub = document.createElement('div');

    postBodyStub.appendChild(document.createTextNode('Open'));
    postBodyStub.setAttribute('class', 'postbody-stub');
    postBody.style.display = 'none';
    postBodyContainer.appendChild(postBodyStub);
}

function showPostBody(postBodyContainer) {
    // Turns on the visibility of the given post body. Should be called only
    // when the visibility is turned off.
    //
    // Argument:
    //
    // - postBodyContainer (node)

    var postBodyStub = getPostBodyStubFromContainer(postBodyContainer);
    var postBody = getPostBodyFromContainer(postBodyContainer);

    postBody.style.display = 'block';
    postBodyContainer.removeChild(postBodyStub);
}

// High level funtions

function togglePostBodyVisibility(id) {
    // Toggles the visibility of the given post body.
    //
    // Argument:
    //
    // - id (str): the id of the post body container

    var postBodyContainer = document.getElementById(id);

    if (isPostBodyVisible(postBodyContainer)) {
        hidePostBody(postBodyContainer);
    } else {
        showPostBody(postBodyContainer);
    }
}

function hideAllPostBodies() {
    // Turns off the visibility for all visible post bodies.

    var postBodyContainers = getPostBodyContainers();

    for (var i = 0; i < postBodyContainers.length; i++) {
        var postBodyContainer = postBodyContainers[i];
        if (isPostBodyVisible(postBodyContainer)) {
            hidePostBody(postBodyContainer);
        }
    }
}

function showAllPostBodies() {
    // Turns on the visibility for all hidden post bodies.

    var postBodyContainers = getPostBodyContainers();

    for (var i = 0; i < postBodyContainers.length; i++) {
        var postBodyContainer = postBodyContainers[i];
        if (!isPostBodyVisible(postBodyContainer)) {
            showPostBody(postBodyContainer);
        }
    }
}
