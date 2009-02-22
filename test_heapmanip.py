#!/usr/bin/python

"""Tests the heapmanip module.

Usage:
    
    python heapmaniptest.py
"""

from __future__ import with_statement
import StringIO
import unittest
import tempfile
import os
import os.path
import ConfigParser
import re

from heapmanip import *


class MailDBHandler(object):

    """A class that helps implementing the tester classes by containing
    functions commonly used by them."""
    
    # Creating an ordered array of dates.
    dates = [ 'Date: Wed, 20 Aug 2008 17:41:0%d +0200\n' % i \
              for i in range(6) ]

    def setUpDirs(self):
        self._dir = tempfile.mkdtemp()
        self._postfile_dir = os.path.join(self._dir, 'mail')
        self._html_dir = os.path.join(self._dir, 'html')
        os.mkdir(self._postfile_dir)
        os.mkdir(self._html_dir)

    def tearDownDirs(self):
        shutil.rmtree(self._dir)

    def createMailDB(self):
        return MailDB(self._postfile_dir, self._html_dir)

    def postFileName(self, fname):
        return os.path.join(self._postfile_dir, fname)

    def add_post(self, index, inreplyto=None):
        """Adds a new post to maildb."""
        messid = str(index) + '@'
        inreplyto = str(inreplyto) + '@' if inreplyto != None else ''
        s = ('From: author%s\n' % (index,) +
             'Subject: subject%s\n' % (index,) +
             'Message-Id: %s\n' % (messid,) +
             'In-Reply-To: %s\n' % (inreplyto,))
        if not self._skipdates:
            s += MailDBHandler.dates[index]
        self._maildb.add_new_post(Post.from_str(s))

    def create_threadst(self, skipdates=False):
        """Adds a thread structure to the maildb with the following structure.

        0 <- 1 <- 2
          <- 3
        4
        """

        self._skipdates = skipdates
        self.add_post(0)
        self.add_post(1, 0)
        self.add_post(2, 1)
        self.add_post(3, 0)
        self.add_post(4)
        self._posts = [ self._maildb.post(str(i)) for i in range(5) ]


class TestUtilities(unittest.TestCase):

    """Tests the utility functions of heapmanip."""

    def test_calc_timestamp(self):
        ts = calc_timestamp('Wed, 20 Aug 2008 17:41:30 +0200')
        self.assertEquals(ts, 1219246890.0)

    def test_HeapException(self):
        def f():
            raise HeapException, 'description'
        self.assertRaises(HeapException, f)

        try:
            raise HeapException, 'description'
        except HeapException, h:
            self.assertEquals(h.value, 'description')
            self.assertEquals(str(h), "'description'")


class TestOptionHandling(unittest.TestCase):

    def f(a, b, c=1, d=2):
        pass

    def test_arginfo(self):
        def f(a, b, c=1, d=2):
            pass
        self.assertEquals(arginfo(f), (['a', 'b'], {'c':1, 'd':2}))
        f2 = TestOptionHandling.f
        self.assertEquals(arginfo(f2), (['a', 'b'], {'c':1, 'd':2}))

    def test_set_defaultoptions(self):

        def f(other1, a, b=1, c=2, other2=None):
            pass

        options = {'a':0, 'b': 1}
        set_defaultoptions(options, f, ['other1', 'other2'])
        self.assertEquals(options, {'a':0, 'b':1, 'c':2})

        options = {'b': 1}
        def try_():
            set_defaultoptions(options, f, ['other1', 'other2'])
        self.assertRaises(HeapException, try_)

        options = {'a':0, 'b': 1, 'other': 2}
        def try_():
            set_defaultoptions(options, f, ['other1', 'other2'])
        self.assertRaises(HeapException, try_)

# global strings for tests

post1_text = '''\
From: author
Subject: subject
Flag: flag1
Message-Id: <0@gmail.com>
Flag: flag2
Date: Wed, 20 Aug 2008 17:41:30 +0200'''

post2_text = post1_text + '\n'
post3_text = post1_text + '\n\n'
post4_text = post1_text + '\n\nHi'
post5_text = post1_text + '\n\nHi\n'
post6_text = post1_text + '\n\nHi\n\n\n'

post1_dict1 = {'From': ['author'],
               'Subject': ['subject'],
               'Message-Id': ['<0@gmail.com>'],
               'Date': ['Wed, 20 Aug 2008 17:41:30 +0200'],
               'Flag': ['flag1', 'flag2']}

post1_dict2 = {'From': 'author',
               'Subject': 'subject',
               'Message-Id': '<0@gmail.com>',
               'In-Reply-To': '',
               'Date': 'Wed, 20 Aug 2008 17:41:30 +0200',
               'Flag': ['flag1', 'flag2'],
               'Tag': []}

post_output = '''\
From: author
Subject: subject
Message-Id: <0@gmail.com>
Date: Wed, 20 Aug 2008 17:41:30 +0200
Flag: flag1
Flag: flag2

'''

post1_output = post_output + '\n'
post4_output = post_output + 'Hi\n'


