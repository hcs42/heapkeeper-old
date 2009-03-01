#!/usr/bin/python

from __future__ import with_statement
import unittest

from heaplib import *


class TestUtilities(unittest.TestCase):

    """Tests the utility functions of heapmanip."""

    def test_calc_timestamp(self):
        ts = calc_timestamp('Wed, 20 Aug 2008 17:41:30 +0200')
        self.assertEquals(ts, 1219246890.0)

    def test_HeapException(self):
        def f():
            raise HeapException, 'description'
        self.assertRaises(HeapException, f)

        try:
            raise HeapException, 'description'
        except HeapException, h:
            self.assertEquals(h.value, 'description')
            self.assertEquals(str(h), "'description'")


class TestOptionHandling(unittest.TestCase):

    def f(a, b, c=1, d=2):
        pass

    def test_arginfo(self):
        def f(a, b, c=1, d=2):
            pass
        self.assertEquals(arginfo(f), (['a', 'b'], {'c':1, 'd':2}))
        f2 = TestOptionHandling.f
        self.assertEquals(arginfo(f2), (['a', 'b'], {'c':1, 'd':2}))

    def test_set_defaultoptions(self):

        def f(other1, a, b=1, c=2, other2=None):
            pass

        options = {'a':0, 'b': 1}
        set_defaultoptions(options, f, ['other1', 'other2'])
        self.assertEquals(options, {'a':0, 'b':1, 'c':2})

        options = {'b': 1}
        def try_():
            set_defaultoptions(options, f, ['other1', 'other2'])
        self.assertRaises(HeapException, try_)

        options = {'a':0, 'b': 1, 'other': 2}
        def try_():
            set_defaultoptions(options, f, ['other1', 'other2'])
        self.assertRaises(HeapException, try_)


if __name__ == '__main__':
    unittest.main()
