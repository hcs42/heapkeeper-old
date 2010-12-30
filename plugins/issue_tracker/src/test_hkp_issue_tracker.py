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

# Copyright (C) 2010 Csaba Hoch

"""Tests the hkp_issue_tracker module."""


from __future__ import with_statement

import unittest

import hkutils
import hkp_issue_tracker
import test_hkgen
import test_hkweb


class Test_BaseITGenerator(object):

    def test_write_main_index_page(self):
        # This test case would fail because of issue heap://hh/699
        pass

class Test_StaticITGenerator(Test_BaseITGenerator,
                             test_hkgen.Test_StaticGenerator):

    """Tests |StaticITGenerator|."""

    def create_generator(self):
        """Returns a generator object to be used for the testing.

        **Returns:** |StaticITGenerator|
        """

        return hkp_issue_tracker.StaticITGenerator(self._postdb, 'my_heap')


class Test_WebITGenerator(Test_BaseITGenerator,
                          test_hkweb.Test_WebGenerator):

    """Tests |WebITGenerator|."""

    def create_generator(self):
        """Returns a generator object to be used for the testing.

        **Returns:** |WebGenerator|
        """

        return hkp_issue_tracker.WebITGenerator(self._postdb, 'my_heap')


if __name__ == '__main__':
    hkutils.set_log(False)
    unittest.main()
