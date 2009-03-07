#!/usr/bin/python

from __future__ import with_statement
import unittest

import heaplib


class TestUtilities(unittest.TestCase):

    """Tests the utility functions of heapmanip."""

    def test_calc_timestamp(self):
        ts = heaplib.calc_timestamp('Wed, 20 Aug 2008 17:41:30 +0200')
        self.assertEquals(ts, 1219246890.0)

    def test_HeapException(self):
        def f():
            raise heaplib.HeapException, 'description'
        self.assertRaises(heaplib.HeapException, f)

        try:
            raise heaplib.HeapException, 'description'
        except heaplib.HeapException, h:
            self.assertEquals(h.value, 'description')
            self.assertEquals(str(h), "'description'")


class TestOptionHandling(unittest.TestCase):

    def f(a, b, c=1, d=2):
        pass

    def test_arginfo(self):
        def f(a, b, c=1, d=2):
            pass
        self.assertEquals(heaplib.arginfo(f), (['a', 'b'], {'c':1, 'd':2}))
        f2 = TestOptionHandling.f
        self.assertEquals(heaplib.arginfo(f2), (['a', 'b'], {'c':1, 'd':2}))

    def test_set_defaultoptions(self):

        def f(other1, a, b=1, c=2, other2=None):
            pass

        options = {'a':0, 'b': 1}
        heaplib.set_defaultoptions(options, f, ['other1', 'other2'])
        self.assertEquals(options, {'a':0, 'b':1, 'c':2})

        options = {'b': 1}
        def try_():
            heaplib.set_defaultoptions(options, f, ['other1', 'other2'])
        self.assertRaises(heaplib.HeapException, try_)

        options = {'a':0, 'b': 1, 'other': 2}
        def try_():
            heaplib.set_defaultoptions(options, f, ['other1', 'other2'])
        self.assertRaises(heaplib.HeapException, try_)

    def test_set_dict_items(self):
        class A:
            pass
        a = A()
        d = {'self': 0, 'something': 1}
        heaplib.set_dict_items(a, d)
        self.assertEquals(a.something, 1)

        def f():
            a.self
        self.assertRaises(AttributeError, f)

if __name__ == '__main__':
    unittest.main()
