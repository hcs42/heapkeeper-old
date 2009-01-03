#!/usr/bin/python

import StringIO
import unittest

from heapmanip import *

class TestMail(unittest.TestCase):

    def setUp(self):
        self.expl_header_1 = '''\
From: author
Subject: subject
Flag: flag1
Message-Id: <0@gmail.com>
Flag: flag2
Date: Wed, 20 Aug 2008 17:41:30 +0200'''
        self.expl_header_2 = self.expl_header_1 + '\n'

    def _testParseHeaders(self, s):
        sio = StringIO.StringIO(s)
        m = Mail('0')
        h1 = Mail.parse_headers(sio)
        self.assertEquals(h1, {'From': ['author'],
                               'Subject': ['subject'],
                               'Message-Id': ['<0@gmail.com>'],
                               'Date': ['Wed, 20 Aug 2008 17:41:30 +0200'],
                               'Flag': ['flag1', 'flag2']})
        h2 = Mail.create_headers(h1)
        self.assertEquals(h2, {'From': 'author',
                               'Subject': 'subject',
                               'Message-Id': '<0@gmail.com>',
                               'In-Reply-To': '',
                               'Date': 'Wed, 20 Aug 2008 17:41:30 +0200',
                               'Flag': ['flag1', 'flag2'],
                               'Tag': []})

        m.set_headers(h2)
        self.assertEquals(m.get_author(), 'author')
        self.assertEquals(m.get_subject(), 'subject')
        self.assertEquals(m.get_messid(), '<0@gmail.com>')
        self.assertEquals(m.get_inreplyto(), '')
        self.assertEquals(m.get_date(), 'Wed, 20 Aug 2008 17:41:30 +0200')
        self.assertEquals(m.get_deleted(), False)

    def testParseHeaders(self):
        self._testParseHeaders(self.expl_header_1)
        self._testParseHeaders(self.expl_header_2)

    def testDump(self):
        m = Mail('0')
        sio1 = StringIO.StringIO(self.expl_header_2)
        m.set_headers(Mail.create_headers(Mail.parse_headers(sio1)))
        m.set_body('x\n')
        sio2 = StringIO.StringIO()
        m.dump(sio2)
        self.assertEquals(sio2.getvalue(),
'''From: author
Subject: subject
Message-Id: <0@gmail.com>
Date: Wed, 20 Aug 2008 17:41:30 +0200
Flag: flag1
Flag: flag2

x
''')

if __name__ == '__main__':
    unittest.main()
