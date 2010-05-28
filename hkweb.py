# -*- coding: utf-8 -*-

# This file is part of Heapkeeper.
#
# Heapkeeper is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Heapkeeper is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Heapkeeper.  If not, see <http://www.gnu.org/licenses/>.

# Copyright (C) 2009-2010 Csaba Hoch
# Copyright (C) 2009 Attila Nagy

"""Module for dynamic web output in Heapkeeper.

This module adds a facility to start a web application (complete with its own
web server) from |hkshell| via a simple command.

The output is fully customizable the same way as the static output.

hkweb can be started from the |hkshell| in the following way:

    >>> import hkweb
    >>> hkweb.start()

|hkweb| is executed in a separate daemon thread. When |hkshell| is closed, the
|hkweb| thread is automatically stopped.
"""


import json
import sys
import threading
import web as webpy

import hkutils
import hklib
import hkgen
import hkshell


##### Global variables #####

urls = (
    r'/', 'Index',
    r'/([A-Za-z0-9_-]+\.css)', 'Fetch',
    r'/(thread\\.png)', 'Fetch',
    r'/(external/[A-Za-z0-9_-]+\.js)', 'Fetch',
    r'/(static/[A-Za-z0-9_.-]+)', 'Fetch',
    r'/posts/(.*)', 'Post',
    r'/raw-post-bodies/(.*)', 'RawPostBody',
    r'/set-post-body/(.*)', 'SetPostBody',
    r'/get-post-body/(.*)', 'GetPostBody',
    )

log = []


##### Generator classes #####

class WebGenerator(hkgen.Generator):
    """A Generator that is modified according to the needs of dynamic web page
    generation."""

    def __init__(self, postdb):
        hkgen.Generator.__init__(self, postdb)
        self.options.cssfiles.append("static/hkweb.css")

    def print_html_head_content(self):
        """Prints the content in the HTML header.

        **Returns:** |HtmlText|
        """

        return \
            ['    <link rel="stylesheet" href="/%s" type="text/css" />\n' %
             (css,)
             for css in self.options.cssfiles]

    def print_postitem_link(self, postitem):
        """Prints the thread link of the post item in hkweb-compatible form."""

        return ('/posts/', postitem.post.post_id_str())


class IndexGenerator(WebGenerator):
    """Generator that generates the index page."""

    def __init__(self, postdb):
        WebGenerator.__init__(self, postdb)