class TestPost1(unittest.TestCase):

    """Tests the Post class."""

    def testParsing(self):

        sio = StringIO.StringIO(post1_text)
        self.assertEquals(Post.parse_header(sio), post1_dict1)
        sio.close()

        sio = StringIO.StringIO(post2_text)
        self.assertEquals(Post.parse_header(sio), post1_dict1)
        sio.close()

    def testEmpty(self):
        p = Post.from_str('')
        self.assertEquals(p.heapid(), None)
        self.assertEquals(p.author(), '')
        self.assertEquals(p.subject(), '')
        self.assertEquals(p.messid(), '')
        self.assertEquals(p.inreplyto(), '')
        self.assertEquals(p.date(), '')
        self.assertEquals(p.is_deleted(), False)
        self.assertEquals(p.is_modified(), True)
        self.assertEquals(p.body(), '\n')
        p2 = Post.create_empty()
        self.assertEquals(p, p2)

    def testInit(self):
        p = Post.from_str(post4_text)

        # testing initialisation
        self.assertEquals(p.heapid(), None)
        self.assertEquals(p.author(), 'author')
        self.assertEquals(p.subject(), 'subject')
        self.assertEquals(p.messid(), '<0@gmail.com>')
        self.assertEquals(p.inreplyto(), '')
        self.assertEquals(p.date(), 'Wed, 20 Aug 2008 17:41:30 +0200')
        self.assertEquals(p.is_deleted(), False)
        self.assertEquals(p.is_modified(), True)
        self.assertEquals(p.body(), 'Hi\n')

        # testing modification
        p.set_author('author2')
        self.assertEquals(p.author(), 'author2')

        p.set_subject('subject2')
        self.assertEquals(p.subject(), 'subject2')

        p.set_messid('@')
        self.assertEquals(p.messid(), '@')

        p.set_inreplyto('@@')
        self.assertEquals(p.inreplyto(), '@@')

        p.set_date('Wed, 20 Aug 2008 17:41:31 +0200')
        self.assertEquals(p.date(), \
                          'Wed, 20 Aug 2008 17:41:31 +0200')

        p.set_body('newbody')
        self.assertEquals(p.body(), 'newbody\n')
        p.set_body('\n newbody \n \n')
        self.assertEquals(p.body(), 'newbody\n')

        p.delete()
        self.assertEquals(p.is_deleted(), True)

    def testWrite(self):

        def check_write(input, output):
            """Checks that if a post is read from input, it will produce
            output when written."""
            p = Post.from_str(input)
            sio2 = StringIO.StringIO()
            p.write(sio2)
            self.assertEquals(sio2.getvalue(), output)
            sio2.close()

        check_write(post1_text, post1_output)
        check_write(post4_text, post4_output)

    def testBodyStripping(self):
        p1 = Post.from_str(post1_text)
        p2 = Post.from_str(post2_text)
        p3 = Post.from_str(post3_text)
        p4 = Post.from_str(post4_text)
        p5 = Post.from_str(post5_text)
        p6 = Post.from_str(post6_text)

        # p1 == p2 == p3 != p4 == p5 == p6
        self.assertEquals(p1, p2)
        self.assertEquals(p1, p3)
        self.assertNotEquals(p1, p4)
        self.assertEquals(p4, p5)
        self.assertEquals(p4, p6)

    def testSubject(self):
        def post_ws(subject):
            """Creates a post with the given subject."""
            return Post.from_str('Subject: ' + subject)

        # testing whitespace handling
        self.assertEquals(post_ws('subject').real_subject(), 'subject')
        self.assertEquals(post_ws(' subject ').real_subject(), ' subject ')
        self.assertEquals(post_ws('1\n 2').real_subject(), '1\n2')
        self.assertEquals(post_ws(' 1 \n  2 ').real_subject(), ' 1 \n 2 ')

        # testing removing the "Re:" prefix
        l = [post_ws('subject'),
             post_ws(' subject '),
             post_ws('Re: subject'),
             post_ws('re: subject'),
             post_ws('Re:subject'),
             post_ws('re:subject')]
        for p in l:
            self.assertEquals(p.subject(), 'subject')

    def testTagsFlags(self):

        p = Post.from_str('Flag: f1\nFlag: f2\nTag: t1\nTag: t2')
        self.assertEquals(p.flags(), ['f1', 'f2'])
        self.assertEquals(p.tags(), ['t1', 't2'])
        self.assertEquals(p.has_tag('t1'), True)
        self.assertEquals(p.has_tag('t2'), True)

        # They cannot be modified via the get methods
        #p.flags()[0] = ''
        #p.tags()[0] = ''
        #self.assertEquals(p.flags(), ['f1', 'f2'])
        #self.assertEquals(p.tags(), ['t1', 't2'])

        # Iterator
        l = []
        for tag in p.tags():
            l.append(tag)
        self.assertEquals(l, ['t1', 't2'])

        # Set methods
        p.set_flags(['f'])
        self.assertEquals(p.flags(), ['f'])
        p.set_tags(['t'])
        self.assertEquals(p.tags(), ['t'])
        self.assertEquals(p.has_tag('t'), True)
        self.assertEquals(p.has_tag('t1'), False)
        self.assertEquals(p.has_tag('t2'), False)

        # Sorting
        p = Post.from_str('Flag: f2\nFlag: f1\nTag: t2\nTag: t1')
        self.assertEquals(p.flags(), ['f1', 'f2']) # flags are sorted
        self.assertEquals(p.tags(), ['t1', 't2'])  # tags are sorted

    def testParseTagsInSubject(self):

        def test(subject1, subject2, tags):
            self.assertEquals((subject2, tags), Post.parse_subject(subject1))

        test('', '', [])
        test('Subject',              'Subject', [])
        test('[a]Subject',           'Subject', ['a'])
        test('[a]',                  '', ['a'])
        test('[a] ',                 '', ['a'])
        test(' [ab] Subject ',       'Subject', ['ab'])
        test('[a][b]Subject',        'Subject', ['a', 'b'])
        test(' [ a ] [ b ] Subject', 'Subject', ['a', 'b'])
        test('Sub[c]ject',           'Sub[c]ject', [])
        test('[a][b]Sub[c]ject',     'Sub[c]ject', ['a', 'b'])
        test(' [a] [b] Sub [c] ject','Sub [c] ject', ['a', 'b'])

        p = Post.from_str('Subject: [t1][t2] subject\nTag: t3')
        p.normalize_subject()
        self.assertEquals(p.subject(), 'subject')
        self.assertEquals(p.tags(), ['t3', 't1', 't2'])


class TestPost2(unittest.TestCase):

    """Tests the Post class.

    The test functions in this class perform file operations."""

    def setUp(self):
        self._dir = tempfile.mkdtemp()

    def testFromFile(self):
        fname = os.path.join(self._dir, 'postfile')
        string_to_file(post1_text, fname)
        p = Post.from_file(fname)

        self.assertEquals(p.heapid(), None)
        self.assertEquals(p.author(), 'author')
        self.assertEquals(p.subject(), 'subject')
        self.assertEquals(p.messid(), '<0@gmail.com>')
        self.assertEquals(p.inreplyto(), '')
        self.assertEquals(p.date(), 'Wed, 20 Aug 2008 17:41:30 +0200')
        self.assertEquals(p.is_deleted(), False)
        self.assertEquals(p.is_modified(), True)
        self.assertEquals(p.body(), '\n')

    def tearDown(self):
        shutil.rmtree(self._dir)


