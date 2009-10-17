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

"""Executes the unit tests on Heapkeeper.

If executed without arguments, it runs all tests:

    $ python test.py

It can be used to run a specific test:

    $ python test.py test_hklib TestPostDB2 testThreadstructCycle1
"""


import sys
import unittest

import hklib


testmodules = ['test_hkutils',
               'test_hklib',
               'test_hkshell',
               'test_hkcustomlib']

def main(args):
    hklib.set_log(False)
    if args in [['-h'], '--help']:
        sys.stdout.write(__doc__)
    elif args == []:
        suites = \
            [ unittest.TestLoader().loadTestsFromModule(__import__(modname))
              for modname in testmodules ]
        suite = unittest.TestSuite(suites)
        unittest.TextTestRunner(verbosity=0).run(suite)
    elif len(args) == 3:
        modname, testcasename, funname = args
        suite = unittest.TestSuite()
        testcase = getattr(__import__(modname), testcasename)
        suite.addTest(testcase(funname))
        unittest.TextTestRunner(verbosity=0).run(suite)
    else:
        print 'Incorrect arguments.\n' \
              'Run "python test.py --help" for help.'

if __name__ == '__main__':
    main(sys.argv[1:])
