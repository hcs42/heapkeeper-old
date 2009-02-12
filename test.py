#!/usr/bin/python
"""
Tests the Heapmanipulator.

If executed without arguments, it runs all tests:

    python test.py

It can be used to run a specific test:

    python test.py test_heapmanip TestMailDB2 testThreadstructCycle1
"""

import sys
import unittest
import heapmanip
import test_heapmanip
import test_heapia

if __name__ == '__main__':
    args = sys.argv[1:]
    heapmanip.set_log(False)
    if args == []:
        suite1 = unittest.TestLoader().loadTestsFromModule(test_heapmanip)
        suite2 = unittest.TestLoader().loadTestsFromModule(test_heapia)
        suite = unittest.TestSuite([suite1, suite2])
    elif len(args) == 3:
        modname, testcasename, funname = args
        suite = unittest.TestSuite()
        testcase = getattr(__import__(modname), testcasename)
        suite.addTest(testcase(funname))
    unittest.TextTestRunner(verbosity=0).run(suite)