class TestMailDB1(unittest.TestCase, MailDBHandler):

    """Tests the MailDB class (and its cooperation with the Post class)."""

    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self._postfile_dir = os.path.join(self._dir, 'mail')
        self._html_dir = os.path.join(self._dir, 'html')

    def createDirs(self):
        os.mkdir(self._postfile_dir)
        os.mkdir(self._html_dir)

    def postFileName(self, fname):
        return os.path.join(self._postfile_dir, fname)

    def testEmpty(self):
        """Tests the empty MailDB."""
        maildb = self.createMailDB()
        self.assert_(os.path.exists(self._postfile_dir))
        self.assertEquals(maildb.postfile_dir(), self._postfile_dir)
        self.assertEquals(maildb.html_dir(), self._html_dir)
        self.assertEquals(maildb.heapids(), [])

    def testOnlyMail(self):
        """Tests that only the files with ".mail" postfix are read."""
        self.createDirs()
        string_to_file('Subject: s1', self.postFileName('1.mail'))
        string_to_file('Subject: sx', self.postFileName('xy.mail'))
        string_to_file('Subject: s2', self.postFileName('2.other'))
        string_to_file('Subject: s3', self.postFileName('3mail'))
        maildb = self.createMailDB()
        self.assertEquals(set(maildb.heapids()), set(['1', 'xy']))
        self.assertEquals(maildb.next_heapid(), '2')

    def testConfig(self):
        """Tests the MailDB.__init__ which has a ConfigParser argument."""
        self.createDirs()
        string_to_file('Subject: s1', self.postFileName('1.mail'))
        configFileText = '''\
[paths]
mail=%s
html=%s
''' % (self._postfile_dir, self._html_dir)
        configFileName = os.path.join(self._dir, 'heap.cfg')
        string_to_file(configFileText, configFileName)
        config = ConfigParser.ConfigParser()
        config.read(configFileName)
        maildb = MailDB.from_config(config)
        self.assertEquals(set(maildb.heapids()), set(['1']))

    def testGetMethods(self):
        """Tests the 'get' methods of MailDB."""
        self.createDirs()
        string_to_file('Message-Id: mess1', self.postFileName('1.mail'))
        string_to_file('Message-Id: mess2', self.postFileName('2.mail'))
        maildb = self.createMailDB()
        self.assertEquals(set(maildb.heapids()), set(['1', '2']))
        self.assertEquals(maildb.next_heapid(), '3')
        self.assertEquals(maildb.next_heapid(), '4')
        p1 = maildb.post('1')
        p2 = maildb.post('2')
        self.assertEquals(set([p1, p2]), set(maildb.posts()))
        self.assert_(p1 is maildb.post_by_messid('mess1'))
        self.assert_(p2 is maildb.post_by_messid('mess2'))

    def testModifications(self):
        """Tests the 'set' methods of MailDB."""

        # Initialisation
        self.createDirs()
        postfile1 = self.postFileName('1.mail')
        postfile2 = self.postFileName('2.mail')
        string_to_file('Message-Id: mess1', postfile1)
        string_to_file('Message-Id: mess2', postfile2)
        maildb = self.createMailDB()
        p1 = maildb.post('1')
        p2 = maildb.post('2')

        # Modifying and saving a post
        p1.set_subject('subject')
        self.assertEquals('Message-Id: mess1', file_to_string(postfile1))
        self.assertEquals('Message-Id: mess2', file_to_string(postfile2))
        maildb.save()
        postfile1_str = 'Subject: subject\nMessage-Id: mess1\n\n\n'
        self.assertEquals(postfile1_str, file_to_string(postfile1))
        self.assertEquals('Message-Id: mess2', file_to_string(postfile2))
        
        # Adding a new post
        postfile3 = self.postFileName('3.mail')
        p3 = Post.from_str('Subject: subject3')
        maildb.add_new_post(p3)
        self.assertEquals(set(maildb.heapids()), set(['1', '2', '3']))
        self.assertFalse(os.path.exists(postfile3))
        maildb.save()
        self.assert_(os.path.exists(postfile3))

        # Deleting a post
        self.assertEquals(set([p1, p2, p3]), set(maildb.posts()))
        self.assertEquals(set([p1, p2, p3]), set(maildb.real_posts()))
        p1.delete()
        self.assertEquals(set([p2, p3]), set(maildb.posts()))
        self.assertEquals(set([p1, p2, p3]), set(maildb.real_posts()))

    def testThreadstructHeapid(self):
        """Testing that the thread structure also works when the In-Reply-To
        is defined by a heapid.
        
        If the same messid and heapid exist, the former has priority."""

        # 1 <- 2
        # 3
        # 4 <- 5
        self.createDirs()
        maildb = self.createMailDB()
        maildb.add_new_post(Post.from_str(''))               # #0
        maildb.add_new_post(Post.from_str('In-Reply-To: 0')) # #1
        maildb.add_new_post(Post.from_str(''))               # #2
        maildb.add_new_post(Post.from_str('Message-Id: 2'))  # #3
        maildb.add_new_post(Post.from_str('In-Reply-To: 2')) # #4

        ts = {None: ['0', '2', '3'],
              '0': ['1'],
              '3': ['4']}
        self.assertEquals(ts, maildb.threadstruct())

    def tearDown(self):
        shutil.rmtree(self._dir)


