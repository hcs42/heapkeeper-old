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

"""Tests the hkshell module.

Usage:

    $ python test_hkshell.py
"""


from __future__ import with_statement

import os
import time
import unittest

import hkutils
import hklib
import hkshell
import test_hklib


class Test__1(unittest.TestCase):

    """Tests that do not require a PostDB."""

    def test__listeners(self):

        def listener(e):
            event_list.append(e.type)

        ## Testing the `listener` list and the `event` function

        event_list = []
        hkshell.event(0)
        hkshell.listeners.append(listener)
        hkshell.event(1)
        hkshell.listeners.append(listener)

        # The following event will be received by the `listener` function twice
        hkshell.event(2)

        hkshell.listeners.remove(listener)
        hkshell.event(3)
        hkshell.listeners.remove(listener)
        hkshell.event(4)
        self.assertEquals(event_list, [1, 2, 2, 3])

        ## Testing the `append_listener` and `remove_listener` functions

        event_list = []
        hkshell.event(0)
        hkshell.append_listener(listener)

        # a listener cannot be appended if it's in the list
        self.assertRaises(
            hkutils.HkException,
            lambda: hkshell.append_listener(listener))

        hkshell.event(1)
        hkshell.remove_listener(listener)

        # a listener cannot be removed if it's not in the list
        self.assertRaises(
            hkutils.HkException,
            lambda: hkshell.remove_listener(listener))

        hkshell.event(2)
        self.assertEquals(event_list, [1])

        ## Testing instance variables of Event

        def listener2(e):
            event_list.append(e)

        event_list = []
        hkshell.append_listener(listener2)
        hkshell.event(type='mytype')
        hkshell.event(type='mytype', command='mycommand')
        hkshell.remove_listener(listener2)

        self.assertEquals(event_list[0].type, 'mytype')
        self.assertEquals(event_list[0].command, None)
        self.assertEquals(event_list[1].type, 'mytype')
        self.assertEquals(event_list[1].command, 'mycommand')

    def test_hkshell_events(self):

        hkshell.append_listener(lambda e: event_list.append(e))

        ## Testing the add_events decorator

        # Default name for the `command` attribute

        @hkshell.add_events()
        def f():
            hkshell.event(type='f_body', command='f')
            return 1

        event_list = []
        result = f()

        self.assertEquals(result, 1)
        self.assertEquals(event_list[0].type, 'before')
        self.assertEquals(event_list[0].command, 'f')
        self.assertEquals(event_list[1].type, 'f_body')
        self.assertEquals(event_list[1].command, 'f')
        self.assertEquals(event_list[2].type, 'after')
        self.assertEquals(event_list[2].command, 'f')

        # Specified name for the `command` attribute

        @hkshell.add_events('f_cmd1')
        def f():
            hkshell.event(type='f_body', command='f_cmd2')
            return 1

        event_list = []
        result = f()

        self.assertEquals(result, 1)
        self.assertEquals(event_list[0].type, 'before')
        self.assertEquals(event_list[0].command, 'f_cmd1')
        self.assertEquals(event_list[1].type, 'f_body')
        self.assertEquals(event_list[1].command, 'f_cmd2')
        self.assertEquals(event_list[2].type, 'after')
        self.assertEquals(event_list[2].command, 'f_cmd1')


