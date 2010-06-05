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

# Copyright (C) 2009-2010 Csaba Hoch
# Copyright (C) 2009 Attila Nagy

"""My (Csaba Hoch) hkrc."""


import datetime
import itertools

import hkutils
import hkgen
import hkshell
import hk_issue_tracker


class MyGenerator(hkgen.Generator):

    def __init__(self, postdb):
        """Constructor.

        **Arguments:**

        - `postdb` (|PostDB|)
        """

        super(MyGenerator, self).__init__(postdb)
        self.options.shortsubject = True
        self.options.shorttags = True
        self.options.cssfiles.append('../static/css/issues.css')
        self.options.files_to_copy.append('static/css/issues.css')

    def calc(self):

        postdb = self._postdb
        all = postdb.all()
        def is_hh_post(post):
            return post.heap_id() == 'hh' or post.has_tag('hh')
        self.hh_posts = all.collect(is_hh_post)
        self.ums_posts = all - self.hh_posts
        self.review_needed_posts = all.collect(self.is_review_needed)
        self.review_needed_threads = \
            self.review_needed_posts.expb().collect.is_root()

    def is_review_needed(self, post):
        return not post.has_tag('reviewed')

    def print_main_index_page(self):
        """Prints the main index page.

        **Returns:** |HtmlText|
        """

        normal_postitems = self.walk_thread(None)
        normal_postitems = self.reverse_threads(normal_postitems)

        if self._postdb.has_cycle():
            cycle_postitems = self.walk_postitems(self._postdb.walk_cycles())
            return (
                self.section(
                    '0', 'Posts in cycles',
                    self.print_postitems(cycle_postitems),
                    flat=True),
                self.section(
                    '1', 'Other posts',
                    self.print_postitems(normal_postitems)))
        else:
            return self.print_postitems(normal_postitems)

    def print_html_head_content(self):
        return (hkgen.Generator.print_html_head_content(self),
                '    <link rel="shortcut icon" href="%s">\n' % (self._favicon))

    def enclose_my_posts_core(self, xpostitems):

        # Get the post items for the expanded post set
        xpostitems = self.walk_exp_posts(xpostitems)

        # Reverse the post items
        xpostitems = self.reverse_threads(xpostitems)

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

        return xpostitems

    def print_stat(self, posts):
        return (
            'Number of posts: ', str(len(posts)),
        )

    def print_ums_page(self):
        xpostitems = self.enclose_my_posts_core(self.ums_posts)
        return (self.print_stat(self.ums_posts),
                self.print_postitems(xpostitems))

    def print_hh_page(self):
        xpostitems = self.enclose_my_posts_core(self.hh_posts)
        return (self.print_stat(self.hh_posts),
                self.print_postitems(xpostitems))

    def write_my_pages(self):
        # Call self.calc before you call this function

        hkutils.log('Generating ums.html...')
        self.options.html_title = 'UMS heap'
        self._favicon = "http://hcs42.github.com/favicons/ums.png"
        self.write_page(
            'index/ums.html',
            self.print_ums_page())

        hkutils.log('Generating hh.html...')
        self.options.html_title = 'Heapkeeper heap'
        self._favicon = "http://hcs42.github.com/favicons/hh.png"
        self.write_page(
            'index/hh.html',
            self.print_hh_page())

    def write_all(self):
        """Writes the main index page, the thread pages and the post pages."""

        self._favicon = "http://hcs42.github.com/favicons/heap.png"
        self.write_main_index_page()
        self.write_thread_pages()
        self.write_my_pages()


class MyIssueTrackerGenerator(hk_issue_tracker.Generator):

    def __init__(self, postdb):
        """Constructor.

        **Arguments:**

        - `postdb` (|PostDB|)
        """

        super(MyIssueTrackerGenerator, self).__init__(postdb)

        # My CSS files that modifies the stuff in the default issues.css file.
        # It is located in my HTML directory.
        self.options.cssfiles.append('../issues_hcs.css')

    def print_html_head_content(self):
        return (hkgen.Generator.print_html_head_content(self),
                '    <link rel="shortcut icon" href='
                '"http://hcs42.github.com/favicons/it.png"> ')

    def is_thread_open_idea(self, root):
        return root.has_tag('idea')

    def calc(self):
        hk_issue_tracker.Generator.calc(self)
        open_idea_threads = \
            self.issue_threads.collect(self.is_thread_open_idea)
        self.open_idea_threads = open_idea_threads

    def enclose_issue_posts_core(self, posts):
        xpostitems = \
            hk_issue_tracker.Generator.enclose_issue_posts_core(self, posts)

        # We add 'open' spans around the threads that are open
        xpostitems = itertools.imap(
                         self.enclose_threads(
                            'open-idea',
                            self.open_idea_threads),
                         xpostitems)
        return xpostitems


