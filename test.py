#!/usr/bin/python

import unittest
import heapmanip
import test_heapmanip
import test_heapia

if __name__ == '__main__':
    heapmanip.set_log(False)
    suite1 = unittest.TestLoader().loadTestsFromModule(test_heapmanip)
    suite2 = unittest.TestLoader().loadTestsFromModule(test_heapia)
    suite = unittest.TestSuite([suite1, suite2])
    unittest.TextTestRunner(verbosity=0).run(suite)

