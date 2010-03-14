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

import ConfigParser
import itertools
import os
import os.path
import re
import shutil
import StringIO
import tempfile
import unittest

import hkutils
import hklib


class Test__logging(unittest.TestCase):

    """Tests the logging functions of hklib."""

    def test__1(self):

        """Tests the following functions:

        - :func:`hklib.set_log`
        - :func:`hklib.log`
        """

        # We use a custom log function
        old_log_fun = hklib.log_fun
        def log_fun(*args):
            log.append(list(args))
        hklib.set_log(log_fun)

        # Test logging
        log = []
        hklib.log('first line', 'second line')
        hklib.log('third line')
        self.assertEquals(
            log,
            [['first line', 'second line'],
             ['third line']])

        # Setting the original logging function back
        hklib.set_log(old_log_fun)


class PostDBHandler(object):

    """Helps implementing the tester classes by containing functions commonly
    used by them."""

    # Creating an ordered array of dates. (Increment the number after `range`
    # if you need more posts.)
    dates = [ 'Date: Wed, 20 Aug 2008 17:41:0%d +0200\n' % i \
              for i in range(10) ]

    def setUpDirs(self):
        """Sets up the following temporary directories:

        - tempdir/heaps/my_heap
        - tempdir/heaps/my_other_heap
        - tempdir/html

        Also, it redirects the logging into a variable.
        """

        self._dir = tempfile.mkdtemp()
        self._heaps_dir = os.path.join(self._dir, 'heaps_dir')
        self._myheap_dir = os.path.join(self._heaps_dir, 'my_heap_dir')
        self._myotherheap_dir = \
            os.path.join(self._heaps_dir, 'my_other_heap_dir')
        self._html_dir = \
            os.path.join(self._dir, 'html_dir')
        self._html_myheap_dir = \
            os.path.join(self._html_dir, 'my_heap_dir')
        self._html_myotherheap_dir = \
            os.path.join(self._html_dir, 'my_other_heap_dir')
        os.mkdir(self._heaps_dir)
        os.mkdir(self._myheap_dir)
        os.mkdir(self._myotherheap_dir)
        os.mkdir(self._html_dir)
        os.mkdir(self._html_myheap_dir)
        os.mkdir(self._html_myotherheap_dir)

        # We use a custom log function
        self._log = []
        self._old_log_fun = hklib.log_fun
        def log_fun(*args):
            self._log.append(''.join(args))
        hklib.set_log(log_fun)

    def tearDownDirs(self):
        """Removes the temporary directories and checks that no logs are
        left."""

        shutil.rmtree(self._dir)

        # Setting the original logging function back
        self.assertEquals(self._log, [])
        hklib.set_log(self._old_log_fun)

    def create_postdb(self):
        """Creates a post database.

        Two heaps will be added: ``'my_heap'`` and ``'my_other_heap'``.

        **Returns:** |PostDB|
        """

        postdb = hklib.PostDB()
        postdb.add_heap('my_heap', self._myheap_dir)
        postdb.add_heap('my_other_heap', self._myotherheap_dir)
        postdb.set_html_dir(self._html_dir)
        self._postdb = postdb
        return postdb

    def add_post(self, index, parent=None, messid=None, heap_id='my_heap'):
        """Adds a new post to the post database.

        The attributes of the post will be created as follows:

        - The author will be 'author'+index.
        - The subject will be 'subject'+index.
        - The message id will be index+'@'.
        - The parent will be `parent`, if specified.
        - If self._skipdates is False, the post with a newer index will
          have a newer date; otherwise the post will not have a date.
        - The body will be 'body'+index.
        """

        # Actually would not be necessary to specify the `index` parameter for
        # this function, but it is done so that here we can check that the
        # caller knows what will be the post index of the post created.
        post_index = self._postdb.next_post_index(heap_id)
        self.assertEquals(str(index), post_index)

        if messid == None:
            messid = index

        parent = str(parent) + '@' if parent != None else ''
        s = ('Author: author%s\n' % (index,) +
             'Subject: subject%s\n' % (index,) +
             'Message-Id: %s@\n' % (messid,) +
             'Parent: %s\n' % (parent,))
        if not self._skipdates:
            s += PostDBHandler.dates[index] + '\n'
        s += ('\n' +
              'body%s' % (index,))
        post = hklib.Post.from_str(s)
        self._postdb.add_new_post(post, heap_id, post_index)
        return post

    def p(self, prepost):
        """Returns the given post from ``'my_heap'``.

        **Argument:**

        - `prepost` (|PrePost|)

        **Returns:** |Post|
        """

        return self._postdb.post(('my_heap', prepost))

    def po(self, prepost):
        """Returns the given post from ``'my_other_heap'``.

        **Argument:**

        - `prepost` (|PrePost|)

        **Returns:** |Post|
        """

        return self._postdb.post(('my_other_heap', prepost))

    def i(self, index):
        return ('my_heap', str(index))

    def io(self, index):
        return ('my_other_heap', str(index))

    def create_threadst(self, skipdates=False):
        """Adds a posts to the postdb with the following thread structure.

        my_heap::

            0 <- 1 <- 2
              <- 3
            4

        my_other_heap::

            0
        """

        self._skipdates = skipdates

        # We changed the heapid numbering to start from 1 instead of 0. A
        # large portion of the tests would have had to be rewritten as a
        # result, so for the moment, we use this workaround.
        self._postdb._next_post_index[('my_heap', '')] = 0
        self._postdb._next_post_index[('my_other_heap', '')] = 0

        self.add_post(0)
        self.add_post(1, 0)
        self.add_post(2, 1)
        self.add_post(3, 0)
        self.add_post(4)

        self.add_post(0, messid='other0', heap_id='my_other_heap')

    def introduce_cycle(self):
        """Introcudes a cycle in the thread structure."""

        # New thread structure:
        #
        # 0 <- 1 <- 2
        # 4
        # 3 <- 5 <- 6 <- 7
        #  \        ^
        #   -------/
        self.add_post(5, 3),
        self.add_post(6, 5),
        self.add_post(7, 6),
        self.p(3).set_parent(7)

    def pop_log(self):
        """Set the log to empty but return the previous logs.

        **Returns:** str
        """

        log = self._log
        self._log = []
        return '\n'.join(log)


