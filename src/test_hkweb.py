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

# Copyright (C) 2010-2011 Csaba Hoch

"""Tests the hkweb module.

Usage:

    $ python src/test_hkweb.py
"""


from __future__ import with_statement

import os
import unittest

import hkutils
import hkshell
import hkweb
import test_hklib
import test_hkgen


##### Generator classes #####

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


##### Server classes #####

class Test__servers(unittest.TestCase, test_hklib.PostDBHandler):

    """Tests server classes in |hkweb|."""

    def setUp(self):
        """Creates a temporary working directory."""

        self.setUpDirs()
        self.create_postdb()
        self.create_threadst()

        self._orig_workingdir = os.getcwd()
        os.chdir(self._dir)

        self.start_hkshell()
        self.start_hkweb()

    def start_hkshell(self):
        """Starts hkshell if it is not started."""

        if hkshell.hkshell_started:
            return

        config_file = os.path.join(self._dir, 'test.cfg')
        config_str = \
            ('[paths]\n'
             'html_dir=my_html_dir\n'
             '\n'
             '[heaps/my_heap]\n'
             'heap_id=my_heap\n'
             'name=My heap\n'
             'path=my_heap_dir\n')
        hkutils.string_to_file(config_str, config_file)

        cmdl_options, args = \
            hkshell.parse_args(['--configfile', 'test.cfg', '--noshell',
                                '--hkrc', 'NONE'])
        hkshell.main(cmdl_options, args)
        hkshell.options.postdb = self._postdb

        self.assertEqual(
            self.pop_log(),
            'Warning: post directory does not exists: "my_heap_dir"\n'
            'Post directory has been created.\n'
            'Warning: HTML directory does not exists: "my_html_dir"\n'
            'HTML directory has been created.')

    def start_hkweb(self):
        """Starts hkweb if it is not started."""
        if hkweb.hkweb_ports == []:
            hkweb.start(retries=20, silent=True)

    def tearDown(self):
        """Deletes the temporary working directory."""
        os.chdir(self._orig_workingdir)
        self.tearDownDirs()

    def test_Index(self):
        """Tests :class:`hkweb.Index`."""

        gen = hkweb.IndexGenerator(self._postdb)

        self.assertTextStructsAreEqual(
            hkshell.options.web_server.webapp.request('/').data,
            gen.print_html_page(gen.print_main()))

    def test_Post(self):
        """Tests :class:`hkweb.Post`."""

        gen = hkweb.PostPageGenerator(self._postdb)

        self.assertTextStructsAreEqual(
            hkshell.options.web_server.webapp.request('/posts/my_heap/0').data,
            gen.print_html_page(gen.print_main('my_heap/0')))

    def test_Search_get_posts(self):
        """Tests :func:`hkweb.Search.get_posts`."""

        s = hkweb.Search()
        postdb = self._postdb

        self.assertEqual(
            s.get_posts({'posts': ['my_heap/0', 'my_heap/3']}),
            postdb.postset(['my_heap/0', 'my_heap/3']))

        self.assertEqual(
            s.get_posts({'term': '3'}),
            postdb.postset(['my_heap/3']))

    def test_Search(self):
        """Tests :class:`hkweb.Search`."""

        ## Testing search term for an existing post

        gen = hkweb.SearchPageGenerator(self._postdb, 'my_heap/3')

        numbers = ('Posts found: 1<br/>All posts shown: 4')
        numbers_box = gen.enclose(numbers, 'div', 'info-box')
        main_content = (numbers_box, gen.print_search_page())

        js_code = \
            ('<script  type="text/javascript" language="JavaScript">\n'
             '$("#searchbar-term").val("3");\n'
             '$("#searchbar-term").focus();\n'
             '</script>\n')

        content = (gen.print_searchbar(),
                   main_content,
                   gen.print_js_links(),
                   js_code)

        self.assertTextStructsAreEqual(
            hkshell.options.web_server.webapp.request('/search?term=3').data,
            gen.print_html_page(content))

        ## Testing search specified by 'posts'

        gen = hkweb.SearchPageGenerator(self._postdb, 'my_heap/3')

        numbers = ('Posts found: 1<br/>All posts shown: 4')
        numbers_box = gen.enclose(numbers, 'div', 'info-box')
        main_content = (numbers_box, gen.print_search_page())

        js_code = \
            ('<script  type="text/javascript" language="JavaScript">\n'
             '$("#searchbar-term").focus();\n'
             '</script>\n')

        content = (gen.print_searchbar(),
                   main_content,
                   gen.print_js_links(),
                   js_code)

        url = '/search?posts=%00["my_heap/3"]'
        self.assertTextStructsAreEqual(
            hkshell.options.web_server.webapp.request(url).data,
            gen.print_html_page(content))

        ## Testing search page with no search term

        gen = hkweb.SearchPageGenerator(self._postdb, [])

        js_code = \
            ('<script  type="text/javascript" language="JavaScript">\n'
             '$("#searchbar-term").focus();\n'
             '</script>\n')

        content = (gen.print_searchbar(),
                   '',
                   gen.print_js_links(),
                   js_code)

        self.assertTextStructsAreEqual(
            hkshell.options.web_server.webapp.request('/search').data,
            gen.print_html_page(content))

        ## Testing search page with specifying a non-existent post

        url = '/search?posts=%00["nosuchpost"]'
        self.assertTextStructsAreEqual(
            hkshell.options.web_server.webapp.request(url).data,
            'Post not found: nosuchpost')

        ## Testing search term for an existing post

        gen = hkweb.SearchPageGenerator(self._postdb, [])

        js_code = \
            ('<script  type="text/javascript" language="JavaScript">\n'
             '$("#searchbar-term").val("nosuchpost");\n'
             '$("#searchbar-term").focus();\n'
             '</script>\n')

        content = (gen.print_searchbar(),
                   'No post found.',
                   gen.print_js_links(),
                   js_code)

        url = '/search?term=nosuchpost'
        self.assertTextStructsAreEqual(
            hkshell.options.web_server.webapp.request(url).data,
            gen.print_html_page(content))

    def test_ShowJSon(self):
        """Tests :class:`hkweb.ShowJSon`."""

        bp = 'JSon dictionary of the query parameters: ' # boilerplate

        # Basic test
        url = '/show-json?key=value'
        self.assertTextStructsAreEqual(
            hkshell.options.web_server.webapp.request(url).data,
            bp + "{'key': 'value'}")

        # Testing incorrect arguments
        url = '/show-json?key=%00NotCorrectJsonObject'
        self.assertTextStructsAreEqual(
            hkshell.options.web_server.webapp.request(url).data,
            ('Error: the "key" parameter is not a valid JSON object: ' +
             '\x00NotCorrectJsonObject'))

        # Testing empty parameter list
        url = '/show-json'
        self.assertTextStructsAreEqual(
            hkshell.options.web_server.webapp.request(url).data,
            bp + "{}")

        # Testing special characters
        url = '/show-json?key=%00"value <br>\\n"'
        self.assertTextStructsAreEqual(
            hkshell.options.web_server.webapp.request(url).data,
            bp + "{'key': 'value &lt;br&gt;\\n'}")


if __name__ == '__main__':
    hkutils.set_log(False)
    unittest.main()
