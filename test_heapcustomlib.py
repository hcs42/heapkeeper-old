#!/usr/bin/python

"""Tests the heapmanip module.

Usage:
    
    python heapmaniptest.py
"""

import time
import unittest
import heapmanip
import test_heapmanip
from heapcustomlib import *


class Test1(unittest.TestCase, test_heapmanip.MailDBHandler):

    def setUp(self):
        self.setUpDirs()
        self._maildb = self.createMailDB()
        self.create_threadst()

    def tearDown(self):
        self.tearDownDirs()

    def test_format_date(self):

        options = date_defopts({'localtime_fun': time.gmtime})
        self.assertEquals(format_date(self._posts[0], options), '(2008.08.20.)')

        options['date_format'] = '%Y.%m.%d. %H:%M:%S'
        self.assertEquals(
            format_date(self._posts[0], options),
            '2008.08.20. 15:41:00')

    def test_create_should_print_date_fun(self):

        genopts = heapmanip.GeneratorOptions()
        genopts.sections = [heapmanip.Section('', self._maildb.all())]
        genopts.section = genopts.sections[0]

        # date options
        options = date_defopts({'maildb': self._maildb,
                                'timedelta': datetime.timedelta(seconds=3)})
        f = create_should_print_date_fun(options)

        # Dates for post 0 and 4 has to be printed, because they do not have a
        # parent
        self.assertEquals(f(self._posts[0], genopts), True)
        self.assertEquals(f(self._posts[4], genopts), True)

        # Date for post 3 has to be printed, because its parent is much older
        # (much=4 seconds, but the 'timedelta' is 3)
        self.assertEquals(f(self._posts[3], genopts), True)

        # Dates for post 1 and 2 should not be printed, because they have
        # parents who are not much older than them
        self.assertEquals(f(self._posts[1], genopts), False)
        self.assertEquals(f(self._posts[2], genopts), False)

        # Flat genopts: all date has to be printed
        genopts.section.is_flat = True
        self.assertEquals(f(self._posts[0], genopts), True)
        self.assertEquals(f(self._posts[1], genopts), True)
        self.assertEquals(f(self._posts[2], genopts), True)
        self.assertEquals(f(self._posts[3], genopts), True)
        self.assertEquals(f(self._posts[4], genopts), True)

    def test_create_date_fun(self):

        genopts = heapmanip.GeneratorOptions()
        genopts.sections = [heapmanip.Section('', self._maildb.all())]
        genopts.section = genopts.sections[0]

        def my_should_fun(post, genopts):
            return post.heapid() in ['1', '3']
        # date options
        options = date_defopts({'maildb': self._maildb,
                                'should_print_date_fun': my_should_fun})
        f = create_date_fun(options)

        self.assertEquals(f(self._posts[0], genopts), None)
        self.assertNotEquals(f(self._posts[1], genopts), None)
        self.assertEquals(f(self._posts[2], genopts), None)
        self.assertNotEquals(f(self._posts[3], genopts), None)
        self.assertEquals(f(self._posts[4], genopts), None)

if __name__ == '__main__':
    heapmanip.set_log(False)
    unittest.main()