class PostPageGenerator(WebGenerator):
    """Generator that generates post pages.

    The generated post pages show the thread of the post. With the help of
    Javascript, the web browser is asked to jump to the relevant post.
    """

    def __init__(self, postdb):
        WebGenerator.__init__(self, postdb)

    def set_post_id(self, post_id):
        post = self._postdb.post(post_id)
        if post is None:
            return 'No such post: "%s"' % (post_id,)
        root = self._postdb.root(post)
        if root is None:
            return 'The post is in a cycle: "%s"' % (post_id,)
        self._requested_post = post
        heap_id, post_index = post.post_id()
        id = 'post-summary-' + heap_id + '-' + post_index
        self.options.html_body_attributes += \
            'onload="ScrollToId(\'' + id + '\');"'
        self.options.html_title = post.subject()

        self._root = root
        self._post = post

    def print_post_page(self, post_id):
        self.set_post_id(post_id)

        buttons = \
            self.enclose(
                (self.enclose(
                     'Hide all post bodies',
                     class_='button global-button',
                     id='hide-all-post-bodies'),
                 self.enclose(
                     'Show all post bodies',
                     class_='button global-button',
                     id='show-all-post-bodies')),
                class_='global-buttons',
                tag='div')

        js_files = ('/external/jquery.js',
                    '/external/json2.js',
                    '/static/hkweb.js')
        js_links = \
            [('<script type="text/javascript" src="%s"></script>\n' %
              (js_file,)) for js_file in js_files]

        return (buttons,
                self.print_thread_page(self._root),
                js_links)

    def get_postsummary_fields_main(self, postitem):
        """Returns the fields of the post summary when the pos position is
        ``"main"``.

        The function gets the usual buttons from |Generator| and adds its own
        buttons.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** iterable(|PostItemPrinterFun|)
        """

        old_fields = \
            hkgen.Generator.get_postsummary_fields_main(self, postitem)
        new_fields = [self.print_hkweb_summary_buttons]
        return tuple(list(old_fields) + new_fields)

    def print_hkweb_summary_buttons(self, postitem):
        """Prints the post id of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        # Post link example: /#post_hh/12
        heap_id, post_index = postitem.post.post_id()
        post_link = ('/#post-summary-' + heap_id + '-' + post_index)

        heap_id, post_index = postitem.post.post_id()
        post_id = heap_id + '-' + post_index
        id = 'post-body-show-button-' + post_id

        return \
            (self.enclose(
                 self.print_link(post_link, 'Back to the index'),
                 class_='button post-summary-button'),
             self.enclose(
                 'Show body',
                 class_='button post-summary-button',
                 id=id,
                 attributes=' style="display: none;"'))

    def print_postitem_body(self, postitem):
        """Prints the body the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        body = hkgen.Generator.print_postitem_body(self, postitem)

        heap_id, post_index = postitem.post.post_id()
        post_id = heap_id + '-' + post_index

        buttons = \
            self.enclose(
                (self.enclose(
                     'Hide',
                     class_='button post-body-button',
                     id='post-body-hide-button-' + post_id),
                 self.enclose(
                     'Edit',
                     class_='button post-body-button',
                     id='post-body-edit-button-' + post_id),
                 self.enclose(
                     'Save',
                     class_='button post-body-button',
                     id='post-body-save-button-' + post_id,
                     attributes='style="display: none;"'),
                 self.enclose(
                     'Cancel',
                     class_='button post-body-button',
                     id='post-body-cancel-button-' + post_id,
                     attributes='style="display: none;"')),
                class_='post-body-buttons',
                tag='div')

        return self.enclose(
                   (buttons, body),
                   tag='div',
                   class_='post-body-container',
                   newlines=True,
                   id='post-body-container-' + post_id)

class PostBodyGenerator(hkgen.Generator):

    def __init__(self, postdb):
        hkgen.Generator.__init__(self, postdb)

    def print_post_body(self, post_id):

        post = self._postdb.post(post_id)
        if post is None:
            return 'No such post: "%s"' % (post_id,)

        postitem = hklib.PostItem('main', post)
        postitem.print_post_body = True
        body_str = self.print_postitem_body(postitem)
        return body_str


##### Server classes #####


class WebpyServer(object):
    """Base class for webservers."""

    def __init__(self):
        self._postdb = hkshell.postdb()


class HkPageServer(object):
    """Base class for webservers that serve a "usual" HTML page that is
    generated by a Heapkeeper generator."""

    def __init__(self):
        self._postdb = hkshell.postdb()

    def serve_html(self, content, generator):
        """Creates a HTML page that contains the given content.

        **Argument:**

        - `content` (|HtmlText|)

        **Returns:** str
        """

        webpy.header('Content-type', 'text/html')
        webpy.header('Transfer-Encoding', 'chunked')
        page = generator.print_html_page(content)
        return hkutils.textstruct_to_str(page)


class Index(HkPageServer):
    """Serves the index page that shows all posts."""

    def __init__(self):
        HkPageServer.__init__(self)

    def GET(self):
        generator = IndexGenerator(self._postdb)
        content = generator.print_main_index_page()
        return self.serve_html(content, generator)


class Post(HkPageServer):
    """Serves the post pages.

    Served URL: ``/post/<heap>/<post index>``"""

    def __init__(self):
        HkPageServer.__init__(self)

    def GET(self, name):
        post_id = hkutils.uutf8(name)
        generator = PostPageGenerator(self._postdb)
        content = generator.print_post_page(post_id)
        return self.serve_html(content, generator)


