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

# Copyright (C) 2009 Csaba Hoch
# Copyright (C) 2009 Attila Nagy

"""Tests the hklib module.

Usage:
    
    $ python test_hklib.py
"""

from __future__ import with_statement
import StringIO
import unittest
import tempfile
import os
import os.path
import ConfigParser
import re

from hklib import *


class PostDBHandler(object):

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

    def createPostDB(self):
        return PostDB(self._postfile_dir, self._html_dir)

    def postFileName(self, fname):
        return os.path.join(self._postfile_dir, fname)

    def add_post(self, index, parent=None):
        """Adds a new post to postdb.
        
        The attributes of the post will be created as follows:
        - The author will be 'author'+index.
        - The subject will be 'subject'+index.
        - The message id will be index+'@'.
        - The parent will be `parent`, if specified.
        - If self._skipdates is False, the post with a newer index will
          have a newer date; otherwise the post will not have a date.
        - The body will be 'body'+index.
        """

        parent = str(parent) + '@' if parent != None else ''
        s = ('Author: author%s\n' % (index,) +
             'Subject: subject%s\n' % (index,) +
             'Message-Id: %s@\n' % (index,) +
             'Parent: %s\n' % (parent,))
        if not self._skipdates:
            s += PostDBHandler.dates[index] + '\n'
        s += ('\n' +
              'body%s' % (index,))
        self._postdb.add_new_post(Post.from_str(s))

    def create_threadst(self, skipdates=False):
        """Adds a thread structure to the postdb with the following structure.

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
        self._posts = [ self._postdb.post(str(i)) for i in range(5) ]


# global strings for tests

post1_text = '''\
Author: author
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

post1_dict1 = {'Author': ['author'],
               'Subject': ['subject'],
               'Message-Id': ['<0@gmail.com>'],
               'Date': ['Wed, 20 Aug 2008 17:41:30 +0200'],
               'Flag': ['flag1', 'flag2']}

post1_dict2 = {'Author': 'author',
               'Subject': 'subject',
               'Message-Id': '<0@gmail.com>',
               'Parent': '',
               'Date': 'Wed, 20 Aug 2008 17:41:30 +0200',
               'Flag': ['flag1', 'flag2'],
               'Tag': []}

post_output = '''\
Author: author
Subject: subject
Message-Id: <0@gmail.com>
Date: Wed, 20 Aug 2008 17:41:30 +0200
Flag: flag1
Flag: flag2

'''

post1_output = post_output + '\n'
post4_output = post_output + 'Hi\n'


class Test_Post__1(unittest.TestCase):

    """Tests the Post class."""

    def test__parsing(self):

        sio = StringIO.StringIO(post1_text)
        self.assertEquals(Post.parse_header(sio), post1_dict1)
        sio.close()

        sio = StringIO.StringIO(post2_text)
        self.assertEquals(Post.parse_header(sio), post1_dict1)
        sio.close()

        self.assertRaises(
            hkutils.HkException,
            lambda: Post.from_str('Malformatted post.'))

    def test__empty(self):
        p = Post.from_str('')
        self.assertEquals(p.heapid(), None)
        self.assertEquals(p.author(), '')
        self.assertEquals(p.subject(), '')
        self.assertEquals(p.messid(), '')
        self.assertEquals(p.parent(), '')
        self.assertEquals(p.date(), '')
        self.assertEquals(p.is_deleted(), False)
        self.assertEquals(p.is_modified(), True)
        self.assertEquals(p.body(), '\n')
        p2 = Post.create_empty()
        self.assertEquals(p, p2)

    def test_init(self):
        p = Post.from_str(post4_text)

        # testing initialisation
        self.assertEquals(p.heapid(), None)
        self.assertEquals(p.author(), 'author')
        self.assertEquals(p.subject(), 'subject')
        self.assertEquals(p.messid(), '<0@gmail.com>')
        self.assertEquals(p.parent(), '')
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

        p.set_parent('@@')
        self.assertEquals(p.parent(), '@@')

        p.set_date('Wed, 20 Aug 2008 17:41:31 +0200')
        self.assertEquals(p.date(), \
                          'Wed, 20 Aug 2008 17:41:31 +0200')

        p.set_body('newbody')
        self.assertEquals(p.body(), 'newbody\n')
        p.set_body('\n newbody \n \n')
        self.assertEquals(p.body(), 'newbody\n')

        p.delete()
        self.assertEquals(p.is_deleted(), True)

    def test_write(self):

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

    def test__body_stripping(self):
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

    def test__subject(self):
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

    def test__tags_flags(self):

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

    def test__parse_tags_in_subject(self):

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


class Test_Post__2(unittest.TestCase):

    """Tests the Post class.

    The test functions in this class perform file operations."""

    def setUp(self):
        self._dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._dir)

    def test_from_file(self):
        fname = os.path.join(self._dir, 'postfile')
        hkutils.string_to_file(post1_text, fname)
        p = Post.from_file(fname)

        self.assertEquals(p.heapid(), None)
        self.assertEquals(p.author(), 'author')
        self.assertEquals(p.subject(), 'subject')
        self.assertEquals(p.messid(), '<0@gmail.com>')
        self.assertEquals(p.parent(), '')
        self.assertEquals(p.date(), 'Wed, 20 Aug 2008 17:41:30 +0200')
        self.assertEquals(p.is_deleted(), False)
        self.assertEquals(p.is_modified(), True)
        self.assertEquals(p.body(), '\n')


class Test_Post__3(unittest.TestCase, PostDBHandler):

    """Tests the Post class."""

    def setUp(self):
        self.setUpDirs()

        # 1 <- 2
        #      3
        postfile1 = self.postFileName('1.post')
        postfile2 = self.postFileName('2.post')
        postfile3 = self.postFileName('3.post')
        hkutils.string_to_file('Message-Id: 1@', postfile1)
        hkutils.string_to_file('Message-Id: 2@\nParent: 1@', postfile2)
        hkutils.string_to_file('Message-Id: 3@\nParent: 1@', postfile3)
        self._postdb = self.createPostDB()

    def tearDown(self):
        self.tearDownDirs()

    def test__filenames(self):
        p1 = self._postdb.post('1')
        p2 = self._postdb.post('2')

        self.assertEquals(
            p1.postfilename(),
            os.path.join(self._postfile_dir, '1.post'))

        self.assertEquals(
            p1.htmlfilebasename(),
            '1.html')

        self.assertEquals(
            p1.htmlfilename(),
            os.path.join(self._html_dir, '1.html'))

        self.assertEquals(
            p1.htmlthreadbasename(),
            'thread_1.html')

        self.assertEquals(
            p1.htmlthreadfilename(),
            os.path.join(self._html_dir, 'thread_1.html'))

        self.assertRaises(
            AssertionError,
            lambda: p2.htmlthreadbasename())

        self.assertRaises(
            AssertionError,
            lambda: p2.htmlthreadfilename())


class Test_PostDB__1(unittest.TestCase, PostDBHandler):

    """Tests the PostDB class (and its cooperation with the Post class)."""

    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self._postfile_dir = os.path.join(self._dir, 'mail')
        self._html_dir = os.path.join(self._dir, 'html')

    def tearDown(self):
        shutil.rmtree(self._dir)

    def createDirs(self):
        os.mkdir(self._postfile_dir)
        os.mkdir(self._html_dir)

    def postFileName(self, fname):
        return os.path.join(self._postfile_dir, fname)

    def testEmpty(self):
        """Tests the empty PostDB."""
        postdb = self.createPostDB()
        self.assert_(os.path.exists(self._postfile_dir))
        self.assertEquals(postdb.postfile_dir(), self._postfile_dir)
        self.assertEquals(postdb.html_dir(), self._html_dir)
        self.assertEquals(postdb.heapids(), [])

    def testOnlyPost(self):
        """Tests that only the files with ".post" postfix are read."""
        self.createDirs()
        hkutils.string_to_file('Subject: s1', self.postFileName('1.post'))
        hkutils.string_to_file('Subject: sx', self.postFileName('xy.post'))
        hkutils.string_to_file('Subject: s2', self.postFileName('2.other'))
        hkutils.string_to_file('Subject: s3', self.postFileName('3post'))
        postdb = self.createPostDB()
        self.assertEquals(set(postdb.heapids()), set(['1', 'xy']))
        self.assertEquals(postdb.next_heapid(), '2')

    def testConfig(self):
        """Tests the PostDB.__init__ which has a ConfigParser argument."""
        self.createDirs()
        hkutils.string_to_file('Subject: s1', self.postFileName('1.post'))
        configFileText = '''\
[paths]
mail=%s
html=%s
''' % (self._postfile_dir, self._html_dir)
        configFileName = os.path.join(self._dir, 'hk.cfg')
        hkutils.string_to_file(configFileText, configFileName)
        config = ConfigParser.ConfigParser()
        config.read(configFileName)
        postdb = PostDB.from_config(config)
        self.assertEquals(set(postdb.heapids()), set(['1']))

    def testGetMethods(self):
        """Tests the 'get' methods of PostDB."""
        self.createDirs()
        hkutils.string_to_file('Message-Id: mess1',
                               self.postFileName('1.post'))
        hkutils.string_to_file('Message-Id: mess2',
                               self.postFileName('2.post'))
        postdb = self.createPostDB()
        self.assertEquals(set(postdb.heapids()), set(['1', '2']))
        self.assertEquals(postdb.next_heapid(), '3')
        self.assertEquals(postdb.next_heapid(), '4')
        p1 = postdb.post('1')
        p2 = postdb.post('2')
        self.assertEquals(set([p1, p2]), set(postdb.posts()))
        self.assert_(p1 is postdb.post_by_messid('mess1'))
        self.assert_(p2 is postdb.post_by_messid('mess2'))

    def testModifications(self):
        """Tests the 'set' methods of PostDB."""

        # Initialisation
        self.createDirs()
        postfile1 = self.postFileName('1.post')
        postfile2 = self.postFileName('2.post')
        hkutils.string_to_file('Message-Id: mess1', postfile1)
        hkutils.string_to_file('Message-Id: mess2', postfile2)
        postdb = self.createPostDB()
        p1 = postdb.post('1')
        p2 = postdb.post('2')

        # Modifying and saving a post
        p1.set_subject('subject')
        self.assertEquals('Message-Id: mess1',
                          hkutils.file_to_string(postfile1))
        self.assertEquals('Message-Id: mess2',
                          hkutils.file_to_string(postfile2))
        postdb.save()
        postfile1_str = 'Subject: subject\nMessage-Id: mess1\n\n\n'
        self.assertEquals(postfile1_str,
                          hkutils.file_to_string(postfile1))
        self.assertEquals('Message-Id: mess2',
                          hkutils.file_to_string(postfile2))
        
        # Adding a new post
        postfile3 = self.postFileName('3.post')
        p3 = Post.from_str('Subject: subject3')
        postdb.add_new_post(p3)
        self.assertEquals(set(postdb.heapids()), set(['1', '2', '3']))
        self.assertFalse(os.path.exists(postfile3))
        postdb.save()
        self.assert_(os.path.exists(postfile3))

        # Deleting a post
        self.assertEquals(set([p1, p2, p3]), set(postdb.posts()))
        self.assertEquals(set([p1, p2, p3]), set(postdb.real_posts()))
        p1.delete()
        self.assertEquals(set([p2, p3]), set(postdb.posts()))
        self.assertEquals(set([p1, p2, p3]), set(postdb.real_posts()))

    def test_reload(self):

        # Initialization
        self.createDirs()
        postdb = self.createPostDB()
        postdb.add_new_post(Post.from_str(''))
        p1 = postdb.post('0')

        # Saving a subject; setting a new one but abandoning it
        p1.set_subject('sub1')
        postdb.save()

        # A change that will be lost.
        p1.set_subject('sub2')

        # A change on the disk that will be loaded.
        hkutils.string_to_file('Subject: sub_new', self.postFileName('x.post'))

        postdb.reload()
        postdb.save()

        # The subject of p1 is unchanged, x.mail is loaded
        self.assertEquals(p1.subject(), 'sub1')
        self.assert_(postdb.post('0') is p1)
        self.assertEquals(
            hkutils.file_to_string(p1.postfilename()),
            'Subject: sub1\n\n\n')
        self.assertEquals(postdb.post('x').subject(), 'sub_new')

    def testThreadstructHeapid(self):
        """Testing that the thread structure also works when the Parent
        is defined by a heapid.
        
        If the same messid and heapid exist, the former has priority."""

        # 1 <- 2
        # 3
        # 4 <- 5
        self.createDirs()
        postdb = self.createPostDB()
        postdb.add_new_post(Post.from_str(''))               # #0
        postdb.add_new_post(Post.from_str('Parent: 0')) # #1
        postdb.add_new_post(Post.from_str(''))               # #2
        postdb.add_new_post(Post.from_str('Message-Id: 2'))  # #3
        postdb.add_new_post(Post.from_str('Parent: 2')) # #4

        ts = {None: ['0', '2', '3'],
              '0': ['1'],
              '3': ['4']}
        self.assertEquals(ts, postdb.threadstruct())


class TestPostDB2(unittest.TestCase, PostDBHandler):

    def setUp(self):
        self.setUpDirs()
        self._postdb = self.createPostDB()
        self.create_threadst()

    def tearDown(self):
        self.tearDownDirs()

    def test_threadstruct(self):
        """Tests the thread structure computing method."""

        postdb = self._postdb
        # Testing PostDB.threadstruct

        ts = {None: ['0', '4'],
              '0': ['1', '3'],
              '1': ['2']}
        self.assertEquals(ts, postdb.threadstruct())

        # Modifying the PostDB
        self.add_post(5, 0)
        ts = {None: ['0', '4'],
              '0': ['1', '3', '5'],
              '1': ['2']}
        self.assertEquals(ts, postdb.threadstruct())

        # Deleting a post
        postdb.post('1').delete()
        ts = {None: ['0', '2', '4'],
              '0': ['3', '5']}
        self.assertEquals(ts, postdb.threadstruct())

        postdb.post('0').delete()
        ts = {None: ['2', '3', '4', '5']}
        self.assertEquals(ts, postdb.threadstruct())

        postdb.post('2').delete()
        postdb.post('3').delete()
        postdb.post('4').delete()
        postdb.post('5').delete()
        ts = {None: []}
        self.assertEquals(ts, postdb.threadstruct())

    def test_iter_thread(self):
        postdb = self._postdb
        p = self._posts

        def test(post, result):
            self.assertEquals(result, \
                              [ p.heapid() for p in postdb.iter_thread(post)])

        test(None, ['0', '1', '2', '3', '4'])
        test(p[0], ['0', '1', '2', '3'])
        test(p[1], ['1', '2'])
        test(p[2], ['2'])
        test(p[3], ['3'])
        test(p[4], ['4'])

        # if the post is not in the postdb, AssertionError will be raised
        def f():
            test(Post.from_str(''), [])
        self.assertRaises(AssertionError, f)
    
    def test_parent(self):
        postdb = self._postdb

        def test(post_heapid, parent_heapid):
            if parent_heapid != None:
                parentpost = postdb.post(parent_heapid)
            else:
                parentpost = None
            self.assertEquals(postdb.parent(postdb.post(post_heapid)), \
                              parentpost)

        test('0', None)
        test('1', '0')
        test('2', '1')
        test('3', '0')
        test('4', None)

    def test_root(self):
        postdb = self._postdb

        def test(post_heapid, parent_heapid):
            if parent_heapid != None:
                parentpost = postdb.post(parent_heapid)
            else:
                parentpost = None
            self.assertEquals(postdb.root(postdb.post(post_heapid)), \
                              parentpost)

        test('0', '0')
        test('1', '0')
        test('2', '0')
        test('3', '0')
        test('4', '4')

    def threadstruct_cycle_general(self, parents, threadstruct, cycles):
        """The general function that tests the cycle detection of the thread
        structure computing method.

        It modifies the post database according to the parents argument,
        then checks that the thread structture and the cycles of the modified
        database are as expected.
        
        Arguments:
        parents: Contains child->parent pairs, which indicate that the child
            post should be modified as if it were a reply to parent.
            Type: dict(heapid, heapid)
        threadstruct: The excepted thread structure.
            Type: dict(None | heapid, [heapid])
        cycles: Posts that are in a cycle.
            Type: [heapid]
        """

        postdb = self._postdb
        p = self._posts
        for child, parent in parents.items():
            postdb.post(child).set_parent(parent)
        self.assertEquals(threadstruct, postdb.threadstruct())
        self.assert_(postdb.cycles().is_set(cycles))
        if cycles == []:
            self.assertFalse(postdb.has_cycle())
        else:
            self.assert_(postdb.has_cycle())

    def test_threadstruct_cycle__1(self):
        self.threadstruct_cycle_general(
            {},
            {None: ['0', '4'],
             '0': ['1', '3'],
             '1': ['2']},
            [])

    def test_threadstruct_cycle__2(self):
        self.threadstruct_cycle_general(
            {'1': '2'},
            {None: ['0', '4'],
                  '0': ['3'],
                  '1': ['2'],
                  '2': ['1']},
            ['1', '2'])

    def test_threadstruct_cycle__3(self):
        self.threadstruct_cycle_general(
            {'0': '2'},
            {None: ['4'],
             '0': ['1', '3'],
             '1': ['2'],
             '2': ['0']},
            ['0', '1', '2', '3'])

    def test_threadstruct_cycle__4(self):
        self.threadstruct_cycle_general(
            {'0': '0'},
            {None: ['4'],
             '0': ['0', '1', '3'],
             '1': ['2']},
            ['0', '1', '2', '3'])


class Test_PostSet(unittest.TestCase, PostDBHandler):

    """Tests the PostSet class."""

    def setUp(self):
        self.setUpDirs()

        # 1 <- 2
        #      3
        postfile1 = self.postFileName('1.post')
        postfile2 = self.postFileName('2.post')
        postfile3 = self.postFileName('3.post')
        hkutils.string_to_file('Message-Id: 1@', postfile1)
        hkutils.string_to_file('Message-Id: 2@\nParent: 1@', postfile2)
        hkutils.string_to_file('Message-Id: 3@\nParent: 1@', postfile3)
        self._postdb = self.createPostDB()

    def tearDown(self):
        self.tearDownDirs()

    def test__empty(self):
        postdb = self._postdb
        p1 = postdb.post('1')
        p2 = postdb.post('2')
        ps1 = PostSet(postdb, set())

        self.assertNotEquals(ps1, set())
        self.assert_(ps1 != set())
        self.assertFalse(ps1 == set())
        self.assert_(ps1.is_set(set()))

        self.assertEquals(ps1, PostSet(postdb, []))
        self.assert_(ps1 == PostSet(postdb, []))
        self.assertFalse(ps1 != PostSet(postdb, []))

    def test_copy(self):
        """Tests PostSet.copy and PostSet.empty_clone."""

        postdb = self._postdb
        ps_all = self._postdb.all().copy()
        p1 = postdb.post('1')
        p2 = postdb.post('2')
        p3 = postdb.post('3')

        ps1 = ps_all.copy()
        self.assert_(ps1 == ps_all)
        self.assertFalse(ps1 != ps_all)
        self.assertFalse(ps1 is ps_all)

        ps1.remove(p1)
        self.assertFalse(ps1 == ps_all)
        self.assert_(ps1 != ps_all)

        self.assert_(ps_all.is_set(set([p1, p2, p3])))
        self.assert_(ps1.is_set(set([p2, p3])))
        self.assert_(ps_all._postdb is ps1._postdb)

        ps2 = ps_all.empty_clone()
        self.assert_(ps_all.is_set(set([p1, p2, p3])))
        self.assert_(ps2.is_set(set([])))
        self.assert_(ps_all._postdb is ps2._postdb)

    def test__1(self):
        postdb = self._postdb
        p1 = postdb.post('1')
        p2 = postdb.post('2')
        p3 = postdb.post('3')

        # __init__, _to_set
        ps0 = PostSet(postdb, set([p1]))
        ps02 = PostSet(postdb, [p1])
        ps03 = PostSet(postdb, p1)
        psh1= PostSet(postdb, set(['1']))
        psh2 = PostSet(postdb, ['1'])
        psh3 = PostSet(postdb, '1')
        psh4 = PostSet(postdb, 1)
        self.assertEquals(ps0, ps02)
        self.assertEquals(ps0, ps03)
        self.assertEquals(ps0, psh1)
        self.assertEquals(ps0, psh2)
        self.assertEquals(ps0, psh3)
        self.assertEquals(ps0, psh4)

        ps01 = postdb.postset(set([p1]))
        ps02 = postdb.postset([p1])
        ps03 = postdb.postset(p1)
        psh1= postdb.postset(set(['1']))
        psh2 = postdb.postset(['1'])
        psh3 = postdb.postset('1')
        psh3 = postdb.postset(1)
        self.assertEquals(ps0, ps01)
        self.assertEquals(ps0, ps02)
        self.assertEquals(ps0, ps03)
        self.assertEquals(ps0, psh1)
        self.assertEquals(ps0, psh2)
        self.assertEquals(ps0, psh3)
        self.assertEquals(ps0, psh4)

        ps1 = PostSet(postdb, set([p1, p2]))
        ps2 = PostSet(postdb, set([p2, p3]))
        ps3 = PostSet(postdb, [p2, p3])
        ps4 = PostSet(postdb, ps3)
        self.assertNotEquals(ps1, ps2)
        self.assertEquals(ps2, ps3)
        self.assertEquals(ps2, ps4)

        def f():
            PostSet(postdb, 'nosuchpost')
        self.assertRaises(KeyError, f)

        def f():
            PostSet(postdb, 1.0)
        self.assertRaises(TypeError, f)

        # is_set
        self.assert_(ps0.is_set(set([p1])))
        self.assert_(ps0.is_set([p1]))
        self.assert_(ps0.is_set(p1))
        self.assert_(ps1.is_set((p1, p2)))
        self.assert_(ps1.is_set([p1, p2]))
        self.assert_(ps2.is_set(ps3))

        # &, |, -, ^
        ps1 = PostSet(postdb, [p1, p2])
        ps2 = PostSet(postdb, [p1, p3])
        ps3 = PostSet(postdb, [p2, p3])
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

        # PostDB.all
        ps_all = PostSet(postdb, [p1, p2, p3])
        ps2 = PostSet(postdb, set([p2, p3]))
        self.assertEquals(ps_all, postdb.all())
        p1.delete()
        self.assertEquals(ps2, postdb.all())

        # clear, update
        ps1.clear()
        self.assert_(ps1.is_set([]))
        ps1.update(set([p1, p2]))
        self.assert_(ps1.is_set([p1, p2]))

    def test_get_attr(self):
        """Tests the PostSet.__get_attr__ method."""

        postdb = self._postdb
        def f():
            PostSet(postdb, []).nonexisting_method
        self.assertRaises(AttributeError, f)

    def test_forall(self):
        """Tests the PostSet.forall method."""

        def testSubjects(s1, s2, s3):
            self.assertEquals(s1, p1.subject())
            self.assertEquals(s2, p2.subject())
            self.assertEquals(s3, p3.subject())

        postdb = self._postdb
        p1 = postdb.post('1')
        p2 = postdb.post('2')
        p3 = postdb.post('3')
        testSubjects('', '', '')

        PostSet(postdb, []).forall.set_subject('x')
        testSubjects('', '', '')
        PostSet(postdb, [p1]).forall.set_subject('x')
        testSubjects('x', '', '')
        postdb.all().forall(lambda p: p.set_subject('z'))
        testSubjects('z', 'z', 'z')
        postdb.all().forall.set_subject('y')
        testSubjects('y', 'y', 'y')

        # Nonexisting methods will cause exceptions...
        def f():
            postdb.all().forall.nonexisting_method()
        self.assertRaises(AttributeError, f)

        # ...unless the postset is empty
        PostSet(postdb, []).forall.nonexisting_method()
        testSubjects('y', 'y', 'y')

    def test_collect(self):
        """Tests the PostSet.collect method."""

        postdb = self._postdb
        p1 = postdb.post('1')
        p1.set_tags(['t1'])
        p2 = postdb.post('2')
        p2.set_tags(['t2'])
        p3 = postdb.post('3')
        p3.set_tags(['t1'])

        ps1 = postdb.all().collect.has_tag('t1')
        self.assert_(ps1.is_set([p1, p3]))
        ps2 = postdb.all().collect(lambda p: False)
        self.assert_(ps2.is_set([]))
        ps3 = postdb.all().collect(lambda p: True)
        self.assert_(ps3.is_set([p1, p2, p3]))
        ps4 = postdb.all().collect(lambda p: p.has_tag('t1'))
        self.assert_(ps4.is_set([p1, p3]))

        def f():
            postdb.all().collect(lambda p: None)
        self.assertRaises(AssertionError, f)

        ps_roots = postdb.all().collect.is_root()
        self.assert_(ps_roots.is_set([p1]))


class Test_PostSet__threads(unittest.TestCase, PostDBHandler):

    """Tests thread centric methods of the PostSet class."""

    # Thread structure:
    # 0 <- 1 <- 2
    #   <- 3
    # 4

    def setUp(self):
        self.setUpDirs()
        self._postdb = self.createPostDB()
        self.create_threadst()

    def tearDown(self):
        self.tearDownDirs()

    def _test_exp(self, methodname):
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

        def test_exp_2(heapids_1, heapids_2):
            p = self._posts
            posts_1 = [ self._posts[int(i)] for i in heapids_1 ]
            posts_2 = [ self._posts[int(i)] for i in heapids_2 ]
            ps = PostSet(self._postdb, posts_1)

            # Testing that the real output is the expected output.
            self.assert_(eval('ps.' + methodname + '()').is_set(posts_2))

            # Testing that the exp() method did not change ps
            self.assert_(ps.is_set(posts_1))

        return test_exp_2

    def test_expb(self):
        test = self._test_exp('expb')

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

    def test_expf(self):
        test = self._test_exp('expf')

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

    def test_exp(self):
        test = self._test_exp('exp')

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
    
    def test_sorted_list(self):
        ps = self._postdb.postset(self._posts)
        self.assertEquals(ps.sorted_list(), self._posts)


class Test_Html(unittest.TestCase):

    def test_escape(self):

        def test(unescaped, escaped):
            self.assertEquals(Html.escape(unescaped), escaped)

        test('a<b', 'a&lt;b')
        test('a>b', 'a&gt;b')
        test('a&b', 'a&amp;b')

    def test_doc_header(self):
        r = re.compile(
                '<title>mytitle</title>.*'
                '<link rel=stylesheet href="mycss" type="text/css">.*'
                '<h1 id="header">myh1</h1>',
                re.IGNORECASE | re.DOTALL)
        search = r.search(Html.doc_header('mytitle', 'myh1', 'mycss'))
        self.assertNotEquals(search, None)

    def test_link(self):
        self.assertEquals(Html.link('mylink', 'mystuff'),
                          '<a href="mylink">mystuff</a>')

    def test_enclose(self):
        self.assertEquals(Html.enclose('myclass', 'mystuff'),
                          '<span class="myclass">mystuff</span>')
        self.assertEquals(Html.enclose('myclass', 'mystuff', 'mytag'),
                          '<mytag class="myclass">mystuff</mytag>')

    def test_post_summary(self):
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

    def test_list(self):
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


class Test_Generator(unittest.TestCase, PostDBHandler):

    """Tests the Generator class."""

    def setUp(self):
        self.setUpDirs()
        self._orig_workingdir = os.getcwd()

    def tearDown(self):
        os.chdir(self._orig_workingdir)
        self.tearDownDirs()

    def p(self, postindex):
        return self._posts[postindex]

    def init(self, create_threadst=True):
        postdb = self._postdb = self.createPostDB()
        g = Generator(postdb)
        if create_threadst:
            self.create_threadst()
        return postdb, g, self.p

    def index_html(self):
        index_html_name = os.path.join(self._html_dir, 'index.html')
        return hkutils.file_to_string(index_html_name)

    def test_settle_files_to_copy(self):
        
        postdb, g, p = self.init()

        orig_cssfile = os.path.join(self._dir, 'my.css')
        new_cssfile = os.path.join(postdb.html_dir(), 'my.css')
        hkutils.string_to_file('css content', orig_cssfile)
        self.assertFalse(os.path.exists(new_cssfile))

        genopts = GeneratorOptions()
        genopts.cssfile = 'my.css'
        os.chdir(self._dir)
        g.settle_files_to_copy(genopts)
        self.assert_(os.path.exists(new_cssfile))

    def test_post(self):

        def subheader(content):
             return Html.enclose(tag='div', class_=None, id='subheader',
                                 content=content, newlines=True)

        postdb, g, p = self.init()
        
        genopts = GeneratorOptions()
        genopts.sections = [Section('Sec1', [p(1)]),
                            Section('Sec2', [p(4)])]

        h1 = Html.escape('author0') + ': ' + Html.escape('subject0')
        self.assertEquals(
            g.post(p(0), genopts),
            Html.doc_header(h1, h1, 'heapindex.css') +
            subheader(
                Html.link('index.html', 'Back to the index') + '\n' +
                Html.enclose('index', Html.escape('<0>')) + '\n') +
            Html.enclose('postbody', Html.escape('body0\n'), tag='pre') +
            Html.doc_footer())

        # Printing date

        def date_fun(post, genopts2):
            return 'date%s' % (self._posts.index(post),)
        genopts.date_fun = date_fun

        h1 = Html.escape('author0') + ': ' + Html.escape('subject0')
        self.assertEquals(
            g.post(p(0), genopts),
            Html.doc_header(h1, h1, 'heapindex.css') +
            subheader(
                Html.link('index.html', 'Back to the index') + '\n' +
                Html.enclose('index', Html.escape('<0>')) + '\n') +
            Html.enclose('date', 'date0') + '\n' +
            Html.enclose('postbody', Html.escape('body0\n'), tag='pre') +
            Html.doc_footer())
        
        # Printing thread

        genopts.date_fun = lambda post, genopts: None
        genopts.print_thread_of_post = True
        gen_post_html = g.post(p(2), genopts)
        
        genopts.section = Section('Thread', [p(2)])
        h1 = Html.escape('author2') + ': ' + Html.escape('subject2')
        my_post_html = \
            (Html.doc_header(h1, h1, 'heapindex.css') +
             subheader(
                 Html.link('index.html', 'Back to the index') + '\n' +
                 Html.enclose('index', Html.escape('<2>')) + '\n') +
             g.thread(p(0), genopts) +
             Html.enclose('postbody', Html.escape('body2\n'), tag='pre') +
             Html.doc_footer())
        del genopts.section

        self.assertEquals(
            gen_post_html,
            my_post_html)

    def test_index_toc(self):
        postdb, g, p = self.init(create_threadst=False)
        self.create_threadst(skipdates=True)
        
        genopts = GeneratorOptions()
        sections = [Section('Sec1', [p(1)]),
                    Section('Sec2', [p(4)])]

        self.assertEquals(
            g.index_toc(sections, genopts),
            Html.list(
                [Html.link('#section_0', 'Sec1'),
                 Html.link('#section_1', 'Sec2')],
                'tableofcontents'))

    def test_post_summary(self):
        postdb, g, p = self.init()
        div = Html.post_summary_div

        genopts = GeneratorOptions()
        genopts.sections = [Section('Sec1', [p(1)]),
                            Section('Sec2', [p(4)])]
        genopts.section = genopts.sections[0]

        # basic case
        self.assertEquals(
            g.post_summary(p(0), genopts),
            div('0.html', 'author0', 'subject0', [], '0', None, False))

        # subject
        self.assertEquals(
            g.post_summary(p(0), genopts, 'mysubject'),
            div('0.html', 'author0', 'mysubject', [], '0', None, False))

        self.assertEquals(
            g.post_summary(p(0), genopts, STAR),
            div('0.html', 'author0', STAR, [], '0', None, False))

        # tags
        self.assertEquals(
            g.post_summary(p(0), genopts,tags=['t1','t2']),
            div('0.html', 'author0', 'subject0', ['t1', 't2'], '0', None,
                False))

        self.assertEquals(
            g.post_summary(p(0), genopts, tags=STAR),
            div('0.html', 'author0', 'subject0', STAR, '0', None, False))

    def test_post_summary__flat(self):
        postdb, g, p = self.init()

        genopts = GeneratorOptions()
        genopts.sections = [Section('Sec1', [p(1)], is_flat=True),
                            Section('Sec2', [p(4)])]
        genopts.section = genopts.sections[0]

        table = Html.post_summary_table
        self.assertEquals(
            g.post_summary(p(0), genopts),
            table('0.html', 'author0', 'subject0', [], '0', None, False))

    def test_post_summary__date(self):
        
        def date_fun(post, genopts2):
            self.assertEquals(post.heapid(), str((self._posts.index(post))))
            return 'date%s' % (self._posts.index(post),)

        postdb, g, p = self.init()

        genopts = GeneratorOptions()
        genopts.date_fun = date_fun
        genopts.sections = [Section('Sec1', [p(1)]),
                            Section('Sec2', [p(4)])]
        genopts.section = genopts.sections[0]

        div = Html.post_summary_div
        self.assertEquals(
            g.post_summary(p(0), genopts),
            div('0.html', 'author0', 'subject0', [], '0', 'date0', False))

    def test_thread(self):
        postdb, g, p = self.init()

        genopts = GeneratorOptions()
        genopts.sections = [Section('Sec1', [p(1)]),
                            Section('Sec2', [p(4)])]
        genopts.section = genopts.sections[0]

        self.assertEquals(
            g.thread(p(4), genopts),
            g.post_summary(p(4), genopts, thread_link='thread_4.html') +
            g.post_summary_end())

        self.assertEquals(
            g.thread(p(0), genopts),
            g.post_summary(p(0), genopts, thread_link='thread_0.html') +
            g.post_summary(p(1), genopts) +
            g.post_summary(p(2), genopts) +
            g.post_summary_end() + # end of 2
            g.post_summary_end() + # end of 1
            g.post_summary(p(3), genopts) +
            g.post_summary_end() + # end of 3
            g.post_summary_end()) # end of 0

        genopts.sections = [Section('Sec', [p(1), p(4)])]
        genopts.section = genopts.sections[0]

        self.assertEquals(
            g.thread(None, genopts),
            g.post_summary(self._posts[0], genopts) +
            g.post_summary(self._posts[1], genopts) +
            g.post_summary(self._posts[2], genopts) +
            g.post_summary_end() + # end of 2
            g.post_summary_end() + # end of 1
            g.post_summary(self._posts[3], genopts) +
            g.post_summary_end() + # end of 3
            g.post_summary_end() + # end of 0
            g.post_summary(self._posts[4], genopts) +
            g.post_summary_end()) # end of 4

    def test_thread__shortsubject(self):
        postdb, g, p = self.init()

        genopts = GeneratorOptions()
        genopts.sections = [Section('Sec', [p(1), p(4)])]
        genopts.section = genopts.sections[0]
        genopts.shortsubject = True

        # All posts have the same subject.

        for i in range(5):
            p(i).set_subject('subject')

        self.assertEquals(
            g.thread(None, genopts),
            g.post_summary(p(0), genopts) +
            g.post_summary(p(1), genopts, subject=STAR) +
            g.post_summary(p(2), genopts, subject=STAR) +
            g.post_summary_end() + # end of 2
            g.post_summary_end() + # end of 1
            g.post_summary(p(3), genopts, subject=STAR) +
            g.post_summary_end() + # end of 3
            g.post_summary_end() + # end of 0
            g.post_summary(p(4), genopts) +
            g.post_summary_end()) # end of 4

        # All but one posts have the same subject.

        p(3).set_subject('subject3')

        self.assertEquals(
            g.thread(None, genopts),
            g.post_summary(p(0), genopts) +
            g.post_summary(p(1), genopts, subject=STAR) +
            g.post_summary(p(2), genopts, subject=STAR) +
            g.post_summary_end() + # end of 2
            g.post_summary_end() + # end of 1
            g.post_summary(p(3), genopts) +
            g.post_summary_end() + # end of 3
            g.post_summary_end() + # end of 0
            g.post_summary(p(4), genopts) +
            g.post_summary_end()) # end of 4

    def test_thread__cycles(self):
        postdb, g, p = self.init()
        p(1).set_parent('2')

        genopts = GeneratorOptions()
        genopts.sections = [Section('Sec', [p(1), p(4)])]
        genopts.section = genopts.sections[0]

        # One thread.
        self.assertEquals(
            g.thread(p(0), genopts),
            g.post_summary(p(0), genopts, thread_link='thread_0.html') +
            g.post_summary(p(3), genopts) +
            g.post_summary_end() + # end of 3
            g.post_summary_end()) # end of 0

        # All threads.

        self.assertEquals(
            g.thread(None, genopts),
            g.post_summary(p(0), genopts) +
            g.post_summary(p(3), genopts) +
            g.post_summary_end() + # end of 3
            g.post_summary_end() + # end of 0
            g.post_summary(p(4), genopts) +
            g.post_summary_end()) # end of 4

    def test_section(self):
        postdb, g, p = self.init()

        # Tests empty section.
        genopts = GeneratorOptions()
        genopts.sections = [Section('Sec', [])]
        genopts.section = genopts.sections[0]

        self.assertEquals(
            g.section(0, genopts),
            Html.section_begin('section_0', 'Sec') +
            Html.section_end())

        # Tests where not every post is in the section.
        genopts = GeneratorOptions()
        genopts.sections = [Section('Sec1', [p(1)]),
                            Section('Sec2', [p(4)])]
        genopts.section = genopts.sections[0]

        self.assertEquals(
            g.section(0, genopts),
            Html.section_begin('section_0', 'Sec1') +
            g.thread(p(0), genopts) +
            Html.section_end())

        # Tests where more than one threads are in the section.
        genopts = GeneratorOptions()
        genopts.sections = [Section('Sec', [p(1), p(4)])]
        genopts.section = genopts.sections[0]

        self.assertEquals(
            g.section(0, genopts),
            Html.section_begin('section_0', 'Sec') +
            g.thread(p(0), genopts) +
            g.thread(p(4), genopts) +
            Html.section_end())

    def flat_result(self, generator, genopts, posts):
        """Prints the posts flatly and puts them into a section called
        'Sec', which should have index 0."""
        return \
            (Html.section_begin('section_0', 'Sec') +
             Html.enclose(
                 'flatlist',
                 ''.join([ generator.post_summary(post, genopts)
                           for post in posts ]),
                 tag='table', newlines=True) +
             Html.section_end())

    def test_section__flat(self):
        postdb, g, p = self.init()

        # Tests flat printing with list.
        genopts = GeneratorOptions()
        genopts.sections = [Section('Sec', [p(1), p(4)])]
        genopts.section = genopts.sections[0]
        genopts.section.is_flat = True

        self.assertEquals(
            g.section(0, genopts),
            self.flat_result(g, genopts, [p(1), p(4)]))

        # Tests flat printing with list in the reversed order.
        genopts = GeneratorOptions()
        genopts.sections = [Section('Sec', [p(4), p(1)])]
        genopts.section = genopts.sections[0]
        genopts.section.is_flat = True

        self.assertEquals(
            g.section(0, genopts),
            self.flat_result(g, genopts, [p(4), p(1)]))

        # Tests flat printing with PostSet.
        genopts = GeneratorOptions()
        genopts.sections = [Section('Sec', postdb.postset([p(1), p(4)]))]
        genopts.section = genopts.sections[0]
        genopts.section.is_flat = True
        self.assertEquals(
            g.section(0, genopts),
            self.flat_result(g, genopts, [p(1), p(4)]))

    def test_section__cycle(self):
        postdb, g, p = self.init()
        p(1).set_parent('2')

        # Tests empty section.
        genopts = GeneratorOptions()
        genopts.sections = [Section('Sec', CYCLES)]
        genopts.section = genopts.sections[0]
        genopts.postdb = postdb

        self.assertEquals(
            g.section(0, genopts),
            self.flat_result(g, genopts, [p(1), p(2)]))

    def test_gen_indices(self):

        postdb, g, p = self.init()

        index = Index()
        index.sections = [Section('Sec1', [p(1)]),
                          Section('Sec2', [p(4)])]

        genopts = GeneratorOptions()
        genopts.indices = [index]
        genopts.write_toc = False
        genopts.html_title = 'myhtmltitle'
        genopts.html_h1 = 'myhtmlh1'
        genopts.cssfile = 'mycssfile'

        os.chdir(self._dir)
        hkutils.string_to_file('css content', 'mycssfile')

        genopts.section = index.sections[0]
        section0_html = g.section(0, genopts)
        genopts.section = index.sections[1]
        section1_html = g.section(1, genopts)
        del genopts.section

        # normal

        g.gen_indices(genopts)
        self.assertEquals(
            self.index_html(),
            Html.doc_header('myhtmltitle', 'myhtmlh1', 'mycssfile') +
            section0_html +
            section1_html +
            Html.doc_footer())

        # write_toc option

        genopts.write_toc = True
        g.gen_indices(genopts)

        self.assertEquals(
            self.index_html(),
            Html.doc_header('myhtmltitle', 'myhtmlh1', 'mycssfile') +
            g.index_toc(index.sections, genopts) +
            section0_html +
            section1_html +
            Html.doc_footer())

    def test_gen_posts(self):

        postdb, g, p = self.init()

        index = Index()
        index.sections = [Section('Sec1', [p(1)]),
                          Section('Sec2', [p(4)])]

        genopts = GeneratorOptions()
        genopts.indices = [index]
        genopts.html_title = 'myhtmltitle'
        genopts.html_h1 = 'myhtmlh1'
        genopts.cssfile = 'mycssfile'
        genopts.trycopyfiles = False

        # normal

        g.gen_posts(genopts)
        post0_htmlfile = os.path.join(self._html_dir, '0.html')
        post0_htmlstr = hkutils.file_to_string(post0_htmlfile)

        self.assertEquals(
            post0_htmlstr,
            g.post(p(0), genopts))


if __name__ == '__main__':
    set_log(False)
    unittest.main()