class TestMailDB2(unittest.TestCase, MailDBHandler):

    def setUp(self):
        self.setUpDirs()
        self._maildb = self.createMailDB()
        self.create_threadst()

    def testThreadstruct(self):
        """Tests the thread structure computing method."""

        maildb = self._maildb
        # Testing MailDB.threadstruct

        ts = {None: ['0', '4'],
              '0': ['1', '3'],
              '1': ['2']}
        self.assertEquals(ts, maildb.threadstruct())

        # Modifying the MailDB
        self.add_post(5, 0)
        ts = {None: ['0', '4'],
              '0': ['1', '3', '5'],
              '1': ['2']}
        self.assertEquals(ts, maildb.threadstruct())

        # Deleting a post
        maildb.post('1').delete()
        ts = {None: ['0', '2', '4'],
              '0': ['3', '5']}
        self.assertEquals(ts, maildb.threadstruct())

        maildb.post('0').delete()
        ts = {None: ['2', '3', '4', '5']}
        self.assertEquals(ts, maildb.threadstruct())

        maildb.post('2').delete()
        maildb.post('3').delete()
        maildb.post('4').delete()
        maildb.post('5').delete()
        ts = {None: []}
        self.assertEquals(ts, maildb.threadstruct())

    def testIterThread(self):
        """Tests the MailDB.iter_thread method."""
        maildb = self._maildb
        p = self._posts

        def test(post, result):
            self.assertEquals(result, \
                              [ p.heapid() for p in maildb.iter_thread(post)])

        test(None, ['0', '1', '2', '3', '4'])
        test(p[0], ['0', '1', '2', '3'])
        test(p[1], ['1', '2'])
        test(p[2], ['2'])
        test(p[3], ['3'])
        test(p[4], ['4'])

        # if the post is not in the maildb, AssertionError will be raised
        def f():
            test(Post.from_str(''), [])
        self.assertRaises(AssertionError, f)
    
    def testPrev(self):
        """Tests the 'prev' method."""
        maildb = self._maildb

        def test(post_heapid, prev_heapid):
            if prev_heapid != None:
                prev_post = maildb.post(prev_heapid)
            else:
                prev_post = None
            self.assertEquals(maildb.prev(maildb.post(post_heapid)), \
                              prev_post)

        test('0', None)
        test('1', '0')
        test('2', '1')
        test('3', '0')
        test('4', None)

    def testRoot(self):
        """Tests the 'root' method."""
        maildb = self._maildb

        def test(post_heapid, prev_heapid):
            if prev_heapid != None:
                prev_post = maildb.post(prev_heapid)
            else:
                prev_post = None
            self.assertEquals(maildb.root(maildb.post(post_heapid)), \
                              prev_post)

        test('0', '0')
        test('1', '0')
        test('2', '0')
        test('3', '0')
        test('4', '4')

    def threadstructCycle_general(self, inreplytos, threadstruct, cycles):
        """The general function that tests the cycle detection of the thread
        structure computing method.

        It modifies the mail database according to the inreplytos argument,
        then checks that the thread structture and the cycles of the modified
        database are as expected.
        
        Arguments:
        inreplytos: Contains child->parent pairs, which indicate that the child
            post should be modified as if it were a reply to parent.
            Type: dict(heapid, heapid)
        threadstruct: The excepted thread structure.
            Type: dict(None | heapid, [heapid])
        cycles: Posts that are in a cycle.
            Type: [heapid]
        """

        maildb = self._maildb
        p = self._posts
        for child, parent in inreplytos.items():
            maildb.post(child).set_inreplyto(parent)
        self.assertEquals(threadstruct, maildb.threadstruct())
        self.assert_(maildb.cycles().is_set(cycles))
        if cycles == []:
            self.assertFalse(maildb.has_cycle())
        else:
            self.assert_(maildb.has_cycle())

    def testThreadstructCycle1(self):
        self.threadstructCycle_general(
            {},
            {None: ['0', '4'],
             '0': ['1', '3'],
             '1': ['2']},
            [])

    def testThreadstructCycle2(self):
        self.threadstructCycle_general(
            {'1': '2'},
            {None: ['0', '4'],
                  '0': ['3'],
                  '1': ['2'],
                  '2': ['1']},
            ['1', '2'])

    def testThreadstructCycle3(self):
        self.threadstructCycle_general(
            {'0': '2'},
            {None: ['4'],
             '0': ['1', '3'],
             '1': ['2'],
             '2': ['0']},
            ['0', '1', '2', '3'])

    def testThreadstructCycle4(self):
        self.threadstructCycle_general(
            {'0': '0'},
            {None: ['4'],
             '0': ['0', '1', '3'],
             '1': ['2']},
            ['0', '1', '2', '3'])

    def tearDown(self):
        self.tearDownDirs()


