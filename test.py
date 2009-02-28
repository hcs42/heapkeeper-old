#!/usr/bin/python

"""test.py: tests the Heapmanipulator.

If executed without arguments, it runs all tests:

    $ python test.py

It can be used to run a specific test:

    $ python test.py test_heapmanip TestMailDB2 testThreadstructCycle1
"""

import sys
import unittest
import heapmanip

testmodules = ['test_heapmanip', 'test_heapia', 'test_heapcustomlib']

def main(args):
    heapmanip.set_log(False)
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