class Test_Post(unittest.TestCase, PostDBHandler):

    """Tests :class:`hklib.Post`."""

    def setUp(self):
        self.setUpDirs()
        self.create_postdb()
        self.create_threadst()

    def tearDown(self):
        self.tearDownDirs()

    def test_is_post_id(self):
        """Tests :func:`hklib.Post.is_post_id`."""

        # post index is a string
        self.assertTrue(hklib.Post.is_post_id(('myheap', 'mypost')))

        # post index is an integer
        self.assertTrue(hklib.Post.is_post_id(('myheap', 0)))

        # post id is a string
        self.assertTrue(hklib.Post.is_post_id('myheap/mypost'))

        # heap id is not a string
        self.assertFalse(hklib.Post.is_post_id((0, 1)))

        # post index is not a string nor an integer
        self.assertFalse(hklib.Post.is_post_id(('myheap', [])))

        # too long tuple
        self.assertFalse(hklib.Post.is_post_id(('myheap', 'mypost', 1)))

        # too short tuple
        self.assertFalse(hklib.Post.is_post_id(('myheap')))

        # not a tuple
        self.assertFalse(hklib.Post.is_post_id(['myheap', 'mypost']))

        # post id is a string but not a correct one
        self.assertFalse(hklib.Post.is_post_id('myheap'))

        # post id is a string but not a correct one
        self.assertFalse(hklib.Post.is_post_id('a/b/c'))

    def test_assert_is_post_id(self):
        """Tests :func:`hklib.Post.assert_is_post_id`."""

        # assertion passes
        self.assertEquals(
            hklib.Post.assert_is_post_id(('myheap', 'mypost')),
            None)

        # assertion fails
        self.assertRaises(
            AssertionError,
            lambda: hklib.Post.assert_is_post_id((0, 1)))

    def test_unify_post_id(self):
        """Tests :func:`hklib.Post.unify_post_id`."""

        # None
        self.assertEquals(
            hklib.Post.unify_post_id(None),
            None)

        # post index is a string
        self.assertEquals(
            hklib.Post.unify_post_id(('myheap', 'mypost')),
            ('myheap', 'mypost'))

        # post index is an integer
        self.assertEquals(
            hklib.Post.unify_post_id(('myheap', 0)),
            ('myheap', '0'))

        # post id is a string
        self.assertTrue(
            hklib.Post.unify_post_id('myheap/mypost'),
            ('myheap', 'mypost'))

    def test_parse_header(self):
        """Tests :func:`hklib.Post.parse_header`."""

        sio = StringIO.StringIO(
                  'Author: author\n'
                  'Subject: subject\n'
                  'Flag: flag1\n'
                  'Message-Id: <0@gmail.com>\n'
                  'Flag: flag2\n'
                  'Date: Wed, 20 Aug 2008 17:41:30 +0200\n')

        self.assertEquals(
            hklib.Post.parse_header(sio),
            {'Author': ['author'],
             'Subject': ['subject'],
             'Message-Id': ['<0@gmail.com>'],
             'Date': ['Wed, 20 Aug 2008 17:41:30 +0200'],
             'Flag': ['flag1', 'flag2']})
        sio.close()

        self.assertRaises(
            hkutils.HkException,
            lambda: hklib.Post.from_str('Malformatted post.'))

    def test_create_header(self):
        """Tests the following functions:

        - :func:`hklib.Post.parse`
        - :func:`hklib.Post.from_str`
        """

        # Testing a normal post.
        #
        # The 'Nosuchattr' attribute is not known to `create_header`, so we
        # should get a warning.
        self.assertEquals(
            hklib.Post.create_header(
                {'Author': ['someone'],
                 'Nosuchattr': ['1', '2']}),
            {'Author': 'someone',
             'Parent': '',
             'Flag': [],
             'Tag': [],
             'Date': '',
             'Message-Id': '',
             'Subject': '',
             'Reference': [],
             'Nosuchattr': ['1', '2']})
        self.assertEquals(
            self.pop_log(),
            'WARNING: Additional attribute in post: "Nosuchattr"')

        # Testing a malformatted post.
        self.assertRaises(
            hkutils.HkException,
            lambda: hklib.Post.from_str('Malformatted post.'))

    def test_parse(self):
        """Tests the following functions:

        - :func:`hklib.Post.create_header`
        - :func:`hklib.Post.__eq__`
        """

        s = ('Author: author\n'
             'Subject: subject\n'
             'Flag: flag1\n'
             'Message-Id: <0@gmail.com>\n'
             'Flag: flag2\n'
             'Date: Wed, 20 Aug 2008 17:41:30 +0200\n')

        d = {'Author': 'author',
             'Subject': 'subject',
             'Message-Id': '<0@gmail.com>',
             'Parent': '',
             'Date': 'Wed, 20 Aug 2008 17:41:30 +0200',
             'Flag': ['flag1', 'flag2'],
             'Tag': [],
             'Reference': []}

        p1 = hklib.Post.from_str(s)
        p2 = hklib.Post.from_str(s + '\n')
        p3 = hklib.Post.from_str(s + '\n\n')
        p4 = hklib.Post.from_str(s + '\n\nHi')
        p5 = hklib.Post.from_str(s + '\n\nHi\n')
        p6 = hklib.Post.from_str(s + '\n\nHi\n\n\n')
        p7 = hklib.Post.from_str(s + '\n\nHi\n\nHi')

        # Checking the post header
        self.assertEquals(p1._header, d)

        # checking the bodies of the posts
        self.assertEquals(p1.body(), '\n')
        self.assertEquals(p2.body(), '\n')
        self.assertEquals(p3.body(), '\n')
        self.assertEquals(p4.body(), 'Hi\n')
        self.assertEquals(p5.body(), 'Hi\n')
        self.assertEquals(p6.body(), 'Hi\n')
        self.assertEquals(p7.body(), 'Hi\n\nHi\n')

        # p1 == p2 == p3 != p4 == p5 == p6
        self.assertEquals(p1, p2)
        self.assertEquals(p1, p3)
        self.assertNotEquals(p1, p4)
        self.assertEquals(p4, p5)
        self.assertEquals(p4, p6)

        p8 = hklib.Post.from_str(s, ('my_heap', 0))
        p9 = hklib.Post.from_str(s, ('my_heap', 0))
        p10 = hklib.Post.from_str(s, ('my_heap', 1))
        p11 = hklib.Post.from_str(s, ('my_other_heap', 0))

        # p8 == p9 != p10 != p11
        self.assertEquals(p8, p9)
        for post1, post2 in itertools.combinations([p8, p10, p11], 2):
            self.assertNotEquals(post1, post2)
            self.assertNotEquals(post2, post1)

    def test__init(self):
        """Tests the following functions:

        - :func:`hklib.Post.__init__`
        - :func:`hklib.Post.from_str`
        - :func:`hklib.Post.create_empty`
        - :func:`hklib.Post.post_id`
        - :func:`hklib.Post.heap_id`
        - :func:`hklib.Post.post_index`
        - :func:`hklib.Post.post_id_str`
        """

        # Empty post
        post = hklib.Post.from_str('')
        self.assertEquals(post.post_id(), None)
        self.assertRaises(hkutils.HkException, lambda: post.heap_id())
        self.assertRaises(hkutils.HkException, lambda: post.post_index())
        self.assertEquals(post.author(), '')
        self.assertEquals(post.subject(), '')
        self.assertEquals(post.messid(), '')
        self.assertEquals(post.parent(), '')
        self.assertEquals(post.date(), '')
        self.assertEquals(post.is_deleted(), False)
        self.assertEquals(post.is_modified(), True)
        self.assertEquals(post.body(), '\n')

        p2 = hklib.Post.create_empty()
        self.assertEquals(post, p2)

        # Normal post without parent
        p0 = self.p(0)
        self.assertEquals(p0.post_id(), ('my_heap', '0'))
        self.assertEquals(p0.heap_id(), 'my_heap')
        self.assertEquals(p0.post_index(), '0')
        self.assertEquals(p0.post_id_str(), 'my_heap/0')
        self.assertEquals(p0.author(), 'author0')
        self.assertEquals(p0.subject(), 'subject0')
        self.assertEquals(p0.messid(), '0@')
        self.assertEquals(p0.parent(), '')
        self.assertEquals(p0.date(), 'Wed, 20 Aug 2008 17:41:00 +0200')
        self.assertEquals(p0.is_deleted(), False)
        self.assertEquals(p0.is_modified(), True)
        self.assertEquals(p0.body(), 'body0\n')

        # Normal post with parent
        p1 = self.p(1)
        self.assertEquals(p1.parent(), '0@')

    def test_from_file(self):
        """Tests :func:`hklib.Post.from_file`."""

        fname = os.path.join(self._dir, 'postfile')
        hkutils.string_to_file(self.p(0).postfile_str(), fname)
        p = hklib.Post.from_file(fname)

        self.assertEquals(p.post_id(), None)
        self.assertEquals(p.author(), 'author0')
        self.assertEquals(p.subject(), 'subject0')
        self.assertEquals(p.messid(), '0@')
        self.assertEquals(p.parent(), '')
        self.assertEquals(p.date(), 'Wed, 20 Aug 2008 17:41:00 +0200')
        self.assertEquals(p.is_deleted(), False)
        self.assertEquals(p.is_modified(), True)
        self.assertEquals(p.body(), 'body0\n')

    def test__modifications(self):
        """Tests the basic functionality of the following functions, by putting
        emphasis on the modification of the post:

        - :func:`hklib.Post.touch`
        - :func:`hklib.Post.is_modified`
        - :func:`hklib.Post.author`
        - :func:`hklib.Post.set_author`
        - :func:`hklib.Post.real_subject`
        - :func:`hklib.Post.subject`
        - :func:`hklib.Post.set_subject`
        - :func:`hklib.Post.messid`
        - :func:`hklib.Post.set_messid`
        - :func:`hklib.Post.parent`
        - :func:`hklib.Post.set_parent`
        - :func:`hklib.Post.date`
        - :func:`hklib.Post.set_date`
        - :func:`hklib.Post.tags`
        - :func:`hklib.Post.set_tags`
        - :func:`hklib.Post.body`
        - :func:`hklib.Post.set_body`
        """

        ## Testing the touch-system

        # Setting is_modified to False by saving the post database
        self._postdb.save()
        p0 = self.p(0)
        self.assertEquals(p0.is_modified(), False)

        # If we touch it, it becomes True
        p0.touch()
        self.assertEquals(p0.is_modified(), True)

        # If we save it, it becomes False again
        p0.save()
        self.assertEquals(p0.is_modified(), False)

        ## Testing concrete modifications

        def check_modified():
            self.assertTrue(p0.is_modified())
            p0._modified = False

        p0.set_author('author2')
        self.assertEquals(p0.author(), 'author2')
        check_modified()

        p0.set_subject('subject2')
        self.assertEquals(p0.subject(), 'subject2')
        self.assertEquals(p0.real_subject(), 'subject2')
        check_modified()

        p0.set_messid('@')
        self.assertEquals(p0.messid(), '@')
        check_modified()

        p0.set_parent('@@')
        self.assertEquals(p0.parent(), '@@')
        check_modified()

        p0.set_date('Wed, 20 Aug 2008 17:41:31 +0200')
        self.assertEquals(p0.date(), 'Wed, 20 Aug 2008 17:41:31 +0200')
        check_modified()

        p0.set_tags(['mytag1', 'mytag2'])
        self.assertEquals(p0.tags(), ['mytag1', 'mytag2'])
        check_modified()

        p0.set_flags(['myflag1', 'myflag2'])
        self.assertEquals(p0.flags(), ['myflag1', 'myflag2'])
        check_modified()

        p0.set_refs(['1', '2'])
        self.assertEquals(p0.refs(), ['1', '2'])
        check_modified()

        p0.set_body('newbody')
        self.assertEquals(p0.body(), 'newbody\n')
        check_modified()

        p0.set_body('\n newbody \n \n')
        self.assertEquals(p0.body(), 'newbody\n')
        check_modified()

        p0.delete()
        self.assertEquals(p0.is_deleted(), True)
        self.assertEquals(p0.post_id(), ('my_heap', '0'))
        self.assertEquals(p0.author(), '')
        self.assertEquals(p0.subject(), '')
        self.assertEquals(p0.messid(), '@')
        self.assertEquals(p0.parent(), '')
        self.assertEquals(p0.date(), '')
        self.assertEquals(p0.is_modified(), True)
        self.assertEquals(p0.body(), '')

    def test_write(self):
        """Tests :func:`hklib.Post.write`.

        The `force_print` argument is tested in :func:`test_postfile_str`."""

        def check_write(input, output):
            """Checks that if a post is read from `input`, it will produce
            `output` when written."""
            p = hklib.Post.from_str(input)
            sio = StringIO.StringIO()
            p.write(sio)
            self.assertEquals(sio.getvalue(), output)
            sio.close()

        # Testing empty post
        check_write('', '\n\n')

        # Testing that the attributes are reordered
        check_write(
            ('Subject: subject\n'
             'Flag: flag1\n'
             'Message-Id: <0@gmail.com>\n'
             'Flag: flag2\n'
             'Date: Wed, 20 Aug 2008 17:41:30 +0200\n'
             'Author: author\n'
             '\n'
             'Body'),
            ('Author: author\n'
             'Subject: subject\n'
             'Message-Id: <0@gmail.com>\n'
             'Date: Wed, 20 Aug 2008 17:41:30 +0200\n'
             'Flag: flag1\n'
             'Flag: flag2\n'
             '\n'
             'Body\n'))

        # Testing when the post has attributes unknown to Hk
        check_write(
            ('Author: author\n'
             'Nosuchattr: something 1\n'
             'Nosuchattr2: something 2\n'
             'Nosuchattr2: something 3\n'),
            ('Author: author\n'
             'Nosuchattr: something 1\n'
             'Nosuchattr2: something 2\n'
             'Nosuchattr2: something 3\n\n\n'))

        self.assertEquals(
            self.pop_log(),
            ('WARNING: Additional attribute in post: "Nosuchattr"\n'
             'WARNING: Additional attribute in post: "Nosuchattr2"'))

    def test_postfile_str(self):
        """Tests :func:`hklib.Post.postfile_str`."""

        # Basic test
        self.assertEquals(
            hklib.Post.from_str('Author: me').postfile_str(),
            'Author: me\n\n\n')

        # Testing empty post
        post_str = ''
        self.assertEquals(
            hklib.Post.from_str('').postfile_str(),
            '\n\n')

        # Testing when force_set is not empty
        post_str = ''
        self.assertEquals(
            hklib.Post.from_str(post_str).\
                postfile_str(force_print=set(['Author'])),
            'Author: \n\n\n')

    def test_meta_dict(self):
        """Tests :func:`hklib.Post.meta_dict`."""

        # empty post
        self.assertEquals(
            hklib.Post.from_str('\n\n').meta_dict(),
            {})

        # meta with value
        self.assertEquals(
            hklib.Post.from_str('\n\n[key value]').meta_dict(),
            {'key': 'value'})

        # meta with value with whitespace
        self.assertEquals(
            hklib.Post.from_str('\n\n[key this is a long value]').meta_dict(),
            {'key': 'this is a long value'})

        # meta without value
        self.assertEquals(
            hklib.Post.from_str('\n\n[key]').meta_dict(),
            {'key': None})

        # no meta because it is no alone in the line
        self.assertEquals(
            hklib.Post.from_str('\n\nx[key value]').meta_dict(),
            {})
        self.assertEquals(
            hklib.Post.from_str('\n\n[key value]x').meta_dict(),
            {})

        # whitespace
        self.assertEquals(
            hklib.Post.from_str('\n\n [ key  value ] ').meta_dict(),
            {'key': 'value'})

        # two metas
        self.assertEquals(
            hklib.Post.from_str('\n\n[key]\n[key2 value2]').meta_dict(),
            {'key': None, 'key2': 'value2'})

        # same meta key twice
        self.assertEquals(
            hklib.Post.from_str('\n\n[key value]\n[key value2]').meta_dict(),
            {'key': 'value2'})

    def test__subject(self):
        """Tests issues related to the subject."""

        def post_ws(subject):
            """Creates a post with the given subject."""
            return hklib.Post.from_str('Subject: ' + subject)

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
        """Tests issues related to tags and flags."""

        p = hklib.Post.from_str('Flag: f1\nFlag: f2\nTag: t1\nTag: t2')
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
        p = hklib.Post.from_str('Flag: f2\nFlag: f1\nTag: t2\nTag: t1')
        self.assertEquals(p.flags(), ['f1', 'f2']) # flags are sorted
        self.assertEquals(p.tags(), ['t1', 't2'])  # tags are sorted

    def test__parse_tags_in_subject(self):
        """Tests the following functions:

        - :func:`hklib.Post.parse_subject`
        - :func:`hklib.Post.normalize_subject`
        """

        def test(subject1, subject2, tags):
            self.assertEquals(
                (subject2, tags),
                hklib.Post.parse_subject(subject1))

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

        p = hklib.Post.from_str('Subject: [t1][t2] subject\nTag: t3')
        p.normalize_subject()
        self.assertEquals(p.subject(), 'subject')
        self.assertEquals(p.tags(), ['t3', 't1', 't2'])

    def test__sort(self):
        """Tests the following functions:

        - :func:`hklib.Post.__eq__`
        - :func:`hklib.Post.__ne__`
        - :func:`hklib.Post.__lt__`
        - :func:`hklib.Post.__gt__`
        - :func:`hklib.Post.__le__`
        - :func:`hklib.Post.__ge__`
        """

        from_str = hklib.Post.from_str
        d1 = from_str('Date: Thu, 16 Oct 2008 18:56:36 +0200', 'my_heap/3')
        d2 = from_str('Date: Fri, 17 Oct 2008 18:56:36 +0200', 'my_heap/2')
        d3 = from_str('Date: Sat, 18 Oct 2008 18:56:36 +0200', 'my_heap/1')
        n1 = from_str('', 'my_heap/6')
        n2 = from_str('', 'my_heap/5')
        n3 = from_str('', 'my_heap/4')
        d4 = from_str('Date: Sun, 19 Oct 2008 18:56:36 +0200', 'my_heap/7')
        d5 = from_str('Date: Sun, 19 Oct 2008 18:56:36 +0200', 'my_heap/8')

        order = [d1, d2, d3, n3, n2, n1, d4, d5]
        for p1, p2 in itertools.combinations(order, 2):
            self.assertTrue(p1 < p2)
            self.assertFalse(p2 < p1)
            self.assertFalse(p1 > p2)
            self.assertTrue(p2 > p1)
            self.assertTrue(p1 <= p2)
            self.assertFalse(p2 <= p1)
            self.assertFalse(p1 >= p2)
            self.assertTrue(p2 >= p1)
            self.assertTrue(p2 != p1)
            self.assertTrue(p1 != p2)
            self.assertFalse(p2 == p1)
            self.assertFalse(p1 == p2)

    def test__filenames(self):
        """Tests the following functions:

        - :func:`hklib.Post.postfilename`
        - :func:`hklib.Post.htmlfilebasename`
        - :func:`hklib.Post.htmlfilename`
        - :func:`hklib.Post.htmlthreadbasename`
        - :func:`hklib.Post.htmlthreadfilename`
        """

        self.assertEquals(
            self.p(0).postfilename(),
            os.path.join(self._myheap_dir, '0.post'))

        self.assertEquals(
            self.p(0).htmlfilebasename(),
            os.path.join('my_heap', '0.html'))

        self.assertEquals(
            self.p(0).htmlfilename(),
            os.path.join(self._html_dir, 'my_heap', '0.html'))

        self.assertEquals(
            self.p(0).htmlthreadbasename(),
            os.path.join('my_heap', 'thread_0.html'))

        # htmlthreadbasename shall be called only for root posts
        self.assertRaises(
            AssertionError,
            lambda: self.p(1).htmlthreadbasename())

        self.assertEquals(
            self.p(0).htmlthreadfilename(),
            os.path.join(self._html_dir, 'my_heap', 'thread_0.html'))

        # htmlthreadfilename shall be called only for root posts
        self.assertRaises(
            AssertionError,
            lambda: self.p(1).htmlthreadfilename())

    def test_repr(self):
        """Tests :func:`hklib.Post.__repr__`."""

        self.assertEquals(
            str(self.p(0)),
            '<post my_heap/0>')

        self.assertEquals(
            str(hklib.Post.from_str('')),
            '<post object without post id>')


