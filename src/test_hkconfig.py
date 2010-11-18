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

"""Tests the hkconfig module.

Usage:

    $ python src/test_hkconfig.py
"""


import unittest

import hkutils
import hkconfig


class Test__config(unittest.TestCase):

    """Tests the configuration objects."""

    def test__format_3(self):
        """Tests the following functions:

        - :func:`hkconfig:unify_format`
        - :func:`hkconfig:unify_format_3`
        - :func:`hkconfig:unify_str_to_str_dict`
        - :func:`hkconfig:unify_server`
        """

        # Specifying only the mandatory fields
        self.assertEqual(
             hkconfig.unify_config(
                 {'paths': {'html_dir': '-html_dir'},
                  'heaps': {'-heap': {'path': '-path'}}}),
             {'paths': {'html_dir': '-html_dir'},
              'heaps': {'-heap': {'path': '-path',
                                  'id': '-heap',
                                  'name': '-heap',
                                  'nicknames': {}}},
              'nicknames': {},
              'accounts': {}})

        # Specifying all fields
        self.assertEqual(
             hkconfig.unify_config(
                 {'paths': {'html_dir': '-html_dir'},
                  'heaps': {'-heap': {'path': '-path',
                                      'id': '-id',
                                      'name': '-name',
                                      'server': {'host': '-host2',
                                                 'port': '2222',
                                                 'imaps': 'true',
                                                 'username': '-user2',
                                                 'password': '-pw2'},
                                      'nicknames': {'a': 'b'}}},
                  'server': {'host': '-host',
                             'port': '1111',
                             'imaps': 'false',
                             'username': '-username',
                             'password': '-password'},
                  'nicknames': {'c': 'd'},
                  'accounts': {'user1': 'pass1',
                               'user2': 'pass2'}}),
             {'paths': {'html_dir': '-html_dir'},
              'heaps': {'-heap': {'path': '-path',
                                  'id': '-id',
                                  'name': '-name',
                                  'server': {'host': '-host2',
                                             'port': 2222,
                                             'imaps': 'true',
                                             'username': '-user2',
                                             'password': '-pw2'},
                                  'nicknames': {'a': 'b'}}},
              'server': {'host': '-host',
                         'port': 1111,
                         'imaps': 'false',
                         'username': '-username',
                         'password': '-password'},
              'nicknames': {'c': 'd'},
              'accounts': {'user1': 'pass1',
                           'user2': 'pass2'}})

        # Testing when server/password is not specified
        self.assertEqual(
             hkconfig.unify_config(
                 {'paths': {'html_dir': '-html_dir'},
                  'heaps': {'-heap': {'path': '-path'}},
                  'server': {'host': '-host',
                             'port': '1111',
                             'username': '-username'}}),
             {'paths': {'html_dir': '-html_dir'},
              'heaps': {'-heap': {'path': '-path',
                                  'id': '-heap',
                                  'name': '-heap',
                                  'nicknames': {}}},
              'server': {'host': '-host',
                         'port': 1111,
                         'username': '-username'},
              'nicknames': {},
              'accounts': {}})

        # Testing several heaps
        self.assertEqual(
             hkconfig.unify_config(
                 {'paths': {'html_dir': '-html_dir'},
                  'heaps': {'-heap1': {'path': '-path1'},
                            '-heap2': {'path': '-path2'}}}),
             {'paths': {'html_dir': '-html_dir'},
              'heaps': {'-heap1': {'path': '-path1',
                                   'id': '-heap1',
                                   'name': '-heap1',
                                   'nicknames': {}},
                        '-heap2': {'path': '-path2',
                                   'id': '-heap2',
                                   'name': '-heap2',
                                   'nicknames': {}}},
              'nicknames': {},
              'accounts': {}})

        # Testing several heaps
        self.assertRaises(
            KeyError,
            lambda: hkconfig.unify_config({}))


if __name__ == '__main__':
    hkutils.set_log(False)
    unittest.main()
