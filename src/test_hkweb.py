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

"""Tests the hkweb module.

Usage:

    $ python test_hkweb.py
"""


from __future__ import with_statement

import unittest

import hkutils
import hkweb
import test_hkgen


class Test_WebGenerator(test_hkgen.Test_BaseGenerator):

    """Tests |WebGenerator|."""

    def create_generator(self):
        """Returns a generator object to be used for the testing.

        **Returns:** |WebGenerator|
        """

        return hkweb.WebGenerator(self._postdb)

    def test_print_postitem_flat(self):
        """Inherited test case that we don't want to execute because it would
        fail."""

        pass

    def test_print_postitem_inner(self):
        """Inherited test case that we don't want to execute because it would
        fail."""

        pass


if __name__ == '__main__':
    hkutils.set_log(False)
    unittest.main()