class Test_PostDB(unittest.TestCase, PostDBHandler):

    """Tests :class:`hklib.PostDB` (and its cooperation with
    :class:`hklib.Post`)."""

    def setUp(self):
        self.setUpDirs()
        self.create_postdb()
        self.create_threadst()

    def tearDown(self):
        self.tearDownDirs()

    def test__init(self):
        """Tests the following functions:

        - :func:`hklib.PostDB.__init__`
        - :func:`hklib.PostDB.html_dir`
        """

        postdb = self._postdb

        self.assertEquals(postdb.html_dir(), self._html_dir)

        # Checking the data attributes

        self.assertEquals(
            postdb._heaps,
            {'my_heap': self._myheap_dir,
             'my_other_heap': self._myotherheap_dir})

        self.assertEquals(
            postdb._html_dir,
            self._html_dir)

        self.assertEquals(
            postdb._next_post_index,
            {('my_heap', ''): 5,
             ('my_other_heap', ''): 1})

        self.assertEquals(
            postdb.post_id_to_post,
            {self.i(0): self.p(0),
             self.i(1): self.p(1),
             self.i(2): self.p(2),
             self.i(3): self.p(3),
             self.i(4): self.p(4),
             self.io(0): self.po(0)})

        self.assertEquals(
            postdb.messid_to_post_id,
            {'0@': self.i(0),
             '1@': self.i(1),
             '2@': self.i(2),
             '3@': self.i(3),
             '4@': self.i(4),
             'other0@': self.io(0)})

        self.assertEquals(
            postdb.listeners,
            [])

    def test_add_post_to_dicts(self):
        """Tests :func:`hklib.PostDB.add_post_to_dicts`."""

        postdb = self._postdb

        # Adding a post without messid

        p = hklib.Post.from_str('', ('my_heap', '10'))
        expected_postid_to_post = postdb.post_id_to_post.copy()
        expected_postid_to_post.update({('my_heap', '10'): p})
        expected_messid_to_postid = postdb.messid_to_post_id.copy()

        postdb.add_post_to_dicts(p)
        self.assertEquals(
            postdb.post_id_to_post,
            expected_postid_to_post)
        self.assertEquals(
            postdb.messid_to_post_id,
            expected_messid_to_postid)

        # Adding a post with a messid

        p = hklib.Post.from_str('Message-Id: 11@', ('my_heap', '11'))
        expected_postid_to_post = postdb.post_id_to_post.copy()
        expected_postid_to_post.update({('my_heap', '11'): p})
        expected_messid_to_postid = postdb.messid_to_post_id.copy()
        expected_messid_to_postid.update({'11@': ('my_heap', '11')})

        postdb.add_post_to_dicts(p)
        self.assertEquals(
            postdb.post_id_to_post,
            expected_postid_to_post)
        self.assertEquals(
            postdb.messid_to_post_id,
            expected_messid_to_postid)

        # Adding a post with an already used messid

        p = hklib.Post.from_str('Message-Id: 0@', ('my_heap', '12'))
        expected_postid_to_post = postdb.post_id_to_post.copy()
        expected_postid_to_post.update({('my_heap', '12'): p})
        expected_messid_to_postid = postdb.messid_to_post_id.copy()

        postdb.add_post_to_dicts(p)
        self.assertEquals(
            postdb.post_id_to_post,
            expected_postid_to_post)
        self.assertEquals(
            postdb.messid_to_post_id,
            expected_messid_to_postid)

        self.assertEquals(
            self.pop_log(),
            ("Warning: post ('my_heap', '12') has message id 0@, but that "
             "message id is already used by post ('my_heap', '0')."))

    def test_remove_post_from_dicts(self):
        """Tests :func:`hklib.PostDB.remove_post_from_dicts`."""

        postdb = self._postdb

        # Removing a post

        p0 = self.p(0)
        expected_postid_to_post = postdb.post_id_to_post.copy()
        del expected_postid_to_post[('my_heap', '0')]
        expected_messid_to_postid = postdb.messid_to_post_id.copy()
        del expected_messid_to_postid['0@']

        postdb.remove_post_from_dicts(p0)
        self.assertEquals(
            postdb.post_id_to_post,
            expected_postid_to_post)
        self.assertEquals(
            postdb.messid_to_post_id,
            expected_messid_to_postid)

        #
        # Removing a post when there are conflicting messids:
        # first remove the post that possesses the messid
        #

        # Creating the conflicting post

        p1_other = hklib.Post.from_str('Message-Id: 1@', ('my_heap', 'other1'))
        postdb.add_post_to_dicts(p1_other)
        self.assertEquals(
            self.pop_log(),
            ("Warning: post ('my_heap', 'other1') has message id 1@, but that "
             "message id is already used by post ('my_heap', '1')."))
        p1 = self.p(1)

        # Removing the original owner: nobody will have the message id
        # (this could change in the future)

        expected_postid_to_post = postdb.post_id_to_post.copy()
        del expected_postid_to_post[('my_heap', '1')]
        expected_messid_to_postid = postdb.messid_to_post_id.copy()
        del expected_messid_to_postid['1@']

        postdb.remove_post_from_dicts(p1)
        self.assertEquals(
            postdb.post_id_to_post,
            expected_postid_to_post)
        self.assertEquals(
            postdb.messid_to_post_id,
            expected_messid_to_postid)

        # Removing the other post: the messid_to_post_id dictionary will not
        # change

        expected_postid_to_post = postdb.post_id_to_post.copy()
        del expected_postid_to_post[('my_heap', 'other1')]
        expected_messid_to_postid = postdb.messid_to_post_id.copy()

        postdb.remove_post_from_dicts(p1_other)
        self.assertEquals(
            postdb.post_id_to_post,
            expected_postid_to_post)
        self.assertEquals(
            postdb.messid_to_post_id,
            expected_messid_to_postid)

        #
        # Removing a post when there are conflicting messids:
        # first remove the post that do not possess the messid
        #

        # Creating the conflicting post

        p2_other = hklib.Post.from_str('Message-Id: 2@', ('my_heap', 'other2'))
        postdb.add_post_to_dicts(p2_other)
        self.assertEquals(
            self.pop_log(),
            ("Warning: post ('my_heap', 'other2') has message id 2@, but that "
             "message id is already used by post ('my_heap', '2')."))
        p2 = self.p(2)

        # Removing the post that is not the owner: the messid_to_post_id
        # dictionary will not change

        expected_postid_to_post = postdb.post_id_to_post.copy()
        del expected_postid_to_post[('my_heap', 'other2')]
        expected_messid_to_postid = postdb.messid_to_post_id.copy()

        postdb.remove_post_from_dicts(p2_other)
        self.assertEquals(
            postdb.post_id_to_post,
            expected_postid_to_post)
        self.assertEquals(
            postdb.messid_to_post_id,
            expected_messid_to_postid)

        # Removing the other post: the messid will be removed from
        # the messid_to_post_id dictionary

        expected_postid_to_post = postdb.post_id_to_post.copy()
        del expected_postid_to_post[('my_heap', '2')]
        expected_messid_to_postid = postdb.messid_to_post_id.copy()
        del expected_messid_to_postid['2@']

        postdb.remove_post_from_dicts(p2)
        self.assertEquals(
            postdb.post_id_to_post,
            expected_postid_to_post)
        self.assertEquals(
            postdb.messid_to_post_id,
            expected_messid_to_postid)

    def test_load_heap(self):
        """Tests :func:`load_heap`."""

        postdb = self._postdb

        #
        # Modifying and loading an existing heap ('my_heap').
        #

        # We test that only the files with ".post" postfix are read.

        # Creating new posts and loading them instead of the pre-loaded ones

        def post_path(fname):
            return os.path.join(self._myheap_dir, fname)

        hkutils.string_to_file('Subject: s1', post_path('1.post'))
        hkutils.string_to_file('Subject: sx', post_path('xy.post'))
        hkutils.string_to_file('Subject: s2', post_path('2.other'))
        hkutils.string_to_file('Subject: s3', post_path('3post'))
        postdb.load_heap('my_heap')

        self.assertEquals(
            set(postdb.post_id_to_post.keys()),
            set([('my_heap', '1'),
                 ('my_heap', 'xy'),
                 ('my_other_heap', '0')]))

        self.assertEquals(
            postdb.next_post_index('my_heap'),
            '2')

        #
        # Modifying and loading a new heap ('my_new_heap').
        #

        heap_dir = os.path.join(self._dir, 'my_new_heap')
        os.mkdir(heap_dir)

        # We test that only the files with ".post" postfix are read.

        # Creating new posts and loading them instead of the pre-loaded ones
        hkutils.string_to_file('Subject: s1', os.path.join(heap_dir, '1.post'))
        hkutils.string_to_file('Subject: sx', os.path.join(heap_dir, 'ab.post'))
        hkutils.string_to_file('Subject: s2', os.path.join(heap_dir, '2.other'))
        hkutils.string_to_file('Subject: s3', os.path.join(heap_dir, '3post'))

        postdb._heaps['my_new_heap'] = heap_dir
        postdb.load_heap('my_new_heap')

        self.assertEquals(
            set(postdb.post_id_to_post.keys()),
            set([('my_heap', '1'),
                 ('my_heap', 'xy'),
                 ('my_other_heap', '0'),
                 ('my_new_heap', '1'),
                 ('my_new_heap', 'ab')]))

        self.assertEquals(
            postdb.next_post_index('my_new_heap'),
            '2')

    def test_add_heap(self):
        """Tests :func:`add_heap`."""

        postdb = self._postdb

        # Adding a new heap

        heap_dir_1 = os.path.join(self._dir, 'my_new_heap_dir_1')
        postdb.add_heap('my_new_heap_1', heap_dir_1)
        self.assertEquals(
            self.pop_log(),
            ('Warning: post directory does not exists: "%s"\n'
             'Post directory has been created.'
             % (heap_dir_1,)))

        self.assertEquals(
            postdb._heaps,
            {'my_other_heap': self._myotherheap_dir,
             'my_heap': self._myheap_dir,
             'my_new_heap_1': heap_dir_1})

        self.assertEquals(
            len(postdb.post_id_to_post.keys()),
            6)

        self.assertEquals(
            postdb.next_post_index('my_new_heap_1'),
            '1')

        # Adding a heap that has posts

        heap_dir_2 = os.path.join(self._dir, 'my_new_heap_dir_2')
        os.mkdir(heap_dir_2)
        hkutils.string_to_file('Subject: s1', os.path.join(heap_dir_2, '1.post'))
        postdb.add_heap('my_new_heap_2', heap_dir_2)

        self.assertEquals(
            len(postdb.post_id_to_post.keys()),
            7)

        self.assertEquals(
            postdb.next_post_index('my_new_heap_2'),
            '2')

    def test_set_html_dir(self):
        """Tests :func:`set_html_dir`."""

        postdb = self._postdb

        # Non-existing directory

        html_dir_1 = os.path.join(self._dir, 'html_dir_1')
        postdb.set_html_dir(html_dir_1)
        self.assertEquals(
            postdb._html_dir,
            html_dir_1)
        self.assertEquals(
            self.pop_log(),
            ('Warning: HTML directory does not exists: "%s"\n'
             'HTML directory has been created.'
             % (html_dir_1,)))

        # Existing directory

        html_dir_2 = os.path.join(self._dir, 'html_dir_2')
        os.mkdir(html_dir_2)
        postdb.set_html_dir(html_dir_2)
        self.assertEquals(
            postdb._html_dir,
            html_dir_2)

    def test_get_heaps_from_config(self):
        """Tests :func:`hklib.PostDB.get_heaps_from_config`."""

        # "paths/heaps" is specified

        config = ConfigParser.ConfigParser()
        config.add_section('paths')
        config.set('paths', 'heaps',
                   'my_heap1:my_heap_dir_1;my_heap2:my_heap_dir_2')

        heaps = hklib.PostDB.get_heaps_from_config(config)
        self.assertEquals(
            heaps,
            {'my_heap1': 'my_heap_dir_1',
             'my_heap2': 'my_heap_dir_2'})

        # Testing whitespace stripping

        config = ConfigParser.ConfigParser()
        config.add_section('paths')
        config.set('paths', 'heaps',
                   ' my_heap1 : my_heap_dir_1 ; my_heap2 : my_heap_dir_2 ')

        heaps = hklib.PostDB.get_heaps_from_config(config)
        self.assertEquals(
            heaps,
            {'my_heap1': 'my_heap_dir_1',
             'my_heap2': 'my_heap_dir_2'})

        # No "paths/heaps", only "paths/mail"

        config = ConfigParser.ConfigParser()
        config.add_section('paths')
        config.set('paths', 'mail', 'my_heap_dir')

        heaps = hklib.PostDB.get_heaps_from_config(config)
        self.assertEquals(
            heaps,
            {'': 'my_heap_dir'})
        self.assertEquals(
            self.pop_log(),
            ('Config file contains a "paths/mail" option that should be '
             'replaced by "paths/heaps". See the documentation for more '
             'information.'))

        # Neither "paths/heaps", nor "paths/mail" is specified

        config = ConfigParser.ConfigParser()
        self.assertRaises(
            hkutils.HkException,
            lambda: hklib.PostDB.get_heaps_from_config(config))

    def test_read_config(self):
        """Tests :func:`hklib.PostDB.read_config`."""

        postdb  = self._postdb
        new_heap_dir = os.path.join(self._dir, 'new_heap_dir')
        os.mkdir(new_heap_dir)
        hkutils.string_to_file(
            'Subject: s1',
            os.path.join(new_heap_dir, '1.post'))

        html_dir = os.path.join(self._dir, 'new_html_dir')
        os.mkdir(html_dir)

        config = ConfigParser.ConfigParser()
        config.add_section('paths')
        config.set('paths', 'html', html_dir)
        config.set('paths', 'heaps', 'new_heap:' + new_heap_dir)

        postdb.read_config(config)

        # The new heap goes next to the other heaps. Currently the heaps that
        # are not present in the configuration are not touched by read_config.
        self.assertEquals(
            postdb._heaps,
            {'my_heap': self._myheap_dir,
             'my_other_heap': self._myotherheap_dir,
             'new_heap': new_heap_dir})

        # The post was read
        self.assert_(postdb.post('new_heap/1') != None)

        # The html_dir was set
        self.assertEquals(postdb.html_dir(), html_dir)

    def test__get_methods(self):
        """Tests the following functions:

        - :func:`hklib.PostDB.has_post_id`
        - :func:`hklib.PostDB.has_heap_id`
        - :func:`hklib.PostDB.postset`
        - :func:`hklib.PostDB.post_by_post_id`
        - :func:`hklib.PostDB.post_by_messid`
        - :func:`hklib.PostDB.postfile_name`
        - :func:`hklib.PostDB.html_dir`
        """

        postdb = self._postdb

        # Testing has_post_id
        self.assertTrue(postdb.has_post_id(('my_heap', '0')))
        self.assertFalse(postdb.has_post_id(('my_heap', 'x')))

        # Testing has_heap_id
        self.assertTrue(postdb.has_heap_id('my_heap'))
        self.assertFalse(postdb.has_heap_id('nosuchheap'))

        # Testing next_post_index
        self.assertEquals(postdb.next_post_index('my_heap'), '5')

        # Testing postset
        self.assertEquals(
            postdb.postset(['my_heap/0']),
            hklib.PostSet(postdb, self.p(0)))

        # Testing post_by_post_id
        self.assertEquals(
            postdb.post_by_post_id('my_heap/0'),
            self.p(0))
        self.assertEquals(
            postdb.post_by_post_id('my_heap/111'),
            None)

        # Testing post_by_messid
        self.assertEquals(
            postdb.post_by_messid('0@'),
            self.p(0))
        self.assertEquals(
            postdb.post_by_messid('111@'),
            None)

        # Testing postfile_name
        self.assertEquals(
            postdb.postfile_name(self.p(0)),
            os.path.join(self._myheap_dir, '0.post'))

        # Testing html_dir
        self.assertEquals(
            postdb.html_dir(),
            os.path.join(self._html_dir))

    def test_next_post_index(self):
        """Tests :func:`hklib.PostDB.next_post_index`."""
        postdb = self._postdb

        # Basic test
        self.assertEquals(postdb.next_post_index('my_heap'), '5')
        self.assertEquals(postdb.next_post_index('my_heap'), '6')

        # We don't fill in the holes
        postdb.invalidate_next_post_index_cache()
        postdb.add_new_post(hklib.Post.create_empty(), 'my_heap', '9')
        self.assertEquals(postdb.next_post_index('my_heap'), '10')

        # Testing prefixed
        self.assertEquals(postdb.next_post_index('my_heap', 'a_'), 'a_1')
        self.assertEquals(postdb.next_post_index('my_heap', 'a_'), 'a_2')

    def test__modifications(self):
        """Tests the following functions:

        - :func:`hklib.PostDB.real_posts`
        - :func:`hklib.PostDB.posts`
        - :func:`hklib.PostDB._recalc_posts`
        - :func:`hklib.PostDB.save`
        """

        postdb = self.create_postdb()

        # Initialisation
        new_heap_dir = os.path.join(self._dir, 'new_heap_dir')
        os.mkdir(new_heap_dir)
        postfile1 = os.path.join(new_heap_dir, '1.post')
        postfile2 = os.path.join(new_heap_dir, '2.post')
        hkutils.string_to_file('Message-Id: mess1', postfile1)
        hkutils.string_to_file('Message-Id: mess2', postfile2)
        postdb.add_heap('new_heap', new_heap_dir)
        p1 = postdb.post('new_heap/1')
        p2 = postdb.post('new_heap/2')

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
        postfile3 = os.path.join(new_heap_dir, '3.post')
        p3 = hklib.Post.from_str('Subject: subject3')
        postdb.add_new_post(p3, 'new_heap')
        self.assertEquals(
            set(postdb.post_id_to_post.keys()),
            set([('new_heap', '1'),
                 ('new_heap', '2'),
                 ('new_heap', '3')]))
        self.assertFalse(os.path.exists(postfile3))
        postdb.save()
        self.assert_(os.path.exists(postfile3))

        # Deleting a post
        self.assertEquals(set([p1, p2, p3]), set(postdb.posts()))
        self.assertEquals(set([p1, p2, p3]), set(postdb.real_posts()))
        p1.delete()
        self.assertEquals(set([p2, p3]), set(postdb.posts()))
        self.assertEquals(set([p1, p2, p3]), set(postdb.real_posts()))

    def test_post(self):
        """Tests :func:`hklib.PostDB.post`."""

        postdb = self._postdb
        p0 = self.p(0)

        # Specifying the post

        self.assertEquals(postdb.post(p0), p0)

        # Specifying the post id

        self.assertEquals(postdb.post('my_heap/0'), p0)
        self.assertEquals(postdb.post(('my_heap', '0')), p0)
        self.assertEquals(postdb.post(('my_heap', 0)), p0)

        # Specifying the post index

        self.assertEquals(postdb.post('0', heap_id_hint='my_heap'), p0)
        self.assertEquals(postdb.post(0, heap_id_hint='my_heap'), p0)
        self.assertEquals(postdb.post('0'), None) # no hint -> post not found
        self.assertEquals(postdb.post(0), None) # no hint -> post not found

        # bad hint -> post not found
        self.assertEquals(postdb.post('1', heap_id_hint='my_other_heap'), None)

        # Specifying the message id

        self.assertEquals(postdb.post('0@'), p0)

        # Testing the `raise_exception` parameter

        self.assertEquals(postdb.post('nosuchpost'), None)
        self.assertRaises(
            hklib.PostNotFoundError,
            lambda: postdb.post('nosuchpost', raise_exception=True))

    def test_reload(self):
        """Tests the following functions:

        - :func:`hklib.PostDB.save`
        - :func:`hklib.PostDB.reload`
        """

        # Initialization
        postdb = self._postdb
        p1 = postdb.add_new_post(hklib.Post.from_str(''), 'my_heap', '11')

        # Saving a subject
        p1.set_subject('sub1')
        postdb.save()

        # A change that will be lost.
        p1.set_subject('sub2')

        # A change on the disk that will be loaded.
        hkutils.string_to_file(
            'Subject: sub_new',
            os.path.join(self._myheap_dir, 'x.post'))

        postdb.reload()
        postdb.save()

        # The subject of p1 is unchanged, x.mail is loaded
        self.assertEquals(p1.subject(), 'sub1')
        self.assert_(postdb.post('my_heap/11') is p1)
        self.assertEquals(
            hkutils.file_to_string(p1.postfilename()),
            'Subject: sub1\n\n\n')
        self.assertEquals(postdb.post('my_heap/x').subject(), 'sub_new')

    def test_add_new_post(self):
        """Tests :func:`hklib.PostDB.add_new_post`."""

        postdb = self._postdb

        p1 = postdb.add_new_post(hklib.Post.from_str(''), 'my_heap')
        self.assert_(postdb.post('my_heap/5') is p1)

        # Testing the `post_index` parameter
        p2 = postdb.add_new_post(hklib.Post.from_str(''), 'my_heap', '11')
        self.assert_(postdb.post('my_heap/11') is p2)

        # Testing the `prefix` parameter
        p3 = \
            postdb.add_new_post(
                hklib.Post.from_str(''),
                'my_heap',
                prefix='my_prefix_')
        self.assert_(postdb.post('my_heap/my_prefix_1') is p3)

        p4 = \
            postdb.add_new_post(
                hklib.Post.from_str(''),
                'my_heap',
                prefix='my_prefix_')
        self.assert_(postdb.post('my_heap/my_prefix_2') is p4)

    def test_all(self):
        """Tests the following functions:

        - :func:`hklib.PostDB.all`
        - :func:`hklib.PostDB._recalc_all`
        """

        postdb = self._postdb

        # If we call `all` twice without modifying the post database, the
        # returned objects should be the same and they should be equal to
        # `all_posts_1`

        all_posts_1 = \
            postdb.postset(
                [self.p(0),
                 self.p(1),
                 self.p(2),
                 self.p(3),
                 self.p(4),
                 postdb.post('my_other_heap/0')])
        all_1 = postdb.all()
        all_2 = postdb.all()
        self.assert_(all_1 is all_2)
        self.assertEquals(all_posts_1, all_1)

        # If we modify the post database, `all` should return a different
        # object then previously and the previously returned object should be
        # unmodified

        p5 = self.add_post(5)
        all_posts_2 = all_posts_1 | p5
        all_3 = postdb.all()
        self.assertEquals(all_posts_2, all_3)
        # `all_1` was not modified:
        self.assertEquals(all_posts_1, all_1)

    def test_threadstruct(self):
        """Tests the following functions:

        - :func:`hklib.PostDB.threadstruct`
        - :func:`hklib.PostDB._recalc_threadstruct`
        """

        postdb = self._postdb

        # If we call `threadstruct` twice without modifying the post database,
        # the returned objects should be the same and they should be equal to
        # `expected_ts_1`

        expected_ts_1 = \
            {None: [self.i(0), self.io(0), self.i(4)],
             self.i(0): [self.i(1), self.i(3)],
             self.i(1): [self.i(2)]}
        ts1 = postdb.threadstruct()
        ts2 = postdb.threadstruct()
        self.assert_(ts1 is ts2)
        self.assertEquals(ts1, expected_ts_1)

        # If we modify the post database, `threadstruct` should return a
        # different object then previously and the previously returned object
        # should be unmodified

        self.add_post(5, 0)
        expected_ts_2 = \
            {None: [self.i(0), self.io(0), self.i(4)],
             self.i(0): [self.i(1), self.i(3), self.i(5)],
             self.i(1): [self.i(2)]}
        ts3 = postdb.threadstruct()
        self.assertEquals(ts3, expected_ts_2)
        # `ts1` was not modified:
        self.assertEquals(ts1, expected_ts_1)

        # Deleting posts

        self.p(1).delete()
        expected_ts = \
            {None: [self.i(0), self.io(0), self.i(2), self.i(4)],
             self.i(0): [self.i(3), self.i(5)]}
        self.assertEquals(postdb.threadstruct(), expected_ts)

        self.p(0).delete()
        expected_ts = \
            {None: [self.io(0), self.i(2), self.i(3), self.i(4), self.i(5)]}
        self.assertEquals(postdb.threadstruct(), expected_ts)

        self.p(2).delete()
        self.p(3).delete()
        self.p(4).delete()
        self.p(5).delete()
        self.po(0).delete()
        expected_ts = {None: []}
        self.assertEquals(postdb.threadstruct(), expected_ts)

        # Testing that the thread structure also works when the Parent is
        # defined by a heapid.

        # If the same messid and heapid exist, the former has priority.
        add = postdb.add_new_post
        add(hklib.Post.from_str(''), 'new_heap')               # #1
        add(hklib.Post.from_str('Parent: 1'), 'new_heap')      # #2
        add(hklib.Post.from_str(''), 'new_heap')               # #3
        add(hklib.Post.from_str('Message-Id: 2'), 'new_heap')  # #4
        add(hklib.Post.from_str('Parent: 4'), 'new_heap')      # #5

        ts = {None: [('new_heap', '1'),
                     ('new_heap', '3'),
                     ('new_heap', '4')],
              ('new_heap', '1'): [('new_heap', '2')],
              ('new_heap', '4'): [('new_heap', '5')]}
        self.assertEquals(postdb.threadstruct(), ts)

    def test_parent(self):
        """Tests :func:`hklib.PostDB.parent`."""

        postdb = self._postdb

        self.assertEquals(postdb.parent(self.p(0)), None)
        self.assertEquals(postdb.parent(self.p(1)), self.p(0))
        self.assertEquals(postdb.parent(self.p(2)), self.p(1))
        self.assertEquals(postdb.parent(self.p(3)), self.p(0))
        self.assertEquals(postdb.parent(self.p(4)), None)
        self.assertEquals(postdb.parent(self.po(0)), None)

    def test_root(self):
        """Tests :func:`hklib.PostDB.parent`."""

        postdb = self._postdb

        ## Testing when there is no cycle

        self.assertEquals(postdb.root(self.p(0)), self.p(0))
        self.assertEquals(postdb.root(self.p(1)), self.p(0))
        self.assertEquals(postdb.root(self.p(2)), self.p(0))
        self.assertEquals(postdb.root(self.p(3)), self.p(0))
        self.assertEquals(postdb.root(self.p(4)), self.p(4))
        self.assertEquals(postdb.root(self.po(0)), self.po(0))

        ## Testing cycles

        self.introduce_cycle()

        # Normal posts:
        self.assertEquals(postdb.root(self.p(0)), self.p(0))
        self.assertEquals(postdb.root(self.p(1)), self.p(0))
        self.assertEquals(postdb.root(self.p(2)), self.p(0))
        self.assertEquals(postdb.root(self.p(4)), self.p(4))
        self.assertEquals(postdb.root(self.po(0)), self.po(0))


        # Posts in cycle:
        self.assertEquals(postdb.root(self.p(3)), None)
        self.assertEquals(postdb.root(self.p(5)), None)
        self.assertEquals(postdb.root(self.p(6)), None)
        self.assertEquals(postdb.root(self.p(7)), None)

    def test_children(self):
        """Tests :func:`hklib.PostDB.children`."""

        postdb = self._postdb

        self.assertEquals(
            postdb.children(None),
            [self.p(0), self.po(0), self.p(4)])
        self.assertEquals(postdb.children(self.p(0)), [self.p(1), self.p(3)])
        self.assertEquals(postdb.children(self.p(1)), [self.p(2)])
        self.assertEquals(postdb.children(self.p(2)), [])
        self.assertEquals(postdb.children(self.p(3)), [])
        self.assertEquals(postdb.children(self.p(4)), [])
        self.assertEquals(postdb.children(self.po(0)), [])

        # Testing the `threadstruct` parameter

        ts = {('my_heap', '0'): [self.p(1)]}
        self.assertEquals(
            postdb.children(self.p(0), ts),
            [self.p(1)])
        self.assertEquals(
            postdb.children(self.p(1), ts),
            [])

        # Testing incorrect threadstruct

        ts = {('my_heap', '0'): 'badvalue'}
        self.assertRaises(
            AssertionError,
            lambda: postdb.children(self.p(0), ts))

    def test_iter_thread(self):
        """Tests :func:`hklib.PostDB.iter_thread`."""

        postdb = self._postdb
        p = self.p
        po = self.po

        self.assertEquals(
            list(postdb.iter_thread(None)),
            [p(0), p(1), p(2), p(3), po(0), p(4)])
        self.assertEquals(
            list(postdb.iter_thread(p(0))),
            [p(0), p(1), p(2), p(3)])
        self.assertEquals(list(postdb.iter_thread(p(1))), [p(1), p(2)])
        self.assertEquals(list(postdb.iter_thread(p(2))), [p(2)])
        self.assertEquals(list(postdb.iter_thread(p(3))), [p(3)])
        self.assertEquals(list(postdb.iter_thread(p(4))), [p(4)])
        self.assertEquals(list(postdb.iter_thread(po(0))), [po(0)])

        # If the post is not in the postdb, AssertionError will be raised
        self.assertRaises(
            AssertionError,
            lambda: list(postdb.iter_thread(hklib.Post.from_str(''))))

        # Testing the `threadstruct` parameter
        ts = {('my_heap', '0'): [self.p(1)]}
        self.assertEquals(
            list(postdb.iter_thread(p(0), ts)),
            [p(0), p(1)])

    def test_walk_thread(self):
        """Tests :func:`hklib.PostDB.walk_thread`."""

        postdb = self._postdb

        def test(root, expected_result):
            """Tests whether the the :func:`hklib.PostDB.walk_thread` function
            returns the given result when executed with the given root."""

            postitem_strings = [str(postitem) + '\n'
                                for postitem in postdb.walk_thread(root)]
            postitem_strings = ''.join(postitem_strings)
            self.assertEquals(postitem_strings, expected_result)

        # The indentation in the following expressions reflects the thread
        # structure of the posts.

        test(None,
             ("<PostItem: pos=begin, post_id=my_heap/0, level=0>\n"
                "<PostItem: pos=begin, post_id=my_heap/1, level=1>\n"
                  "<PostItem: pos=begin, post_id=my_heap/2, level=2>\n"
                  "<PostItem: pos=end, post_id=my_heap/2, level=2>\n"
                "<PostItem: pos=end, post_id=my_heap/1, level=1>\n"
                "<PostItem: pos=begin, post_id=my_heap/3, level=1>\n"
                "<PostItem: pos=end, post_id=my_heap/3, level=1>\n"
              "<PostItem: pos=end, post_id=my_heap/0, level=0>\n"
              "<PostItem: pos=begin, post_id=my_other_heap/0, level=0>\n"
              "<PostItem: pos=end, post_id=my_other_heap/0, level=0>\n"
              "<PostItem: pos=begin, post_id=my_heap/4, level=0>\n"
              "<PostItem: pos=end, post_id=my_heap/4, level=0>\n"))

        test(self.p(0),
             ("<PostItem: pos=begin, post_id=my_heap/0, level=0>\n"
                "<PostItem: pos=begin, post_id=my_heap/1, level=1>\n"
                  "<PostItem: pos=begin, post_id=my_heap/2, level=2>\n"
                  "<PostItem: pos=end, post_id=my_heap/2, level=2>\n"
                "<PostItem: pos=end, post_id=my_heap/1, level=1>\n"
                "<PostItem: pos=begin, post_id=my_heap/3, level=1>\n"
                "<PostItem: pos=end, post_id=my_heap/3, level=1>\n"
              "<PostItem: pos=end, post_id=my_heap/0, level=0>\n"))

        test(self.p(1),
             ("<PostItem: pos=begin, post_id=my_heap/1, level=0>\n"
                "<PostItem: pos=begin, post_id=my_heap/2, level=1>\n"
                "<PostItem: pos=end, post_id=my_heap/2, level=1>\n"
              "<PostItem: pos=end, post_id=my_heap/1, level=0>\n"))
        test(self.p(2),
             ("<PostItem: pos=begin, post_id=my_heap/2, level=0>\n"
              "<PostItem: pos=end, post_id=my_heap/2, level=0>\n"))
        test(self.p(3),
             ("<PostItem: pos=begin, post_id=my_heap/3, level=0>\n"
              "<PostItem: pos=end, post_id=my_heap/3, level=0>\n"))
        test(self.p(4),
             ("<PostItem: pos=begin, post_id=my_heap/4, level=0>\n"
              "<PostItem: pos=end, post_id=my_heap/4, level=0>\n"))

        # Testing the `threadstruct` parameter

        ts = {('my_heap', '0'): [self.p(1)]}
        self.assertEquals(
            ''.join([str(postitem) + '\n'
                     for postitem in postdb.walk_thread(self.p(0), ts)]),
             ("<PostItem: pos=begin, post_id=my_heap/0, level=0>\n"
                "<PostItem: pos=begin, post_id=my_heap/1, level=1>\n"
                "<PostItem: pos=end, post_id=my_heap/1, level=1>\n"
              "<PostItem: pos=end, post_id=my_heap/0, level=0>\n"))

        # Testing the `yield_main` parameter

        def test(root, expected_result):
            """Tests whether the the :func:`PostDB.walk_thread` function
            returns the given result when executed with the given root."""

            postitem_strings = \
                [ str(postitem) + '\n'
                  for postitem in postdb.walk_thread(root, yield_main=True) ]
            postitem_strings = ''.join(postitem_strings)
            self.assertEquals(postitem_strings, expected_result)

        test(None,
             ("<PostItem: pos=begin, post_id=my_heap/0, level=0>\n"
              "<PostItem: pos=main, post_id=my_heap/0, level=0>\n"
                "<PostItem: pos=begin, post_id=my_heap/1, level=1>\n"
                "<PostItem: pos=main, post_id=my_heap/1, level=1>\n"
                  "<PostItem: pos=begin, post_id=my_heap/2, level=2>\n"
                  "<PostItem: pos=main, post_id=my_heap/2, level=2>\n"
                  "<PostItem: pos=end, post_id=my_heap/2, level=2>\n"
                "<PostItem: pos=end, post_id=my_heap/1, level=1>\n"
                "<PostItem: pos=begin, post_id=my_heap/3, level=1>\n"
                "<PostItem: pos=main, post_id=my_heap/3, level=1>\n"
                "<PostItem: pos=end, post_id=my_heap/3, level=1>\n"
              "<PostItem: pos=end, post_id=my_heap/0, level=0>\n"
              "<PostItem: pos=begin, post_id=my_other_heap/0, level=0>\n"
              "<PostItem: pos=main, post_id=my_other_heap/0, level=0>\n"
              "<PostItem: pos=end, post_id=my_other_heap/0, level=0>\n"
              "<PostItem: pos=begin, post_id=my_heap/4, level=0>\n"
              "<PostItem: pos=main, post_id=my_heap/4, level=0>\n"
              "<PostItem: pos=end, post_id=my_heap/4, level=0>\n"))

        # If the post is not in the postdb, AssertionError will be raised

        self.assertRaises(
            AssertionError,
            lambda: test(hklib.Post.from_str(''), []))

    def test_cycles(self):
        """Tests the following functions:

        - :func:`hklib.PostDB.cycles`
        - :func:`hklib.PostDB.has_cycle`
        - :func:`hklib.PostDB._recalc_cycles`
        """

        postdb = self._postdb

        # Testing when there are no cycles
        self.assertEquals(postdb.has_cycle(), False)
        self.assertEquals(postdb.cycles(), postdb.postset([]))

        # Testing cycles
        self.introduce_cycle()
        self.assertEquals(postdb.has_cycle(), True)
        self.assertEquals(
            postdb.cycles(),
            postdb.postset([self.p(3), self.p(5), self.p(6), self.p(7)]))

    def test_walk_cycles(self):
        """Tests :func:`hklib.PostDB.walk_cycles`."""

        # Testing when there are no cycles
        self.assertEquals(
            [pi for pi in self._postdb.walk_cycles()],
            [])

        # Testing cycles
        self.introduce_cycle()
        self.assertEquals(
            [ pi for pi in self._postdb.walk_cycles() ],
            [hklib.PostItem(pos='flat', post=self.p(3), level=0),
             hklib.PostItem(pos='flat', post=self.p(5), level=0),
             hklib.PostItem(pos='flat', post=self.p(6), level=0),
             hklib.PostItem(pos='flat', post=self.p(7), level=0)])

    def threadstruct_cycle_general(self, parents, threadstruct, cycles):
        """The general function that tests the cycle detection of the thread
        structure computing method.

        It modifies the post database according to the parents argument,
        then checks that the thread structture and the cycles of the modified
        database are as expected.

        **Arguments:**

        - `parents` ({|PostId|: |PostId|}) -- Contains child -> parent pairs,
          which indicate that the child post should be modified as if it were a
          reply to parent.
        - `threadstruct` ({(``None`` | |PostId|): [|PostId|]}) -- The excepted
          thread structure.
        - `cycles` ([|PostId|]) -- Posts that are in a cycle.
        """

        postdb = self._postdb
        for child, parent in parents.items():
            postdb.post(child).set_parent(parent)
        self.assertEquals(postdb.threadstruct(), threadstruct)
        self.assert_(postdb.cycles().is_set(cycles))
        if cycles == []:
            self.assertFalse(postdb.has_cycle())
        else:
            self.assert_(postdb.has_cycle())

    def test__threadstruct_cycle_1(self):
        """Tests the following functions:

        - :func:`hklib.PostDB.cycles`
        - :func:`hklib.PostDB.has_cycle`
        - :func:`hklib.PostDB._recalc_cycles`
        """

        i = self.i
        io = self.io
        self.threadstruct_cycle_general(
            {},
            {None: [self.i(0), io(0), i(4)],
             i(0): [i(1), i(3)],
             i(1): [i(2)]},
            [])

    def test__threadstruct_cycle_2(self):
        """Tests the following functions:

        - :func:`hklib.PostDB.cycles`
        - :func:`hklib.PostDB.has_cycle`
        - :func:`hklib.PostDB._recalc_cycles`
        """

        i = self.i
        io = self.io
        self.threadstruct_cycle_general(
            {i(1): i(2)},
            {None: [i(0), io(0), i(4)],
             i(0): [i(3)],
             i(1): [i(2)],
             i(2): [i(1)]},
            [i(1), i(2)])

    def test__threadstruct_cycle_3(self):
        """Tests the following functions:

        - :func:`hklib.PostDB.cycles`
        - :func:`hklib.PostDB.has_cycle`
        - :func:`hklib.PostDB._recalc_cycles`
        """

        i = self.i
        io = self.io
        self.threadstruct_cycle_general(
            {i(0): i(2)},
            {None: [io(0), i(4)],
             i(0): [i(1), i(3)],
             i(1): [i(2)],
             i(2): [i(0)]},
            [i(0), i(1), i(2), i(3)])

    def test__threadstruct_cycle_4(self):
        """Tests the following functions:

        - :func:`hklib.PostDB.cycles`
        - :func:`hklib.PostDB.has_cycle`
        - :func:`hklib.PostDB._recalc_cycles`
        """

        i = self.i
        io = self.io
        self.threadstruct_cycle_general(
            {i(0): i(0)},
            {None: [io(0), i(4)],
             i(0): [i(0), i(1), i(3)],
             i(1): [i(2)]},
            [i(0), i(1), i(2), i(3)])

    def test_roots(self):
        """Tests the following functions:

        - :func:`hklib.PostDB.roots`
        - :func:`hklib.PostDB._recalc_roots`
        """

        postdb = self._postdb
        p = self.p
        po = self.po

        # If we call `roots` twice without modifying the post database, the
        # returned objects should be the same

        roots1 = postdb.roots()
        roots2 = postdb.roots()
        self.assert_(roots1 is roots2)
        self.assertEquals(roots1, [p(0), po(0), p(4)])

        # If we modify the post database, `root` should return a different
        # object then previously and the previously returned object should be
        # unmodified

        self.add_post(5, None)
        roots3 = postdb.roots()
        self.assertEquals(roots3, [p(0), po(0), p(4), p(5)])
        # `root1` was not modified:
        self.assertEquals(roots1, [p(0), po(0), p(4)])

    def test_threads(self):
        """Tests the following functions:

        - :func:`hklib.PostDB.threads`
        - :func:`hklib.PostDB._recalc_threads`
        """

        postdb = self._postdb
        p = self.p
        po = self.po

        # If we call `threads` twice without modifying the post database, the
        # returned objects should be the same

        threads1 = postdb.threads()
        threads2 = postdb.threads()
        self.assert_(threads1 is threads2)
        self.assertEquals(
            threads1,
            {p(0): postdb.postset([p(0), p(1), p(2), p(3)]),
             po(0): postdb.postset([po(0)]),
             p(4): postdb.postset([p(4)])})

        # If we modify the post database, `threads` should return a different
        # object then previously and the previously returned object should be
        # unmodified

        self.add_post(5, None)
        threads3 = postdb.threads()
        self.assertEquals(
            threads3,
            {p(0): postdb.postset([p(0), p(1), p(2), p(3)]),
             po(0): postdb.postset([po(0)]),
             p(4): postdb.postset([p(4)]),
             p(5): postdb.postset([p(5)])})
        # `threads1` was not modified:
        self.assertEquals(
            threads1,
            {p(0): postdb.postset([p(0), p(1), p(2), p(3)]),
             po(0): postdb.postset([po(0)]),
             p(4): postdb.postset([p(4)])})


