#!/usr/bin/python

"""Tests the heapia module.

Usage:
    
    python heapiatest.py
"""

from __future__ import with_statement
import unittest

import heaplib
import heapmanip
import test_heapmanip
import heapia

class Test1(unittest.TestCase, test_heapmanip.MailDBHandler):

    """Tests the heapia module."""

    # Thread structure:
    # 0 <- 1 <- 2
    #   <- 3
    # 4

    def setUp(self):
        self.setUpDirs()
        self._maildb = self.createMailDB()
        self.create_threadst()
        heapia.set_option('auto_gen_var', False)
        heapia.set_option('auto_save', False)
        heapia.set_option('auto_threadstruct', False)
        heapia.set_option('maildb', self._maildb)

    def tearDown(self):
        self.tearDownDirs()

    def test_h(self):
        heapia.cmd_help()

    def test_tagset(self):
        def test(pretagset, tagset):
            self.assertEquals(heapia.tagset(pretagset), tagset)
        test('t', set(['t']))
        test('t1', set(['t1']))
        test(['t'], set(['t']))
        test(['t1', 't2'], set(['t1', 't2']))
        test(set(['t']), set(['t']))
        test(set(['t1', 't2']), set(['t1', 't2']))

        def f():
            heapia.tagset(0)
        self.assertRaises(heaplib.HeapException, f)

    def tags(self):
        return [ self._posts[i].tags() for i in range(5) ]

    def test_pt_1(self):
        self.assertEquals(self.tags(), [[],[],[],[],[]])
        self._posts[1].add_tag('t')
        self.assertEquals(self.tags(), [[],['t'],[],[],[]])
        heapia.pt(1)
        self.assertEquals(self.tags(), [[],['t'],['t'],[],[]])

    def test_pt_2(self):
        self._posts[0].add_tag('t1')
        self._posts[1].add_tag('t2')
        heapia.pt(0)
        self.assertEquals(self.tags(), [['t1'],['t1','t2'],['t1'],['t1'],[]])

    def test_pt_3(self):
        self._posts[0].add_tag('t1')
        self._posts[0].add_tag('t2')
        heapia.pt(0)
        t = ['t1', 't2']
        self.assertEquals(self.tags(), [t, t, t, t, []])

if __name__ == '__main__':
    heapmanip.set_log(False)
    unittest.main()
