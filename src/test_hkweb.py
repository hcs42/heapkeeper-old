#!/usr/bin/env python

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

"""Tests the hkweb module.

Usage:

    $ python src/test_hkweb.py
"""


from __future__ import with_statement

import unittest

import hkutils
import hkweb
import test_hkgen


class Test_WebGenerator(test_hkgen.Test_BaseGenerator):

    """Tests :class:`hkweb.WebGenerator`."""

    def create_generator(self):
        """Returns a generator object to be used for the testing.

        **Returns:** :class:`hkweb.WebGenerator`
        """

        return hkweb.WebGenerator(self._postdb)

    def test_print_html_head_content(self):
        """Tests the following functions:

        - :func:`hkweb.WebGenerator.get_static_path`
        - :func:`hkgen.BaseGenerator.print_html_head_content`
        """

        postdb, g, p = self.get_ouv()

        # We overwrite some options of the generator so that we can use these
        # in our test cases. Since different subclasses of BaseGenerator have
        # different options, this way testing will be easier because we can
        # hardcode these values in the tests.
        g.options.js_files = ['static/js/myjs.js']
        g.options.cssfiles = ['static/css/mycss1.css', 'static/css/mycss2.css']
        g.options.favicon = 'static/images/myicon.ico'

        self.assertTextStructsAreEqual(
            g.print_html_head_content(),
            ('    <link rel="stylesheet" href="/static/css/mycss1.css" '
             'type="text/css" />\n'
             '    <link rel="stylesheet" href="/static/css/mycss2.css" '
             'type="text/css" />\n'
             '    <link rel="shortcut icon" '
             'href="/static/images/myicon.ico">\n'))

    def test_print_postitem_flat(self):
        """Inherited test case that we don't want to execute because it would
        fail."""

        pass

    def test_print_postitem_inner(self):
        """Inherited test case that we don't want to execute because it would
        fail."""

        pass


class Test_IndexGenerator(Test_WebGenerator):

    """Tests :class:`hkweb.IndexGenerator`."""

    def create_generator(self):
        """Returns a generator object to be used for the testing.

        **Returns:** :class:`hkweb.IndexGenerator`
        """

        return hkweb.IndexGenerator(self._postdb)

    def test_print_main(self):
        """Tests :func:`hkweb.IndexGenerator.print_main`."""

        # We don't actually examine the result, but we at least test that no
        # exception occurs.

        postdb, g, p = self.get_ouv()
        g.print_main()


class Test_PostPageGenerator(Test_WebGenerator):

    """Tests :class:`hkweb.PostPageGenerator`."""

    def create_generator(self):
        """Returns a generator object to be used for the testing.

        **Returns:** :class:`hkweb.PostPageGenerator`
        """

        return hkweb.PostPageGenerator(self._postdb)

    def test_print_main(self):
        """Tests :func:`hkweb.PostPageGenerator.print_main`."""

        # We don't actually examine the result, but we at least test that no
        # exception occurs.

        postdb, g, p = self.get_ouv()
        g.print_main('my_heap/0')


class Test_SearchPageGenerator(Test_PostPageGenerator):

    """Tests :class:`hkweb.SearchPageGenerator`."""

    def create_generator(self):
        """Returns a generator object to be used for the testing.

        **Returns:** :class:`hkweb.SearchPageGenerator`
        """

        return hkweb.SearchPageGenerator(self._postdb, ['my_heap/0'])

    def test_print_search_page(self):
        """Tests :func:`hkweb.SearchPageGenerator.print_search_page`."""

        # We don't actually examine the result, but we at least test that no
        # exception occurs.

        postdb, g, p = self.get_ouv()
        g.print_search_page()


class Test_PostBodyGenerator(Test_WebGenerator):

    """Tests :class:`hkweb.PostBodyGenerator`."""

    def create_generator(self):
        """Returns a generator object to be used for the testing.

        **Returns:** :class:`hkweb.PostBodyGenerator`
        """

        return hkweb.PostBodyGenerator(self._postdb)

    def test_print_post_body(self):
        """Tests :func:`hkweb.PostBodyGenerator.print_post_body`."""

        postdb, g, p = self.get_ouv()

        # Basic test
        self.assertTextStructsAreEqual(
            g.print_post_body('my_heap/0'),
            '<pre class="post-body-content">body0\n</pre>')

        # Testing a non-existig post
        self.assertTextStructsAreEqual(
            g.print_post_body('my_heap/nosuchpost'),
            'No such post: "my_heap/nosuchpost"')


if __name__ == '__main__':
    hkutils.set_log(False)
    unittest.main()