class TestPostSet(unittest.TestCase, MailDBHandler):

    """Tests the PostSet class."""

    def setUp(self):
        self.setUpDirs()

        # 1 <- 2
        #      3
        postfile1 = self.postFileName('1.mail')
        postfile2 = self.postFileName('2.mail')
        postfile3 = self.postFileName('3.mail')
        string_to_file('Message-Id: 1@', postfile1)
        string_to_file('Message-Id: 2@\nIn-Reply-To: 1@', postfile2)
        string_to_file('Message-Id: 3@\nIn-Reply-To: 1@', postfile3)
        self._maildb = self.createMailDB()

    def testEmpty(self):
        maildb = self._maildb
        p1 = maildb.post('1')
        p2 = maildb.post('2')
        ps1 = PostSet(maildb, set())

        self.assertNotEquals(ps1, set())
        self.assert_(ps1 != set())
        self.assertFalse(ps1 == set())
        self.assert_(ps1.is_set(set()))

        self.assertEquals(ps1, PostSet(maildb, []))
        self.assert_(ps1 == PostSet(maildb, []))
        self.assertFalse(ps1 != PostSet(maildb, []))

    def testCopy(self):
        """Tests PostSet.copy and PostSet.empty_clone."""

        maildb = self._maildb
        ps_all = self._maildb.all().copy()
        p1 = maildb.post('1')
        p2 = maildb.post('2')
        p3 = maildb.post('3')

        ps1 = ps_all.copy()
        self.assert_(ps1 == ps_all)
        self.assertFalse(ps1 != ps_all)
        self.assertFalse(ps1 is ps_all)

        ps1.remove(p1)
        self.assertFalse(ps1 == ps_all)
        self.assert_(ps1 != ps_all)

        self.assert_(ps_all.is_set(set([p1, p2, p3])))
        self.assert_(ps1.is_set(set([p2, p3])))
        self.assert_(ps_all._maildb is ps1._maildb)

        ps2 = ps_all.empty_clone()
        self.assert_(ps_all.is_set(set([p1, p2, p3])))
        self.assert_(ps2.is_set(set([])))
        self.assert_(ps_all._maildb is ps2._maildb)

    def test1(self):
        maildb = self._maildb
        p1 = maildb.post('1')
        p2 = maildb.post('2')
        p3 = maildb.post('3')

        # __init__, _to_set
        ps0 = PostSet(maildb, set([p1]))
        ps02 = PostSet(maildb, [p1])
        ps03 = PostSet(maildb, p1)
        psh1= PostSet(maildb, set(['1']))
        psh2 = PostSet(maildb, ['1'])
        psh3 = PostSet(maildb, '1')
        psh4 = PostSet(maildb, 1)
        self.assertEquals(ps0, ps02)
        self.assertEquals(ps0, ps03)
        self.assertEquals(ps0, psh1)
        self.assertEquals(ps0, psh2)
        self.assertEquals(ps0, psh3)
        self.assertEquals(ps0, psh4)

        ps01 = maildb.postset(set([p1]))
        ps02 = maildb.postset([p1])
        ps03 = maildb.postset(p1)
        psh1= maildb.postset(set(['1']))
        psh2 = maildb.postset(['1'])
        psh3 = maildb.postset('1')
        psh3 = maildb.postset(1)
        self.assertEquals(ps0, ps01)
        self.assertEquals(ps0, ps02)
        self.assertEquals(ps0, ps03)
        self.assertEquals(ps0, psh1)
        self.assertEquals(ps0, psh2)
        self.assertEquals(ps0, psh3)
        self.assertEquals(ps0, psh4)

        ps1 = PostSet(maildb, set([p1, p2]))
        ps2 = PostSet(maildb, set([p2, p3]))
        ps3 = PostSet(maildb, [p2, p3])
        ps4 = PostSet(maildb, ps3)
        self.assertNotEquals(ps1, ps2)
        self.assertEquals(ps2, ps3)
        self.assertEquals(ps2, ps4)

        def f():
            PostSet(maildb, 'nosuchpost')
        self.assertRaises(KeyError, f)

        def f():
            PostSet(maildb, 1.0)
        self.assertRaises(TypeError, f)

        # is_set
        self.assert_(ps0.is_set(set([p1])))
        self.assert_(ps0.is_set([p1]))
        self.assert_(ps0.is_set(p1))
        self.assert_(ps1.is_set((p1, p2)))
        self.assert_(ps1.is_set([p1, p2]))
        self.assert_(ps2.is_set(ps3))

        # &, |, -, ^
        ps1 = PostSet(maildb, [p1, p2])
        ps2 = PostSet(maildb, [p1, p3])
        ps3 = PostSet(maildb, [p2, p3])
        ps1l = [p1, p2]
        ps2l = [p1, p3]
        ps3l = [p2, p3]

        def test(postset, s):
            self.assert_(postset.is_set(s))

        # &, intersection
        test(ps1 & ps2, [p1])
        test(ps1 & ps2l, [p1])
        test(ps1l & ps2, [p1])
        test(ps1 & ps2 & ps3, [])
        test(ps1.intersection(ps2l), [p1])

        ps1c = ps1.copy()
        ps1c &= ps2
        test(ps1c, [p1])

        ps1c = ps1.copy()
        ps1c.intersection_update(ps2l)
        test(ps1c, [p1])

        # |, union
        test(ps1.union(ps2l), [p1, p2, p3])
        test(ps1 | ps2, [p1, p2, p3])
        test(ps1 | ps2l, [p1, p2, p3])
        test(ps1l | ps2, [p1, p2, p3])
        test(ps1 | ps2 | ps3, [p1, p2, p3])

        ps1c = ps1.copy()
        ps1c |= ps2
        test(ps1c, [p1, p2, p3])

        ps1c = ps1.copy()
        ps1c.update(ps2l)
        test(ps1c, [p1, p2, p3])

        # -, difference
        test(ps1.difference(ps2l), [p2])
        test(ps1 - ps2l, [p2])
        test(ps1l - ps2, [p2])
        test(ps1 - ps2 - ps3, [])

        ps1c = ps1.copy()
        ps1c -= ps2
        test(ps1c, [p2])

        ps1c = ps1.copy()
        ps1c.difference_update(ps2l)
        test(ps1c, [p2])

        # ^, symmetric_difference
        test(ps1.symmetric_difference(ps2l), [p2, p3])
        test(ps1 ^ ps2, [p2, p3])
        test(ps1 ^ ps2l, [p2, p3])
        test(ps1l ^ ps2, [p2, p3])
        test(ps1 ^ ps2 ^ ps3, [])

        ps1c = ps1.copy()
        ps1c ^= ps2
        test(ps1c, [p2, p3])

        ps1c = ps1.copy()
        ps1c.symmetric_difference_update(ps2)
        test(ps1c, [p2, p3])

        # PostSet.construct 
        test(ps1 & set([p1, p3]), [p1])
        test(ps1 & [p1, p3], [p1])
        test(ps1 & p1, [p1])
        test(ps1 & '1', [p1])
        test(ps1 & 1, [p1])
        test(set([p1, p3]) & ps1, [p1])
        test([p1, p3] & ps1, [p1])
        test(p1 & ps1, [p1])
        test('1' & ps1, [p1])
        test(1 & ps1, [p1])

        def f():
            test(ps1 & 1.0, [p1])
        self.assertRaises(TypeError, f)

        def f():
            test(1.0 & ps1, [p1])
        self.assertRaises(TypeError, f)

        # MailDB.all
        ps_all = PostSet(maildb, [p1, p2, p3])
        ps2 = PostSet(maildb, set([p2, p3]))
        self.assertEquals(ps_all, maildb.all())
        p1.delete()
        self.assertEquals(ps2, maildb.all())

        # clear, update
        ps1.clear()
        self.assert_(ps1.is_set([]))
        ps1.update(set([p1, p2]))
        self.assert_(ps1.is_set([p1, p2]))

    def testGetAttr(self):
        """Tests the PostSet.__get_attr__ method."""

        maildb = self._maildb
        def f():
            PostSet(maildb, []).nonexisting_method
        self.assertRaises(AttributeError, f)

    def testForall(self):
        """Tests the PostSet.forall method."""

        def testSubjects(s1, s2, s3):
            self.assertEquals(s1, p1.subject())
            self.assertEquals(s2, p2.subject())
            self.assertEquals(s3, p3.subject())

        maildb = self._maildb
        p1 = maildb.post('1')
        p2 = maildb.post('2')
        p3 = maildb.post('3')
        testSubjects('', '', '')

        PostSet(maildb, []).forall.set_subject('x')
        testSubjects('', '', '')
        PostSet(maildb, [p1]).forall.set_subject('x')
        testSubjects('x', '', '')
        maildb.all().forall(lambda p: p.set_subject('z'))
        testSubjects('z', 'z', 'z')
        maildb.all().forall.set_subject('y')
        testSubjects('y', 'y', 'y')

        # Nonexisting methods will cause exceptions...
        def f():
            maildb.all().forall.nonexisting_method()
        self.assertRaises(AttributeError, f)

        # ...unless the postset is empty
        PostSet(maildb, []).forall.nonexisting_method()
        testSubjects('y', 'y', 'y')

    def testCollect(self):
        """Tests the PostSet.collect method."""

        maildb = self._maildb
        p1 = maildb.post('1')
        p1.set_tags(['t1'])
        p2 = maildb.post('2')
        p2.set_tags(['t2'])
        p3 = maildb.post('3')
        p3.set_tags(['t1'])

        ps1 = maildb.all().collect.has_tag('t1')
        self.assert_(ps1.is_set([p1, p3]))
        ps2 = maildb.all().collect(lambda p: False)
        self.assert_(ps2.is_set([]))
        ps3 = maildb.all().collect(lambda p: True)
        self.assert_(ps3.is_set([p1, p2, p3]))
        ps4 = maildb.all().collect(lambda p: p.has_tag('t1'))
        self.assert_(ps4.is_set([p1, p3]))

        def f():
            maildb.all().collect(lambda p: None)
        self.assertRaises(AssertionError, f)

        ps_roots = maildb.all().collect.is_root()
        self.assert_(ps_roots.is_set([p1]))

    def tearDown(self):
        self.tearDownDirs()


