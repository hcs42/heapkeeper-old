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

class TestMailDB(unittest.TestCase):

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

    def testThreadstruct(self):
        """Tests the thread structure computing method."""

        def add_post(index, inreplyto=None):
            messid = str(index) + '@'
            inreplyto = str(inreplyto) + '@' if inreplyto != None else ''
            s = 'Message-Id: ' + messid + '\n' + \
                'In-Reply-To: ' + inreplyto + '\n' + \
                dates[index]
            maildb.add_new_post(Post.from_str(s))

        # 0 <- 1 <- 2
        #   <- 3
        # 4

        # Creating an ordered array of dates.
        dates = [ 'Date: Wed, 20 Aug 2008 17:41:0%d +0200\n' % i \
                   for i in range(10) ]

        self.createDirs()
        maildb = self.createMailDB()
        add_post(0)
        add_post(1, 0)
        add_post(2, 1)
        add_post(3, 0)
        add_post(4)

        ts = {None: ['0', '4'],
              '0': ['1', '3'],
              '1': ['2']}
        self.assertEquals(ts, maildb.threadstruct())

    def tearDown(self):
        shutil.rmtree(self._dir)



class TestGenerator(unittest.TestCase):

    """Tests the Generator class."""

    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self._postfile_dir = os.path.join(self._dir, 'mail')
        self._html_dir = os.path.join(self._dir, 'html')
        os.mkdir(self._postfile_dir)
        os.mkdir(self._html_dir)

    def createMailDB(self):
        return MailDB(self._postfile_dir, self._html_dir)

    def postFileName(self, fname):
        return os.path.join(self._postfile_dir, fname)

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
        p1 = maildb.post('1')
        p2 = maildb.post('2')

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
        shutil.rmtree(self._dir)

if __name__ == '__main__':
    set_log(False)
    unittest.main()