class RawPostBody(WebpyServer):
    """Serves raw post bodies.

    Served URL: ``/raw-post-bodies/<heap>/<post index>``"""

    def __init__(self):
        WebpyServer.__init__(self)

    def GET(self, name):
        webpy.header('Content-type', 'text/plain')
        webpy.header('Transfer-Encoding', 'chunked')
        post_id = hkutils.uutf8(name)
        post = self._postdb.post(post_id)
        if post is None:
            return 'No such post: "%s"' % (post_id,)
        content = post.body()
        return content


class AjaxServer(WebpyServer):
    """Base class for classes that serve AJAX requests.

    The concrete classes should implement the `execute` method."""

    def __init__(self):
        WebpyServer.__init__(self)

    def POST(self, name_uni):
        # RFC4627: "The MIME media type for JSON text is application/json."
        webpy.header('Content-type','application/json')
        webpy.header('Transfer-Encoding','chunked')
        name = hkutils.uutf8(name_uni)
        input = webpy.input()
        args = json.loads(input.get('args'))
        result = self.execute(name, args)
        return json.dumps(result)


class SetPostBody(AjaxServer):
    """Sets the body of the given post.

    Served URL: ``/set-post-body/<heap>/<post index>``"""

    def __init__(self):
        AjaxServer.__init__(self)

    def execute(self, post_id, args):
        """Sets the post body.

        **Argument:**

        - `args` ({'new_body_text': str})

        **Returns:** {'error': str} | {'new_body_html': str}
        """

        post = self._postdb.post(post_id)
        if post is None:
            return {'error': 'No such post: "%s"' % (post_id,)}

        newPostBodyText = args.get('new_body_text')
        if newPostBodyText is None:
            return {'error': 'No post body specified'}
        else:
            newPostBodyText = hkutils.uutf8(newPostBodyText)

        post.set_body(newPostBodyText)

        # Generating the HTML for the new body
        generator = PostBodyGenerator(self._postdb)
        new_body_html = generator.print_post_body(post_id)
        new_body_html = hkutils.textstruct_to_str(new_body_html)

        return {'new_body_html': new_body_html}


class GetPostBody(AjaxServer):
    """Gets the body of the given post.

    Served URL: ``/get-post-body/<heap>/<post index>``"""

    def __init__(self):
        AjaxServer.__init__(self)

    def execute(self, post_id, args):
        # Unused argument 'postitem' # pylint: disable-msg=W0613
        """Gets the post body.

        **Argument:**

        - `args` ({})

        **Returns:** {'error': str} | {'body_html': str}
        """

        post = self._postdb.post(post_id)
        if post is None:
            return {'error': 'No such post: "%s"' % (post_id,)}

        # Generating the HTML for the new body
        generator = PostBodyGenerator(self._postdb)
        new_body_html = generator.print_post_body(post_id)
        new_body_html = hkutils.textstruct_to_str(new_body_html)

        return {'body_html': new_body_html}


class Fetch(object):
    """Serves the files that should be served unchanged."""

    def GET(self, name):
        filename = hkutils.uutf8(name)
        return hkutils.file_to_string(filename)


##### Main server class #####

class Server(threading.Thread):
    """Implements the hkweb server thread."""

    def __init__(self, port):
        super(Server, self).__init__()
        self.daemon = True
        self._port = port

    def run(self):

        # Passing the port parameter to web.py is ugly, but the mailing list
        # entries I have found so far suggest this, and it does the job. A
        # wrapper around sys would be the answer, which should be done anyway
        # to control logging (there sys.stderr should be diverted).
        sys.argv = (None, str(self._port),)
        WebApp = webpy.application(urls, globals())
        WebApp.run()


##### hkshell commands #####

def start(port=8080):
    options = hkshell.options
    options.web_server = Server(port)
    options.web_server.start()
    hklib.log('Web service started.')