class TestPostSetThreads(unittest.TestCase, MailDBHandler):

    """Tests thread centric methods of the PostSet class."""

    # Thread structure:
    # 0 <- 1 <- 2
    #   <- 3
    # 4

    def setUp(self):
        self.setUpDirs()
        self._maildb = self.createMailDB()
        self.create_threadst()

    def _testExp(self, methodname):
        """Tests the PostSet's method that has the given name.
        
        This function returns a function that can test the given method of
        PostSet. The function requires addititonal test arguments that specify
        the concrete test.

        These additional argument are:
        1. The heapids of the posts of the input postset.
        2. The heapids of the posts of the expected output postset.

        The following equality tested:
        input_postset.methodname() = output_postset
        """

        def testExp2(heapids_1, heapids_2):
            p = self._posts
            posts_1 = [ self._posts[int(i)] for i in heapids_1 ]
            posts_2 = [ self._posts[int(i)] for i in heapids_2 ]
            ps = PostSet(self._maildb, posts_1)

            # Testing that the real output is the expected output.
            self.assert_(eval('ps.' + methodname + '()').is_set(posts_2))

            # Testing that the exp() method did not change ps
            self.assert_(ps.is_set(posts_1))

        return testExp2

    def testExpb(self):
        test = self._testExp('expb')

        # 0 in, 4 out
        test('0', '0')
        test('03', '03')
        test('02', '012')
        test('023', '0123')
        test('01', '01')
        test('013', '013')
        test('012', '012')
        test('0123', '0123')

        # 0 in, 4 in
        test('04', '04')
        test('034', '034')
        test('024', '0124')
        test('0234', '01234')
        test('014', '014')
        test('0134', '0134')
        test('0124', '0124')
        test('01234', '01234')

        # 0 out, 4 out
        test('', '')
        test('3', '03')
        test('2', '012')
        test('23', '0123')
        test('1', '01')
        test('13', '013')
        test('12', '012')
        test('123', '0123')

        # 0 out, 4 in
        test('4', '4')
        test('34', '034')
        test('24', '0124')
        test('234', '01234')
        test('14', '014')
        test('134', '0134')
        test('124', '0124')
        test('1234', '01234')

    def testExpf(self):
        test = self._testExp('expf')

        # 0 in, 4 out
        test('0', '0123')
        test('03', '0123')
        test('02', '0123')
        test('023', '0123')
        test('01', '0123')
        test('013', '0123')
        test('012', '0123')
        test('0123', '0123')

        # 0 in, 4 in
        test('04', '01234')
        test('034', '01234')
        test('024', '01234')
        test('0234', '01234')
        test('014', '01234')
        test('0134', '01234')
        test('0124', '01234')
        test('01234', '01234')

        # 0 out, 4 out
        test('', '')
        test('3', '3')
        test('2', '2')
        test('23', '23')
        test('1', '12')
        test('13', '123')
        test('12', '12')
        test('123', '123')

        # 0 out, 4 in
        test('4', '4')
        test('34', '34')
        test('24', '24')
        test('234', '234')
        test('14', '124')
        test('134', '1234')
        test('124', '124')
        test('1234', '1234')

    def testExp(self):
        test = self._testExp('exp')

        # 0 in, 4 out
        test('0', '0123')
        test('03', '0123')
        test('02', '0123')
        test('023', '0123')
        test('01', '0123')
        test('013', '0123')
        test('012', '0123')
        test('0123', '0123')

        # 0 in, 4 in
        test('04', '01234')
        test('034', '01234')
        test('024', '01234')
        test('0234', '01234')
        test('014', '01234')
        test('0134', '01234')
        test('0124', '01234')
        test('01234', '01234')

        # 0 out, 4 out
        test('', '')
        test('3', '0123')
        test('2', '0123')
        test('23', '0123')
        test('1', '0123')
        test('13', '0123')
        test('12', '0123')
        test('123', '0123')

        # 0 out, 4 in
        test('4', '4')
        test('34', '01234')
        test('24', '01234')
        test('234', '01234')
        test('14', '01234')
        test('134', '01234')
        test('124', '01234')
        test('1234', '01234')
    
    def testSortedList(self):
        ps = self._maildb.postset(self._posts)
        self.assertEquals(ps.sorted_list(), self._posts)

    def tearDown(self):
        self.tearDownDirs()


class TestHtml(unittest.TestCase):

    def testEscape(self):

        def test(unescaped, escaped):
            self.assertEquals(Html.escape(unescaped), escaped)

        test('a<b', 'a&lt;b')
        test('a>b', 'a&gt;b')
        test('a&b', 'a&amp;b')

    def testDocHeader(self):
        r = re.compile(
                '<title>mytitle</title>.*'
                '<link rel=stylesheet href="mycss" type="text/css">.*'
                '<h1 id="header">myh1</h1>',
                re.IGNORECASE | re.DOTALL)
        search = r.search(Html.doc_header('mytitle', 'myh1', 'mycss'))
        self.assertNotEquals(search, None)

    def testLink(self):
        self.assertEquals(Html.link('mylink', 'mystuff'),
                          '<a href="mylink">mystuff</a>')

    def testEnclose(self):
        self.assertEquals(Html.enclose('myclass', 'mystuff'),
                          '<span class="myclass">mystuff</span>')
        self.assertEquals(Html.enclose('myclass', 'mystuff', 'mytag'),
                          '<mytag class="myclass">mystuff</mytag>')

    def testPostSummary(self):
        enc = Html.enclose
        link = Html.link

        # basic case
        self.assertEquals(
            Html.post_summary('mylink', 'myauthor', 'mysubject',
                              ['mytag1', 'mytag2'], 'myindex', None, 'mytag'),
            enc('author', link('mylink', 'myauthor'), 'mytag') + '\n' +
            enc('subject', link('mylink', 'mysubject'), 'mytag') + '\n' +
            enc('tags', link('mylink', '[mytag1, mytag2]'), 'mytag') + '\n' +
            enc('index', '&lt;%s&gt;' % link('mylink', 'myindex'), 'mytag') +
            '\n')

        # subject is STAR
        self.assertEquals(
            Html.post_summary('mylink', 'myauthor', STAR,
                              ['mytag1', 'mytag2'], 'myindex', None, 'mytag'),
            enc('author', link('mylink', 'myauthor'), 'mytag') + '\n' +
            enc('subject', enc('star', link('mylink', '&mdash;')), 'mytag') +
            '\n' +
            enc('tags', link('mylink', '[mytag1, mytag2]'), 'mytag') + '\n' +
            enc('index', '&lt;%s&gt;' % link('mylink', 'myindex'), 'mytag') +
            '\n')

        # 'tags' is STAR
        self.assertEquals(
            Html.post_summary('mylink', 'myauthor', 'mysubject',
                              STAR, 'myindex', None, 'mytag'),
            enc('author', link('mylink', 'myauthor'), 'mytag') + '\n' +
            enc('subject', link('mylink', 'mysubject'), 'mytag') + '\n' +
            enc('tags', enc('star', link('mylink', '[&mdash;]')), 'mytag') +
            '\n' +
            enc('index', '&lt;%s&gt;' % link('mylink', 'myindex'), 'mytag') +
            '\n')

        # specifying a date
        self.assertEquals(
            Html.post_summary('mylink', 'myauthor', 'mysubject',
                              ['mytag1', 'mytag2'], 'myindex', 'mydate',
                              'mytag'),
            enc('author', link('mylink', 'myauthor'), 'mytag') + '\n' +
            enc('subject', link('mylink', 'mysubject'), 'mytag') + '\n' +
            enc('tags', link('mylink', '[mytag1, mytag2]'), 'mytag') + '\n' +
            enc('index', '&lt;%s&gt;' % link('mylink', 'myindex'), 'mytag') +
            '\n' +
            enc('date', link('mylink', 'mydate'), 'mytag') + '\n')

    def testList(self):
        self.assertEquals(
            Html.list(['item 1', 'item 2']),
            '<ul>\n'
            '  <li>item 1</li>\n'
            '  <li>item 2</li>\n'
            '</ul>\n')
        self.assertEquals(
            Html.list(['item 1', 'item 2'], 'myclass'),
            '<ul class="myclass">\n'
            '  <li>item 1</li>\n'
            '  <li>item 2</li>\n'
            '</ul>\n')


