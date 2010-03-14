#!/usr/bin/python

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

# Copyright (C) 2009 Csaba Hoch
# Copyright (C) 2009 Attila Nagy

"""Tests the hkgen module.

Usage:

    $ python test_hkgen.py
"""


from __future__ import with_statement

import os
import time
import unittest

import hkutils
import hklib
import hkgen
import test_hklib


class Test_Generator(unittest.TestCase, test_hklib.PostDBHandler):

    """Tests |Generator|."""

    def setUp(self):
        """Creates a temporary working directory."""

        self.setUpDirs()
        self.create_postdb()
        self.create_threadst()

        self._orig_workingdir = os.getcwd()
        self._generator = hkgen.Generator(self._postdb)
        self.create_postitems()

    def tearDown(self):
        """Deletes the temporary working directory."""
        os.chdir(self._orig_workingdir)
        self.tearDownDirs()

    def get_ouv(self):
        """Returns often used variables.

        **Return:** (|PostDB|, |Generator|, function)
        """

        return self._postdb, self._generator, self.p

    def create_postitems(self):
        """Creates a list of post items.

        **Returns:** [|PostItem|]
        """

        self.postitems = \
            [hklib.PostItem(pos='begin', post=self.p(0), level=0),
             hklib.PostItem(pos='begin', post=self.p(1), level=1),
             hklib.PostItem(pos='end', post=self.p(1), level=1),
             hklib.PostItem(pos='end', post=self.p(0), level=0)]

    def assertTextStructsAreEqual(self, text1, text2):
        """Asserts that the given text structures are equal.

        **Arguments:**

        - `text1` (|TextStruct|)
        - `text2` (|TextStruct|)
        """

        self.assertEqual(
            hkutils.textstruct_to_str(text1),
            hkutils.textstruct_to_str(text2))

    def file_content(self, filename):
        """Returns the content of the given file in the HTML directory.

        **Returns:** str
        """

        long_filename = os.path.join(self._html_dir, filename)
        return hkutils.file_to_string(long_filename)

    def test_escape(self):
        """Tests :func:`hkgen.Generator.escape`."""

        _postdb, g, _p = self.get_ouv()

        def test(unescaped, escaped):
            self.assertTextStructsAreEqual(
                g.escape(unescaped),
                escaped)

        test('a<b', 'a&lt;b')
        test('a>b', 'a&gt;b')
        test('a&b', 'a&amp;b')

    def test_print_link(self):
        """Tests :func:`hkgen.Generator.link`."""

        postdb, g, p = self.get_ouv()

        self.assertTextStructsAreEqual(
            g.print_link('mylink', 'mystuff'),
            '<a href="mylink">mystuff</a>')
        self.assertTextStructsAreEqual(
            g.print_link('"mylink"', 'mystuff'),
            '<a href="%22mylink%22">mystuff</a>')

    def test_enclose(self):
        """Tests :func:`hkgen.Generator.enclose`."""

        postdb, g, p = self.get_ouv()

        # Just the one mandatory parameter
        self.assertTextStructsAreEqual(
            g.enclose('mystuff'),
            '<span>mystuff</span>')

        # Testing the `tag` parameter
        self.assertTextStructsAreEqual(
            g.enclose('mystuff', tag='mytag'),
            '<mytag>mystuff</mytag>')

        # Testint the `class` parameter
        self.assertTextStructsAreEqual(
            g.enclose('mystuff', class_='myclass'),
            '<span class="myclass">mystuff</span>')

        # Testing the `newlines` parameter
        self.assertTextStructsAreEqual(
            g.enclose('mystuff\n', newlines=True),
            '<span>\nmystuff\n</span>\n')

        # Testing the `myid` parameter
        self.assertTextStructsAreEqual(
            g.enclose('mystuff', id='myid'),
            '<span id="myid">mystuff</span>')

        # Testing the `comment` parameter
        self.assertTextStructsAreEqual(
            g.enclose('mystuff', comment='my comment'),
            ('<span><!-- my comment -->'
             'mystuff'
             '</span><!-- my comment -->'))

        # Testing the `closing_comment` parameter when having a class
        self.assertTextStructsAreEqual(
            g.enclose('mystuff', class_='myclass', closing_comment=True),
            ('<span class="myclass">mystuff</span>'
             '<!-- myclass -->'))

        # Testing the `closing_comment` parameter when not having a class
        self.assertTextStructsAreEqual(
            g.enclose('mystuff', closing_comment=True),
            '<span>mystuff</span>')

        # Testing the `title` parameter
        self.assertTextStructsAreEqual(
            g.enclose('mystuff', title='mytitle'),
            '<span title="mytitle">mystuff</span>')

        # Testing the `skip_empty` parameter with empty string
        self.assertTextStructsAreEqual(
            g.enclose('', skip_empty=True),
            '')

        # Testing the `skip_empty` parameter with empty list
        self.assertTextStructsAreEqual(
            g.enclose('', skip_empty=True),
            [])

        # Testing the `skip_empty` parameter with non-empty string
        self.assertTextStructsAreEqual(
            g.enclose('x', skip_empty=True),
            '<span>x</span>')

        # Testing the `skip_empty` parameter turned off with empty string
        self.assertTextStructsAreEqual(
            g.enclose('', skip_empty=False),
            '<span></span>')

        # All parameters have a value
        self.assertTextStructsAreEqual(
            g.enclose('mystuff\n', class_='myclass', tag='mytag',
                      newlines=True, id='myid', comment='my comment',
                      closing_comment=True, title='mytitle'),
            ('<mytag class="myclass" id="myid" title="mytitle">'
             '<!-- my comment -->\n'
             'mystuff\n'
             '</mytag><!-- my comment --><!-- myclass -->\n'))

    def test_section_begin(self):
        """Tests :func:`hkgen.section_begin`."""

        postdb, g, p = self.get_ouv()

        # myid='', section_begin=''
        self.assertTextStructsAreEqual(
            g.section_begin('', ''),
            '<div class="sectionid">\n')

        # myid is not empty
        self.assertTextStructsAreEqual(
            g.section_begin('myid', ''),
            '<div class="sectionid" id="myid">\n')

        # section_begin is not empty
        self.assertTextStructsAreEqual(
            g.section_begin('', 'MyTitle'),
            ('<div class="section">\n'
             '<span class="sectiontitle">MyTitle</span>\n'))

        # neither myid nor section_begin is not empty
        self.assertTextStructsAreEqual(
            g.section_begin('myid', 'MyTitle'),
            ('<div class="section">\n'
             '<span class="sectiontitle" id="myid">MyTitle</span>\n'))

    def test_section_end(self):
        """Tests :func:`hkgen.section_end`."""

        postdb, g, p = self.get_ouv()

        # myid='', section_begin=''
        self.assertTextStructsAreEqual(
            g.section_end(),
            '</div>\n')

    def test_section(self):
        """Tests :func:`hkgen.Generator.section`."""

        postdb, g, p = self.get_ouv()

        self.assertTextStructsAreEqual(
            g.section('mysecid', 'mysectitle', 'myhtmltext'),
            (g.section_begin('section_mysecid', 'mysectitle'),
             'myhtmltext',
             g.section_end()))

        self.assertTextStructsAreEqual(
            g.section('mysecid', 'mysectitle', 'myhtmltext', flat=True),
            (g.section_begin('section_mysecid', 'mysectitle'),
             g.enclose('myhtmltext', 'table', 'flatlist', newlines=True),
             g.section_end()))

    def test_format_timestamp(self):
        """Tests :func:`hkgen.Generator.format_timestamp`."""

        postdb, g, p = self.get_ouv()

        g.options.localtime_fun = time.gmtime
        self.assertEqual(
            g.format_timestamp(p(0).timestamp()),
            '(2008-08-20)')

    def test_print_postitem_main(self):
        """Tests :func:`hkgen.Generator.print_postitem_main`."""

        postdb, g, p = self.get_ouv()
        def enc(class_, content):
            return g.enclose(content, class_=class_)

        # Without post body

        postitem = hklib.PostItem('begin', p(0), 0)
        postitem = g.augment_postitem(postitem)
        postitem.post.set_tags(['tag1', 'tag2'])

        post_link = g.print_link('../my_heap/thread_0.html#post_my_heap/0',
                                 '&lt;my_heap/0&gt;')
        thread_link = g.print_link('../my_heap/thread_0.html',
                                   '<img src="../thread.png" />')
        expected_header = \
            [enc('author', 'author0'), '\n',
             enc('subject', 'subject0'), '\n',
             enc('tags', '[tag1, tag2]'), '\n',
             enc('index', post_link), '\n',
             enc('date', '(2008-08-20)'), '\n']

        self.assertTextStructsAreEqual(
            g.print_postitem_main(postitem),
            g.enclose(
                expected_header,
                class_='postsummary',
                id='post_my_heap/0',
                newlines=True,
                closing_comment=True))

        # With post body

        postitem.print_post_body = True
        expected_body = \
            g.enclose(
                g.enclose(
                    'body0\n',
                    'pre',
                    'postbody'),
                'div',
                'body',
                newlines=True)

        self.assertTextStructsAreEqual(
            g.print_postitem_main(postitem),
            g.enclose(
                (expected_header, expected_body),
                class_='postsummary',
                id='post_my_heap/0',
                newlines=True,
                closing_comment=True))

    def test_print_postitem_flat(self):
        """Tests :func:`hkgen.Generator.print_postitem_flat`."""

        postdb, g, p = self.get_ouv()
        def enctd(class_, content, tag):
            return \
                g.enclose(
                    g.enclose(content, class_=class_),
                    'td')

        # Without post body

        postitem = hklib.PostItem('flat', p(0), 0)
        postitem = g.augment_postitem(postitem)
        postitem.post.set_tags(['tag1', 'tag2'])

        post_link = g.print_link('../my_heap/thread_0.html#post_my_heap/0',
                                 '&lt;my_heap/0&gt;')
        expected_header = \
            g.enclose(
                (enctd('author', 'author0', 'td'), '\n',
                 enctd('subject', 'subject0', 'td'), '\n',
                 enctd('tags', '[tag1, tag2]', 'td'), '\n',
                 enctd('index', post_link, 'td'), '\n',
                 enctd('date', '(2008-08-20)', 'td'), '\n'),
                'tr',
                newlines=True)

        self.assertTextStructsAreEqual(
            g.print_postitem_flat(postitem),
            g.enclose(
                expected_header,
                class_='postsummary',
                newlines=True))

        # With post body
        expected_body = \
            g.enclose(
                g.enclose(
                    g.enclose(
                        g.enclose(
                            'body0\n',
                            'pre',
                            'postbody'),
                        'div',
                        'body',
                        newlines=True),
                    'td colspan=5',
                    newlines=True),
                'tr',
                newlines=True)

        postitem.print_post_body = True
        self.assertTextStructsAreEqual(
            g.print_postitem_flat(postitem),
            g.enclose(
                (expected_header, expected_body),
                'span',
                'postsummary',
                newlines=True))

        # Without post body and some other fields

        postitem.print_post_body = False
        import types

        def print_postitem_date(self, postitem):
            return ''

        hkutils.add_method(g, 'print_postitem_date', print_postitem_date)

        post_link = g.print_link('../my_heap/thread_0.html#post_my_heap/0',
                                 '&lt;my_heap/0&gt;')
        expected_header = \
            [enctd('author', 'author0', 'td'), '\n',
             enctd('subject', 'subject0', 'td'), '\n',
             enctd('tags', '[tag1, tag2]', 'td'), '\n',
             enctd('index', post_link, 'td'), '\n',
             g.enclose('', 'td'), '\n']

        self.assertTextStructsAreEqual(
            g.print_postitem_flat(postitem),
            g.enclose(
                g.enclose(
                    expected_header,
                    'tr',
                    newlines=True),
                class_='postsummary',
                newlines=True))

    def test_walk_postitems(self):
        """Tests the following functions:

        - :func:`hkgen.Generator.augment_postitem`
        - :func:`hkgen.Generator.walk_postitems`
        """

        postdb, g, p = self.get_ouv()
        postitems = list(g.walk_postitems(self.postitems))

        # We check that postitems[0] is only a copy of self.postitems
        self.assert_(postitems[0] is not self.postitems[0])

        # We check that every field was of the post item copied
        self.assertEqual(postitems[0].pos, self.postitems[0].pos)
        self.assertEqual(postitems[0].post, self.postitems[0].post)
        self.assertEqual(postitems[0].level, self.postitems[0].level)

        # We check that the `print_fun` field was added
        self.assertEqual(postitems[0].print_fun, g.print_postitem)

    def test_print_postitems(self):
        """Tests :func:`hkgen.Generator.print_postitem`."""

        postdb, g, p = self.get_ouv()
        postitems = list(g.walk_postitems(self.postitems))
        self.assertTextStructsAreEqual(
            g.print_postitems(postitems),
            [g.print_postitem(postitems[0]),
             g.print_postitem(postitems[1]),
             g.print_postitem(postitems[2]),
             g.print_postitem(postitems[3])])

    def test_write_main_index_page(self):
        """Tests the following functions:

        - :func:`hkgen.Generator.print_main_index_page`
        - :func:`hkgen.Generator.print_html_page`
        - :func:`hkgen.Generator.write_pages`
        - :func:`hkgen.Generator.write_main_index_page`
        """

        postdb, g, p = self.get_ouv()

        # Testing when there are no cycles

        g.write_main_index_page()
        self.assertTextStructsAreEqual(
            self.file_content('index/index.html'),
            [g.print_html_header(),
             g.print_postitems(g.walk_thread(None)),
             g.print_html_footer()])

        # Testing when there is a cycle

        self.introduce_cycle()

        g.write_main_index_page()
        self.assertTextStructsAreEqual(
            self.file_content('index/index.html'),
            [g.print_html_header(),
             g.section( # section of posts in cycles
                 '0', 'Posts in cycles',
                 flat=True,
                 content=
                     g.print_postitems(
                         g.walk_postitems(g._postdb.walk_cycles()))),
             g.section( # section of posts not in cycles
                 '1', 'Other posts',
                  g.print_postitems(g.walk_thread(None))),
             g.print_html_footer()])

        self.assertEqual(
            self.pop_log(),
            ('Generating index.html...\n'
             'Generating index.html...'))

    def test_write_post_pages(self):
        """Tests the following functions:

        - :func:`hkgen.Generator.print_post_page`
        - :func:`hkgen.Generator.write_post_pages`
        """

        postdb, g, p = self.get_ouv()
        pi_begin = hklib.PostItem('begin', p(0), 0)
        pi_main = hklib.PostItem('main', p(0), 0)
        pi_end = hklib.PostItem('end', p(0), 0)
        pi_begin.print_post_body = True
        pi_main.print_post_body = True
        g.options.html_title = 'Post my_heap/0'

        expected_content = \
            (g.print_html_header(),
             g.print_postitem(pi_begin),
             g.print_postitem(pi_main),
             g.print_postitem(pi_end),
             g.print_html_footer())

        g.write_post_pages(write_all=True)
        self.assertTextStructsAreEqual(
            self.file_content('my_heap/0.html'),
            expected_content)

        postitems = [pi_begin, pi_end]
        g.write_post_pages()
        self.assertTextStructsAreEqual(
             [g.print_postitem(pi_begin),
              g.print_postitem(pi_end)],
             g.print_postitems(g.walk_postitems(postitems)))

        self.assertEqual(
            self.pop_log(),
            ('Generating post pages...\n'
             'Generating post pages...'))


if __name__ == '__main__':
    set_log(False)
    unittest.main()
