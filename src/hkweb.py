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

# Copyright (C) 2009-2011 Csaba Hoch
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

Currently only one hkweb instance can execute well at a time, because we have
some global variables.

The :doc:`clientservercommunication` page describes how the server side
(implemented in this module) and client side (mostly implemented in
``hkweb.js``) of hkweb communicate.
"""


import base64
import datetime
import exceptions
import itertools
import json
import re
import socket
import sys
import threading
import web as webpy
import web.wsgiserver

import hkutils
import hklib
import hkgen
import hksearch
import hkshell


##### Global variables #####

# Stores which URL is served by which server
urls = [
    r'/', 'Index',
    r'/(external/[A-Za-z0-9_./-]+)', 'Fetch',
    r'/(static/[A-Za-z0-9_./-]+)', 'Fetch',
    r'/(plugins/[A-Za-z0-9_.-]+/static/[A-Za-z0-9_./-]+)', 'Fetch',
    r'/posts/(.*)', 'Post',
    r'/raw-post-bodies/(.*)', 'RawPostBody',
    r'/raw-post-text/(.*)', 'RawPostText',
    r'/set-post-body', 'SetPostBody',
    r'/get-post-body', 'GetPostBody',
    r'/set-raw-post', 'SetRawPost',
    r'/show-json', 'ShowJSon',
    r'/search.*', 'Search',
    ]


##### HTTP basic authentication #####

def default_deny(realm, username, password, redirect_url):
    # Unused arguments 'password', 'realm', 'redirect_url'
    # pylint: disable=W0613
    hkutils.log('Access denied for user %s.' % username)
    return 'Authentication needed!'

def make_auth(verifier, realm="Heapkeeper", deny=default_deny,
              redirect_url="/"):
    """Creates a decorator that allows the decorated function to run only after
    a successful HTTP basic authentication.

    The authentication is performed by a supplied verifier function.

    **Arguments:**

    - `verifier` (fun(str, str, str)) -- Verifies if the authentication is
      valid and returns the result as bool.
    - `realm` (str) -- The user will see this in the login box.
    - `deny` (fun(str, str, str, str)) -- Function called on failure.
    - `redirect_url` (str) -- Unsuccessful auth throws the user here.
    """

    def decorator(func, *args, **keywords):
        # Unused arguments 'args', 'keywords'
        # pylint: disable=W0613
        def f(*args, **keywords):
            username = None
            password = None
            try:
                b64text = webpy.ctx.env['HTTP_AUTHORIZATION'][6:]
                plaintext = base64.b64decode(b64text)
                colonpos = plaintext.index(':')
                username = plaintext[:colonpos]
                password = plaintext[colonpos + 1:]
            except:
                # TODO: handle absent HTTP_AUTHORIZATION field
                # separately from failed base64 decoding or missing
                # colon in plaintext.
                pass
            if verifier(username, password, realm):
                last_access[username] = datetime.datetime.now()
                # Attach the user's name to the server. The way to
                # find the server depends on whether the function is a
                # bound method.
                if hasattr(func, 'im_self'):
                    func.im_self.user = username
                else:
                    args[0].user = username
                return func(*args, **keywords)
            else:
                webpy.ctx.status = '401 UNAUTHORIZED'
                webpy.header('WWW-Authenticate',
                             'Basic realm="%s"'  % webpy.websafe(realm))
                return deny(realm, username, password, redirect_url)
        return f
    return decorator

def make_minimal_verifier(correct_username, correct_password):
    """Returns a minimalistic username/password verifier.

    **Arguments:**

    - `correct_username` (str)
    - `correct_password` (str)

    **Returns:** fun(str, str, str) -> bool
    """

    # Unused argument 'realm' # pylint: disable=W0613
    def minimal_verifier(username, password, realm):
        """A minimalistic verifier with a hardcoded user/password pair.

        **Arguments:**

        - `username` (str)
        - `password` (str)
        - `realm` (str)

        **Returns:** bool
        """

        return (username == correct_username and
                password == correct_password)
    return minimal_verifier

def account_verifier(username, password, realm):
    # Unused argument 'realm' # pylint: disable=W0613
    """A verifier that uses the account list in the config file.

    **Arguments:**

    - `username` (str)
    - `password` (str)
    - `realm` (str)

    **Returns:** bool
    """


    accounts = hkshell.options.config['accounts']
    if username in accounts:
        correct_password = accounts[username]
        return correct_password == password
    return False

def enable_authentication(username=None, password=None):
    """Enables authentication with single username/password pair or
    account-based pairs.

    If username is omitted, authentication will be based on account data
    specified in the config file. If both username and password are specified,
    these will be the only acceptable username/password pair. If password is
    omitted, it will be the same as the username (not recommended).

    **Argument:**

    - `username` (str | ``None``)
    - `password` (str | ``None``)
    """

    global auth
    if username is None:
        auth = make_auth(verifier=account_verifier)
    else:
        if password is None:
            password = username
        auth = make_auth(verifier=make_minimal_verifier(username, password))

# By default, auth is an identity decorator, that is, authentication
# is disabled. Enable it using `hkweb.enable_authentication()`.
auth = lambda f: f

# This dict keeps track of the time of the last access by users.
last_access = {}

def add_auth(server, auth_decorator):
    """Add authentication to a web.py server class.

    **Arguments:**

    - `server` (:class:`WebpyServer`)
    - `auth_decorator` ()
    """

    server.original_GET = getattr(server, 'GET', None)
    server.original_POST = getattr(server, 'POST', None)
    if server.original_GET:
        server.GET = auth_decorator(server.original_GET)
    if server.original_POST:
        server.POST = auth_decorator(server.original_POST)


##### Utility functions #####

JSON_ESCAPE_CHAR = '\x00'

def get_web_args():
    """Gets the arguments transferred as a JSON object from the web.py module.

    **Returns:** json_object -- It will contain UTF-8 encoded strings instead
    of unicode objects.
    """

    result = {}
    for key, value in webpy.input().items():
        try:

            # If `value` starts with the JSON escape character, a JSON object
            # should be described after the escape character. (E.g. the value
            # '\x00[1,2]' (given as '%00[1,2]' in the query parameter) will
            # become [1, 2]). Otherwise `value` is a string.
            if len(value) > 1 and value[0] == JSON_ESCAPE_CHAR:
                json_value_unicode = json.loads(value[1:])
            else:
                json_value_unicode = value

            json_value = hkutils.json_uutf8(json_value_unicode)
            result[key] = json_value
        except exceptions.ValueError, e:
            raise hkutils.HkException(
                      'Error: the "%s" parameter is not a valid JSON object: '
                      '%s' % (key, value))
    return result

def last():
    """Display the time of the last access in a conveniently interpretable
    ("human-readable") format."""

    access_datetimes = last_access.values()
    if len(access_datetimes) == 0:
        hkutils.log("Access list is empty.")
        return
    access_datetimes.sort()
    last_datetime = access_datetimes[-1]
    now_datetime = datetime.datetime.now()
    last_str = hkutils.humanize_timedelta(now_datetime - last_datetime)
    hkutils.log("Last access was %s ago." % (last_str,))


##### Generator classes #####

class WebGenerator(hkgen.BaseGenerator):

    """A WebGenerator is a |BaseGenerator| that is modified according to the
    needs of dynamic web page generation."""

    def __init__(self, postdb):
        """Constructor.

        **Argument:**

        - `postdb` (|PostDB|)
        """

        hkgen.BaseGenerator.__init__(self, postdb)
        WebGenerator.init(self)

    def init(self):
        # Argument count differs from overridden method # pylint: disable=W0221
        """Initializator."""

        self.options.cssfiles.append('static/css/hkweb.css')
        self.options.js_files = ['external/jquery.js',
                                 'external/json2.js',
                                 'static/js/hkweb.js']

    def get_static_path(self, filename):
        """Returns the path that can be included in the generated HTML pages.

        In case of WebGenerator, the string ``/`` will be prepended to the
        given filename.

        **Argument:**

        - `filename` (str) -- A filename relative to the root directory of
        Heapkeeper.

        **Returns:** str
        """

        return '/' + filename

    def print_postitem_link(self, postitem):
        """Prints the thread link of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        return ('/posts/', postitem.post.post_id_str())

    def print_searchbar(self):
        """Prints a search bar.

        **Returns:** |HtmlText|
        """

        return ('<center>\n'
                '<div class="searchbar-container">\n'
                '  <form id="searchbar-container-form" action="/search"'
                ' method="get">\n'
                '    <input id="searchbar-term" name="term" type="text"'
                ' size="40"/>\n'
                '    <input type="submit" value="Search the heaps" />\n'
                '  </form>\n'
                '</div>\n'
                '</center>\n')

    def print_additional_header(self, info):
        # Unused arguments # pylint: disable=W0613
        """Provided as a hook to be used by plugins.

        This is the method to overwrite when altering the generator to
        add something before the main content of the page. Always call
        the original function when overwriting this function to
        preserve the functionality of any previously started plugins.

        **Argument:**

        - `info` (dict) -- Extra information about the page being printed.

        **Returns:** |HtmlText|
        """

        return ''

    def print_additional_footer(self, info):
        # Unused arguments # pylint: disable=W0613
        """Provided as a hook to be used by plugins.

        See docstring of `print_additional_header` for notes on how to
        use this.

        **Argument:**

        - `info` (dict) -- Extra information about the page being printed.

        **Returns:** |HtmlText|
        """

        return ''