class TestGenerator(unittest.TestCase, MailDBHandler):

    """Tests the Generator class."""

    def setUp(self):
        self.setUpDirs()

    def init(self):
        maildb = self._maildb = self.createMailDB()
        g = Generator(maildb)
        return maildb, g

    def index_html(self):
        index_html_name = os.path.join(self._html_dir, 'index.html')
        return file_to_string(index_html_name)

    def _sections(self, sections):
        assert(isinstance(sections, list))
        for i in range(len(sections)):
            section = sections[i]
            if isinstance(section[1], list):
                sectionposts = [ self._posts[postindex] 
                               for postindex in section[1] ]
                sectionoptions = {} if len(section) == 2 else section[2]
                sections[i] = (section[0], sectionposts, sectionoptions)

        Generator.sections_setdefaultoptions(sections)
        return sections

    def create_input(self, sections, options, sectionindex=None):
        sections = self._sections(sections)
        options2 = {'sections': sections}
        for optionname, optionvalue in options.items():
            options2[optionname] = optionvalue
        Generator.index_setdefaultoptions(options2)
        if sectionindex == None:
            return sections, options2
        else:
            return sections, options2, sections[sectionindex]


    def test_index_toc(self):
        maildb, g = self.init()
        self.create_threadst(skipdates=True)
        
        sections, options = \
            self.create_input(
                [('Sec1', [1]), ('Sec2', [4])],
                {'write_date': False})

        link = Html.link
        self.assertEquals(
            g.index_toc(sections),
            Html.list(
                [link('#section_0', 'Sec1'),
                 link('#section_1', 'Sec2')],
                'tableofcontents'))

    def test_post_summary(self):
        maildb, g = self.init()
        self.create_threadst()

        sections, options, section = \
            self.create_input(
                [('Sec1', [1]), ('Sec2', [4])],
                {'write_date': False},
                sectionindex=0)

        div = Html.post_summary_div

        # basic case
        self.assertEquals(
            g.post_summary(self._posts[0], section, options),
            div('0.html', 'author0', 'subject0', [], '0', None, False))

        # subject
        self.assertEquals(
            g.post_summary(self._posts[0], section, options, 'mysubject'),
            div('0.html', 'author0', 'mysubject', [], '0', None, False))

        self.assertEquals(
            g.post_summary(self._posts[0], section, options, STAR),
            div('0.html', 'author0', STAR, [], '0', None, False))

        # tags
        self.assertEquals(
            g.post_summary(self._posts[0], section, options,tags=['t1','t2']),
            div('0.html', 'author0', 'subject0', ['t1', 't2'], '0', None,
                False))

        self.assertEquals(
            g.post_summary(self._posts[0], section, options, tags=STAR),
            div('0.html', 'author0', 'subject0', STAR, '0', None, False))

    def test_post_summary__flat(self):
        maildb, g = self.init()
        self.create_threadst()

        sections, options, section = \
            self.create_input(
                [('Sec1', [1]), ('Sec2', [4])],
                {'write_date': False},
                sectionindex=0)
        section[2]['flat'] = True

        table = Html.post_summary_table
        self.assertEquals(
            g.post_summary(self._posts[0], section, options),
            table('0.html', 'author0', 'subject0', [], '0', None, False))

    def test_post_summary__date(self):
        
        def date_fun(post, sectionarg):
            self.assertEquals(sectionarg, section)
            self.assertEquals(post.heapid(), str((self._posts.index(post))))
            return 'date%s' % (self._posts.index(post),)

        maildb, g = self.init()
        self.create_threadst()

        sections, options, section = \
            self.create_input(
                [('Sec1', [1]), ('Sec2', [4])],
                {'date_fun': date_fun},
                sectionindex=0)

        div = Html.post_summary_div
        self.assertEquals(
            g.post_summary(self._posts[0], section, options),
            div('0.html', 'author0', 'subject0', [], '0', 'date0', False))

    def test_thread(self):
        maildb, g = self.init()
        self.create_threadst()

        sections, options, section = \
            self.create_input(
                [('Sec1', [1]), ('Sec2', [4])],
                {'write_date': False},
                sectionindex=0)

        self.assertEquals(
            g.thread(self._posts[2], section, options),
            g.post_summary(self._posts[2], section, options) +
            g.post_summary_end())

        self.assertEquals(
            g.thread(self._posts[1], section, options),
            g.post_summary(self._posts[1], section, options) +
            g.post_summary(self._posts[2], section, options) +
            g.post_summary_end() +
            g.post_summary_end())

        self.assertEquals(
            g.thread(self._posts[0], section, options),
            g.post_summary(self._posts[0], section, options) +
            g.post_summary(self._posts[1], section, options) +
            g.post_summary(self._posts[2], section, options) +
            g.post_summary_end() + # end of 2
            g.post_summary_end() + # end of 1
            g.post_summary(self._posts[3], section, options) +
            g.post_summary_end() + # end of 3
            g.post_summary_end()) # end of 0

        sections, options, section = \
            self.create_input(
                [('Sec', [1, 4])],
                {'write_date': False},
                sectionindex=0)

        self.assertEquals(
            g.thread(None, section, options),
            g.post_summary(self._posts[0], section, options) +
            g.post_summary(self._posts[1], section, options) +
            g.post_summary(self._posts[2], section, options) +
            g.post_summary_end() + # end of 2
            g.post_summary_end() + # end of 1
            g.post_summary(self._posts[3], section, options) +
            g.post_summary_end() + # end of 3
            g.post_summary_end() + # end of 0
            g.post_summary(self._posts[4], section, options) +
            g.post_summary_end()) # end of 4

    def test_thread__shortsubject(self):
        maildb, g = self.init()
        self.create_threadst()

        sections, options, section = \
            self.create_input(
                [('Sec', [1, 4])],
                {'write_date': False, 'shortsubject': True},
                sectionindex=0)

        # All posts have the same subject.

        for i in range(5):
            self._posts[i].set_subject('subject')

        self.assertEquals(
            g.thread(None, section, options),
            g.post_summary(self._posts[0], section, options) +
            g.post_summary(self._posts[1], section, options, subject=STAR) +
            g.post_summary(self._posts[2], section, options, subject=STAR) +
            g.post_summary_end() + # end of 2
            g.post_summary_end() + # end of 1
            g.post_summary(self._posts[3], section, options, subject=STAR) +
            g.post_summary_end() + # end of 3
            g.post_summary_end() + # end of 0
            g.post_summary(self._posts[4], section, options) +
            g.post_summary_end()) # end of 4

        # All but one posts have the same subject.

        self._posts[3].set_subject('subject3')

        self.assertEquals(
            g.thread(None, section, options),
            g.post_summary(self._posts[0], section, options) +
            g.post_summary(self._posts[1], section, options, subject=STAR) +
            g.post_summary(self._posts[2], section, options, subject=STAR) +
            g.post_summary_end() + # end of 2
            g.post_summary_end() + # end of 1
            g.post_summary(self._posts[3], section, options) +
            g.post_summary_end() + # end of 3
            g.post_summary_end() + # end of 0
            g.post_summary(self._posts[4], section, options) +
            g.post_summary_end()) # end of 4

    def test_thread__cycles(self):
        maildb, g = self.init()
        self.create_threadst()
        maildb.post('1').set_inreplyto('2')

        # One thread.
        sections, options, section = \
            self.create_input(
                [('Sec', [1, 4])],
                {'write_date': False},
                sectionindex=0)

        self.assertEquals(
            g.thread(self._posts[0], section, options),
            g.post_summary(self._posts[0], section, options) +
            g.post_summary(self._posts[3], section, options) +
            g.post_summary_end() + # end of 3
            g.post_summary_end()) # end of 0

        # All threads.
        sections, options, section = \
            self.create_input(
                [('Sec', [1, 4])],
                {'write_date': False},
                sectionindex=0)
        self.assertEquals(
            g.thread(None, section, options),
            g.post_summary(self._posts[0], section, options) +
            g.post_summary(self._posts[3], section, options) +
            g.post_summary_end() + # end of 3
            g.post_summary_end() + # end of 0
            g.post_summary(self._posts[4], section, options) +
            g.post_summary_end()) # end of 4

    def test_section(self):
        maildb, g = self.init()
        self.create_threadst()

        # Tests empty section.
        sections, options, section = \
            self.create_input(
                [('Sec', [])],
                {'write_date': False},
                sectionindex=0)

        self.assertEquals(
            g.section(section, 0, options),
            Html.section_begin('section_0', 'Sec') +
            Html.section_end())

        # Tests where not every post is in the section.
        sections, options, section = \
            self.create_input(
                [('Sec1', [1]), ('Sec2', [4])],
                {'write_date': False},
                sectionindex=0)

        self.assertEquals(
            g.section(section, 0, options),
            Html.section_begin('section_0', 'Sec1') +
            g.thread(self._posts[0], section, options) +
            Html.section_end())

        # Tests where more than one threads are in the section.
        sections, options, section = \
            self.create_input(
                [('Sec', [1, 4])],
                {'write_date': False},
                sectionindex=0)

        self.assertEquals(
            g.section(section, 0, options),
            Html.section_begin('section_0', 'Sec') +
            g.thread(self._posts[0], section, options) +
            g.thread(self._posts[4], section, options) +
            Html.section_end())

        # Tests flat printing

        def flat_result(postindex1, postindex2):
            return \
                (Html.section_begin('section_0', 'Sec') +
                 Html.enclose(
                     'flatlist',
                     g.post_summary(self._posts[postindex1], section,options)+
                     g.post_summary(self._posts[postindex2], section,options),
                     tag='table', newlines=True) +
                 Html.section_end())

        # Tests flat printing with list.
        sections, options, section = \
            self.create_input(
                [('Sec', [1, 4])],
                {'write_date': False},
                sectionindex=0)
        section[2]['flat'] = True
        self.assertEquals(g.section(section, 0, options), flat_result(1, 4))

        # Tests flat printing with list in the reversed order.
        sections, options, section = \
            self.create_input(
                [('Sec', [4, 1])],
                {'write_date': False},
                sectionindex=0)
        section[2]['flat'] = True
        self.assertEquals(g.section(section, 0, options), flat_result(4, 1))

        # Tests flat printing with PostSet.
        sections, options, section = \
            self.create_input(
                [('Sec', maildb.postset([self._posts[1], self._posts[4]]))],
                {'write_date': False},
                sectionindex=0)
        section[2]['flat'] = True
        self.assertEquals(g.section(section, 0, options), flat_result(1, 4))

    def test_index(self):

        maildb, g = self.init()
        self.create_threadst()

        sections, options = \
            self.create_input(
                [('Sec1', [1]), ('Sec2', [4])],
                 {'write_date': False,
                  'write_toc': False,
                  'html_title': 'myhtmltitle',
                  'html_h1': 'myhtmlh1',
                  'cssfile': 'mycssfile'})

        g.index(**options)
        self.assertEquals(
            self.index_html(),
            Html.doc_header('myhtmltitle', 'myhtmlh1', 'mycssfile') +
            g.section(sections[0], 0, options) +
            g.section(sections[1], 1, options) +
            Html.doc_footer())

    def tearDown(self):
        self.tearDownDirs()


if __name__ == '__main__':
    set_log(False)
    unittest.main()
