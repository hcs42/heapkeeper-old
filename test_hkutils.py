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

"""Tests the hkutils module.

Usage:

    $ python test_hkutils.py
"""

from __future__ import with_statement
import unittest
import StringIO

import hkutils


class TestOptionHandling(unittest.TestCase):

    def f(a, b, c=1, d=2):
        pass

    def test_arginfo(self):
        def f(a, b, c=1, d=2):
            pass
        self.assertEquals(hkutils.arginfo(f), (['a', 'b'], {'c':1, 'd':2}))
        f2 = TestOptionHandling.f
        self.assertEquals(hkutils.arginfo(f2), (['a', 'b'], {'c':1, 'd':2}))

    def test_set_defaultoptions(self):

        def f(other1, a, b=1, c=2, other2=None):
            pass

        options = {'a':0, 'b': 1}
        hkutils.set_defaultoptions(options, f, ['other1', 'other2'])
        self.assertEquals(options, {'a':0, 'b':1, 'c':2})

        options = {'b': 1}
        def try_():
            hkutils.set_defaultoptions(options, f, ['other1', 'other2'])
        self.assertRaises(hkutils.HkException, try_)

        options = {'a':0, 'b': 1, 'other': 2}
        def try_():
            hkutils.set_defaultoptions(options, f, ['other1', 'other2'])
        self.assertRaises(hkutils.HkException, try_)

    def test_set_dict_items_1(self):

        class A:
            pass
        a = A()
        d = {'self': 0, 'something': 1, 'notset': hkutils.NOT_SET}
        hkutils.set_dict_items(a, d)
        self.assertEquals(a.something, 1)

        def f():
            a.self
        self.assertRaises(AttributeError, f)

        def f():
            a.notset
        self.assertRaises(AttributeError, f)

    def test_set_dict_items_2(self):

        NOT_SET = hkutils.NOT_SET
        class A(object):
            def __init__(self, x1=NOT_SET, x2=NOT_SET, x3=0, x4=0):
                super(A, self).__init__()
                hkutils.set_dict_items(self, locals())

        a = A(x1=1, x3=1)
        self.assertEquals(a.x1, 1)
        self.assertFalse(hasattr(a, 'x2'))
        self.assertEquals(a.x3, 1)
        self.assertEquals(a.x4, 0)

    def test_check(self):

        class A(object):
            pass

        a = A()
        a.x = 1
        self.assertTrue(hkutils.check(a, ['x']))
        self.assertRaises(AttributeError, lambda: hkutils.check(a, ['y']))


class TestMisc(unittest.TestCase):

    """Tests the utility functions of hklib."""

    def test_calc_timestamp(self):
        ts = hkutils.calc_timestamp('Wed, 20 Aug 2008 17:41:30 +0200')
        self.assertEquals(ts, 1219246890.0)

    def test_HkException(self):
        def f():
            raise hkutils.HkException, 'description'
        self.assertRaises(hkutils.HkException, f)

        try:
            raise hkutils.HkException, 'description'
        except hkutils.HkException, h:
            self.assertEquals(h.value, 'description')
            self.assertEquals(str(h), "'description'")

    def test_textstruct_to_str(self):

        # Converting a string
        self.assertEquals(
            hkutils.textstruct_to_str('text'),
            'text')

        # Converting a structure that contains both lists and tuples
        self.assertEquals(
            hkutils.textstruct_to_str(['text1', ('2', ['3']), '4']),
            'text1234')

        # Trying to converting something that is not a TextStruct
        self.assertRaises(
            TypeError,
            lambda: hkutils.textstruct_to_str(0))

    def test_write_textstruct(self):

        # Writing a string
        sio = StringIO.StringIO()
        hkutils.write_textstruct(sio, 'text')
        self.assertEquals(sio.getvalue(), 'text')

        # Writing a structure that contains both lists and tuples
        sio = StringIO.StringIO()
        hkutils.write_textstruct(sio, ['text1', ('2', ['3']), '4'])
        self.assertEquals(sio.getvalue(), 'text1234')

        # Trying to writing something that is not a TextStruct
        sio = StringIO.StringIO()
        self.assertRaises(
            TypeError,
            lambda: hkutils.write_textstruct(sio, 0))

    def test_plural(self):

        for i in (-1, 1):
            self.assertEquals(hkutils.plural(i), '')
            self.assertEquals(hkutils.plural(i, 'ox', 'oxen'), 'ox')

        for i in (-2, 0, 2):
            self.assertEquals(hkutils.plural(i), 's')
            self.assertEquals(hkutils.plural(i, 'ox', 'oxen'), 'oxen')


if __name__ == '__main__':
    unittest.main()
