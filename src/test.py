#!/usr/bin/env python

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

    $ python src/test.py

It can be used to run a specific test:

    $ python src/test.py test_hklib TestPostDB2 testThreadstructCycle1
"""

import os
import sys
import unittest

import hkutils


def collect_testmodules_from_dir(dir):
    """Collects the list of modules that are test modules from a given
    directory.

    **Returns:** [str]
    """

    testmodules = []
    for filename in os.listdir(dir):
        if filename.startswith('test_') and filename.endswith('.py'):
            testmodules.append(filename[:-3])
    return testmodules

def collect_testmodules():
    """Collects the list of modules that are test modules.

    **Returns:** [str]
    """

    return [testmodule
            for src_dir in ['src'] + hkutils.plugin_src_dirs()
            for testmodule in collect_testmodules_from_dir(src_dir)]


def main(args):

    hkutils.set_log(False)
    if len(args) > 0 and args[0] in ['-h', '--help']:
        sys.stdout.write(__doc__)
    elif args == []:
        testmodules = collect_testmodules()
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
    if not os.path.isfile(os.path.join('src', 'test.py')):
        hkutils.log('Error: You are not in the Heapkeeper main directory.')
        sys.exit(1)
    main(sys.argv[1:])