class Test_PostItem(unittest.TestCase):

    """Tests :class:`hklib.PostItem`."""

    def test_str(self):
        """Tests :func:`hklib.PostItem.__str__`."""

        # hklib.Post with heapid
        post = hklib.Post.from_str('', post_id=('my_heap', 42))
        postitem = hklib.PostItem(pos='begin', post=post, level=0)
        self.assertEquals(
            str(postitem),
            "<PostItem: pos=begin, post_id=my_heap/42, level=0>")

        # hklib.Post without heapid
        post = hklib.Post.from_str('')
        postitem = hklib.PostItem(pos='begin', post=post, level=0)
        self.assertEquals(
            str(postitem),
            "<PostItem: pos=begin, post_id=None, level=0>")

    def test_copy(self):
        """Tests :func:`hklib.PostItem.copy`."""

        # We make a copy of a postitem...
        post = hklib.Post.from_str('', post_id=('my_heap', '42'))
        postitem = hklib.PostItem(pos='begin', post=post, level=0)
        postitem2 = postitem.copy()

        # ...modify its data attributes...
        post2 = hklib.Post.from_str('')
        postitem.pos = 'end'
        postitem.post = post2
        postitem.level = 1

        # ... and check that the data attributes of the copied postitem have
        # not changed
        self.assertEquals(
            str(postitem2),
            "<PostItem: pos=begin, post_id=my_heap/42, level=0>")

    def test_eq(self):
        """Tests :func:`hklib.PostItem.eq`."""

        post = hklib.Post.from_str('', post_id=('my_heap', '42'))
        postitem1 = hklib.PostItem(pos='begin', post=post, level=0)
        postitem2 = hklib.PostItem(pos='begin', post=post, level=0)
        postitem3 = hklib.PostItem(pos='end', post=post, level=0)
        postitem4 = postitem1.copy()
        postitem4.new_attr = 'something'

        self.assertEquals(postitem1, postitem2)
        self.assertNotEquals(postitem1, postitem3)
        self.assertNotEquals(postitem1, postitem4)


