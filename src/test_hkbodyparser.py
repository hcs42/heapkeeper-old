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

"""Tests the |hkbodyparser| module.

Usage:

    $ python src/test_hkbodyparser.py
"""


from __future__ import with_statement

import unittest
import re

import hkutils
import hkbodyparser
import test_hklib


class Test_Segment(unittest.TestCase):

    def test_eq(self):
        """Tests :func:`hkbodyparser.Segment.__eq__`."""

        Segment = hkbodyparser.Segment
        self.assertEqual(Segment(), Segment())
        self.assertNotEqual(Segment(), Segment(text='a'))
        self.assertNotEqual(Segment(), Segment(is_meta=True))

    def test_is_similar(self):
        """Tests :func:`hkbodyparser.Segment.is_similar`."""

        Segment = hkbodyparser.Segment
        self.assertTrue(Segment().is_similar(Segment()))
        self.assertTrue(Segment().is_similar(Segment(text='a')))
        self.assertFalse(Segment().is_similar(Segment(is_meta=True)))

        segment = Segment()
        segment.new_attribute = True
        self.assertFalse(segment.is_similar(Segment()))

    def test_str(self):
        """Tests :func:`hkbodyparser.Segment.__str__`."""

        Segment = hkbodyparser.Segment
        self.assertEqual(
            str(Segment()),
            ("<normal, text=''>"))
        self.assertEqual(
            str(Segment(type='normal',
                        quote_level=1,
                        text='text',
                        key='key',
                        value='value',
                        protocol='prot')),
            ("<normal, quote_level=1, key='key', value='value', "
             "protocol=prot, text='text'>"))

    def test_set_prepost_id_str(self):
        """Tests the following functions:

        - :func:`hkbodyparser.Segment.get_prepost_id_str`
        - :func:`hkbodyparser.Segment.set_prepost_id_str`
        """

        segm = hkbodyparser.Segment('heap_link', text='heap://link')

        self.assertEqual(segm.get_prepost_id_str(), 'link')
        segm.set_prepost_id_str('something')
        self.assertEqual(segm.get_prepost_id_str(), 'something')


