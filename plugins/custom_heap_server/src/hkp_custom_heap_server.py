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

# Copyright (C) 2010 Csaba Hoch

""":mod:`hkp_custom_heap_server` implements the "Custom Heap Server" plugin for
Heapkeeper.

This plugin serves the index page of the given heap.

Example usage:

    >>> import hkp_custom_heap_server
    >>> hkp_custom_heap_server.start('myheap')

Afterwards the index page of the 'myheap' heap will be displayed at
<hostname>:<port>/myheap.
"""


import json

import hkweb


class CustomHeapGenerator(hkweb.IndexGenerator):
    """Generator that generates the index page of posts in the given heap."""

    def __init__(self, postdb, heap_id):
        hkweb.IndexGenerator.__init__(self, postdb)
        self._heap_id = heap_id

    def print_main_index_page(self):
        """Prints the main index page.

        **Returns:** |HtmlText|
        """

        def post_in_heap(post):
            return post.heap_id() == self._heap_id
        posts = self._postdb.all().collect(post_in_heap)

        # Getting the posts in the interesting threads
        xpostitems = self.walk_exp_posts(posts)

        # Printing the page
        return self.print_postitems(xpostitems)


def start(heap_id, url=None):
    """Modified the webserver to serve the given heap index page on the given
    URL.

    **Arguments:**

    - `heap_id` (|HeapId|)
    - `url` (str | ``None``) -- If ``None``, it will be ``"/" + heap_id``.
    """

    if url is None:
        url = '/' + heap_id

    class CustomHeapServer(hkweb.HkPageServer):
        """Serves the index page that shows all posts."""

        def __init__(self):
            hkweb.HkPageServer.__init__(self)

        def GET(self):
            generator = CustomHeapGenerator(self._postdb, heap_id)
            content = generator.print_main()

            # Inserting "heap:<heap_id>" into the search bar
            fill_searchbar_js = \
                ('$("#searchbar-term").val(' +
                 json.dumps("heap:" + heap_id + " ") +
                 ');\n')
            js_code = \
                ('<script  type="text/javascript" language="JavaScript">\n',
                fill_searchbar_js,
                 '</script>\n')

            content = (content, js_code)
            return self.serve_html(content, generator)

    hkweb.insert_urls([url, CustomHeapServer])
