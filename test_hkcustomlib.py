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

"""Tests the hklib module.

Usage:

    $ python test_hklib.py
"""

import time
import unittest
import hklib
import test_hklib
from hkcustomlib import *


class Test__1(unittest.TestCase, test_hklib.PostDBHandler):

    def setUp(self):
        self.setUpDirs()
        self._postdb = self.createPostDB()
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

        genopts = hklib.GeneratorOptions()
        genopts.sections = [hklib.Section('', self._postdb.all())]
        genopts.section = genopts.sections[0]

        # date options
        options = date_defopts({'postdb': self._postdb,
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

        genopts = hklib.GeneratorOptions()
        genopts.sections = [hklib.Section('', self._postdb.all())]
        genopts.section = genopts.sections[0]

        def my_should_fun(post, genopts):
            return post.heapid() in ['1', '3']
        # date options
        options = date_defopts({'postdb': self._postdb,
                                'should_print_date_fun': my_should_fun})
        f = create_date_fun(options)

        self.assertEquals(f(self._posts[0], genopts), None)
        self.assertNotEquals(f(self._posts[1], genopts), None)
        self.assertEquals(f(self._posts[2], genopts), None)
        self.assertNotEquals(f(self._posts[3], genopts), None)
        self.assertEquals(f(self._posts[4], genopts), None)

if __name__ == '__main__':
    hklib.set_log(False)
    unittest.main()
