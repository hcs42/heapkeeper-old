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

from heapmanip import *

class MailDBHandler(object):

    """A class that helps implementing the tester classes by containing
    functions commonly used by them."""
    
    # Creating an ordered array of dates.
    dates = [ 'Date: Wed, 20 Aug 2008 17:41:0%d +0200\n' % i \
              for i in range(20) ]

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
        s = 'Message-Id: ' + messid + '\n' + \
            'In-Reply-To: ' + inreplyto + '\n' + \
            MailDBHandler.dates[index]
        self._maildb.add_new_post(Post.from_str(s))

    def create_threadst(self):
        """Adds a thread structure to the maildb with the following structure.

        0 <- 1 <- 2
          <- 3
        4
        """

        self.add_post(0)
        self.add_post(1, 0)
        self.add_post(2, 1)
        self.add_post(3, 0)
        self.add_post(4)


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

class TestPost(unittest.TestCase):

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

        # They cannot be modified via the get methods
        p.flags()[0] = ''
        p.tags()[0] = ''
        self.assertEquals(p.flags(), ['f1', 'f2'])
        self.assertEquals(p.tags(), ['t1', 't2'])

        # Iterator
        l = []
        for tag in p.tags_iter():
            l.append(tag)
        self.assertEquals(l, ['t1', 't2'])

        # Set methods
        p.set_flags(['f'])
        self.assertEquals(p.flags(), ['f'])
        p.set_tags(['t'])
        self.assertEquals(p.tags(), ['t'])

        # Sorting
        p = Post.from_str('Flag: f2\nFlag: f1\nTag: t2\nTag: t1')
        self.assertEquals(p.flags(), ['f1', 'f2']) # flags are sorted
        self.assertEquals(p.tags(), ['t2', 't1']) # tags are not

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