class Test__2(unittest.TestCase, test_hklib.PostDBHandler):

    """Tests that require a PostDB."""

    # Thread structure:
    # 0 <- 1 <- 2
    #   <- 3
    # 4

    def setUp(self):
        self.setUpDirs()
        self.create_postdb()
        self.create_threadst()

    def tearDown(self):
        self.tearDownDirs()

    def test_ModificationListener(self):

        postdb = self._postdb
        p = self.p

        def my_cmd(fun):
            hkshell.event(type='before')
            fun()
            hkshell.event(type='after')

        # Adding the listener
        mod_listener = hkshell.ModificationListener(postdb)
        self.assertEquals(postdb.listeners, [mod_listener])
        hkshell.append_listener(mod_listener)

        # Using the listener
        self.assert_(mod_listener.touched_posts().is_set([]))
        my_cmd(lambda: None)
        self.assert_(mod_listener.touched_posts().is_set([]))
        my_cmd(lambda: p(0).set_subject("other"))
        self.assert_(mod_listener.touched_posts().is_set([p(0)]))
        my_cmd(lambda: p(1).set_subject("other"))
        my_cmd(lambda: p(2).set_subject("other"))
        self.assert_(mod_listener.touched_posts().is_set([p(2)]))

        def f():
            p(0).set_subject("other2")
            p(1).set_subject("other2")
        my_cmd(f)
        self.assert_(mod_listener.touched_posts().is_set([p(0), p(1)]))

        # Removing the listener
        hkshell.remove_listener(mod_listener)
        mod_listener.close()
        self.assertEquals(postdb.listeners, [])


