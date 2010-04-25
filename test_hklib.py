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

import itertools
import os
import os.path
import shutil
import StringIO
import tempfile
import unittest

import hkutils
import hklib


class PostDBHandler(object):

    """Helps implementing the tester classes by containing functions commonly
    used by them."""

    # Creating an ordered array of dates. (Increment the number after `range`
    # if you need more posts.)
    dates = [ 'Date: Wed, 20 Aug 2008 17:41:0%d +0200\n' % ii \
              for ii in range(10) ]

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
        self._old_log_fun = hkutils.log_fun
        def log_fun(*args):
            self._log.append(''.join(args))
        hkutils.set_log(log_fun)

    def tearDownDirs(self):
        """Removes the temporary directories and checks that no logs are
        left."""

        shutil.rmtree(self._dir)

        # Setting the original logging function back
        self.assertEqual(self._log, [])
        hkutils.set_log(self._old_log_fun)

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
        self.assertEqual(str(index), post_index)

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
        self.assertEqual(
            hklib.Post.assert_is_post_id(('myheap', 'mypost')),
            None)

        # assertion fails
        self.assertRaises(
            AssertionError,
            lambda: hklib.Post.assert_is_post_id((0, 1)))

    def test_unify_post_id(self):
        """Tests :func:`hklib.Post.unify_post_id`."""

        # None
        self.assertEqual(
            hklib.Post.unify_post_id(None),
            None)

        # post index is a string
        self.assertEqual(
            hklib.Post.unify_post_id(('myheap', 'mypost')),
            ('myheap', 'mypost'))

        # post index is an integer
        self.assertEqual(
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

        self.assertEqual(
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
        self.assertEqual(
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
             'Nosuchattr': ['1', '2']})
        self.assertEqual(
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
             'Tag': []}

        p1 = hklib.Post.from_str(s)
        p2 = hklib.Post.from_str(s + '\n')
        p3 = hklib.Post.from_str(s + '\n\n')
        p4 = hklib.Post.from_str(s + '\n\nHi')
        p5 = hklib.Post.from_str(s + '\n\nHi\n')
        p6 = hklib.Post.from_str(s + '\n\nHi\n\n\n')
        p7 = hklib.Post.from_str(s + '\n\nHi\n\nHi')

        # Checking the post header
        self.assertEqual(p1._header, d)

        # checking the bodies of the posts
        self.assertEqual(p1.body(), '\n')
        self.assertEqual(p2.body(), '\n')
        self.assertEqual(p3.body(), '\n')
        self.assertEqual(p4.body(), 'Hi\n')
        self.assertEqual(p5.body(), 'Hi\n')
        self.assertEqual(p6.body(), 'Hi\n')
        self.assertEqual(p7.body(), 'Hi\n\nHi\n')

        # p1 == p2 == p3 != p4 == p5 == p6
        self.assertEqual(p1, p2)
        self.assertEqual(p1, p3)
        self.assertNotEquals(p1, p4)
        self.assertEqual(p4, p5)
        self.assertEqual(p4, p6)

        p8 = hklib.Post.from_str(s, ('my_heap', 0))
        p9 = hklib.Post.from_str(s, ('my_heap', 0))
        p10 = hklib.Post.from_str(s, ('my_heap', 1))
        p11 = hklib.Post.from_str(s, ('my_other_heap', 0))

        # p8 == p9 != p10 != p11
        self.assertEqual(p8, p9)
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
        self.assertEqual(post.post_id(), None)
        self.assertRaises(hkutils.HkException, lambda: post.heap_id())
        self.assertRaises(hkutils.HkException, lambda: post.post_index())
        self.assertEqual(post.author(), '')
        self.assertEqual(post.subject(), '')
        self.assertEqual(post.messid(), '')
        self.assertEqual(post.parent(), '')
        self.assertEqual(post.date(), '')
        self.assertEqual(post.is_deleted(), False)
        self.assertEqual(post.is_modified(), True)
        self.assertEqual(post.body(), '\n')

        p2 = hklib.Post.create_empty()
        self.assertEqual(post, p2)

        # Normal post without parent
        p0 = self.p(0)
        self.assertEqual(p0.post_id(), ('my_heap', '0'))
        self.assertEqual(p0.heap_id(), 'my_heap')
        self.assertEqual(p0.post_index(), '0')
        self.assertEqual(p0.post_id_str(), 'my_heap/0')
        self.assertEqual(p0.author(), 'author0')
        self.assertEqual(p0.subject(), 'subject0')
        self.assertEqual(p0.messid(), '0@')
        self.assertEqual(p0.parent(), '')
        self.assertEqual(p0.date(), 'Wed, 20 Aug 2008 17:41:00 +0200')
        self.assertEqual(p0.is_deleted(), False)
        self.assertEqual(p0.is_modified(), True)
        self.assertEqual(p0.body(), 'body0\n')

        # Normal post with parent
        p1 = self.p(1)
        self.assertEqual(p1.parent(), '0@')

    def test_from_file(self):
        """Tests :func:`hklib.Post.from_file`."""

        fname = os.path.join(self._dir, 'postfile')
        hkutils.string_to_file(self.p(0).postfile_str(), fname)
        p = hklib.Post.from_file(fname)

        self.assertEqual(p.post_id(), None)
        self.assertEqual(p.author(), 'author0')
        self.assertEqual(p.subject(), 'subject0')
        self.assertEqual(p.messid(), '0@')
        self.assertEqual(p.parent(), '')
        self.assertEqual(p.date(), 'Wed, 20 Aug 2008 17:41:00 +0200')
        self.assertEqual(p.is_deleted(), False)
        self.assertEqual(p.is_modified(), True)
        self.assertEqual(p.body(), 'body0\n')

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
        self.assertEqual(p0.is_modified(), False)

        # If we touch it, it becomes True
        p0.touch()
        self.assertEqual(p0.is_modified(), True)

        # If we save it, it becomes False again
        p0.save()
        self.assertEqual(p0.is_modified(), False)

        ## Testing concrete modifications

        def check_modified():
            self.assertTrue(p0.is_modified())
            p0._modified = False

        p0.set_author('author2')
        self.assertEqual(p0.author(), 'author2')
        check_modified()

        p0.set_subject('subject2')
        self.assertEqual(p0.subject(), 'subject2')
        self.assertEqual(p0.real_subject(), 'subject2')
        check_modified()

        p0.set_messid('@')
        self.assertEqual(p0.messid(), '@')
        check_modified()

        p0.set_parent('@@')
        self.assertEqual(p0.parent(), '@@')
        check_modified()

        p0.set_date('Wed, 20 Aug 2008 17:41:31 +0200')
        self.assertEqual(p0.date(), 'Wed, 20 Aug 2008 17:41:31 +0200')
        check_modified()

        p0.set_tags(['mytag1', 'mytag2'])
        self.assertEqual(p0.tags(), ['mytag1', 'mytag2'])
        check_modified()

        p0.set_flags(['myflag1', 'myflag2'])
        self.assertEqual(p0.flags(), ['myflag1', 'myflag2'])
        check_modified()

        p0.set_body('newbody')
        self.assertEqual(p0.body(), 'newbody\n')
        check_modified()

        p0.set_body('\n newbody \n \n')
        self.assertEqual(p0.body(), 'newbody\n')
        check_modified()

        p0.delete()
        self.assertEqual(p0.is_deleted(), True)
        self.assertEqual(p0.post_id(), ('my_heap', '0'))
        self.assertEqual(p0.author(), '')
        self.assertEqual(p0.subject(), '')
        self.assertEqual(p0.messid(), '@')
        self.assertEqual(p0.parent(), '')
        self.assertEqual(p0.date(), '')
        self.assertEqual(p0.is_modified(), True)
        self.assertEqual(p0.body(), '')

    def test_write(self):
        """Tests :func:`hklib.Post.write`.

        The `force_print` argument is tested in :func:`test_postfile_str`."""

        def check_write(input, output):
            """Checks that if a post is read from `input`, it will produce
            `output` when written."""
            p = hklib.Post.from_str(input)
            sio = StringIO.StringIO()
            p.write(sio)
            self.assertEqual(sio.getvalue(), output)
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

        self.assertEqual(
            self.pop_log(),
            ('WARNING: Additional attribute in post: "Nosuchattr"\n'
             'WARNING: Additional attribute in post: "Nosuchattr2"'))

    def test_postfile_str(self):
        """Tests :func:`hklib.Post.postfile_str`."""

        # Basic test
        self.assertEqual(
            hklib.Post.from_str('Author: me').postfile_str(),
            'Author: me\n\n\n')

        # Testing empty post
        post_str = ''
        self.assertEqual(
            hklib.Post.from_str('').postfile_str(),
            '\n\n')

        # Testing when force_set is not empty
        post_str = ''
        self.assertEqual(
            hklib.Post.from_str(post_str).\
                postfile_str(force_print=set(['Author'])),
            'Author: \n\n\n')

    def test_meta_dict(self):
        """Tests :func:`hklib.Post.meta_dict`."""

        # empty post
        self.assertEqual(
            hklib.Post.from_str('\n\n').meta_dict(),
            {})

        # meta with value
        self.assertEqual(
            hklib.Post.from_str('\n\n[key value]').meta_dict(),
            {'key': 'value'})

        # meta with value with whitespace
        self.assertEqual(
            hklib.Post.from_str('\n\n[key this is a long value]').meta_dict(),
            {'key': 'this is a long value'})

        # meta without value
        self.assertEqual(
            hklib.Post.from_str('\n\n[key]').meta_dict(),
            {'key': None})

        # no meta because it is no alone in the line
        self.assertEqual(
            hklib.Post.from_str('\n\nx[key value]').meta_dict(),
            {})
        self.assertEqual(
            hklib.Post.from_str('\n\n[key value]x').meta_dict(),
            {})

        # whitespace
        self.assertEqual(
            hklib.Post.from_str('\n\n [ key  value ] ').meta_dict(),
            {'key': 'value'})

        # two metas
        self.assertEqual(
            hklib.Post.from_str('\n\n[key]\n[key2 value2]').meta_dict(),
            {'key': None, 'key2': 'value2'})

        # same meta key twice
        self.assertEqual(
            hklib.Post.from_str('\n\n[key value]\n[key value2]').meta_dict(),
            {'key': 'value2'})

    def test_body_object(self):
        """Tests the following functions:

        - :func:`hklib.Post.body_object`
        - :func:`hklib.Post._recalc_body_object`
        """

        # empty post
        self.assertEqual(
            str(hklib.Post.from_str('').body_object()),
            '<normal, text=%s>\n' % (repr('\n',)))

        # non-empty post
        self.assertEqual(
            str(hklib.Post.from_str('\nbody\n').body_object()),
            '<normal, text=%s>\n' % (repr('body\n',)))

    def test__subject(self):
        """Tests issues related to the subject."""

        def post_ws(subject):
            """Creates a post with the given subject."""
            return hklib.Post.from_str('Subject: ' + subject)

        # testing whitespace handling
        self.assertEqual(post_ws('subject').real_subject(), 'subject')
        self.assertEqual(post_ws(' subject ').real_subject(), ' subject ')
        self.assertEqual(post_ws('1\n 2').real_subject(), '1\n2')
        self.assertEqual(post_ws(' 1 \n  2 ').real_subject(), ' 1 \n 2 ')

        # testing removing the "Re:" prefix
        l = [post_ws('subject'),
             post_ws(' subject '),
             post_ws('Re: subject'),
             post_ws('re: subject'),
             post_ws('Re:subject'),
             post_ws('re:subject')]
        for p in l:
            self.assertEqual(p.subject(), 'subject')

    def test__tags_flags(self):
        """Tests issues related to tags and flags."""

        p = hklib.Post.from_str('Flag: f1\nFlag: f2\nTag: t1\nTag: t2')
        self.assertEqual(p.flags(), ['f1', 'f2'])
        self.assertEqual(p.tags(), ['t1', 't2'])
        self.assertEqual(p.has_tag('t1'), True)
        self.assertEqual(p.has_tag('t2'), True)

        # They cannot be modified via the get methods
        #p.flags()[0] = ''
        #p.tags()[0] = ''
        #self.assertEqual(p.flags(), ['f1', 'f2'])
        #self.assertEqual(p.tags(), ['t1', 't2'])

        # Iterator
        l = []
        for tag in p.tags():
            l.append(tag)
        self.assertEqual(l, ['t1', 't2'])

        # Set methods
        p.set_flags(['f'])
        self.assertEqual(p.flags(), ['f'])
        p.set_tags(['t'])
        self.assertEqual(p.tags(), ['t'])
        self.assertEqual(p.has_tag('t'), True)
        self.assertEqual(p.has_tag('t1'), False)
        self.assertEqual(p.has_tag('t2'), False)

        # Sorting
        p = hklib.Post.from_str('Flag: f2\nFlag: f1\nTag: t2\nTag: t1')
        self.assertEqual(p.flags(), ['f1', 'f2']) # flags are sorted
        self.assertEqual(p.tags(), ['t1', 't2'])  # tags are sorted

    def test__parse_tags_in_subject(self):
        """Tests the following functions:

        - :func:`hklib.Post.parse_subject`
        - :func:`hklib.Post.normalize_subject`
        """

        def test(subject1, subject2, tags):
            self.assertEqual(
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
        test(' [a] [b] Sub [c] ject', 'Sub [c] ject', ['a', 'b'])

        p = hklib.Post.from_str('Subject: [t1][t2] subject\nTag: t3')
        p.normalize_subject()
        self.assertEqual(p.subject(), 'subject')
        self.assertEqual(p.tags(), ['t3', 't1', 't2'])

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

        self.assertEqual(
            self.p(0).postfilename(),
            os.path.join(self._myheap_dir, '0.post'))

        self.assertEqual(
            self.p(0).htmlfilebasename(),
            os.path.join('my_heap', '0.html'))

        self.assertEqual(
            self.p(0).htmlfilename(),
            os.path.join(self._html_dir, 'my_heap', '0.html'))

        self.assertEqual(
            self.p(0).htmlthreadbasename(),
            os.path.join('my_heap', 'thread_0.html'))

        # htmlthreadbasename shall be called only for root posts
        self.assertRaises(
            AssertionError,
            lambda: self.p(1).htmlthreadbasename())

        self.assertEqual(
            self.p(0).htmlthreadfilename(),
            os.path.join(self._html_dir, 'my_heap', 'thread_0.html'))

        # htmlthreadfilename shall be called only for root posts
        self.assertRaises(
            AssertionError,
            lambda: self.p(1).htmlthreadfilename())

    def test_repr(self):
        """Tests :func:`hklib.Post.__repr__`."""

        self.assertEqual(
            str(self.p(0)),
            '<post my_heap/0>')

        self.assertEqual(
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

        self.assertEqual(postdb.html_dir(), self._html_dir)

        # Checking the data attributes

        self.assertEqual(
            postdb._heaps,
            {'my_heap': self._myheap_dir,
             'my_other_heap': self._myotherheap_dir})

        self.assertEqual(
            postdb._html_dir,
            self._html_dir)

        self.assertEqual(
            postdb._next_post_index,
            {('my_heap', ''): 5,
             ('my_other_heap', ''): 1})

        self.assertEqual(
            postdb.post_id_to_post,
            {self.i(0): self.p(0),
             self.i(1): self.p(1),
             self.i(2): self.p(2),
             self.i(3): self.p(3),
             self.i(4): self.p(4),
             self.io(0): self.po(0)})

        self.assertEqual(
            postdb.messid_to_post_id,
            {'0@': self.i(0),
             '1@': self.i(1),
             '2@': self.i(2),
             '3@': self.i(3),
             '4@': self.i(4),
             'other0@': self.io(0)})

        self.assertEqual(
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
        self.assertEqual(
            postdb.post_id_to_post,
            expected_postid_to_post)
        self.assertEqual(
            postdb.messid_to_post_id,
            expected_messid_to_postid)

        # Adding a post with a messid

        p = hklib.Post.from_str('Message-Id: 11@', ('my_heap', '11'))
        expected_postid_to_post = postdb.post_id_to_post.copy()
        expected_postid_to_post.update({('my_heap', '11'): p})
        expected_messid_to_postid = postdb.messid_to_post_id.copy()
        expected_messid_to_postid.update({'11@': ('my_heap', '11')})

        postdb.add_post_to_dicts(p)
        self.assertEqual(
            postdb.post_id_to_post,
            expected_postid_to_post)
        self.assertEqual(
            postdb.messid_to_post_id,
            expected_messid_to_postid)

        # Adding a post with an already used messid

        p = hklib.Post.from_str('Message-Id: 0@', ('my_heap', '12'))
        expected_postid_to_post = postdb.post_id_to_post.copy()
        expected_postid_to_post.update({('my_heap', '12'): p})
        expected_messid_to_postid = postdb.messid_to_post_id.copy()

        postdb.add_post_to_dicts(p)
        self.assertEqual(
            postdb.post_id_to_post,
            expected_postid_to_post)
        self.assertEqual(
            postdb.messid_to_post_id,
            expected_messid_to_postid)

        self.assertEqual(
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
        self.assertEqual(
            postdb.post_id_to_post,
            expected_postid_to_post)
        self.assertEqual(
            postdb.messid_to_post_id,
            expected_messid_to_postid)

        #
        # Removing a post when there are conflicting messids:
        # first remove the post that possesses the messid
        #

        # Creating the conflicting post

        p1_other = hklib.Post.from_str('Message-Id: 1@', ('my_heap', 'other1'))
        postdb.add_post_to_dicts(p1_other)
        self.assertEqual(
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
        self.assertEqual(
            postdb.post_id_to_post,
            expected_postid_to_post)
        self.assertEqual(
            postdb.messid_to_post_id,
            expected_messid_to_postid)

        # Removing the other post: the messid_to_post_id dictionary will not
        # change

        expected_postid_to_post = postdb.post_id_to_post.copy()
        del expected_postid_to_post[('my_heap', 'other1')]
        expected_messid_to_postid = postdb.messid_to_post_id.copy()

        postdb.remove_post_from_dicts(p1_other)
        self.assertEqual(
            postdb.post_id_to_post,
            expected_postid_to_post)
        self.assertEqual(
            postdb.messid_to_post_id,
            expected_messid_to_postid)

        #
        # Removing a post when there are conflicting messids:
        # first remove the post that do not possess the messid
        #

        # Creating the conflicting post

        p2_other = hklib.Post.from_str('Message-Id: 2@', ('my_heap', 'other2'))
        postdb.add_post_to_dicts(p2_other)
        self.assertEqual(
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
        self.assertEqual(
            postdb.post_id_to_post,
            expected_postid_to_post)
        self.assertEqual(
            postdb.messid_to_post_id,
            expected_messid_to_postid)

        # Removing the other post: the messid will be removed from
        # the messid_to_post_id dictionary

        expected_postid_to_post = postdb.post_id_to_post.copy()
        del expected_postid_to_post[('my_heap', '2')]
        expected_messid_to_postid = postdb.messid_to_post_id.copy()
        del expected_messid_to_postid['2@']

        postdb.remove_post_from_dicts(p2)
        self.assertEqual(
            postdb.post_id_to_post,
            expected_postid_to_post)
        self.assertEqual(
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

        self.assertEqual(
            set(postdb.post_id_to_post.keys()),
            set([('my_heap', '1'),
                 ('my_heap', 'xy'),
                 ('my_other_heap', '0')]))

        self.assertEqual(
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
        hkutils.string_to_file('Subject: sx', os.path.join(heap_dir, 'a.post'))
        hkutils.string_to_file('Subject: s2', os.path.join(heap_dir, '2.xx'))
        hkutils.string_to_file('Subject: s3', os.path.join(heap_dir, '3post'))

        postdb._heaps['my_new_heap'] = heap_dir
        postdb.load_heap('my_new_heap')

        self.assertEqual(
            set(postdb.post_id_to_post.keys()),
            set([('my_heap', '1'),
                 ('my_heap', 'xy'),
                 ('my_other_heap', '0'),
                 ('my_new_heap', '1'),
                 ('my_new_heap', 'a')]))

        self.assertEqual(
            postdb.next_post_index('my_new_heap'),
            '2')

    def test_add_heap(self):
        """Tests :func:`add_heap`."""

        postdb = self._postdb

        # Adding a new heap

        heap_dir_1 = os.path.join(self._dir, 'my_new_heap_dir_1')
        postdb.add_heap('my_new_heap_1', heap_dir_1)
        self.assertEqual(
            self.pop_log(),
            ('Warning: post directory does not exists: "%s"\n'
             'Post directory has been created.'
             % (heap_dir_1,)))

        self.assertEqual(
            postdb._heaps,
            {'my_other_heap': self._myotherheap_dir,
             'my_heap': self._myheap_dir,
             'my_new_heap_1': heap_dir_1})

        self.assertEqual(
            len(postdb.post_id_to_post.keys()),
            6)

        self.assertEqual(
            postdb.next_post_index('my_new_heap_1'),
            '1')

        # Adding a heap that has posts

        heap_dir_2 = os.path.join(self._dir, 'my_new_heap_dir_2')
        os.mkdir(heap_dir_2)
        hkutils.string_to_file('Subject: s1',
                               os.path.join(heap_dir_2, '1.post'))
        postdb.add_heap('my_new_heap_2', heap_dir_2)

        self.assertEqual(
            len(postdb.post_id_to_post.keys()),
            7)

        self.assertEqual(
            postdb.next_post_index('my_new_heap_2'),
            '2')

    def test_set_html_dir(self):
        """Tests :func:`set_html_dir`."""

        postdb = self._postdb

        # Non-existing directory

        html_dir_1 = os.path.join(self._dir, 'html_dir_1')
        postdb.set_html_dir(html_dir_1)
        self.assertEqual(
            postdb._html_dir,
            html_dir_1)
        self.assertEqual(
            self.pop_log(),
            ('Warning: HTML directory does not exists: "%s"\n'
             'HTML directory has been created.'
             % (html_dir_1,)))

        # Existing directory

        html_dir_2 = os.path.join(self._dir, 'html_dir_2')
        os.mkdir(html_dir_2)
        postdb.set_html_dir(html_dir_2)
        self.assertEqual(
            postdb._html_dir,
            html_dir_2)

    def test_get_heaps_from_config(self):
        """Tests :func:`hklib.PostDB.get_heaps_from_config`."""

        # "paths/heaps" is specified

        config = {'heaps':
                     {'my_heap1': {'id' : 'my_heap1',
                                   'path': 'my_heap_dir_1'},
                      'my_heap2': {'id': 'my_heap2',
                                   'path': 'my_heap_dir_2'}}}

        heaps = hklib.PostDB.get_heaps_from_config(config)
        self.assertEqual(
            heaps,
            {'my_heap1': 'my_heap_dir_1',
             'my_heap2': 'my_heap_dir_2'})

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

        config = {'paths': {'html_dir': html_dir},
                  'heaps': {'new_heap': {'id': 'new_heap',
                                         'path': new_heap_dir}}}

        postdb.read_config(config)

        # The new heap goes next to the other heaps. Currently the heaps that
        # are not present in the configuration are not touched by read_config.
        self.assertEqual(
            postdb._heaps,
            {'my_heap': self._myheap_dir,
             'my_other_heap': self._myotherheap_dir,
             'new_heap': new_heap_dir})

        # The post was read
        self.assert_(postdb.post('new_heap/1') != None)

        # The html_dir was set
        self.assertEqual(postdb.html_dir(), html_dir)

    def test__get_methods(self):
        """Tests the following functions:

        - :func:`hklib.PostDB.has_post_id`
        - :func:`hklib.PostDB.heap_ids`
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

        # Testing heap_ids
        self.assertEqual(
            set(postdb.heap_ids()),
            set(['my_heap', 'my_other_heap']))

        # Testing has_heap_id
        self.assertTrue(postdb.has_heap_id('my_heap'))
        self.assertFalse(postdb.has_heap_id('nosuchheap'))

        # Testing next_post_index
        self.assertEqual(postdb.next_post_index('my_heap'), '5')

        # Testing postset
        self.assertEqual(
            postdb.postset(['my_heap/0']),
            hklib.PostSet(postdb, self.p(0)))

        # Testing post_by_post_id
        self.assertEqual(
            postdb.post_by_post_id('my_heap/0'),
            self.p(0))
        self.assertEqual(
            postdb.post_by_post_id('my_heap/111'),
            None)

        # Testing post_by_messid
        self.assertEqual(
            postdb.post_by_messid('0@'),
            self.p(0))
        self.assertEqual(
            postdb.post_by_messid('111@'),
            None)

        # Testing postfile_name
        self.assertEqual(
            postdb.postfile_name(self.p(0)),
            os.path.join(self._myheap_dir, '0.post'))

        # Testing html_dir
        self.assertEqual(
            postdb.html_dir(),
            os.path.join(self._html_dir))

    def test_next_post_index(self):
        """Tests :func:`hklib.PostDB.next_post_index`."""
        postdb = self._postdb

        # Basic test
        self.assertEqual(postdb.next_post_index('my_heap'), '5')
        self.assertEqual(postdb.next_post_index('my_heap'), '6')

        # We don't fill in the holes
        postdb.invalidate_next_post_index_cache()
        postdb.add_new_post(hklib.Post.create_empty(), 'my_heap', '9')
        self.assertEqual(postdb.next_post_index('my_heap'), '10')

        # Testing prefixed
        self.assertEqual(postdb.next_post_index('my_heap', 'a_'), 'a_1')
        self.assertEqual(postdb.next_post_index('my_heap', 'a_'), 'a_2')

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
        self.assertEqual('Message-Id: mess1',
                          hkutils.file_to_string(postfile1))
        self.assertEqual('Message-Id: mess2',
                          hkutils.file_to_string(postfile2))
        postdb.save()
        postfile1_str = 'Subject: subject\nMessage-Id: mess1\n\n\n'
        self.assertEqual(postfile1_str,
                          hkutils.file_to_string(postfile1))
        self.assertEqual('Message-Id: mess2',
                          hkutils.file_to_string(postfile2))

        # Adding a new post
        postfile3 = os.path.join(new_heap_dir, '3.post')
        p3 = hklib.Post.from_str('Subject: subject3')
        postdb.add_new_post(p3, 'new_heap')
        self.assertEqual(
            set(postdb.post_id_to_post.keys()),
            set([('new_heap', '1'),
                 ('new_heap', '2'),
                 ('new_heap', '3')]))
        self.assertFalse(os.path.exists(postfile3))
        postdb.save()
        self.assert_(os.path.exists(postfile3))

        # Deleting a post
        self.assertEqual(set([p1, p2, p3]), set(postdb.posts()))
        self.assertEqual(set([p1, p2, p3]), set(postdb.real_posts()))
        p1.delete()
        self.assertEqual(set([p2, p3]), set(postdb.posts()))
        self.assertEqual(set([p1, p2, p3]), set(postdb.real_posts()))

    def test_post(self):
        """Tests :func:`hklib.PostDB.post`."""

        postdb = self._postdb
        p0 = self.p(0)

        # Specifying the post

        self.assertEqual(postdb.post(p0), p0)

        # Specifying the post id

        self.assertEqual(postdb.post('my_heap/0'), p0)
        self.assertEqual(postdb.post(('my_heap', '0')), p0)
        self.assertEqual(postdb.post(('my_heap', 0)), p0)

        # Specifying the post index

        self.assertEqual(postdb.post('0', heap_id_hint='my_heap'), p0)
        self.assertEqual(postdb.post(0, heap_id_hint='my_heap'), p0)
        self.assertEqual(postdb.post('0'), None) # no hint -> post not found
        self.assertEqual(postdb.post(0), None) # no hint -> post not found

        # bad hint -> post not found
        self.assertEqual(postdb.post('1', heap_id_hint='my_other_heap'), None)

        # Specifying the message id

        self.assertEqual(postdb.post('0@'), p0)

        # Testing the `raise_exception` parameter

        self.assertEqual(postdb.post('nosuchpost'), None)
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
        self.assertEqual(p1.subject(), 'sub1')
        self.assert_(postdb.post('my_heap/11') is p1)
        self.assertEqual(
            hkutils.file_to_string(p1.postfilename()),
            'Subject: sub1\n\n\n')
        self.assertEqual(postdb.post('my_heap/x').subject(), 'sub_new')

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
        self.assertEqual(all_posts_1, all_1)

        # If we modify the post database, `all` should return a different
        # object then previously and the previously returned object should be
        # unmodified

        p5 = self.add_post(5)
        all_posts_2 = all_posts_1 | p5
        all_3 = postdb.all()
        self.assertEqual(all_posts_2, all_3)
        # `all_1` was not modified:
        self.assertEqual(all_posts_1, all_1)

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
        self.assertEqual(ts1, expected_ts_1)

        # If we modify the post database, `threadstruct` should return a
        # different object then previously and the previously returned object
        # should be unmodified

        self.add_post(5, 0)
        expected_ts_2 = \
            {None: [self.i(0), self.io(0), self.i(4)],
             self.i(0): [self.i(1), self.i(3), self.i(5)],
             self.i(1): [self.i(2)]}
        ts3 = postdb.threadstruct()
        self.assertEqual(ts3, expected_ts_2)
        # `ts1` was not modified:
        self.assertEqual(ts1, expected_ts_1)

        # Deleting posts

        self.p(1).delete()
        expected_ts = \
            {None: [self.i(0), self.io(0), self.i(2), self.i(4)],
             self.i(0): [self.i(3), self.i(5)]}
        self.assertEqual(postdb.threadstruct(), expected_ts)

        self.p(0).delete()
        expected_ts = \
            {None: [self.io(0), self.i(2), self.i(3), self.i(4), self.i(5)]}
        self.assertEqual(postdb.threadstruct(), expected_ts)

        self.p(2).delete()
        self.p(3).delete()
        self.p(4).delete()
        self.p(5).delete()
        self.po(0).delete()
        expected_ts = {None: []}
        self.assertEqual(postdb.threadstruct(), expected_ts)

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
        self.assertEqual(postdb.threadstruct(), ts)

    def test_parent(self):
        """Tests :func:`hklib.PostDB.parent`."""

        postdb = self._postdb

        self.assertEqual(postdb.parent(self.p(0)), None)
        self.assertEqual(postdb.parent(self.p(1)), self.p(0))
        self.assertEqual(postdb.parent(self.p(2)), self.p(1))
        self.assertEqual(postdb.parent(self.p(3)), self.p(0))
        self.assertEqual(postdb.parent(self.p(4)), None)
        self.assertEqual(postdb.parent(self.po(0)), None)

    def test_root(self):
        """Tests :func:`hklib.PostDB.parent`."""

        postdb = self._postdb

        ## Testing when there is no cycle

        self.assertEqual(postdb.root(self.p(0)), self.p(0))
        self.assertEqual(postdb.root(self.p(1)), self.p(0))
        self.assertEqual(postdb.root(self.p(2)), self.p(0))
        self.assertEqual(postdb.root(self.p(3)), self.p(0))
        self.assertEqual(postdb.root(self.p(4)), self.p(4))
        self.assertEqual(postdb.root(self.po(0)), self.po(0))

        ## Testing cycles

        self.introduce_cycle()

        # Normal posts:
        self.assertEqual(postdb.root(self.p(0)), self.p(0))
        self.assertEqual(postdb.root(self.p(1)), self.p(0))
        self.assertEqual(postdb.root(self.p(2)), self.p(0))
        self.assertEqual(postdb.root(self.p(4)), self.p(4))
        self.assertEqual(postdb.root(self.po(0)), self.po(0))


        # Posts in cycle:
        self.assertEqual(postdb.root(self.p(3)), None)
        self.assertEqual(postdb.root(self.p(5)), None)
        self.assertEqual(postdb.root(self.p(6)), None)
        self.assertEqual(postdb.root(self.p(7)), None)

    def test_children(self):
        """Tests :func:`hklib.PostDB.children`."""

        postdb = self._postdb

        self.assertEqual(
            postdb.children(None),
            [self.p(0), self.po(0), self.p(4)])
        self.assertEqual(postdb.children(self.p(0)), [self.p(1), self.p(3)])
        self.assertEqual(postdb.children(self.p(1)), [self.p(2)])
        self.assertEqual(postdb.children(self.p(2)), [])
        self.assertEqual(postdb.children(self.p(3)), [])
        self.assertEqual(postdb.children(self.p(4)), [])
        self.assertEqual(postdb.children(self.po(0)), [])

        # Testing the `threadstruct` parameter

        ts = {('my_heap', '0'): [self.p(1)]}
        self.assertEqual(
            postdb.children(self.p(0), ts),
            [self.p(1)])
        self.assertEqual(
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

        self.assertEqual(
            list(postdb.iter_thread(None)),
            [p(0), p(1), p(2), p(3), po(0), p(4)])
        self.assertEqual(
            list(postdb.iter_thread(p(0))),
            [p(0), p(1), p(2), p(3)])
        self.assertEqual(list(postdb.iter_thread(p(1))), [p(1), p(2)])
        self.assertEqual(list(postdb.iter_thread(p(2))), [p(2)])
        self.assertEqual(list(postdb.iter_thread(p(3))), [p(3)])
        self.assertEqual(list(postdb.iter_thread(p(4))), [p(4)])
        self.assertEqual(list(postdb.iter_thread(po(0))), [po(0)])

        # If the post is not in the postdb, AssertionError will be raised
        self.assertRaises(
            AssertionError,
            lambda: list(postdb.iter_thread(hklib.Post.from_str(''))))

        # Testing the `threadstruct` parameter
        ts = {('my_heap', '0'): [self.p(1)]}
        self.assertEqual(
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
            self.assertEqual(postitem_strings, expected_result)

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
        self.assertEqual(
            ''.join([str(postitem) + '\n'
                     for postitem in postdb.walk_thread(self.p(0), ts)]),
             ("<PostItem: pos=begin, post_id=my_heap/0, level=0>\n"
                "<PostItem: pos=begin, post_id=my_heap/1, level=1>\n"
                "<PostItem: pos=end, post_id=my_heap/1, level=1>\n"
              "<PostItem: pos=end, post_id=my_heap/0, level=0>\n"))

        # Testing the `yield_main` parameter

        def test(root, expected_result):
            # function already defined # pylint: disable-msg=E0102
            """Tests whether the the :func:`PostDB.walk_thread` function
            returns the given result when executed with the given root."""

            postitem_strings = \
                [ str(postitem) + '\n'
                  for postitem in postdb.walk_thread(root, yield_main=True) ]
            postitem_strings = ''.join(postitem_strings)
            self.assertEqual(postitem_strings, expected_result)

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
        self.assertEqual(postdb.has_cycle(), False)
        self.assertEqual(postdb.cycles(), postdb.postset([]))

        # Testing cycles
        self.introduce_cycle()
        self.assertEqual(postdb.has_cycle(), True)
        self.assertEqual(
            postdb.cycles(),
            postdb.postset([self.p(3), self.p(5), self.p(6), self.p(7)]))

    def test_walk_cycles(self):
        """Tests :func:`hklib.PostDB.walk_cycles`."""

        # Testing when there are no cycles
        self.assertEqual(
            [pi for pi in self._postdb.walk_cycles()],
            [])

        # Testing cycles
        self.introduce_cycle()
        self.assertEqual(
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
        self.assertEqual(postdb.threadstruct(), threadstruct)
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
        self.assertEqual(roots1, [p(0), po(0), p(4)])

        # If we modify the post database, `root` should return a different
        # object then previously and the previously returned object should be
        # unmodified

        self.add_post(5, None)
        roots3 = postdb.roots()
        self.assertEqual(roots3, [p(0), po(0), p(4), p(5)])
        # `root1` was not modified:
        self.assertEqual(roots1, [p(0), po(0), p(4)])

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
        self.assertEqual(
            threads1,
            {p(0): postdb.postset([p(0), p(1), p(2), p(3)]),
             po(0): postdb.postset([po(0)]),
             p(4): postdb.postset([p(4)])})

        # If we modify the post database, `threads` should return a different
        # object then previously and the previously returned object should be
        # unmodified

        self.add_post(5, None)
        threads3 = postdb.threads()
        self.assertEqual(
            threads3,
            {p(0): postdb.postset([p(0), p(1), p(2), p(3)]),
             po(0): postdb.postset([po(0)]),
             p(4): postdb.postset([p(4)]),
             p(5): postdb.postset([p(5)])})
        # `threads1` was not modified:
        self.assertEqual(
            threads1,
            {p(0): postdb.postset([p(0), p(1), p(2), p(3)]),
             po(0): postdb.postset([po(0)]),
             p(4): postdb.postset([p(4)])})

    def test_move(self):
        """Tests :func:`hklib.PostDB.move`."""

        postdb = self._postdb
        p = self.p
        po = self.po

        # We won't be able to refer to p(0) as `p(0)` because its post id will
        # change
        p0 = self.p(0)

        p(1).set_body('heap://0 heap://my_heap/0')
        p(2).set_body('heap://1 heap://my_heap/1')
        p(3).set_parent('0')
        p(4).set_parent('my_heap/0')
        po(0).set_body('heap://my_heap/0 heap://my_other_heap/0')

        ## Moving within a heap

        postdb.move(p0, 'my_heap/moved')

        # The parent reference of post 1 is unchanged (it references to post 0
        # by its message id) but that of post 3 and 4 is modified (they
        # reference to post 0 by its post id)

        self.assertEqual(
            p(1).parent(),
            '0@')

        self.assertEqual(
            p(3).parent(),
            'moved')

        self.assertEqual(
            p(4).parent(),
            'my_heap/moved')

        # References in bodies were modified

        self.assertEqual(
            p(1).body(),
            'heap://moved heap://my_heap/moved\n')

        self.assertEqual(
            p(2).body(),
            'heap://1 heap://my_heap/1\n')

        self.assertEqual(
            po(0).body(),
            'heap://my_heap/moved heap://my_other_heap/0\n')

        ## Moving across heaps

        postdb.move(p0, 'my_other_heap/moved2')

        # The parent reference of post 1 is unchanged (it references to post 0
        # by its message id) but that of post 3 and 4 is modified (they
        # reference to post 0 by its post id)

        self.assertEqual(
            p(1).parent(),
            '0@')

        self.assertEqual(
            p(3).parent(),
            'my_other_heap/moved2')

        self.assertEqual(
            p(4).parent(),
            'my_other_heap/moved2')

        # References in bodies were modified

        self.assertEqual(
            p(1).body(),
            ('heap://my_other_heap/moved2 '
             'heap://my_other_heap/moved2\n'))

        self.assertEqual(
            p(2).body(),
            'heap://1 heap://my_heap/1\n')

        self.assertEqual(
            po(0).body(),
            'heap://my_other_heap/moved2 heap://my_other_heap/0\n')

        ## Using a placeholder

        postdb.move(p0, 'my_other_heap/moved3', placeholder=True)

        # Checking the placeholder post
        self.assertEquals(
            postdb.postset(postdb.real_posts()).collect.is_deleted(),
            postdb.postset('my_other_heap/moved2'))

        ## Error: post id already occupied

        self.assertRaises(
            hkutils.HkException,
            lambda: postdb.move(p0, 'my_heap/1'))

        self.assertRaises(
            hkutils.HkException,
            lambda: postdb.move(p(1), 'my_heap/1'))

        ## Error: non-existing heap

        self.assertRaises(
            hkutils.HkException,
            lambda: postdb.move(p0, 'my_new_heap/moved'))


class Test_PostItem(unittest.TestCase):

    """Tests :class:`hklib.PostItem`."""

    def test_str(self):
        """Tests :func:`hklib.PostItem.__str__`."""

        # hklib.Post with heapid
        post = hklib.Post.from_str('', post_id=('my_heap', 42))
        postitem = hklib.PostItem(pos='begin', post=post, level=0)
        self.assertEqual(
            str(postitem),
            "<PostItem: pos=begin, post_id=my_heap/42, level=0>")

        # hklib.Post without heapid
        post = hklib.Post.from_str('')
        postitem = hklib.PostItem(pos='begin', post=post, level=0)
        self.assertEqual(
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
        self.assertEqual(
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

        self.assertEqual(postitem1, postitem2)
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

        self.assertEqual(ps1, hklib.PostSet(postdb, []))
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
        self.assertEqual(ps0, ps1)
        self.assertEqual(ps0, ps2)
        self.assertEqual(ps0, ps3)
        self.assertEqual(ps0, ps4)
        self.assertEqual(ps0, ps5)
        self.assertEqual(ps0, ps6)
        self.assertEqual(ps0, ps7)
        self.assertEqual(ps0, ps8)
        self.assertEqual(ps0, ps9)
        self.assertEqual(ps0, ps10)

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
        self.assertEqual(ps_all, postdb.all())
        p1.delete()
        self.assertEqual(ps2, postdb.all())

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
            self.assertEqual(s1, p1.subject())
            self.assertEqual(s2, p2.subject())
            self.assertEqual(s3, p3.subject())

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
        self.assertEqual(
            postdb.all().sorted_list(),
            [p(0), po(0), p(1), p(2), p(3), p(4)])


class Test__config(unittest.TestCase):

    """Tests the configuration objects."""

    def test__format_1(self):
        """Tests the following functions:

        - :func:`hklib:unify_format`
        - :func:`hklib:unify_format_1`
        - :func:`hklib:convert_heaps_f2_to_f3`
        - :func:`hklib:convert_nicknames_f12_to_f3`
        """

        # Specifying only the mandatory fields
        self.assertEqual(
             hklib.unify_config(
                 {'paths': {'mail': 'dir1',
                            'html': '-html'}}),
             {'paths': {'html_dir': '-html'},
              'heaps': {'defaultheap': {'path': 'dir1',
                                        'id': 'defaultheap',
                                        'name': 'defaultheap',
                                        'nicknames': {}}},
              'nicknames': {}})

        # Specifying all fields
        self.assertEqual(
             hklib.unify_config(
                 {'paths': {'mail': 'dir1',
                            'html': '-html'},
                  'server': {'host': '-host',
                             'port': '1111',
                             'username': '-username',
                             'password': '-password'},
                  'nicknames': {0: 'nick1 email1',
                                1: 'nick2 email2'}}),
             {'paths': {'html_dir': '-html'},
              'heaps': {'defaultheap': {'path': 'dir1',
                                        'id': 'defaultheap',
                                        'name': 'defaultheap',
                                        'nicknames': {}}},
              'server': {'host': '-host',
                         'port': 1111,
                         'username': '-username',
                         'password': '-password'},
              'nicknames': {'email1': 'nick1',
                            'email2': 'nick2'}})

        # Not specifying all mandatory fields
        self.assertRaises(
            KeyError,
            lambda: hklib.unify_config({'paths': {'mail': 'dir'}}))

    def test__format_2(self):
        """Tests the following functions:

        - :func:`hklib:unify_format`
        - :func:`hklib:unify_format_2`
        - :func:`hklib:convert_heaps_f2_to_f3`
        - :func:`hklib:convert_nicknames_f12_to_f3`
        """

        # Specifying only the mandatory fields
        self.assertEqual(
             hklib.unify_config(
                 {'paths': {'heaps': 'heap1:dir1;heap2:dir2',
                            'html': '-html'}}),
             {'paths': {'html_dir': '-html'},
              'heaps': {'heap1': {'path': 'dir1',
                                  'id': 'heap1',
                                  'name': 'heap1',
                                  'nicknames': {}},
                        'heap2': {'path': 'dir2',
                                  'id': 'heap2',
                                  'name': 'heap2',
                                  'nicknames': {}}},
              'nicknames': {}})

        # Specifying all fields
        self.assertEqual(
             hklib.unify_config(
                 {'paths': {'heaps': 'heap1:dir1;heap2:dir2',
                            'html': '-html'},
                  'server': {'host': '-host',
                             'port': '1111',
                             'username': '-username',
                             'password': '-password'},
                  'nicknames': {0: 'nick1 email1',
                                1: 'nick2 email2'}}),
             {'paths': {'html_dir': '-html'},
              'heaps': {'heap1': {'path': 'dir1',
                                  'id': 'heap1',
                                  'name': 'heap1',
                                  'nicknames': {}},
                        'heap2': {'path': 'dir2',
                                  'id': 'heap2',
                                  'name': 'heap2',
                                  'nicknames': {}}},
              'server': {'host': '-host',
                         'port': 1111,
                         'username': '-username',
                         'password': '-password'},
              'nicknames': {'email1': 'nick1',
                            'email2': 'nick2'}})

        # Testing several heaps
        self.assertRaises(
            hkutils.HkException,
            lambda: hklib.unify_config({'paths': {'heaps': '',
                                                  'html': '-html'}}))

    def test__format_3(self):
        """Tests the following functions:

        - :func:`hklib:unify_format`
        - :func:`hklib:unify_format_3`
        - :func:`hklib:unify_nicknames`
        - :func:`hklib:unify_server`
        """

        # Specifying only the mandatory fields
        self.assertEqual(
             hklib.unify_config(
                 {'paths': {'html_dir': '-html_dir'},
                  'heaps': {'-heap': {'path': '-path'}}}),
             {'paths': {'html_dir': '-html_dir'},
              'heaps': {'-heap': {'path': '-path',
                                  'id': '-heap',
                                  'name': '-heap',
                                  'nicknames': {}}},
              'nicknames': {}})

        # Specifying all fields
        self.assertEqual(
             hklib.unify_config(
                 {'paths': {'html_dir': '-html_dir'},
                  'heaps': {'-heap': {'path': '-path',
                                      'id': '-id',
                                      'name': '-name',
                                      'server': {'host': '-host2',
                                                 'port': '2222',
                                                 'username': '-user2',
                                                 'password': '-pw2'},
                                      'nicknames': {'a': 'b'}}},
                  'server': {'host': '-host',
                             'port': '1111',
                             'username': '-username',
                             'password': '-password'},
                  'nicknames': {'c': 'd'}}),
             {'paths': {'html_dir': '-html_dir'},
              'heaps': {'-heap': {'path': '-path',
                                  'id': '-id',
                                  'name': '-name',
                                  'server': {'host': '-host2',
                                             'port': 2222,
                                             'username': '-user2',
                                             'password': '-pw2'},
                                  'nicknames': {'a': 'b'}}},
              'server': {'host': '-host',
                         'port': 1111,
                         'username': '-username',
                         'password': '-password'},
              'nicknames': {'c': 'd'}})

        # Testing when server/password is not specified
        self.assertEqual(
             hklib.unify_config(
                 {'paths': {'html_dir': '-html_dir'},
                  'heaps': {'-heap': {'path': '-path'}},
                  'server': {'host': '-host',
                             'port': '1111',
                             'username': '-username'}}),
             {'paths': {'html_dir': '-html_dir'},
              'heaps': {'-heap': {'path': '-path',
                                  'id': '-heap',
                                  'name': '-heap',
                                  'nicknames': {}}},
              'server': {'host': '-host',
                         'port': 1111,
                         'username': '-username'},
              'nicknames': {}})

        # Testing several heaps
        self.assertEqual(
             hklib.unify_config(
                 {'paths': {'html_dir': '-html_dir'},
                  'heaps': {'-heap1': {'path': '-path1'},
                            '-heap2': {'path': '-path2'}}}),
             {'paths': {'html_dir': '-html_dir'},
              'heaps': {'-heap1': {'path': '-path1',
                                   'id': '-heap1',
                                   'name': '-heap1',
                                   'nicknames': {}},
                        '-heap2': {'path': '-path2',
                                   'id': '-heap2',
                                   'name': '-heap2',
                                   'nicknames': {}}},
              'nicknames': {}})

        # Testing several heaps
        self.assertRaises(
            KeyError,
            lambda: hklib.unify_config({}))


if __name__ == '__main__':
    hkutils.set_log(False)
    unittest.main()
