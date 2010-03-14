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


import datetime
import time
import unittest

import hklib
import hkcustomlib
import test_hklib


class Test__1(unittest.TestCase, test_hklib.PostDBHandler):

    def setUp(self):
        self.setUpDirs()
        self.create_postdb()
        self.create_threadst()

    def tearDown(self):
        self.tearDownDirs()

    def test_editor_to_editor_list(self):

        """Tests :func:`hkcustomlib.editor_to_editor_list`."""

        def check(input, output):
            self.assertEqual(
                hkcustomlib.editor_to_editor_list(input),
                output)

        check('vim', ['vim'])
        check('vim arg', ['vim', 'arg'])
        check('vim arg1 arg2', ['vim', 'arg1', 'arg2'])
        check(' vim  arg1  arg2 ', ['vim', 'arg1', 'arg2'])
        check(r'vim long\ argument', ['vim', 'long argument'])
        check(r'vim argument\\with\\backspace',
              ['vim', r'argument\with\backspace'])

        # Incorrect editor variables

        self.assertRaises(
            hkcustomlib.IncorrectEditorException,
            lambda: hkcustomlib.editor_to_editor_list('vim\\'))

        self.assertRaises(
            hkcustomlib.IncorrectEditorException,
            lambda: hkcustomlib.editor_to_editor_list('vim \\x'))

if __name__ == '__main__':
    hklib.set_log(False)
    unittest.main()