class Test__3(unittest.TestCase, test_hklib.PostDBHandler):

    """Tests that require a hkshell."""

    # Thread structure:
    # 0 <- 1 <- 2
    #   <- 3
    # 4

    def setUp(self):

        # Reload is necessary only when the test cases do not clean up after
        # themselves (e.g. they do not set the default hkshell values).

        # reload(hkshell)

        self.setUpDirs()
        self.create_postdb()
        self.create_threadst()
        hkshell.options.postdb = self._postdb
        hkshell.set_heap_id_hint('my_heap')

        # Redirect the output of hkshell to nowhere.
        class NullOutput():
            def write(self, str):
                pass
        hkshell.options.output = NullOutput()

    def tearDown(self):
        self.tearDownDirs()

    def ae(self, x, y):
        self.assertEquals(x, y)

    def init_hkshell(self):
        hkshell.init()

    def my_cmd(self, fun):
        hkshell.event(type='before', command='my_cmd')
        fun()
        hkshell.event(type='after')

    def touch_posts_cmd(self, postindices):
        hkshell.event(type='before', command='touch_posts_cmd')
        for postindex in postindices:
            self.p(postindex).touch()
        hkshell.event(type='after')

    def _test_gen_indices(self, on, off):
        """
        Arguments:
        on -- A function that turns on the `gen_indices` feature.
            Type: fun()
        off -- A function that turns off the `gen_indices` feature.
            Type: fun()
        """

        call_count = [0]

        def gen_indices(postdb):
            call_count[0] += 1
            self.assertEquals(postdb, self._postdb)

        # Initializing hkshell
        hkshell.options.callbacks.gen_indices = gen_indices
        self.init_hkshell()

        # Before turning it on
        self.my_cmd(lambda: self.p(0).touch())
        self.assertEquals(call_count, [0])

        # Testing
        on()
        self.my_cmd(lambda: self.p(0).touch())
        self.assertEquals(call_count, [1])
        off()

        # After turning it off
        self.my_cmd(lambda: self.p(0).touch())
        self.assertEquals(call_count, [1])

    def test_gen_indices_listener(self):
        self._test_gen_indices(
            on=lambda: hkshell.append_listener(hkshell.gen_indices_listener),
            off=lambda: hkshell.remove_listener(hkshell.gen_indices_listener))

    def test_gen_indices__feature(self):
        def on_fun():
            self.assertEquals(hkshell.features()['gen_indices'], 'off')
            hkshell.on('gen_indices')
            self.assertEquals(hkshell.features()['gen_indices'], 'on')
        def off_fun():
            self.assertEquals(hkshell.features()['gen_indices'], 'on')
            hkshell.off('gen_indices')
            self.assertEquals(hkshell.features()['gen_indices'], 'off')
        self._test_gen_indices(on=on_fun, off=off_fun)

    def _test_save(self, on, off):

        self.init_hkshell()

        # Before turning it on
        self.my_cmd(lambda: self.p(0).set_subject('newsubject0'))
        self.assertFalse(os.path.exists(self.p(0).postfilename()))

        on()

        # Auto-save works
        self.my_cmd(lambda: self.p(0).set_subject('newsubject1'))
        post0 = hklib.Post.from_file(self.p(0).postfilename())
        self.assertEquals(post0.subject(), 'newsubject1')

        off()

        # After turning it off
        self.my_cmd(lambda: self.p(0).set_subject('newsubject2'))
        post0 = hklib.Post.from_file(self.p(0).postfilename())
        self.assertEquals(post0.subject(), 'newsubject1')

    def test_save_listener(self):
        self._test_save(
            on=lambda: hkshell.append_listener(hkshell.save_listener),
            off=lambda: hkshell.remove_listener(hkshell.save_listener))

    def test_save_listener(self):
        self._test_save(
            on=lambda: hkshell.on('save'),
            off=lambda: hkshell.off('save'))

    def _test_TouchedPostPrinter(self, on, off):

        class MyOutput():
            @staticmethod
            def write(str):
                output_list.append(str)
        output = MyOutput()

        hkshell.options.output = output
        hkshell.touching_commands.append('touch_posts_cmd')
        self.init_hkshell()

        on()

        # No output should be printed
        output_list = []
        self.my_cmd(lambda: None)
        self.assertEquals(
            output_list,
            [])

        # No post touched
        output_list = []
        self.touch_posts_cmd([])
        self.assertEquals(
            output_list,
            ['No post has been touched.\n'])

        # One post touched
        output_list = []
        self.touch_posts_cmd([1])
        self.assertEquals(
            output_list,
            ['1 post has been touched:\n',
             "['my_heap/1']\n"])

        # More than one posts touched
        output_list = []
        self.touch_posts_cmd([1, 2])
        self.assertEquals(
            output_list,
            ['2 posts have been touched:\n',
             "['my_heap/1', 'my_heap/2']\n"])

        off()

    def test_TouchedPostPrinterListener(self):
        self._test_TouchedPostPrinter(
            on=lambda: hkshell.append_listener(
                           hkshell.touched_post_printer_listener),
            off=lambda: hkshell.remove_listener(
                            hkshell.touched_post_printer_listener))

    def test_TouchedPostPrinter__feature(self):
        def on_fun():
            self.assertEquals(
                hkshell.features()['touched_post_printer'],
                'off')
            hkshell.on('touched_post_printer')
            self.assertEquals(
                hkshell.features()['touched_post_printer'],
                'on')
        def off_fun():
            self.assertEquals(
                hkshell.features()['touched_post_printer'],
                'on')
            hkshell.off('touched_post_printer')
            self.assertEquals(
                hkshell.features()['touched_post_printer'],
                'off')
        self._test_TouchedPostPrinter(on=on_fun, off=off_fun)

    def test_tagset(self):
        def test(pretagset, tagset):
            self.assertEquals(hkshell.tagset(pretagset), tagset)
        test('t', set(['t']))
        test('t1', set(['t1']))
        test(['t'], set(['t']))
        test(['t1', 't2'], set(['t1', 't2']))
        test(set(['t']), set(['t']))
        test(set(['t1', 't2']), set(['t1', 't2']))

        def f():
            hkshell.tagset(0)
        self.assertRaises(hkutils.HkException, f)

    def subjects(self):
        return [ self.p(i).subject() for i in range(5) ]

    def tags(self):
        return [ self.p(i).tags() for i in range(5) ]

    def clear_subjects(self):
        for post in self._postdb.posts():
            post.set_subject('')

    def test_self(self):
        self.init_hkshell()
        self.clear_subjects()
        self.assertEquals(self.subjects(), ['','','','',''])
        self.assertEquals(self.tags(), [[],[],[],[],[]])

    def test_p(self):
        """Tests :func:`hkshell.p`."""

        self.init_hkshell()
        p0 = self.p(0)

        # hkshell.heap_id_hint_var == None

        hkshell.set_heap_id_hint(None)
        self.assertEquals(hkshell.p('my_heap/0'), p0)
        self.assertEquals(hkshell.p(('my_heap', '0')), p0)
        self.assertRaises(hklib.PostNotFoundError, lambda: hkshell.p(0))

        # hkshell.heap_id_hint_var can be used

        hkshell.set_heap_id_hint('my_heap')
        self.assertEquals(hkshell.p('my_heap/0'), p0)
        self.assertEquals(hkshell.p(0), p0)

        hkshell.set_heap_id_hint('my_other_heap')
        self.assertEquals(hkshell.p('my_heap/0'), p0)
        self.assertEquals(hkshell.p(0), self.po(0))

        # hkshell.heap_id_hint_var is not None, but cannot be used

        hkshell.set_heap_id_hint('my_other_heap')
        self.assertRaises(hklib.PostNotFoundError, lambda: hkshell.p(1))

    def test_ls(self):
        """Tests :func:`hkshell.ls`."""

        class MyOutput():
            @staticmethod
            def write(str):
                output_list.append(str)
        self.init_hkshell()
        output = MyOutput()
        hkshell.options.output = output

        hklib.localtime_fun = time.gmtime

        # ls with default parameters
        output_list = []
        hkshell.ls()
        self.assertEquals(
            output_list,
            ['<my_heap/0> subject0  author0 (2008.08.20. 15:41)\n',
             '  <my_heap/1> subject1  author1 (2008.08.20. 15:41)\n',
             '    <my_heap/2> subject2  author2 (2008.08.20. 15:41)\n',
             '  <my_heap/3> subject3  author3 (2008.08.20. 15:41)\n',
             '<my_other_heap/0> subject0  author0 (2008.08.20. 15:41)\n',
             '<my_heap/4> subject4  author4 (2008.08.20. 15:41)\n'])

        # ls with given parameters
        hkshell.aTr('my_heap/1',['mytag1','mytag2'])
        output_list = []
        hkshell.ls(hkshell.ps([1,2,4]),
                   show_author=False, show_tags=True,
                   show_date=False, indent=4)
        self.assertEquals(
            output_list,
            ['    <my_heap/1> subject1  [mytag1,mytag2]\n',
             '        <my_heap/2> subject2  [mytag1,mytag2]\n',
             '<my_heap/4> subject4  []\n'])

    def test_enew(self):
        self.init_hkshell()

        # If we edit the file, a new post is created.
        hkshell.options.callbacks.edit_files = \
            lambda files: set(files) # As if everything were edited
        post = hkshell.enew()
        self.assert_(
            hkshell.modification_listener.touched_posts().is_set([post]))
        self.assertEquals(self.pop_log(), 'Post created.')

        # If we don't edit it, no new post is created.
        hkshell.options.callbacks.edit_files = \
            lambda files: set() # As if nothing were edited
        post = hkshell.enew()
        self.assertEquals(self.pop_log(), 'No change in the data base.')
        self.assertEquals(post, None)
        self.assert_(hkshell.modification_listener.touched_posts().is_set([]))

        def check_content(expected_content):
            """Returns an editor which (instead of editing the file) checks
            that the real content of the file is the same as the expected
            content."""
            def editor(files):
                [file] = files
                real_content = hkutils.file_to_string(file)
                self.assertEquals(expected_content, real_content)
                return [file]
            return editor

        # Calling enew with default arguments
        hkshell.options.callbacks.edit_files = \
            check_content('Author: \nSubject: \n\n\n')
        post = hkshell.enew()
        self.assertEquals(self.pop_log(), 'Post created.')

        # Testing the `author` argument
        hkshell.options.callbacks.edit_files = \
            check_content('Author: author\nSubject: \n\n\n')
        post = hkshell.enew(author='author')
        self.assertEquals(self.pop_log(), 'Post created.')

        # Testing the `parent` argument
        parent = self.p(0)
        parent.set_subject('subject0')
        parent.add_tag('tag1')
        parent.add_tag('tag2')
        hkshell.options.callbacks.edit_files = \
            check_content(
                'Author: \nSubject: subject0\n'
                'Tag: tag1\nTag: tag2\nParent: my_heap/0\n\n\n')
        post = hkshell.enew(parent=self.p(0))
        self.assertEquals(self.pop_log(), 'Post created.')

        # Testing the `prefix` argument
        hkshell.options.callbacks.edit_files = lambda files: set(files)
        post = hkshell.enew(prefix='myprefix')
        self.assert_(post.post_index().startswith('myprefix'))
        self.assertEquals(self.pop_log(), 'Post created.')

    def test_pT__1(self):
        self.init_hkshell()
        hkshell.aT(1, 't')
        self.assertEquals(self.tags(), [[],['t'],[],[],[]])
        hkshell.pT(1)
        self.assertEquals(self.tags(), [[],['t'],['t'],[],[]])

    def test_pT__2(self):
        self.init_hkshell()
        hkshell.aT(0, 't1')
        hkshell.aT(1, 't2')
        hkshell.pT(0)
        self.assertEquals(self.tags(), [['t1'],['t1','t2'],['t1'],['t1'],[]])

    def test_pT__3(self):
        self.init_hkshell()
        hkshell.aT(0, 't1')
        hkshell.aT(0, 't2')
        hkshell.pT(0)
        t = ['t1', 't2']
        self.assertEquals(self.tags(), [t, t, t, t, []])

    def test_aT(self):
        self.init_hkshell()
        hkshell.aT(1, 't')
        self.assertEquals(self.tags(), [[],['t'],[],[],[]])
        hkshell.aT(1, ['t', 'u'])
        self.assertEquals(self.tags(), [[],['t','u'],[],[],[]])

    def test_aTr(self):
        self.init_hkshell()
        hkshell.aTr(1, 't')
        self.assertEquals(self.tags(), [[],['t'],['t'],[],[]])
        hkshell.aTr(1, ['t', 'u'])
        self.assertEquals(self.tags(), [[],['t','u'],['t','u'],[],[]])

    def test_rT_AND_rTr(self):
        self.init_hkshell()
        hkshell.aTr(0, ['t', 'u'])
        self.ae(self.tags(), [['t','u'],['t','u'],['t','u'],['t','u'],[]])
        hkshell.rT(1, ['t'])
        self.ae(self.tags(), [['t','u'],['u'],['t','u'],['t','u'],[]])
        hkshell.rTr(1, ['u'])
        self.ae(self.tags(), [['t','u'],[],['t'],['t','u'],[]])

    def test_sT_AND_sTr(self):
        self.init_hkshell()
        hkshell.aTr(0, ['t', 'u'])
        self.ae(self.tags(), [['t','u'],['t','u'],['t','u'],['t','u'],[]])
        hkshell.sT(1, ['x', 'y'])
        self.ae(self.tags(), [['t','u'],['x','y'],['t','u'],['t','u'],[]])
        hkshell.sTr(1, 'z')
        self.ae(self.tags(), [['t','u'],['z'],['z'],['t','u'],[]])

    def test_sS_AND_pS(self):
        self.init_hkshell()
        self.clear_subjects()
        hkshell.sS(1, 's')
        self.assertEquals(self.subjects(), ['','s','','',''])
        hkshell.pS(1)
        self.assertEquals(self.subjects(), ['','s','s','',''])

    def test_sSr(self):
        self.init_hkshell()
        self.clear_subjects()
        hkshell.sSr(1, 's')
        self.assertEquals(self.subjects(), ['','s','s','',''])

    def test_cS_AND_cSr(self):
        self.init_hkshell()
        self.clear_subjects()
        hkshell.sSr(0, 'su')
        self.assertEquals(self.subjects(), ['su','su','su','su',''])
        hkshell.cS(2)
        self.assertEquals(self.subjects(), ['su','su','Su','su',''])
        hkshell.cSr(0)
        self.assertEquals(self.subjects(), ['Su','Su','Su','Su',''])

if __name__ == '__main__':
    hklib.set_log(False)
    unittest.main()