class MyTestGenerator(MyGenerator):

    def __init__(self, postdb):
        """Constructor.

        **Arguments:**

        - `postdb` (|PostDB|)
        """

        super(MyTestGenerator, self).__init__(postdb)

    def should_print_date(self, postitem):
        """Returns ``True`` if the post is flat, has no parent, or its parent
        it more than 3 days older than itself.

        **Arguments:**

        - `postitem` (|PostItem|)

        **Returns:** bool
        """

        post = postitem.post
        parent = self._postdb.parent(post)
        min_diff = datetime.timedelta(days=3)
        if postitem.pos == 'flat' or parent == None:
            return True
        if (post.date() != '' and parent.date() != '' and
            (post.datetime() - parent.datetime() >= min_diff)):
            return True
        return False

    def print_postitem_date(self, postitem):
        """Prints the date of the post item.

        It uses :func:`should_print_date` to decide whether or not the date
        should be printed.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        timestamp = postitem.post.timestamp()
        if timestamp != 0 and self.should_print_date(postitem):
            return hkgen.Generator.format_timestamp(self, timestamp)
        else:
            return ''


def gen_indices(postdb):
    g = MyIssueTrackerGenerator(postdb)
    g.write_all()
    g = MyGenerator(postdb)
    g.calc()
    g.write_all()

def gen_indices_fast(postdb):
    g = MyIssueTrackerGenerator(postdb)
    g.calc()
    g.write_issues_sorted_page()
    g = MyGenerator(postdb)
    g.write_thread_pages()

hkshell.options.callbacks.gen_indices = gen_indices

@hkshell.hkshell_cmd()
def check_heap_links():
    """Checks that the heap links in post bodies are not broken.

    A few posts are ignored because they only discuss using "heap://" and not
    actually use it.

    **Returns:** |PostSet| -- The set of posts that contain broken link.
    """

    postdb = hkshell.postdb()

    # These posts contain the "heap://" text, but they are OK.
    ignored_posts = [
        '<499FFF71.6060401@gmail.com>',
        '<b29f917d0905230006sac1db4j1aca2a5398cdef6f@mail.gmail.com>',
        '<49B112C3.8050503@gmail.com>',
        '<b29f917d0903060004l71f863c1nbd59ae6da3ef9ab6@mail.gmail.com>',
        '<4A179AE7.5040208@gmail.com>',
        '<49B28509.4000900@gmail.com>',
        '<48F84B73.1090705@gmail.com>',
        '<20100211110220.60214472.nagy.attila.1984@gmail.com>',
        '<4B767962.2080005@gmail.com>',
        '<20090518011928.99444ebf.nagy.attila.1984@gmail.com>',
        '<b29f917d0903020558sd17004dv4dd8da731ddb6ee5@mail.gmail.com>',
        '<4AF7022B.5000301@gmail.com>',
    ]
    ignored_posts = postdb.postset(ignored_posts)

    broken_posts = postdb.postset([])
    for post in postdb.all().sorted_list():
        for segment in post.body_object().segments:
            if segment.type == 'heap_link':
                target_pre = segment.get_prepost_id_str()
                target_post = postdb.post(target_pre, post.heap_id())
                if (target_post is None) and (post not in ignored_posts):
                    broken_posts.add(post)
                    s = 'Broken link in %s to "%s"' % (post, target_pre)
                    hkshell.options.output.write(s + '\n')
    return broken_posts

@hkshell.hkshell_cmd()
def posts_without_date():

    postdb = hkshell.postdb()
    def has_no_date(post):
        return post.date() == ''
    posts = postdb.all().collect(has_no_date)
    for post in posts:
        old_post_id = post.post_id()
        print post, postdb.parent(post)
        post.set_date(postdb.parent(post).date())
    hkshell.s()

@hkshell.hkshell_cmd()
def separate_heaps():

    postdb = hkshell.postdb()
    all = postdb.all()
    def is_hh_post(post):
        return post.heap_id() == 'hh' or post.has_tag('hh')

    hh_posts = all.collect(is_hh_post)
    ums_posts = all - hh_posts

    for i, post in enumerate(hh_posts.sorted_list()):
        postdb.move(post, ('hh', i + 1), placeholder=True)
        post.remove_tag('hh')
        if post.author() == 'Csabi':
            post.set_author('Csaba Hoch')
        elif post.author() == 'Attis':
            post.set_author('Attila Nagy')
        else:
            print 'Unknown author:', post.author()

@hkshell.hkshell_cmd()
def R(pps):
    """Mark thread as reviewed."""
    hkshell.aTr(pps, 'reviewed')

def main():
    hkshell.options.callbacks.gen_indices = gen_indices
    hkshell.options.save_on_ctrl_d = False
    hkshell.on('tpp')
    hkshell.on('s')
    hkshell.on('gi')

main()
