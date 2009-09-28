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

import os
import subprocess
import time
import datetime
import re

import hkutils
import hklib
import hkcustomlib
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
    capitalize('bug')

def is_open(root):
    postdb = root._postdb
    openness = 0
    if root.has_tag('prop'):
        openness += 1
    for post in postdb.postset(root).expf():
        if tag_in_body(post, 'open'):
            openness += 1
        elif tag_in_body(post, 'close'):
            openness -= 1
    return openness > 0

##### Index page generation #####

class IssueTrackerGenerator(hklib.Generator):

    def __init__(self, postdb):
        super(IssueTrackerGenerator, self).__init__(postdb)
        self.open_issues = set()

    def postitem_begin(self, postitem, options):
        result = hklib.Generator.postitem_begin(self, postitem, options)
        post = postitem.post
        parent = self._postdb.parent(post)
        if parent == None and post in self.open_issues:
            result = '<span class="open-issue">' + result
        if post in self.review_needed:
            result = '<span class="review-needed">' + result
        return result

    def postitem_end(self, postitem, options):
        result = hklib.Generator.postitem_end(self, postitem, options)
        post = postitem.post
        parent = self._postdb.parent(post)
        if post in self.review_needed:
            result += '</span><!-- for "review-needed" -->\n'
        if parent == None and post in self.open_issues:
            result += '</span><!-- for "open-issue" -->\n'
        return result

    def postitem_tags(self, postitem, options):
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

def indices(postdb):

    # posts that need review

    ps_review_needed = \
        (postdb.all().
         collect(lambda p: not p.has_tag('reviewed')).
         exp().
         collect.is_root())

    # issues

    def is_issue(root):
        for post in postdb.postset(root).expf():
            if post.has_tag('prop') or post.has_tag('open'):
                return True
        return False

    ps_issues = postdb.postset(postdb.roots()).collect(is_issue)
    ps_open_issues = ps_issues.collect(is_open)
    ps_review_needed_issues = ps_issues & ps_review_needed - ps_open_issues
    ps_closed_issues = ps_issues - ps_open_issues - ps_review_needed_issues

    ps_hh = postdb.all().collect.has_tag('hh')
    ps_post_syntax = postdb.all().collect.has_tag('post syntax')

    # non-hh posts and post syntax posts are both unwanted
    ps_unwanted = (postdb.all() - ps_hh) | ps_post_syntax

    ps_open_issues = ps_open_issues.expf() - ps_unwanted
    ps_review_needed_issues = ps_review_needed_issues.expf() - ps_unwanted
    ps_closed_issues = ps_closed_issues.expf() - ps_unwanted

    ps_wanted = ps_open_issues | ps_review_needed_issues | ps_closed_issues

    # indices

    index_issues = hklib.Index(filename='issues_all.html')
    index_issues.sections = \
        [ hklib.Section("All issues", ps_wanted)]

    index_issues2 = hklib.Index(filename='issues_sorted.html')
    index_issues2.sections = \
        [hklib.Section("Open issues", ps_open_issues),
         hklib.Section("Closed, but review needed", ps_review_needed_issues),
         hklib.Section("Closed issues", ps_closed_issues)]

    return [index_issues, index_issues2], ps_open_issues, ps_review_needed

def create_generator(genopts):
    indices_, open_issues, review_needed = indices(genopts.postdb)
    genopts.indices = indices_
    genopts.html_title = 'Heapkeeper issue tracker'
    genopts.html_h1 = 'Heapkeeper issue tracker'
    genopts.cssfiles = ['heapindex.css', 'issues.css']
    generator = IssueTrackerGenerator(genopts.postdb)
    generator.open_issues = open_issues
    generator.review_needed = review_needed
    return generator

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