class IndexGenerator(WebGenerator):

    """Generator that generates the index page, which contains all posts of
    all heaps in one section."""

    def __init__(self, postdb):
        """Constructor.

        **Argument:**

        - `postdb` (|PostDB|)
        """

        WebGenerator.__init__(self, postdb)
        IndexGenerator.init(self)

    def init(self):
        # Argument count differs from overridden method # pylint: disable=W0221
        """Initializator."""
        pass

    def print_main(self):
        """Prints the main part of the page.

        **Returns:** |HtmlText|
        """

        return (self.print_searchbar(),
                self.print_additional_header({}),
                self.print_main_index_page(),
                self.print_additional_footer({}),
                self.print_js_links())


class PostPageGenerator(WebGenerator):

    """Generator that generates post pages.

    The generated post pages show the thread of the post. With the help of
    Javascript, the web browser is asked to jump to the relevant post.
    """

    def __init__(self, postdb):
        """Constructor.

        **Argument:**

        - `postdb` (|PostDB|)
        """

        WebGenerator.__init__(self, postdb)
        PostPageGenerator.init(self)

    def init(self):
        # Argument count differs from overridden method # pylint: disable=W0221
        """Initializator."""
        pass

    def set_post_id(self, post_id):
        """Sets the post id of the post that is being printed.

        The function will refuse the set the post id if the post does not
        exists, is deleted or is in a cycle.

        The function adds JavaScript code to
        ``self.options.html_body_attributes`` so that the browser will scroll
        to the post with the given id.

        **Argument:**

        - `post_id` (|PrePostId|) -- The id

        **Returns:** ``None`` | str -- If ``None``, the operation was
        successful; otherwise the return value is a string that contains the
        error message.
        """

        post = self._postdb.post(post_id)
        if post is None:
            return 'No such post: "%s"' % (post_id,)
        if post.is_deleted():
            return 'The post was deleted: "%s"' % (post_id,)
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
        """Prints the post page of the given post.

        **Argument:**

        - `post_id` (|PrePostId|)

        **Returns:** |HtmlText|
        """

        result = self.set_post_id(post_id)
        if result is not None:
            return result

        # Post link example: /#post-summary-my_heap-12
        heap_id, post_index = self._post.post_id()
        post_link = ('/#post-summary-' + heap_id + '-' + post_index)

        buttons = \
            self.enclose(
                (self.enclose(
                     self.print_link(post_link, 'Back to the index'),
                     class_='button global-button'), '\n',
                 self.enclose(
                     'Hide all post bodies',
                     class_='button global-button',
                     id='hide-all-post-bodies'), '\n',
                 self.enclose(
                     'Show all post bodies',
                     class_='button global-button',
                     id='show-all-post-bodies'), '\n'),
                class_='global-buttons',
                tag='div',
                newlines=True)

        return (buttons,
                self.print_thread_page(self._root))

    def get_postsummary_fields_inner(self, postitem):
        """Returns the fields of the post summary when the position is
        ``"inner"``.

        The function gets the usual buttons from |BaseGenerator| and adds its
        own buttons.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** iterable(|PostItemPrinterFun|)
        """

        old_fields = \
            hkgen.BaseGenerator.get_postsummary_fields_inner(self, postitem)
        new_fields = [self.print_hkweb_summary_buttons]
        return tuple(list(old_fields) + new_fields)

    def print_hkweb_summary_buttons(self, postitem):
        """Prints the buttons of a post summary.

        **Argument:**

        - `postitem` (|PostItem|) -- The post item to which the summary
          belongs.

        **Returns:** |HtmlText|
        """

        heap_id, post_index = postitem.post.post_id()
        post_id = heap_id + '-' + post_index
        id = 'post-body-show-button-' + post_id

        return \
            (self.enclose(
                 'Show body',
                 class_='button post-summary-button',
                 id=id,
                 attributes=' style="display: none;"'))

    def print_postitem_body(self, postitem):
        """Prints the body of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        body = hkgen.BaseGenerator.print_postitem_body(self, postitem)

        heap_id, post_index = postitem.post.post_id()
        post_id = heap_id + '-' + post_index

        buttons = \
            self.enclose(
                (self.enclose(
                     'Hide',
                     class_='button post-body-button',
                     id='post-body-hide-button-' + post_id), '\n',
                 self.enclose(
                     'Edit',
                     class_='button post-body-button',
                     id='post-body-edit-button-' + post_id), '\n',
                 self.enclose(
                     'Edit raw post',
                     class_='button post-body-button',
                     id='post-raw-edit-button-' + post_id), '\n',
                 self.enclose(
                     'Add child',
                     class_='button post-body-button',
                     id='post-body-addchild-button-' + post_id), '\n',
                 self.enclose(
                     'Save',
                     class_='button post-body-button',
                     id='post-body-save-button-' + post_id,
                     attributes='style="display: none;"'), '\n',
                 self.enclose(
                     'Cancel',
                     class_='button post-body-button',
                     id='post-body-cancel-button-' + post_id,
                     attributes='style="display: none;"'), '\n'),
                class_='post-body-buttons',
                tag='div',
                newlines=True)

        return self.enclose(
                   (buttons, body),
                   tag='div',
                   class_='post-body-container',
                   newlines=True,
                   id='post-body-container-' + post_id)

    def print_main(self, postid):
        """Prints the main part of the page.

        **Argument:**

        - `postid` (|PrePostId|)

        **Returns:** |HtmlText|
        """

        return (self.print_searchbar(),
                self.print_additional_header({'postid': postid}),
                self.print_post_page(postid),
                self.print_additional_footer({'postid': postid}),
                self.print_js_links())


class SearchPageGenerator(PostPageGenerator):

    """Generator that implements a search page."""

    def __init__(self, postdb, preposts):
        """Constructor.

        **Arguments:**

        - `postdb` (|PostDB|)
        - `preposts` (|PrePostId|)
        """

        PostPageGenerator.__init__(self, postdb)
        SearchPageGenerator.init(self, preposts)

    def init(self, preposts):
        # Argument count differs from overridden method # pylint: disable=W0221
        """Initializator."""
        self.posts = self._postdb.postset(preposts)
        self.options.html_title = 'Search page'

    def print_search_page_core(self):
        """Prints the core of a search page.

        **Returns:** |HtmlText|
        """

        # Getting the posts in the interesting threads
        xpostitems = self.walk_exp_posts(self.posts)

        xpostitems = \
            itertools.imap(
                self.set_postitem_attr('print_post_body'),
                xpostitems)
        xpostitems = \
            itertools.imap(
                self.set_postitem_attr('print_parent_post_id'),
                xpostitems)
        xpostitems = \
            itertools.imap(
                self.set_postitem_attr('print_children_post_id'),
                xpostitems)

        # Printing the page
        return self.print_postitems(xpostitems)

    def print_search_page(self):
        """Prints the search page.

        **Returns:** |HtmlText|
        """

        buttons = \
            self.enclose(
                (self.enclose(
                     'Hide all post bodies',
                     class_='button global-button',
                     id='hide-all-post-bodies'), '\n',
                 self.enclose(
                     'Show all post bodies',
                     class_='button global-button',
                     id='show-all-post-bodies'), '\n'),
                class_='global-buttons',
                tag='div',
                newlines=True)

        return (buttons,
                self.print_search_page_core())


class PostBodyGenerator(WebGenerator):

    """Generates the body of a given post."""

    def __init__(self, postdb):
        """Constructor.

        **Argument:**

        - `postdb` (|PostDB|)
        """

        WebGenerator.__init__(self, postdb)
        PostBodyGenerator.init(self)

    def init(self):
        # Argument count differs from overridden method # pylint: disable=W0221
        """Initializator."""
        pass

    def print_post_body(self, post_id):
        """Prints the body of a given post.

        **Argument:**

        - `post_id` (|PrePostId|)

        **Returns:** |HtmlText|
        """

        post = self._postdb.post(post_id)
        if post is None:
            return 'No such post: "%s"' % (post_id,)

        postitem = hklib.PostItem('inner', post)
        postitem.print_post_body = True
        body_str = self.print_postitem_body(postitem)
        return body_str


##### Server classes #####

class WebpyServer(object):

    """Base class for webservers."""

    def __init__(self):
        """Constructor."""

        add_auth(self, auth)
        self._postdb = hkshell.postdb()

class HkPageServer(WebpyServer):

    """Base class for webservers that serve a "usual" HTML page that is
    generated by a Heapkeeper generator."""

    def __init__(self):
        """Constructor."""

        WebpyServer.__init__(self)

    def serve_html(self, content, generator):
        """Serves a HTML page that contains the given content.

        **Argument:**

        - `content` (|HtmlText|)
        - `generator` (|BaseGenerator|) -- Generator to be used for generating
           the HTML headers and footers.

        **Returns:** str
        """

        webpy.header('Content-type', 'text/html')
        webpy.header('Transfer-Encoding', 'chunked')
        page = generator.print_html_page(content)
        return hkutils.textstruct_to_str(page)


class Index(HkPageServer):

    """Serves the index page that shows all posts.

    Served URL: ``/``
    """

    def __init__(self):
        """Constructor."""
        HkPageServer.__init__(self)

    def GET(self):
        """Serves a HTTP GET request.

        **Returns:** str
        """

        generator = IndexGenerator(self._postdb)
        content = generator.print_main()
        return self.serve_html(content, generator)


class Post(HkPageServer):

    """Serves the post pages.

    Served URL: ``/posts/<heap>/<post index>``
    """

    def __init__(self):
        """Constructor."""
        HkPageServer.__init__(self)

    def GET(self, name):
        """Serves a HTTP GET request.

        **Returns:** str
        """

        post_id = hkutils.uutf8(name)
        generator = PostPageGenerator(self._postdb)
        content = generator.print_main(post_id)
        return self.serve_html(content, generator)


class Search(HkPageServer):

    """Serves the search pages.

    Served URL: ``/search``
    """

    def __init__(self):
        """Constructor."""
        HkPageServer.__init__(self)

    def main(self):
        """Serves a HTTP GET or POST request.

        **Returns:** str
        """

        try:
            args = get_web_args()
            preposts = self.get_posts(args)
        except hkutils.HkException, e:
            return str(e)

        if preposts is None:
            # `preposts` is None if there was no search performed. However, in
            # this function, we want to have `preposts` as a list of preposts,
            # and we use `show` to store the information that no search was
            # performed and thus no search result should be shown.
            preposts = []
            show = 'no_search'
        else:
            # 'normal' means here that a search was performed. Later we modify
            # thsi to 'no_post_found' if it turns out that the query does not
            # match any post.
            show = 'normal'

        generator = SearchPageGenerator(self._postdb, preposts)
        if (show == 'normal' and len(generator.posts) == 0):
            show = 'no_post_found'

        if show == 'no_search':
            main_content = ''
        elif show == 'no_post_found':
            main_content = 'No post found.'
        elif show == 'normal':
            active = len(generator.posts)
            all = len(generator.posts.exp())
            numbers = ('Posts found: %d<br/>'
                       'All posts shown: %d' % (active, all))
            numbers_box = generator.enclose(numbers, 'div', 'info-box')
            main_content = (numbers_box, generator.print_search_page())

        term = args.get('term')
        if term is not None:
            # We use json to make sure that `term` is represented in a format
            # readable by JavaScript
            fill_searchbar_js = \
                ('$("#searchbar-term").val(' +
                 json.dumps(term) +
                 ');\n')
        else:
            fill_searchbar_js = ''

        focus_searchbar_js = '$("#searchbar-term").focus();\n'

        js_code = \
            ('<script  type="text/javascript" language="JavaScript">\n',
            fill_searchbar_js,
            focus_searchbar_js,
             '</script>\n')

        content = (generator.print_searchbar(),
                   main_content,
                   generator.print_js_links(),
                   js_code)
        return self.serve_html(content, generator)

    def get_posts(self, args):
        """Gets the post to be displayed.

        If the ``posts`` query parameter is specified, the posts described in
        that will be returned. If the ``term`` query parameter is specified,
        the result of that query will be returned. Otherwise ``None`` will be
        returned.

        **Returns:** |PostSet| | ``None``
        """

        posts = args.get('posts')
        if posts is not None:
            return self._postdb.postset(posts)

        term = args.get('term')
        if term is not None:
            return hksearch.search(term, self._postdb.all())

        return None # only the search bar will be shown

    def GET(self):
        """Serves a HTTP GET request.

        **Returns:** str
        """

        return self.main()

    def POST(self):
        """Serves a HTTP POST request.

        **Returns:** str
        """

        return self.main()


##### Helper servers ######

class ShowJSon(HkPageServer):

    """Serves a page that displays the JSON parameters given to that page.

    Intended only for developers.

    Served URL: ``/showjson``
    """

    def __init__(self):
        """Constructor."""

        HkPageServer.__init__(self)

    def GET(self):
        """Serves a HTTP GET request.

        **Returns:** str
        """

        input = webpy.input()
        try:
            args = get_web_args()
        except hkutils.HkException, e:
            return str(e)
        generator = IndexGenerator(self._postdb)
        content = ("JSon dictionary of the query parameters: ",
                    generator.escape(repr(args)))
        return self.serve_html(content, generator)

    def POST(self):
        """Serves a HTTP POST request.

        **Returns:** str
        """

        return self.GET()


class RawPostBody(WebpyServer):

    """Serves raw post bodies.

    Served URL: ``/raw-post-bodies/<heap>/<post index>``
    """

    def __init__(self):
        """Constructor."""
        WebpyServer.__init__(self)

    def GET(self, name):
        """Serves a HTTP GET request.

        **Returns:** str
        """

        webpy.header('Content-type', 'text/plain')
        webpy.header('Transfer-Encoding', 'chunked')
        post_id = hkutils.uutf8(name)
        post = self._postdb.post(post_id)
        if post is None:
            return 'No such post: "%s"' % (post_id,)
        content = post.body()
        return content


class RawPostText(WebpyServer):

    """Serves raw post text.

    Served URL: ``/raw-post-text/<heap>/<post index>``
    """

    def __init__(self):
        """Constructor."""
        WebpyServer.__init__(self)

    def GET(self, name):
        """Serves a HTTP GET request.

        **Returns:** str
        """

        webpy.header('Content-type', 'text/plain')
        webpy.header('Transfer-Encoding', 'chunked')
        post_id = hkutils.uutf8(name)
        post = self._postdb.post(post_id)
        if post is None:
            return 'No such post: "%s"' % (post_id,)
        content = post.write_str()
        return content


##### AJAX servers #####

class AjaxServer(WebpyServer):

    """Base class for classes that serve AJAX requests.

    This is only a base class and cannot be used as is; it has "abstract
    methods" that should be overridden, otherwise they will throw an exception.
    """

    def __init__(self):
        """Constructor."""
        WebpyServer.__init__(self)
        self._get_request_allowed = False

    def POST(self):
        """Serves a HTTP POST request.

        **Returns:** str
        """

        # RFC4627: "The MIME media type for JSON text is application/json."
        webpy.header('Content-type','application/json')
        webpy.header('Transfer-Encoding','chunked')
        try:
            args = get_web_args()
        except hkutils.HkException, e:
            return str(e)
        result = self.execute(args)
        return json.dumps(result)

    def GET(self):
        """Serves a HTTP GET request.

        **Returns:** str
        """

        if self._get_request_allowed:
            return self.POST()
        else:
            return 'GET request is not allowed for this page'

    def execute(self, args):
        # Unused argument # pylint: disable=W0613
        """Sets the post body.

        This is an abstract method that should be overridden; otherwise it will
        throw an exception.

        **Argument:**

        - `args` ({string: json_object})

        **Returns:** json_object
        """

        s = ('hkweb.AjaxServer.execute: this method should be overridden')
        raise hkutils.HkException(s)


class SetPostBody(AjaxServer):

    """Sets the body of the given post.

    Served URL: ``/set-post-body``
    """

    def __init__(self):
        """Constructor."""
        AjaxServer.__init__(self)

    def execute(self, args):
        """Sets the post body.

        **Argument:**

        - `args` ({'post_id': |PrePostId|, 'new_body_text': str, 'new_count':
          int, 'new': object})

        **Returns:** {'error': str} | {'new_body_html': str} |
        {'new_post_summary': str, 'new_post_id': str}
        """

        postdb = self._postdb

        post_id = args.get('post_id')
        new = args.get('new')
        if new is None:
            post = postdb.post(post_id)
        else:
            parent = postdb.post(post_id)

            # Create new post, make it a child of the existing one.
            post = hklib.Post.from_str('')
            post.set_author(parent.author())
            post.set_subject(parent.subject())
            post.set_date(parent.date())
            post.set_tags(parent.tags())
            post.set_parent(parent.post_id_str())
            heap = parent.heap_id()
            prefix = 'hkweb_'
            hkshell.add_post_to_heap(post, prefix, heap)
            post_id = post.post_id()

        if post is None:
            return {'error': 'No such post: "%s"' % (post_id,)}

        newPostBodyText = args.get('new_body_text')
        if newPostBodyText is None:
            return {'error': 'No post body specified'}

        post.set_body(newPostBodyText)

        # Generating the HTML for the new body or new post summary.
        if new is None:
            generator = PostBodyGenerator(self._postdb)
            new_body_html = generator.print_post_body(post_id)
            new_body_html = hkutils.textstruct_to_str(new_body_html)
            return {'new_body_html': new_body_html}
        else:
            generator = PostPageGenerator(self._postdb)
            generator.set_post_id(post.post_id())
            postitem = hklib.PostItem('inner', post)
            postitem.print_post_body = True
            postitem.print_parent_post_id = True
            postitem.print_children_post_id = True
            new_post_summary = generator.print_postitems([postitem])
            new_post_summary = hkutils.textstruct_to_str(new_post_summary)
            return { 'new_post_summary': new_post_summary,
                     'new_post_id': post.post_id_str()}


class GetPostBody(AjaxServer):

    """Gets the body of the given post.

    Served URL: ``/get-post-body``
    """

    def __init__(self):
        """Constructor."""
        AjaxServer.__init__(self)
        self._get_request_allowed = True

    def execute(self, args):
        # Unused argument 'args' # pylint: disable=W0613
        """Gets the post body.

        **Argument:**

        - `args` ({'post_id': |PrePostId|})

        **Returns:** {'error': str} | {'body_html': str}
        """

        post_id = args.get('post_id')
        post = self._postdb.post(post_id)
        if post is None:
            return {'error': 'No such post: "%s"' % (post_id,)}

        # Generating the HTML for the new body
        generator = PostBodyGenerator(self._postdb)
        new_body_html = generator.print_post_body(post_id)
        new_body_html = hkutils.textstruct_to_str(new_body_html)

        return {'body_html': new_body_html}


class SetRawPost(AjaxServer):

    """Sets the raw content of the given post.

    Served URL: ``/set-raw-post``
    """

    def __init__(self):
        """Constructor."""
        AjaxServer.__init__(self)

    def execute(self, args):
        """Sets the raw content of the given post.

        **Argument:**

        - `args` ({'post_id': |PrePostId|,
                   'new_post_text': str})

        **Returns:** {'error': str} | {'new_post_summary': str}
        """

        post_id = args.get('post_id')
        post = self._postdb.post(post_id)
        if post is None:
            return {'error': 'No such post: "%s"' % (post_id,)}

        new_post_text = args.get('new_post_text')
        if new_post_text is None:
            return {'error': 'No post text specified'}

        old_parent = post.parent()

        # Catch "Exception" # pylint: disable=W0703
        try:
            post.read_str(new_post_text)
        except Exception, e:
            return {'error':
                    'Exception was raised while parsing the post:\n' + str(e)}

        if post.parent() != old_parent:
            major_change = True
        else:
            major_change = False

        # Generating the HTML for the new post text
        generator = PostPageGenerator(self._postdb)
        generator.set_post_id(post.post_id())
        postitem = hklib.PostItem('inner', post)
        postitem.print_post_body = True
        postitem.print_parent_post_id = True
        postitem.print_children_post_id = True
        new_post_summary = generator.print_postitems([postitem])
        new_post_summary = hkutils.textstruct_to_str(new_post_summary)

        return {'new_post_summary': new_post_summary,
                'major_change': major_change}


class Fetch(object):
    """Serves the files that should be served unchanged."""

    def GET(self, name):
        """Serves a HTTP GET request.

        **Argument:**

        - `name` (unicode) -- The name of the URL that was requested.

        **Returns:** str
        """

        filename = hkutils.uutf8(name)
        return hkutils.file_to_string(filename)


##### Main server class #####

class Server(threading.Thread):

    """Implements the hkweb server thread."""

    def __init__(self, port, retries=0, silent=False):
        """

        **Arguments:**

        - `port` (int) -- Port to listen on.
        - `retries` (int) -- Number of retries.
        - `silent` (bool) -- If ``True``, no text will be printed.
        """

        super(Server, self).__init__()
        self.daemon = True
        self._port = port
        self._retries = retries
        self._silent = silent

    def run(self):
        """Called by the threading framework to start the thread."""

        first = self._port
        last = self._port + self._retries
        found = False

        while self._port <= last:
            # Passing the port parameter to web.py is ugly, but the mailing
            # list entries I have found so far suggest this, and it does the
            # job. A wrapper around sys would be the answer, which should be
            # done anyway to control logging (there sys.stderr should be
            # diverted).
            sys.argv = (None, str(self._port),)
            webapp = webpy.application(urls, globals())
            self.webapp = webapp

            try:
                if not self._silent:
                    hkutils.log('Starting web service...')
                webapp.run()

                # I'm not sure this line will ever be executed
                found = True

            except socket.error, e:
                # We don't want to catch exceptions that are not about an
                # address already being in use
                if re.search('Address already in use', str(e)):
                    self._port += 1
                else:
                    exc_info = sys.exc_info()
                    raise exc_info[0], exc_info[1], exc_info[2]

        if not found:
            s = ('No free port found by hkweb in the %s..%s interval' %
                 (first, last))
            hkweb_server_starting_lock.release()
            raise hkutils.HkException(s)


##### Interface functions #####

# True if we use a lock when starting the web server. It can only be used when
# we monkey patch web.py, so it is set to true by monkey_patch_hkweb.
hkweb_using_server_starting_lock = True

# Lock used when starting the web server. If None, it means that the lock is
# not currently used. Otherwise it is a threading.Lock instance.
hkweb_server_starting_lock = None

hkweb_ports = []

def start(port=8080, retries=0, silent=False):
    """Starts the hkweb web server.

    **Argument:**

    - `port` (int) -- The port to listen on.
    - `retries` (int) -- Number of retries.
    - `silent` (bool) -- If ``True``, no text will be printed.

    **Returns**: int | ``None`` -- The port on which the server started to
    listen. If ``None``, it was not started..
    """

    global hkweb_server_starting_lock

    def readyfun():
        # Releasing the lock because the web server has been
        # started
        if hkweb_using_server_starting_lock:
            hkweb_server_starting_lock.release()
            final_port[0] = options.web_server._port
    web.wsgiserver.CherryPyWSGIServer.ready_callbacks.append(readyfun)

    if hkweb_using_server_starting_lock:
        hkweb_server_starting_lock = threading.Lock()
        hkweb_server_starting_lock.acquire()

    options = hkshell.options
    final_port = [None]
    options.web_server = Server(port, retries, silent)
    options.web_server.start()

    if hkweb_using_server_starting_lock:
        hkweb_server_starting_lock.acquire()
        hkweb_server_starting_lock.release()
        hkweb_server_starting_lock = None

    if final_port[0] is not None:
        hkweb_ports.append(final_port[0])
    return final_port[0]

def insert_urls(new_urls):
    """Inserts the given urls before the already handles URLs.

    **Argument:**

    - `new_urls` ([str])

    **Returns:**

    **Example:** ::

        >>> hkweb.insert_urls(['/myurl', 'mymodule.MyServer'])
    """

    urls[0:0] = new_urls