class Test_Body(unittest.TestCase, test_hklib.PostDBHandler):

    """Tests :class:`hklib.Post`."""

    def setUp(self):
        self.setUpDirs()
        self.create_postdb()
        self.create_threadst()

    def tearDown(self):
        self.tearDownDirs()

    def test1(self):

        Segm = hkbodyparser.Segment
        Body = hkbodyparser.Body

        def test(input, expected_segments):
            actual_output = str(hkbodyparser.parse(input))
            body = Body(segments=expected_segments)
            expected_output = str(body)
            self.assertEqual(actual_output, expected_output)

            # We remove the trailing white spaces from the input and compare
            # it to the concatenation of the text in the body segments
            (nice_input, _) = re.subn(r'[ \t]+\n', r'\n', input)
            joined_body_str = \
                ''.join([segment.text for segment in body.segments])
            self.assertEqual(nice_input, joined_body_str)

        # basic test

        test(
            ('a\n'
             'b\n'),
            [Segm(text='a\nb\n')]
        )

        # empty lines

        test(
            ('a\n'
             '\n'
             '\n'
             'b\n'),
            [Segm(text='a\n\n\nb\n')]
        )

        ### Testing meta text

        ## Testing one liner meta text

        # basic test

        test(
            ('[key value text]\n'),
            [Segm(is_meta=True,
                  text='[key value text]',
                  key='key',
                  value='value text'),
             Segm(text='\n')]
        )

        # meta text with normal text

        test(
            ('a\n'
             '[key value text]\n'
             'b\n'),
            [Segm(text='a\n'),
             Segm(is_meta=True,
                  text='[key value text]',
                  key='key',
                  value='value text'),
             Segm(text='\nb\n')]
        )

        # only key, no value
        test(
            ('[a]\n'),
            [Segm(is_meta=True,
                  text='[a]',
                  key='a',
                  value=''),
             Segm(text='\n')]
        )

        # no key, no value
        test(
            ('[]\n'),
            [Segm(is_meta=True,
                  text='[]',
                  key='',
                  value=''),
             Segm(text='\n')]
        )

        ## Testing multiline meta text

        # value present in the first line
        test(
            ('[key value\n'
             'text]\n'),
            [Segm(is_meta=True,
                  text='[key value\ntext]',
                  key='key',
                  value='value\ntext'),
             Segm(text='\n')]
        )

        # value starts at the second line
        test(
            ('[key\n'
             'value text]\n'),
            [Segm(is_meta=True,
                  text='[key\nvalue text]',
                  key='key',
                  value='\nvalue text'),
             Segm(text='\n')]
        )

        # no value
        test(
            ('[key\n'
             ']\n'),
            [Segm(is_meta=True,
                  text='[key\n]',
                  key='key',
                  value='\n'),
             Segm(text='\n')]
        )

        # no key, only value
        test(
            ('[\n'
             'value\n'
             'text]\n'),
            [Segm(is_meta=True,
                  text='[\nvalue\ntext]',
                  key='',
                  value='\nvalue\ntext'),
             Segm(text='\n')]
        )

        # meta text has no end
        test(
            ('[key\n'
             'value\n'),
            [Segm(is_meta=True,
                  text='[key\nvalue\n',
                  key='key',
                  value='\nvalue\n')]
        )

        ## Testing keys

        ## # '[]' can be a key
        ## test(
        ##     ('[[]]\n'),
        ##     [Segm(is_meta=True,
        ##           text='[[]]',
        ##           key='[]',
        ##           value=''),
        ##      Segm(text='\n')]
        ## )
        ##
        ## # ']' can be a key
        ## test(
        ##     ('[]]\n'),
        ##     [Segm(is_meta=True,
        ##           text='[]]',
        ##           key=']',
        ##           value=''),
        ##      Segm(text='\n')]
        ## )

        # '[' can be a key
        test(
            ('[[]\n'),
            [Segm(is_meta=True,
                  text='[[]',
                  key='[',
                  value=''),
             Segm(text='\n')]
        )

        ## Testing white space

        test(
            ('[key   value  text  ]\n'),
            [Segm(is_meta=True,
                  text='[key   value  text  ]',
                  key='key',
                  value='value  text'),
             Segm(text='\n')]
        )

        test(
            ('[ key \n'
             ' value\t\n'
             ' text ] \n'),
            [Segm(is_meta=True,
                  text='[ key\n value\n text ]',
                  key='key',
                  value='\n value\n text'),
             Segm(text='\n')]
        )

        test(
            ('[key\n'
             '\n'
             'text\n'
             '\n'
             ']\n'),
            [Segm(is_meta=True,
                  text='[key\n\ntext\n\n]',
                  key='key',
                  value='\n\ntext\n\n'),
             Segm(text='\n')]
        )

        # Tab is a separator as well
        test(
            ('[key\tvalue]\n'),
            [Segm(is_meta=True,
                  text='[key\tvalue]',
                  key='key',
                  value='value'),
             Segm(text='\n')]
        )

        ### Testing links

        ## http and ftp links

        # basic test

        test(
            ('http://www.example.com\n'),
            [Segm(type='link',
                  text='http://www.example.com',
                  protocol='http'),
             Segm(text='\n')]
        )

        # normal text around the link
        test(
            ('x http://www.example.com x\n'),
            [Segm(text='x '),
             Segm(type='link',
                  text='http://www.example.com',
                  protocol='http'),
             Segm(text=' x\n')]
        )

        # dot at the end of the link
        test(
            ('http://www.example.com.\n'),
            [Segm(type='link',
                  text='http://www.example.com',
                  protocol='http'),
             Segm(text='.\n')]
        )

        # more dots at the end of the link
        test(
            ('http://www.example.com... wow\n'),
            [Segm(type='link',
                  text='http://www.example.com',
                  protocol='http'),
             Segm(text='... wow\n')]
        )

        # more links in a line
        test(
            ('http://www.example.com http://hu/\n'),
            [Segm(type='link',
                  text='http://www.example.com',
                  protocol='http'),
             Segm(text=' '),
             Segm(type='link',
                  text='http://hu/',
                  protocol='http'),
             Segm(text='\n')]
        )

        # ftp link

        test(
            ('ftp://www.example.com/file1\n'),
            [Segm(type='link',
                  text='ftp://www.example.com/file1',
                  protocol='ftp'),
             Segm(text='\n')]
        )

        # link within meta
        test(
            ('[key http://www.example.com]\n'),
            [Segm(is_meta=True,
                  text='[key ',
                  key='key',
                  value='http://www.example.com'),
             Segm(type='link',
                  is_meta=True,
                  text='http://www.example.com',
                  protocol='http'),
             Segm(is_meta=True,
                  text=']',
                  key=None,
                  value=None),
             Segm(text='\n')]
        )

        # link within multi-line meta
        test(
            ('[key http://www.example.com\n'
             'http://www.example.com]\n'),
            [Segm(is_meta=True,
                  text='[key ',
                  key='key',
                  value='http://www.example.com\nhttp://www.example.com'),
             Segm(type='link',
                  is_meta=True,
                  text='http://www.example.com',
                  protocol='http'),
             Segm(is_meta=True,
                  text='\n'),
             Segm(type='link',
                  is_meta=True,
                  text='http://www.example.com',
                  protocol='http'),
             Segm(is_meta=True,
                  text=']'),
             Segm(text='\n')]
        )

        # heap link within meta
        test(
            ('[key heap://ums/12]\n'),
            [Segm(is_meta=True,
                  text='[key ',
                  key='key',
                  value='heap://ums/12'),
             Segm(type='heap_link',
                  is_meta=True,
                  text='heap://ums/12',
                  value='ums/12'),
             Segm(is_meta=True,
                  text=']',
                  key=None,
                  value=None),
             Segm(text='\n')]
        )

        # link within a meta: the key is not interpreted as a link
        test(
            ('[http://www.example.com value]\n'),
            [Segm(is_meta=True,
                  text='[http://www.example.com value]',
                  key='http://www.example.com',
                  value='value'),
             Segm(text='\n')]
        )

        ## Heap links

        # basic test

        test(
            ('heap://ums/12\n'),
            [Segm(type='heap_link', text='heap://ums/12', value='ums/12'),
             Segm(text='\n')]
        )

        ### Testing quotes

        # basic test
        test(
            ('> level 1\n'
             '> level 1\n'
             '>> level 2\n'
             '> >  level 2\n'
             'not quote\n'
             ' > not quote\n'),
            [Segm(text='> level 1\n'
                       '> level 1\n',
                  quote_level=1),
             Segm(text='>> level 2\n'
                       '> >  level 2\n',
                  quote_level=2),
             Segm(text='not quote\n'
                       ' > not quote\n')]
        )

        # links within quotes
        test(
            ('> http://x http://y\n'
             '>http://z x\n'),
            [Segm(quote_level=1, text='> '),
             Segm(quote_level=1, type='link',
                  text='http://x',
                  protocol='http'),
             Segm(quote_level=1, text=' '),
             Segm(quote_level=1, type='link',
                  text='http://y',
                  protocol='http'),
             Segm(quote_level=1, text='\n>'),
             Segm(quote_level=1, type='link',
                  text='http://z',
                  protocol='http'),
             Segm(quote_level=1, text=' x\n')]
        )

        # no meta within quotes
        test(
            ('> [not meta]\n'),
            [Segm(quote_level=1, text='> [not meta]\n')]
        )

        ### Testing raw blocks

        test(
            ('normal text\n'
             '\n'
             '    verbatim\n'
             '\n'
             'normal text\n'),
            [Segm(text='normal text\n\n'),
             Segm(type='raw',
                  text='    verbatim\n'),
             Segm(text='\nnormal text\n')]
        )

        test(
            ('normal text\n'
             '\n'
             '    verbatim\n'
             '\n'
             '    still verbatim\n'
             '\n'
             'normal text\n'),
            [Segm(text='normal text\n\n'),
             Segm(type='raw',
                  text='    verbatim\n'
                       '\n'
                       '    still verbatim\n'),
             Segm(text='\nnormal text\n')]
        )

        # Verbatim in quotes

        test(
            ('> normal text\n'
             '> \n'
             '>     verbatim\n'
             '> \n'
             '> normal text\n'),
            [Segm(text='> normal text\n'
                       '>\n',
                  quote_level=1),
             Segm(type='raw',
                  text='>     verbatim\n',
                  quote_level=1),
             Segm(text='>\n'
                       '> normal text\n',
                  quote_level=1)]
        )

        test(
            ('>     verbatim\n'
             '> \n'
             '>     still verbatim\n'
             '> \n'
             '> normal text\n'),
            [Segm(type='raw',
                  text='>     verbatim\n'
                       '>\n'
                       '>     still verbatim\n',
                  quote_level=1),
             Segm(text='>\n'
                       '> normal text\n',
                  quote_level=1)]
        )

        # Verbatim finished by different quote level
        # Verbatim finished by end of body

        test(
            ('>> normal text\n'
             '>> \n'
             '>>     verbatim\n'
             '>    other verbatim\n'),
            [Segm(text='>> normal text\n'
                       '>>\n',
                  quote_level=2),
             Segm(type='raw',
                  text='>>     verbatim\n',
                  quote_level=2),
             Segm(type='raw',
                  text='>    other verbatim\n',
                  quote_level=1)]
        )

        # Not verbatim because of missing empty line

        test(
            ('normal text\n'
             '    not verbatim\n'),
            [Segm(text='normal text\n    not verbatim\n')]
        )

        ### Testing API

        p = self.p(0)
        p.set_body('a\nb\n')
        self.assertEqual(
            str(p.body_object()),
            '<normal, text=%s>\n' % (repr('a\nb\n'),))

        body = hkbodyparser.Body([Segm(text='a'), Segm(text='b')])
        self.assertEqual(
            body.body_str(),
            'ab')

if __name__ == '__main__':
    hkutils.set_log(False)
    unittest.main()