class Test_PostSet(unittest.TestCase, PostDBHandler):

    """Tests :class:`hklib.PostSet`."""

    def setUp(self):
        self.setUpDirs()
        self.create_postdb()
        self.create_threadst()

    def tearDown(self):
        self.tearDownDirs()

    def test__empty(self):
        """Tests the empty post set."""

        postdb = self._postdb
        ps1 = hklib.PostSet(postdb, set())

        self.assertNotEquals(ps1, set())
        self.assert_(ps1 != set())
        self.assertFalse(ps1 == set())
        self.assert_(ps1.is_set(set()))

        self.assertEquals(ps1, hklib.PostSet(postdb, []))
        self.assert_(ps1 == hklib.PostSet(postdb, []))
        self.assertFalse(ps1 != hklib.PostSet(postdb, []))

    def test_copy(self):
        """Tests the following functions:

        - :func:`hklib.PostSet.copy`
        - :func:`hklib.PostSet.empty_clone`
        """

        postdb = self._postdb
        postdb.remove_post_from_dicts(self.p(0))
        postdb.remove_post_from_dicts(self.p(4))
        postdb.remove_post_from_dicts(self.po(0))
        ps_all = self._postdb.all().copy()
        p1 = self.p(1)
        p2 = self.p(2)
        p3 = self.p(3)

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
        """Tests the following functions:

        - :func:`hklib.PostSet.__init__`
        - :func:`hklib.PostSet._to_set`
        - :func:`hklib.PostSet.__eq__`
        - :func:`hklib.PostSet.__ne__`
        - :func:`hklib.PostSet.is_set`
        - :func:`hklib.PostSet.construct`
        - :func:`hklib.PostSet.__and__`
        - :func:`hklib.PostSet.__rand__`
        - :func:`hklib.PostSet.intersection`
        - :func:`hklib.PostSet.intersection_update`
        - :func:`hklib.PostSet.__or__`
        - :func:`hklib.PostSet.__ror__`
        - :func:`hklib.PostSet.union`
        - :func:`hklib.PostSet.update`
        - :func:`hklib.PostSet.__sub__`
        - :func:`hklib.PostSet.__rsub__`
        - :func:`hklib.PostSet.difference`
        - :func:`hklib.PostSet.difference_update`
        - :func:`hklib.PostSet.__xor__`
        - :func:`hklib.PostSet.__rxor__`
        - :func:`hklib.PostSet.symmetric_difference`
        - :func:`hklib.PostSet.symmetric_difference_update`
        """

        postdb = self._postdb
        p = self.p
        po = self.po
        p1 = self.p(1)
        p2 = self.p(2)
        p3 = self.p(3)

        ## Testing `__init__` and `_to_set`

        ps0 = hklib.PostSet(postdb, set([p1]))
        ps1 = hklib.PostSet(postdb, [p1])
        ps2 = hklib.PostSet(postdb, p1)
        ps3 = hklib.PostSet(postdb, set([('my_heap', '1')]))
        ps3 = hklib.PostSet(postdb, set([('my_heap', 1)]))
        ps4 = hklib.PostSet(postdb, set(['my_heap/1']))
        ps5 = hklib.PostSet(postdb, [('my_heap', '1')])
        ps6 = hklib.PostSet(postdb, [('my_heap', 1)])
        ps7 = hklib.PostSet(postdb, ['my_heap/1'])
        ps8 = hklib.PostSet(postdb, ('my_heap', '1'))
        ps9 = hklib.PostSet(postdb, ('my_heap', 1))
        ps10 = hklib.PostSet(postdb, 'my_heap/1')
        self.assertEquals(ps0, ps1)
        self.assertEquals(ps0, ps2)
        self.assertEquals(ps0, ps3)
        self.assertEquals(ps0, ps4)
        self.assertEquals(ps0, ps5)
        self.assertEquals(ps0, ps6)
        self.assertEquals(ps0, ps7)
        self.assertEquals(ps0, ps8)
        self.assertEquals(ps0, ps9)
        self.assertEquals(ps0, ps10)

        self.assertRaises(
            hklib.PostNotFoundError,
            lambda: hklib.PostSet(postdb, 'nosuchpost'))

        self.assertRaises(
            TypeError,
            lambda: hklib.PostSet(postdb, 1.0))

        ## Creating the post sets that will be used for the tests

        ps1 = hklib.PostSet(postdb, set([p1, p2]))
        ps2 = hklib.PostSet(postdb, set([p2, p3]))
        ps3 = hklib.PostSet(postdb, [p2, p3])
        ps4 = hklib.PostSet(postdb, ps3)

        ## Testing `__eq__` and `__ne__`

        self.assert_(ps1 != ps2)
        self.assert_(ps2 == ps3)
        self.assert_(ps2 == ps4)

        self.assertFalse(ps1 == ps2)
        self.assertFalse(ps2 != ps3)
        self.assertFalse(ps2 != ps4)

        ## Testing `is_set`

        self.assert_(ps0.is_set(set([p1])))
        self.assert_(ps0.is_set([p1]))
        self.assert_(ps0.is_set(p1))
        self.assert_(ps1.is_set([p1, p2]))
        self.assert_(ps2.is_set(ps3))

        # If the argument of `is_set` is a tuple, it is assumed to be a post id
        self.assertRaises(
            hklib.PostNotFoundError,
            lambda: ps1.is_set((p1, p2)))

        ## Testing &, |, -, ^

        ps1 = hklib.PostSet(postdb, [p1, p2])
        ps2 = hklib.PostSet(postdb, [p1, p3])
        ps3 = hklib.PostSet(postdb, [p2, p3])
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

        ## PostSet.construct

        test(ps1 & set([p1, p3]), [p1])
        test(ps1 & [p1, p3], [p1])
        test(ps1 & p1, [p1])
        test(ps1 & 'my_heap/1', [p1])
        test(set([p1, p3]) & ps1, [p1])
        test([p1, p3] & ps1, [p1])
        test(p1 & ps1, [p1])
        test('my_heap/1' & ps1, [p1])

        self.assertRaises(
            TypeError,
            lambda: test(ps1 & 1.0, [p1]))

        self.assertRaises(
            TypeError,
            lambda: test(1.0 & ps1, [p1]))

        ## Testing PostDB.all

        ps_all = hklib.PostSet(postdb, [p(0), p(1), p(2), p(3), p(4), po(0)])
        ps2 = hklib.PostSet(postdb, set([p(0), p(2), p(3), p(4), po(0)]))
        self.assertEquals(ps_all, postdb.all())
        p1.delete()
        self.assertEquals(ps2, postdb.all())

        ## Testing `clear` and `update`

        ps1.clear()
        self.assert_(ps1.is_set([]))
        ps1.update(set([p1, p2]))
        self.assert_(ps1.is_set([p1, p2]))

    def test_get_attr(self):
        """Tests :func:`hklib.PostSet.__get_attr__`."""

        postdb = self._postdb
        self.assertRaises(
            AttributeError,
            lambda: hklib.PostSet(postdb, []).nonexisting_method)

    def test_forall(self):
        """Tests :func:`hklib.PostSet.forall` and
        :class:`hklib.PostSetForallDelegate`."""

        def testSubjects(s1, s2, s3):
            self.assertEquals(s1, p1.subject())
            self.assertEquals(s2, p2.subject())
            self.assertEquals(s3, p3.subject())

        postdb = self._postdb
        p1 = self.p(1)
        p2 = self.p(2)
        p3 = self.p(3)
        testSubjects('subject1', 'subject2', 'subject3')

        hklib.PostSet(postdb, []).forall.set_subject('x')
        testSubjects('subject1', 'subject2', 'subject3')
        hklib.PostSet(postdb, [p1]).forall.set_subject('x')
        testSubjects('x', 'subject2', 'subject3')
        postdb.all().forall(lambda p: p.set_subject('z'))
        testSubjects('z', 'z', 'z')
        postdb.all().forall.set_subject('y')
        testSubjects('y', 'y', 'y')

        # Nonexisting methods will cause exceptions...
        self.assertRaises(
            AttributeError,
            lambda: postdb.all().forall.nonexisting_method())

        # ...unless the postset is empty
        hklib.PostSet(postdb, []).forall.nonexisting_method()
        testSubjects('y', 'y', 'y')

    def test_collect(self):
        """Tests :func:`hklib.PostSet.collect` and
        :class:`hklib.PostSetCollectDelegate`."""

        postdb = self._postdb
        p = self.p
        po = self.po
        p1 = self.p(1)
        p2 = self.p(2)
        p3 = self.p(3)
        p1.set_tags(['t1'])
        p2.set_tags(['t2'])
        p3.set_tags(['t1'])

        ps1 = postdb.all().collect.has_tag('t1')
        self.assert_(ps1.is_set([p1, p3]))
        ps2 = postdb.all().collect(lambda p: False)
        self.assert_(ps2.is_set([]))
        ps3 = postdb.all().collect(lambda p: True)
        self.assert_(ps3.is_set([p(0), p(1), p(2), p(3), p(4), po(0)]))
        ps4 = postdb.all().collect(lambda p: p.has_tag('t1'))
        self.assert_(ps4.is_set([p1, p3]))

        self.assertRaises(
            AssertionError,
            lambda: postdb.all().collect(lambda p: None))

        ps_roots = postdb.all().collect.is_root()
        self.assert_(ps_roots.is_set([p(0), po(0), p(4)]))

    def _test_exp(self, methodname):
        """Tests the PostSet's method that has the given name.

        This function returns a function that can test the given method of
        PostSet. The function requires addititonal test arguments that specify
        the concrete test.

        These additional argument are:
        1. The heapids of the posts of the input postset.
        2. The heapids of the posts of the expected output postset.

        The following equality tested::

            input_postset.methodname() = output_postset

        For example the following calls ::

            test = self._test_exp('expb')
            test('02', '012')

        will test that ::

            postdb.postset([self.p('0'), self.p('2')]).expb() ==
            postdb.postset([self.p('0'), self.p('1'), self.p('2')])
        """

        def test_exp_2(post_indices_1, post_indices_2):
            posts_1 = [ self.p(i) for i in post_indices_1 ]
            posts_2 = [ self.p(i) for i in post_indices_2 ]
            ps = hklib.PostSet(self._postdb, posts_1)

            # Testing that the real output is the expected output.
            self.assert_(eval('ps.' + methodname + '()').is_set(posts_2))

            # Testing that the exp() method did not change ps
            self.assert_(ps.is_set(posts_1))

        return test_exp_2

    def test_expb(self):
        """Tests :func:`hklib.PostSet.expb`."""

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
        """Tests :func:`hklib.PostSet.expf`."""

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
        """Tests :func:`hklib.PostSet.exp`."""

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
        """Tests :func:`hklib.PostSet.sorted_list`."""

        p = self.p
        po = self.po
        postdb = self._postdb
        self.assertEquals(
            postdb.all().sorted_list(),
            [p(0), po(0), p(1), p(2), p(3), p(4)])


if __name__ == '__main__':
    set_log(False)
    unittest.main()
