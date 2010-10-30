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

This plugin serves an issue tracker based on a heap.

Example usage:

    >>> import hkp_issue_tracker
    >>> hkp_issue_tracker.start('myheap')

Afterwards an issue tracker page based on the 'myheap' heap will be displayed
at <hostname>:<port>/myheap-issue-tracker.
"""


import hklib
import hkutils
import hksearch
import hkweb
import hk_issue_tracker


class IssueTrackerGenerator(hk_issue_tracker.Generator, hkweb.WebGenerator):
    """Generator that generates an issue tracker page based on the given
    heap."""

    def __init__(self, postdb, heap_id):
        # "hk_issue_tracker.Generator.__init__" is not called
        # pylint: disable=W0231
        hkweb.WebGenerator.__init__(self, postdb)
        self._heap_id = heap_id
        static_dir = 'plugins/issue_tracker/static'
        self.options.cssfiles.append(static_dir + '/css/issues.css')
        self.options.favicon = static_dir + '/images/it.png'

    def section(self, id, title, content, flat=False):
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

    def enclose_issue_posts_core(self, posts):
        """Walks the given post set and encloses the issue posts.

        **Argument:**

        - `posts` (|PostSet|) -- The posts that should be enclosed.

        **Returns:** iterable(|PostItem|)
        """

        return \
           self.reverse_threads(
               [hklib.PostItem(pos='flat', post=post)
                for post in posts.collect.is_root().sorted_list()])

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

    def print_postitem_open(self, postitem):
        open_msg = 'OPEN' if self.is_thread_open(postitem.post) else ''
        return self.enclose(
                   open_msg,
                   class_='open',
                   skip_empty=True)

    def print_postitem_type(self, postitem):
        return self.enclose(
                   self.print_postitem_type_core(postitem),
                   class_='type',
                   skip_empty=True)

    def print_postitem_tags(self, postitem):
        return self.enclose(
                   self.print_postitem_tags_core(postitem),
                   class_='type',
                   skip_empty=True)

    def print_postitem_type_core(self, postitem):
        post = postitem.post
        post_tags = set(post.tags())
        type, _ = self.separate_type_and_tags(post_tags)

        if len(type) == 0:
            return ''
        else:
            return '[%s]' % (', '.join(type),)

    def print_postitem_tags_core(self, postitem):
        post = postitem.post
        post_tags = set(post.tags())
        _, tags = self.separate_type_and_tags(post_tags)

        if len(tags) == 0:
            return ''
        else:
            return '[%s]' % (', '.join(tags),)

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

    def get_thread_meta(self, root, meta):
        values = []
        thread = hklib.PostSet(self._postdb, root).expf()
        for p in thread:
            meta_dict = p.meta_dict()
            if meta_dict.has_key(meta):
                values.append(meta_dict[meta])
        return values

    def print_issues_page(self):
        return \
            (self.section(
                'open',
                'Open issues',
                self.enclose_issue_posts(self.open_section),
                flat=True))

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

    class CustomHeapServer(hkweb.HkPageServer):
        """Serves the index page that shows all posts."""

        def __init__(self):
            hkweb.HkPageServer.__init__(self)

        def GET(self):
            generator = IssueTrackerGenerator(self._postdb, heap_id)
            content = generator.print_main()
            return self.serve_html(content, generator)

    hkweb.insert_urls([url, CustomHeapServer])

    def issue_target(post, pattern):
        postdb = post._postdb
        root = postdb.root(post)
        gen = hk_issue_tracker.Generator(postdb)
        if pattern == 'issue':
            return gen.is_thread_issue(root)
        elif pattern == 'open':
            return gen.is_thread_open(root)
        else:
            return False

    hksearch.add_target_type('issue', issue_target)
