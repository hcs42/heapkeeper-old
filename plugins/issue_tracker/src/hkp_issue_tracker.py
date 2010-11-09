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

# Copyright (C) 2010 Csaba Hoch

""":mod:`hkp_issue_tracker` implements the "Issue Tracker" plugin for
Heapkeeper.

This plugin generates an issue tracker page based on a heap. It can be used to
generate static web pages as well as serving the issue tracking page through
the web interface (|hkweb|).

An example of starting the web server::

    >>> import hkp_issue_tracker
    >>> hkp_issue_tracker.start('myheap')

Afterwards an issue tracker page based on the 'myheap' heap will be displayed
at ``<hostname>:<port>/myheap-issue-tracker``.

An example of generating a static issue tracker page::

    >>> import hkp_issue_tracker
    >>> gen = hkp_issue_tracker.StaticITGenerator(postdb(), 'myheap')
    >>> gen.write_all()
    Generating issues.html...
    >>>

After calling the ``write_all`` function, the page will be written into the
``index/issues-myheap.html`` file.
"""


import itertools

import hklib
import hkutils
import hksearch
import hkweb
import hkgen


##### Base issue tracker generator #####

class BaseITGenerator(hkgen.BaseGenerator):

    # Initialization

    def __init__(self, postdb, heap_id):
        hkgen.BaseGenerator.__init__(postdb)
        BaseITGenerator.init(self, heap_id)

    def init(self, heap_id):
        self._heap_id = heap_id
        self.options.html_title = 'Heapkeeper issue tracker'
        self.options.html_h1 = 'Heapkeeper issue tracker'
        self.options.cssfiles.append('../static/css/issues.css')
        self.options.files_to_copy.append('static/css/issues.css')
        self.options.flat_issues = True

    # Calculations about issues

    def is_hh_post(self, post):
        return post.heap_id() == 'hh' or post.has_tag('hh')

    def is_thread_issue(self, root):
        for post in self._postdb.postset(root).expf():
            if (self.is_hh_post(post) and
                not post.has_tag('post syntax') and
                (post.has_tag('prop') or post.has_tag('issue') or
                 post.has_tag('bug') or post.has_tag('feature'))):
                return True
        return False

    def is_post_wanted(self, post):
        return (self.is_hh_post(post) and not post.has_tag('post syntax') and
                not post.has_tag('meta'))

    def is_review_needed(self, post):
        return not post.has_tag('reviewed')

    def is_thread_open(self, root):
        openness = 0
        if (root.has_tag('prop') or root.has_tag('issue') or
            root.has_tag('bug') or root.has_tag('feature')):
            openness += 1
        for post in self._postdb.postset(root).expf():
            if 'open' in post.meta_dict():
                openness += 1
            elif 'close' in post.meta_dict():
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

    # Printing the issues

    # ONLY NONFLAT
    def red(self, s):
        return hkutils.textstruct_to_str(self.enclose(s, class_='important'))

    # ONLY NONFLAT
    def mod_set(self, tagset):
        def capitalize(tag):
            if tag in tagset:
                tagset.remove(tag)
                tagset.add(self.red(tag.upper()))
        capitalize('prop')
        capitalize('issue')
        capitalize('feature')
        capitalize('bug')

    # ONLY NONFLAT
    def print_postitem_tags_core_NONFLAT(self, postitem):
        post = postitem.post
        parent = self._postdb.parent(post)
        post_tags = set(post.tags())
        self.mod_set(post_tags)
        if parent is None or postitem.pos == 'flat':
            tags = post_tags
        else:
            parent_tags = set(parent.tags())
            self.mod_set(parent_tags)
            tags = \
                set([ '-' + tag for tag in parent_tags - post_tags]).union( \
                set([ '+' + tag for tag in post_tags - parent_tags]))

        if 'close' in post.meta_dict():
            tags.add(self.red('CLOSE'))
        if 'open' in post.meta_dict():
            tags.add(self.red('OPEN'))
        if len(tags) == 0:
            return ''
        else:
            return '[%s]' % (', '.join(tags),)

    # ONLY NONFLAT
    def print_postitem_meta_info_core(self, postitem):
        """Prints issue-related meta information about the post.

        If the post contains meta information about the effort, version,
        priority and assignment of the issue, those are printed.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        meta_dict = postitem.post.meta_dict()
        items = []

        def item(key, prefix=''):
            """Creates an |HtmlStr| about the given meta information found in
            `meta_dict` and appends it to `items`.

            **Arguments:**

            - `key` (str) -- The key by which the meta information is stored in
              `meta_dict`.
            - `prefix` (str) -- The prefix to be prepended before the meta
              information.
            """

            value = meta_dict.get(key)
            if value is not None:
                html_text = (prefix, self.escape(value))
                html_text = self.enclose(html_text, class_=key, title=key)
                items.append(html_text)

        item('effort')
        item('version', prefix='v')
        item('priority')
        item('assign')
        return hkutils.insert_sep(items, ', ')

    # ONLY NONFLAT
    def print_postitem_meta_info(self, postitem):
        return self.enclose(
                   self.print_postitem_meta_info_core(postitem),
                   class_='meta-info',
                   skip_empty=True)

    # ONLY NONFLAT
    def get_postsummary_fields_inner(self, postitem):
        return (
            self.print_postitem_author,
            self.print_postitem_subject,
            self.print_postitem_threadlink,
            self.print_postitem_tags,
            self.print_postitem_post_id,
            self.print_postitem_parent_post_id,
            self.print_postitem_date,
            self.print_postitem_meta_info,
        )

    # ONLY FLAT
    def separate_type_and_tags(self, tagset):
        """Separates tags describing type and topic.

        **Argument:**

        - `tagset` ([str])

        **Returns:** ((str), (str))
        """

        type = []

        def separate(tag):
            if tag in tagset:
                tagset.remove(tag)
                type.append(tag)
        def eliminate(tag):
            if tag in tagset:
                tagset.remove(tag)
        for tag in ('prop', 'issue', 'feature', 'bug'):
            separate(tag)
        for tag in ('reviewed', 'open', 'OPEN', 'closed', 'CLOSED'):
            eliminate(tag)
        return (type, tagset)

    # ONLY FLAT
    def print_postitem_open(self, postitem):
        open_msg = 'OPEN' if self.is_thread_open(postitem.post) else ''
        return self.enclose(
                   open_msg,
                   class_='open',
                   skip_empty=True)

    # ONLY FLAT
    def print_postitem_type_core(self, postitem):
        post = postitem.post
        post_tags = set(post.tags())
        type, _ = self.separate_type_and_tags(post_tags)

        if len(type) == 0:
            return ''
        else:
            return '[%s]' % (', '.join(type),)

    # ONLY FLAT
    def print_postitem_type(self, postitem):
        return self.enclose(
                   self.print_postitem_type_core(postitem),
                   class_='type',
                   skip_empty=True)

    # ONLY FLAT
    def print_postitem_tags_core(self, postitem):
        post = postitem.post
        post_tags = set(post.tags())
        _, tags = self.separate_type_and_tags(post_tags)

        if len(tags) == 0:
            return ''
        else:
            return '[%s]' % (', '.join(tags),)

    # ONLY FLAT
    def print_postitem_tags(self, postitem):
        return self.enclose(
                   self.print_postitem_tags_core(postitem),
                   class_='type',
                   skip_empty=True)

    # ONLY FLAT
    def get_thread_meta(self, root, meta):
        values = []
        thread = hklib.PostSet(self._postdb, root).expf()
        for p in thread:
            meta_dict = p.meta_dict()
            if meta_dict.has_key(meta):
                values.append(meta_dict[meta])
        return values

    # ONLY FLAT
    def make_print_postitem_for_meta(self, meta):
        """This is a factory that manufactures a function to get the union
        of values for a given meta in a thread."""

        def print_postitem_meta(postitem):
            values = self.get_thread_meta(postitem.post, meta)
            return self.enclose(
                       ', '.join(values),
                       class_=meta,
                       skip_empty=True)
        return print_postitem_meta

    # ONLY FLAT
    def get_postsummary_fields_flat(self, postitem):

        def make_enclosed(fun, *args, **kwargs):
            def enclosed(postitem):
                res = fun(postitem)
                return self.enclose(res, *args, **kwargs)
            return enclosed

        fields = (
            self.print_postitem_open,
            self.print_postitem_subject,
            self.print_postitem_type,
            self.print_postitem_tags,
            self.print_postitem_post_id,
            self.make_print_postitem_for_meta('priority'),
            self.make_print_postitem_for_meta('assign'),
            self.make_print_postitem_for_meta('effort'),
            self.print_postitem_date,
        )
        return [make_enclosed(field, 'div', class_='field_%d' % (n,))
                for n, field in enumerate(fields)]

    # ONLY FLAT
    def enclose_issue_posts_core_flat(self, posts):
        """Walks the given post set and encloses the issue posts.

        **Argument:**

        - `posts` (|PostSet|) -- The posts that should be enclosed.

        **Returns:** iterable(|PostItem|)
        """

        return \
           self.reverse_threads(
               [hklib.PostItem(pos='flat', post=post)
                for post in posts.collect.is_root().sorted_list()])

    # ONLY NONFLAT
    def enclose_issue_posts_core_nonflat(self, posts):
        """Walks the given post set and encloses the issue posts that posts
        that need review/are open into ``'review_needed'`` and ``'open-issue'``
        spans.

        **Argument:**

        - `posts` (|PostSet|) -- The posts that should be enclosed.

        **Returns:** iterable(|PostItem|)
        """

        # Get the post items for the expanded post set
        xpostitems = self.walk_exp_posts(posts)

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

        # We add 'open' spans around the threads that are open
        xpostitems = itertools.imap(
                         self.enclose_threads(
                            'open-issue',
                            self.open_threads),
                         xpostitems)
        return xpostitems

    # BOTH
    def enclose_issue_posts_core(self, posts):
        """Walks the given post set and encloses the issue posts.

        **Argument:**

        - `posts` (|PostSet|) -- The posts that should be enclosed.

        **Returns:** iterable(|PostItem|)
        """

        if self.options.flat_issues:
            return self.enclose_issue_posts_core_flat(posts)
        else:
            return self.enclose_issue_posts_core_nonflat(posts)

    # BOTH FLAT AND NONFLAT
    def enclose_issue_posts(self, posts):
        xpostitems = self.enclose_issue_posts_core(posts)
        return self.print_postitems(xpostitems)

    # ONLY FLAT
    def print_issue_summary(self, id, title, content, flat=False):
        assert hkutils.is_textstruct(content), \
               'Parameter is not a valid text structure:\n%s\n' % (content,)

        if flat:
            raw_headers = ('State', 'Description', 'Type', 'Tags', 'ID',
                           'Priority', 'Assigned to', 'Manhour', 'Date')
            header = [self.enclose(h, 'th', id='th_%d' % (n,), newlines=True)
                      for n,h in enumerate(raw_headers)]
            content_theader = self.enclose(header,
                                           'theader',
                                           'flatlist',
                                           newlines=True)
            content_tbody = \
                self.enclose(content, 'tbody', 'flatlist', newlines=True)
            content_all = (content_theader, content_tbody)
            content = \
                self.enclose(content_all, 'table', 'flatlist', newlines=True)
        return (self.section_begin('section_%s' % (id,), title),
                content,
                self.section_end())

    # ONLY FLAT
    def print_issues_page_flat(self):
        return \
            (self.print_issue_summary(
                'open',
                'Open issues',
                self.enclose_issue_posts(self.open_section),
                flat=True))

    # ONLY FLAT
    def print_issues_page_nonflat(self):
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

    # BOTH
    def print_issues_page(self):
        if self.options.flat_issues:
            return self.print_issues_page_flat()
        else:
            return self.print_issues_page_nonflat()

##### Static issue tracker generator #####

class StaticITGenerator(BaseITGenerator, hkgen.StaticGenerator):
    """Generator that generates an issue tracker page based on the given
    heap."""

    def __init__(self, postdb, heap_id):
        # __init__ methods # pylint: disable=W0231,W0233
        hkgen.BaseGenerator.__init__(self, postdb)
        BaseITGenerator.init(self, heap_id)
        hkgen.StaticGenerator.init(self)
        StaticITGenerator.init(self)

    def init(self):
        # Argument count differs from overridden method # pylint: disable=W0221
        pass

    def write_all(self):
        self.calc()
        hkutils.log('Generating issues.html...')
        self.options.html_title = 'Sorted issues'
        filename = 'index/issues-%s.html' % (self._heap_id,)
        self.write_page(
            filename,
            self.print_issues_page())

##### Web issue tracker generator #####

class WebITGenerator(BaseITGenerator, hkweb.WebGenerator):
    """Generator that generates an issue tracker page based on the given
    heap."""

    def __init__(self, postdb, heap_id):
        # __init__ methods # pylint: disable=W0231,W0233
        hkgen.BaseGenerator.__init__(self, postdb)
        BaseITGenerator.init(self, heap_id)
        hkweb.WebGenerator.init(self)
        WebITGenerator.init(self)

    def init(self):
        # Argument count differs from overridden method # pylint: disable=W0221
        static_dir = 'plugins/issue_tracker/static'
        self.options.cssfiles.append(static_dir + '/css/issues.css')
        self.options.favicon = static_dir + '/images/it.png'

    def print_main(self):
        self.calc()
        return (self.print_searchbar(),
                self.print_issues_page())


def start(heap_id, url=None):
    """Modified the webserver to serve the given heap index page on the given
    URL.

    **Arguments:**

    - `heap_id` (|HeapId|)
    - `url` (str | ``None``) -- If ``None``, it will be ``"/" + heap_id``.
    """

    if url is None:
        url = '/' + heap_id + '-issue-tracker'

    def make_CustomHeapServer(flat_issues):

        class CustomHeapServer(hkweb.HkPageServer):
            """Serves the index page that shows all posts."""

            def __init__(self):
                hkweb.HkPageServer.__init__(self)

            def GET(self):
                generator = WebITGenerator(self._postdb, heap_id)
                generator.options.flat_issues = flat_issues
                content = generator.print_main()
                return self.serve_html(content, generator)

        return CustomHeapServer

    hkweb.insert_urls(
        [url, make_CustomHeapServer(flat_issues=True)])
    hkweb.insert_urls(
        [url + '-threaded', make_CustomHeapServer(flat_issues=False)])

    def issue_target(post, pattern):
        postdb = post._postdb
        root = postdb.root(post)
        gen = BaseITGenerator(postdb)
        if pattern == 'issue':
            return gen.is_thread_issue(root)
        elif pattern == 'open':
            return gen.is_thread_open(root)
        else:
            return False

    hksearch.add_target_type('issue', issue_target)
