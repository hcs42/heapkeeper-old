# -*- coding: utf-8 -*-

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

"""Module for issue tracking with Heapkeeper.

If you want to use it, the simplest way is to append its invocation to your
`gen_indices` function in your hkrc::

    import hkshell
    import hkcustomlib

    def gen_indices(postdb):

        # Default index.html:
        hkcustomlib.gen_indices(postdb)

        # Own index pages
        # ...

        # Issue tracker
        genopts = hklib.GeneratorOptions()
        genopts.postdb = postdb
        generator = issue_tracker.create_generator(genopts)
        generator.gen_indices(genopts)

    hkshell.options.callbacks.gen_indices = gen_indices
"""


import datetime
import itertools
import os
import re
import subprocess
import time

import hkutils
import hklib
import hkcustomlib
import hkgen
import hkshell


##### Utilities #####

def has_tag(tags):
    def has_tag_fun(post):
        for tag in tags:
            if post.has_tag(tag):
                return True
        return False
    return has_tag_fun

def ct(tagset, sign):
    return set([ sign + tag for tag in tagset])

def tag_in_body(post, tag):
    return re.search(r'^\[%s\]$' % (tag,), post.body(), re.MULTILINE)

def red(s):
    return hklib.Html.enclose('important', s)

def mod_set(tagset):
    def capitalize(tag):
        if tag in tagset:
            tagset.remove(tag)
            tagset.add(red(tag.upper()))
    capitalize('prop')
    capitalize('issue')
    capitalize('bug')

##### Index page generation #####

class Generator(hkgen.Generator):

    def __init__(self, postdb):
        super(Generator, self).__init__(postdb)
        self.options.html_title = 'Heapkeeper issue tracker'
        self.options.html_h1 = 'Heapkeeper issue tracker'
        self.options.cssfiles = ['heapindex.css', 'issues.css']

    def print_postitem_tags(self, postitem):
        post = postitem.post
        parent = self._postdb.parent(post)
        post_tags = set(post.tags())
        mod_set(post_tags)
        if parent is None:
            tags = post_tags
        else:
            parent_tags = set(parent.tags())
            mod_set(parent_tags)
            tags = \
                set([ '-' + tag for tag in parent_tags - post_tags]).union( \
                set([ '+' + tag for tag in post_tags - parent_tags]))

        if tag_in_body(post, 'close'):
            tags.add(red('CLOSE'))
        if tag_in_body(post, 'open'):
            tags.add(red('OPEN'))
        if len(tags) == 0:
            return ''
        else:
            return '[%s]' % (', '.join(tags),)

    def is_thread_issue(self, root):
        for post in self._postdb.postset(root).expf():
            if (post.has_tag('hh') and
                not post.has_tag('post syntax') and
                (post.has_tag('prop') or post.has_tag('issue') or
                 post.has_tag('bug'))):
                return True
        return False

    def is_post_wanted(self, post):
        return (post.has_tag('hh') and not post.has_tag('post syntax'))

    def is_review_needed(self, post):
        return not post.has_tag('reviewed')

    def is_thread_open(self, root):
        openness = 0
        if (root.has_tag('prop') or root.has_tag('issue') or
            root.has_tag('bug')):
            openness += 1
        for post in self._postdb.postset(root).expf():
            if tag_in_body(post, 'open'):
                openness += 1
            elif tag_in_body(post, 'close'):
                openness -= 1
        return openness > 0

    def calc(self):

        # These are the threads and posts that are interesting for us
        postdb = self._postdb
        roots = postdb.postset(postdb.roots())
        issue_threads = roots.collect(self.is_thread_issue)
        issue_posts = issue_threads.expf().collect(self.is_post_wanted)

        open_threads = issue_threads.collect(self.is_thread_open)
        open_posts = open_threads.expf() & issue_posts

        review_needed_posts = issue_posts.collect(self.is_review_needed)
        review_needed_threads = review_needed_posts.expb().collect.is_root()

        all_section = issue_posts
        open_section = open_posts
        review_needed_section = \
            review_needed_posts.exp() & issue_posts - open_posts
        closed_section = issue_posts - open_section - review_needed_section

        self.issue_threads = issue_threads
        self.issue_posts = issue_posts
        self.all_section = all_section
        self.open_threads = open_threads
        self.open_posts = open_posts
        self.open_section = open_section
        self.review_needed_posts = review_needed_posts
        self.review_needed_threads = review_needed_threads
        self.review_needed_section = review_needed_section
        self.closed_section = closed_section

    def enclose_issue_posts(self, posts):
        """Walks the given post set and encloses the issue posts that posts
        that need review/are open into ``'review_needed'`` and ``'open-issue'``
        spans.

        **Argument:**

        - `posts` (|PostSet|) -- The posts that should be enclosed.

        **Returns:** iterable(|PostItem|)
        """

        # Get the post items for the expanded post set
        xpostitems = self.walk_exp_posts(posts)

        # We add 'review-needed' spans around the posts that need review
        xpostitems = itertools.imap(
                        self.enclose_posts(
                            'review-needed-post',
                            self.review_needed_posts),
                        xpostitems)

        # We add 'review-needed' spans around the threads that need review
        xpostitems = itertools.imap(
                         self.enclose_threads(
                            'review-needed-thread',
                            self.review_needed_threads),
                         xpostitems)

        # We add 'open' spans around the threads that are open
        xpostitems = itertools.imap(
                         self.enclose_threads(
                            'open-issue',
                            self.open_threads),
                         xpostitems)

        return self.print_postitems(xpostitems)

    def print_issues_all_page(self):

        return \
            self.section(
                'all',
                'All issues',
                self.enclose_issue_posts(self.all_section))

    def print_issues_sorted_page(self):
        return \
            (self.section(
                'open',
                'Open issues',
                self.enclose_issue_posts(self.open_section)),
             self.section(
                'review_needed',
                'Closed, but review needed',
                self.enclose_issue_posts(self.review_needed_section)),
             self.section(
                'closed',
                'Closed issues',
                self.enclose_issue_posts(self.closed_section)))

    def write_issues_all_page(self):
        # Call self.calc before you call this function

        hklib.log('Generating issues_all.html...')
        self.options.html_title = 'All issues'
        self.write_page(
            'issues_all.html',
            self.print_issues_all_page())

    def write_issues_sorted_page(self):
        # Call self.calc before you call this function

        hklib.log('Generating issues_sorted.html...')
        self.options.html_title = 'Sorted issues'
        self.write_page(
             'issues_sorted.html',
             self.print_issues_sorted_page())

    def write_all(self):
        self.calc()
        self.write_issues_all_page()
        self.write_issues_sorted_page()

##### hkshell commands #####

@hkshell.hkshell_cmd(postset_operation=True, touching_command=True)
def cl(posts):
    def add_close(post):
        post.set_body('[close]\n\n' + post.body())
    posts.forall(add_close)

@hkshell.hkshell_cmd(postset_operation=True, touching_command=True)
def op(posts):
    def add_open(post):
        post.set_body('[open]\n\n' + post.body())
    posts.forall(add_open)