class TestMailDB(unittest.TestCase, MailDBHandler):

    """Tests the MailDB class (and its cooperation with the Post class)."""

    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self._postfile_dir = os.path.join(self._dir, 'mail')
        self._html_dir = os.path.join(self._dir, 'html')

    def createMailDB(self):
        return MailDB(self._postfile_dir, self._html_dir)

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

    def testPrev(self):
        """Tests the 'prev' method."""

        maildb = self.createMailDB()
        self._maildb = maildb
        self.create_threadst()

        def test_prev(post_heapid, prev_heapid):
            if prev_heapid != None:
                prev_post = maildb.post(prev_heapid)
            else:
                prev_post = None
            self.assertEquals(maildb.prev(maildb.post(post_heapid)), \
                              prev_post)

        test_prev('0', None)
        test_prev('1', '0')
        test_prev('2', '1')
        test_prev('3', '0')
        test_prev('4', None)

    def testRoot(self):
        """Tests the 'prev' method."""

        maildb = self.createMailDB()
        self._maildb = maildb
        self.create_threadst()

        def test_root(post_heapid, prev_heapid):
            if prev_heapid != None:
                prev_post = maildb.post(prev_heapid)
            else:
                prev_post = None
            self.assertEquals(maildb.root(maildb.post(post_heapid)), \
                              prev_post)

        test_root('0', '0')
        test_root('1', '0')
        test_root('2', '0')
        test_root('3', '0')
        test_root('4', '4')

    def testThreadstruct(self):
        """Tests the thread structure computing method."""

        maildb = self.createMailDB()
        self._maildb = maildb
        self.create_threadst()

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
        maildb = self.createMailDB()
        self._maildb = maildb
        self.create_threadst()
        p = [ maildb.post(str(i)) for i in range(5) ]

        def test_iter(post, result):
            self.assertEquals(result, \
                              [ p.heapid() for p in maildb.iter_thread(post)])

        test_iter(None, ['0', '1', '2', '3', '4'])
        test_iter(p[0], ['0', '1', '2', '3'])
        test_iter(p[1], ['1', '2'])
        test_iter(p[2], ['2'])
        test_iter(p[3], ['3'])
        test_iter(p[4], ['4'])

        # if the post is not in the maildb, AssertionError will be raised
        def f():
            test_iter(Post.from_str(''), [])
        self.assertRaises(AssertionError, f)
    
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
        self.assert_(ps1.is_set(set()))
        self.assertEquals(ps1, PostSet(maildb, []))

    def test1(self):
        maildb = self._maildb
        p1 = maildb.post('1')
        p2 = maildb.post('2')
        p3 = maildb.post('3')

        # __init__, to_set
        ps0 = PostSet(maildb, set([p1]))
        ps02 = PostSet(maildb, [p1])
        ps03 = PostSet(maildb, p1)
        self.assertEquals(ps0, ps02)
        self.assertEquals(ps0, ps03)

        ps1 = PostSet(maildb, set([p1, p2]))
        ps2 = PostSet(maildb, set([p2, p3]))
        ps3 = PostSet(maildb, [p2, p3])
        ps4 = PostSet(maildb, ps3)
        self.assertNotEquals(ps1, ps2)
        self.assertEquals(ps2, ps3)
        self.assertEquals(ps2, ps4)

        def f():
            PostSet(maildb, 0)
        self.assertRaises(HeapException, f)

        # is_set
        self.assert_(ps0.is_set(set([p1])))
        self.assert_(ps0.is_set([p1]))
        self.assert_(ps0.is_set(p1))
        self.assert_(ps1.is_set((p1, p2)))
        self.assert_(ps1.is_set([p1, p2]))
        self.assert_(ps2.is_set(ps3))

        # &, |, -
        self.assert_((ps1 & ps2).is_set(set([p2])))
        self.assert_((ps1 & ps2).is_set([p2]))
        self.assert_((ps1 | ps2).is_set([p1, p2, p3]))
        self.assert_((ps1 - ps2).is_set([p1]))

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

        PostSet(maildb, []).forall().set_subject('x')
        testSubjects('', '', '')
        PostSet(maildb, [p1]).forall().set_subject('x')
        testSubjects('x', '', '')
        maildb.all().forall().set_subject('y')
        testSubjects('y', 'y', 'y')

        # Nonexisting methods will cause exceptions...
        def f():
            maildb.all().forall().nonexisting_method()
        self.assertRaises(AttributeError, f)

        # ...unless the postset is empty
        PostSet(maildb, []).forall().nonexisting_method()
        testSubjects('y', 'y', 'y')

        # fa is the same as forall()
        maildb.all().fa.set_subject('')
        PostSet(maildb, []).fa.set_subject('x')
        testSubjects('', '', '')
        PostSet(maildb, [p1]).fa.set_subject('x')
        testSubjects('x', '', '')
        maildb.all().fa.set_subject('y')
        testSubjects('y', 'y', 'y')

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
        self._p = [ self._maildb.post(str(i)) for i in range(5) ]

    def testExpf(self):
        maildb = self._maildb
        p = self._p

        def test_expf(heapids_1, heapids_2):
            posts_1 = [ p[int(i)] for i in heapids_1 ]
            posts_2 = [ p[int(i)] for i in heapids_2 ]
            self.assert_(PostSet(maildb, posts_1).expf().is_set(posts_2))

        # 0 in, 4 out
        test_expf('0', '0123')
        test_expf('03', '0123')
        test_expf('02', '0123')
        test_expf('023', '0123')
        test_expf('01', '0123')
        test_expf('013', '0123')
        test_expf('012', '0123')
        test_expf('0123', '0123')

        # 0 in, 4 in
        test_expf('04', '01234')
        test_expf('034', '01234')
        test_expf('024', '01234')
        test_expf('0234', '01234')
        test_expf('014', '01234')
        test_expf('0134', '01234')
        test_expf('0124', '01234')
        test_expf('01234', '01234')

        # 0 out, 4 out
        test_expf('', '')
        test_expf('3', '3')
        test_expf('2', '2')
        test_expf('23', '23')
        test_expf('1', '12')
        test_expf('13', '123')
        test_expf('12', '12')
        test_expf('123', '123')

        # 0 out, 4 in
        test_expf('4', '4')
        test_expf('34', '34')
        test_expf('24', '24')
        test_expf('234', '234')
        test_expf('14', '124')
        test_expf('134', '1234')
        test_expf('124', '124')
        test_expf('1234', '1234')

    def tearDown(self):
        self.tearDownDirs()


class TestGenerator(unittest.TestCase, MailDBHandler):

    """Tests the Generator class."""

    def setUp(self):
        self.setUpDirs()

    def indexHtml(self):
        index_html_name = os.path.join(self._html_dir, 'index.html')
        return file_to_string(index_html_name)

    def testEmpty(self):
        """Tests the empty MailDB."""
        maildb = self.createMailDB()
        g = Generator(maildb)
        g.index_html()
        s = html_header % ('Heap Index', 'heapindex.css', 'UMS Heap') + \
            html_footer
        self.assertEquals(self.indexHtml(), s)

    def test1(self):
        """Tests the MailDB with two posts."""

        # Initialisation
        postfile1 = self.postFileName('1.mail')
        postfile2 = self.postFileName('x.mail')
        string_to_file('Message-Id: mess1', postfile1)
        string_to_file('Message-Id: mess2\nIn-Reply-To: mess1', postfile2)
        maildb = self.createMailDB()
        g = Generator(maildb)
        g.index_html()
        s = html_header % ('Heap Index', 'heapindex.css', 'UMS Heap') + \
            html_one_mail % ('1.html', '', '1', '', '&nbsp; ()') + \
            html_one_mail % ('x.html', '', 'x', '', '&nbsp; ()') + \
            '</div>\n</div>\n' + \
            html_footer
        self.assertEquals(self.indexHtml(), s)

    def tearDown(self):
        self.tearDownDirs()

if __name__ == '__main__':
    set_log(False)
    unittest.main()
