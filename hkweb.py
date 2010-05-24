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


import sys
import threading
import web as webpy

import hkutils
import hklib
import hkgen
import hkshell


##### Global variables #####

urls = (
    '/', 'Index',
    '/(heapindex\\.css)', 'Fetch',
    '/(thread\\.png)', 'Fetch',
    '/(.*\\.js)', 'Fetch',
    '/posts/(.*)', 'Post',
    )

log = []


##### Generator classes #####

class WebGenerator(hkgen.Generator):
    """A Generator that is modified according to the needs of dynamic web page
    generation."""

    def __init__(self, postdb):
        hkgen.Generator.__init__(self, postdb)

    def print_html_head_content(self):
        """Prints the content in the HTML header.

        **Returns:** |HtmlText|
        """

        return \
            ['    <link rel=stylesheet href="/%s" type="text/css">\n' % (css,)
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

    def print_post_page(self, post_id):
        post = self._postdb.post(post_id)
        if post is None:
            return 'No such post: "%s"' % (post_id,)
        root = self._postdb.root(post)
        if root is None:
            return 'The post is in a cycle: "%s"' % (post_id,)
        self._requested_post = post
        post_id_str = post.post_id_str()
        self.options.html_body_attributes += \
            ' onload="ScrollToId(\'post_' + post_id_str + '\')";'
        self.options.html_title = post.subject()

        buttons = \
            self.enclose(
                (self.enclose(
                     self.print_link('javascript:hideAllPostBodies();',
                                     'Hide all post bodies'),
                     class_='global-button'),
                 self.enclose(
                     self.print_link('javascript:showAllPostBodies();',
                                     'Show all post bodies'),
                     class_='global-button')),
                class_='global-buttons',
                tag='div')

        content = (buttons,
                   self.print_thread_page(root),
                   '<script type="text/javascript" src="/jquery.js">'
                   '</script>\n'
                   '<script type="text/javascript" src="/hk.js"></script>')
        return content

    def get_postsummary_fields_main(self, postitem):

        old_fields = \
            hkgen.Generator.get_postsummary_fields_main(self, postitem)
        new_fields = [self.print_postitem_back]
        return tuple(list(old_fields) + new_fields)

    def print_postitem_back_core(self, postitem):
        """Prints the core of the post id of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        # post link example: /#post_hh/12
        post_link = ('/#post_' + postitem.post.post_id_str())
        return self.print_link(post_link, 'Back to the index')

    def print_postitem_back(self, postitem):
        """Prints the post id of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        return self.enclose(
                   self.print_postitem_back_core(postitem),
                   class_='back-to-index')

    def print_postitem_body(self, postitem):
        """Prints the body the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        body = hkgen.Generator.print_postitem_body(self, postitem)

        id = 'post-body-container-' + postitem.post.post_id_str()
        action = '"javascript:togglePostBodyVisibility(\'' + id + '\')"'

        return self.enclose(
                   body,
                   class_='body-container',
                   skip_empty=True,
                   newlines=True,
                   id=id,
                   attributes=' onclick=' + action)


##### Server classes #####

class WebpyServer(object):

    def __init__(self):
        self._postdb = hkshell.postdb()

    def serve_html(self, content):
        webpy.header('Content-type','text/html')
        webpy.header('Transfer-Encoding','chunked')
        page = self.generator.print_html_page(content)
        return hkutils.textstruct_to_str(page)

class Index(WebpyServer):
    """Serves the index page."""

    def __init__(self):
        WebpyServer.__init__(self)

    def GET(self):
        generator = IndexGenerator(self._postdb)
        self.generator = generator
        content = generator.print_main_index_page()
        return self.serve_html(content)

class Post(WebpyServer):
    """Serves the post pages (``/post/<heap>/<post index>``)."""

    def __init__(self):
        WebpyServer.__init__(self)

    def GET(self, name):
        generator = PostPageGenerator(self._postdb)
        self.generator = generator
        content = generator.print_post_page(post_id=str(name))
        return self.serve_html(content)

class Fetch(object):
    """Serves the files that should be served unchanged."""

    def GET(self, name):
        filename = str(name)
        return hkutils.file_to_string(filename)

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

@hkshell.hkshell_cmd()
def start(port=8080):
    options = hkshell.options
    options.web_server = Server(port)
    options.web_server.start()
    hklib.log('Web service started.')
