#!/usr/bin/python

"""Tests the heapmanip module.

Usage:
    
    python heapmaniptest.py
"""

from __future__ import with_statement
import unittest

import heapmanip
import test_heapmanip
import heapia

class Test1(unittest.TestCase, test_heapmanip.MailDBHandler):

    """Tests XXX."""

    # Thread structure:
    # 0 <- 1 <- 2
    #   <- 3
    # 4

    def setUp(self):
        self.setUpDirs()
        self._maildb = self.createMailDB()
        self.create_threadst()

    def test1(self):
        pass

    def tearDown(self):
        self.tearDownDirs()

if __name__ == '__main__':
    heapmanip.set_log(False)
    unittest.main()
