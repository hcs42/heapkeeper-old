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

# All methods of this class are documented and tested except where explicitly
# noted.

"""|hkgen| generates HTML pages from posts.

Pseudo-types
''''''''''''

|hkgen| has pseudo-types that are not real Python types, but we use them as
types in the documentation so we can talk about them easily.

.. _hkgen_PostItemModifierFun:

- **PostItemModifierFun(postitem)** -- A function that modifies and returns a
  post item. Usually it modifies how the post item is printed.

  Real type: fun(|PostItem|) -> |PostItem|

.. _hkgen_PostItemPrinterFun:

- **PostItemPrinterFun(postitem)** -- A function that prints something based on
  a post item. (E.g. its author.)

  Real type: fun(|PostItem|) -> |HtmlText|
"""


from __future__ import with_statement

import datetime
import itertools
import os
import re
import shutil
import time

import hkutils
import hklib


class Generator(object):

    """A Generator object can generate various HTML strings and files from the
    post database.

    Currently it can generate three kinds of HTML files: index pages, thread
    pages and post pages, but can be modified so that it will generate other
    kind of pages.

    **Data attributes:**

    - `_postdb` (|PostDB|) -- The post database.
    - `options` (|GeneratorOptions|)

    **Used patterns:**

    - :ref:`creating_a_long_string_pattern`
    """

    def __init__(self, postdb):
        """Constructor.

        **Arguments:**

        - `postdb` (|PostDB|)
        """

        super(Generator, self).__init__()
        self._postdb = postdb
        self.options = hklib.GeneratorOptions()

        self.options.cssfiles = ['../heapindex.css']
        self.options.files_to_copy = ['heapindex.css', 'thread.png']

        # html_h1 is the same as html_title by default
        self.options.html_h1 = None

        self.options.shortsubject = True
        self.options.shorttags = True
        self.options.localtime_fun = time.localtime

    # Printing general HTML

    def escape(self, text):
        """Escapes the given text so that it will appear correctly when
        inserted into HTML.

        **Argument:**

        - `text` (|TextStruct|)

        **Returns:** |HtmlText|

        **Example:** ::

            >>> generator.escape('<text>')
            '&lt;text&gt;'
        """

        def escape_char(matchobject):
            """Escapes one character based on a match."""
            whole = matchobject.group(0)
            if whole == '<':
                return '&lt;'
            elif whole == '>':
                return '&gt;'
            elif whole == '&':
                return '&amp;'

        return re.sub(r'[<>&]',
                      escape_char,
                      hkutils.textstruct_to_str(text))

    # TODO: test
    def escape_link(self, link):
        """Escapes a link by replacing the double quotes to ``%22``.

        **Argument:**

        - `link` (|HtmlText|)

        **Returns:** |HtmlText|
        """

        return hkutils.textstruct_to_str(link).replace('"', '%22')

    def print_link(self, link, content):
        """Creates a link that encloses the given content.

        **Arguments:**

        - `link` (|TextStruct|)
        - `content` (|HtmlText|)

        **Returns:** |HtmlText|

        **Example:** ::

            >>> generator.print_link('mylink', 'mystuff'),
            '<a href="mylink">mystuff</a>'
        """

        if content == '':
            return ''
        return ('<a href="', self.escape_link(link), '">', content, '</a>')

    # TODO: test
    def print_comment(self, content):
        """Prints an HTML comment.

        **Argument:**

        - `content` (|HtmlText|) -- Should not contain HTML tags.

        **Returns:** |HtmlText|
        """

        return ('<!-- ', content, ' -->')

    # TODO test: comment and closing_comment args
    def enclose(self, content, tag='span', class_=None, newlines=False,
                id=None, comment=None, closing_comment=False, title=None,
                skip_empty=False):
        """Encloses the given content into a tag.

        **Arguments:**

        - `content` (|HtmlText|) -- The content to be placed between the
          opening and closing tags.
        - `tag` (|HtmlText|) -- The name of the tag to be printed.
        - `class_` (|HtmlText| | ``None``) -- The ``class`` of the tag. If
          ``None``, the tag will not have a ``class`` attribute.
        - `newlines` (bool) -- If ``True``, a newline character will be placed
          after both the opening and the tags.
        - `id` (|HtmlText| | ``None``) -- The ``id`` of the tag. If ``None``,
          the tag will not have an ``id`` attribute.
        - `comment` (|HtmlText| | ``None``) -- Comment that should be written
          after the enclosing tags.
        - `closing_comment` (bool) -- Whether a comment should be written after
          the closing tag about the class of the matching tag.
        - `title` (|HtmlText| | ``None``) -- Text for the ``title`` attribute
          of the tag.
        - `skip_empty` (bool) -- If ``True`` and ``content `` is an empty
          string or list, the function returns an empty string.
          (Note: ``content`` may be empty without being an empty string or
          list: e.g. the ``[[], []]`` text structure will be converted to an
          empty string, but this function will not consider it as empty. This
          is due to efficiency reasons.)

        **Returns:** |HtmlText|

        **Example:** ::

            >>> generator = hkgen.Generator(postdb())

            >>> text = generator.enclose('mycontent', 'div', 'chapter')
            >>> print hkutils.textstruct_to_str(text)
            <div class="chapter">mycontent</div>

            >>> text = generator.enclose(
            ...            'mycontent\\n',
            ...            class_='chapter',
            ...            newlines=True,
            ...            id="chap-10",
            ...            comment="Chapter 10",
            ...            closing_comment=True)
            >>> print hkutils.textstruct_to_str(text)
            <span class="chapter" id="chap-10"><!-- Chapter 10 -->
            mycontent
            </span><!-- Chapter 10 --><!-- chapter -->
        """

        assert hkutils.is_textstruct(content), \
               'Parameter is not a valid text structure:\n%s\n' % (content,)

        if skip_empty and (content == [] or content == ''):
            return ''

        newline = '\n' if newlines else ''
        classstr = (' class="', class_, '"') if class_ != None else ''
        idstr = (' id="', id, '"') if id != None else ''
        title_str = (' title="', title, '"') if title != None else ''
        comment_str = self.print_comment(comment) if comment != None else ''

        if closing_comment and class_ is not None:
            closing_comment_str = self.print_comment(class_)
        else:
            closing_comment_str = ''

        return ('<', tag, classstr, idstr, title_str, '>',
                comment_str, newline,
                content,
                '</', tag, '>', comment_str, closing_comment_str, newline)

    def section_begin(self, sectionid, sectiontitle):
        """Prints the beginning of a section.

        If `sectiontitle` is an empty string, no title is displayed.

        **Arguments:**

        - `sectionid` (str)
        - `sectiontitle` (|HtmlText|)

        **Returns:** |HtmlText|
        """

        if sectionid == '':
            sectionid_str = ''
        else:
            sectionid_str = ' id="%s"' % (sectionid,)

        if sectiontitle == '':
            return '<div class="sectionid"%s>\n' % (sectionid_str,)
        else:
            return ('<div class="section">\n',
                    '<span class="sectiontitle"%s>' % (sectionid_str,),
                    sectiontitle,
                    '</span>\n')

    def section_end(self):
        """Prints the end of a section.

        **Returns:** |HtmlText|
        """

        return '</div>\n'

    def section(self, id, title, content, flat=False):
        """Encloses the given HTML text into a section.

        **Arguments:**

        - `id` (str) -- The unique identifier of the section (``'section_'`` +
          id will be used as an id in the HTML).
        - `title` (str) -- The title of the section.
        - `content` (|HtmlText|) -- The HTML text to be in the section.
        - `flat` (bool) -- The section contains flat post items.

        **Returns:** |HtmlText|
        """

        assert hkutils.is_textstruct(content), \
               'Parameter is not a valid text structure:\n%s\n' % (content,)

        if flat:
            content = \
                self.enclose(content, 'table', 'flatlist', newlines=True)
        return (self.section_begin('section_%s' % (id,), title),
                content,
                self.section_end())

    # Printing one post item

    # TODO: test
    def postitem_is_star_needed(self, postitem, param):
        """Determines if we can use a "star" to denote the repetition of the
        parent post's subject or tags.

        We can use a star if the following conditions are all met:

        - using stars is enabled (`shortsubject`, `shorttags` options),
        - the post item is not flat,
        - the post described has a parent,
        - the value of the property being examined is the same as that of the
          parent.

        **Arguments:**

        - `postitem` (|PostItem|) -- The post item being examined.
        - `param` (str) -- The name of the parameter to examine, either
          ``'subject'`` or ``'tags'``.

        **Returns:** bool
        """

        enabled = getattr(self.options, 'short' + param)
        if not enabled:
            return False

        post = postitem.post
        parent = self._postdb.parent(post)
        if parent is None:
            return False

        getter = getattr(post, param)
        parent_getter = getattr(parent, param)

        return (postitem.pos != 'flat' and
                getter() == parent_getter())

    # TODO: test
    def print_postitem_author_core(self, postitem):
        """Prints the core of the author of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        return self.escape(postitem.post.author())

    # TODO: test
    def print_postitem_author(self, postitem):
        """Prints the author of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        return self.enclose(
                   self.print_postitem_author_core(postitem),
                   class_='author',
                   skip_empty=True)

    # TODO: test
    def print_postitem_subject_core(self, postitem):
        """Prints the core of the subject of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        post = postitem.post
        parent = self._postdb.parent(post)
        subject = post.subject()
        if self.postitem_is_star_needed(postitem, 'subject'):
            return self.enclose('&mdash;', class_='star')
        else:
            return subject

    # TODO: test
    def print_postitem_subject(self, postitem):
        """Prints the subject of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        return self.enclose(
                   self.print_postitem_subject_core(postitem),
                   class_='subject',
                   skip_empty=True)

    # TODO: test
    def print_postitem_tags_core(self, postitem):
        """Prints the core of the tags of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        post = postitem.post
        parent = self._postdb.parent(post)

        post_tags = set(post.tags())
        if parent is None or postitem.pos == 'flat':
            tags = post_tags
        else:
            parent_tags = set(parent.tags())
            tags = \
                (set([ '-' + tag for tag in parent_tags - post_tags]) |
                 set([ '+' + tag for tag in post_tags - parent_tags]))
        tags = sorted(tags)
        if tags == []:
            return ''
        else:
            return '[%s]' % (', '.join(tags),)

    # TODO: test
    def print_postitem_tags(self, postitem):
        """Prints the tags of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        return self.enclose(
                   self.print_postitem_tags_core(postitem),
                   class_='tags',
                   skip_empty=True)

    # TODO: test
    def print_postitem_threadlink_core(self, postitem):
        """Prints the core of the thread link of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        post = postitem.post
        if self._postdb.parent(post) is None:
            return self.print_link(
                       ('../', post.htmlthreadbasename()),
                       '<img src="../thread.png" />'),
        else:
            return ''

    # TODO: test
    def print_postitem_threadlink(self, postitem):
        """Prints the thread link of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        return self.enclose(
                   self.print_postitem_threadlink_core(postitem),
                   class_='button',
                   skip_empty=True)

    # TODO: test
    def print_postitem_post_id_core(self, postitem):
        """Prints the core of the post id of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        return \
            self.print_link(
                self.print_postitem_link(postitem),
                self.escape('<%s>' % (postitem.post.post_id_str(),)))

    # TODO: test
    def print_postitem_post_id(self, postitem):
        """Prints the post id of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        return self.enclose(
                   self.print_postitem_post_id_core(postitem),
                   class_='index',
                   skip_empty=True)

    # TODO: test
    def print_postitem_parent_post_id_core(self, postitem):
        """Prints the core of the post id of the parent of the post.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        if (hasattr(postitem, 'print_parent_post_id') and
            postitem.print_parent_post_id):

            parent = self._postdb.parent(postitem.post)
            if parent is not None:
                parent_postitem = hklib.PostItem('main', parent)
                return \
                    self.print_link(
                        self.print_postitem_link(parent_postitem),
                        ('&lt;&uarr;',
                         self.escape(parent.post_id_str()),
                         '&gt;'))
            else:
                return self.escape('<root>')
        else:
            return ''

    # TODO: test
    def print_postitem_parent_post_id(self, postitem):
        """Prints the post id of the parent of the post.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        return self.enclose(
                   self.print_postitem_parent_post_id_core(postitem),
                   class_='parent',
                   skip_empty=True)

    # TODO test
    def format_timestamp(self, timestamp):
        """Formats the date of the given post.

        **Arguments:**

        - `timestamp` (timestamp)

        **Returns:** str
        """

        return time.strftime('(%Y-%m-%d)',
                             self.options.localtime_fun(timestamp))

    # TODO: test
    def print_postitem_date_core(self, postitem):
        """Prints the core of the date of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        timestamp = postitem.post.timestamp()
        if timestamp == 0:
            return ''
        else:
            return self.format_timestamp(timestamp)

    # TODO: test
    def print_postitem_date(self, postitem):
        """Prints the date the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        return self.enclose(
                   self.print_postitem_date_core(postitem),
                   class_='date',
                   skip_empty=True)

    # TODO test
    def print_postitem_body_core(self, postitem):
        """Prints the core of the body the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        if hasattr(postitem, 'print_post_body') and postitem.print_post_body:

            body_html = []
            for segment in postitem.post.body_object().segments:
                s = self.escape(segment.text)

                if segment.type == 'link' and segment.protocol == 'http':
                    s = self.print_link(segment.text, s)
                elif segment.type == 'heap_link':
                    heap_id = postitem.post.heap_id()
                    target_post = \
                        self._postdb.post(segment.get_prepost_id_str(),
                                          heap_id)
                    if target_post is not None:
                        target_postitem = \
                            hklib.PostItem(pos='main', post=target_post)
                        s = self.print_link(
                                self.print_postitem_link(target_postitem),
                                s)

                if segment.is_meta:
                    s = self.enclose(s, class_='meta-text')

                if segment.quote_level != 0:

                    # The following code prints the name of the author before
                    # each quote.
                    #
                    # if len(segment.text) > 0 and segment.text[0] == '>':
                    #     ql = segment.quote_level
                    #     p = postitem.post
                    #     while ql != 0 and p is not None:
                    #         p = self._postdb.parent(p)
                    #         ql -= 1
                    #     if p is not None:
                    #         s = p.author() + ':\n' + s
                    #     else:
                    #         author = ''

                    class_ = 'quote-%s' % (segment.quote_level,)
                    s = self.enclose(s, class_=class_)
                    s = self.enclose(s, class_='quote')

                body_html.append(s)
            return self.enclose(body_html,
                                'pre',
                                'postbody')
        else:
            return ''

    # TODO: test
    def print_postitem_body(self, postitem):
        """Prints the body the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        return self.enclose(
                   self.print_postitem_body_core(postitem),
                   'div',
                   'body',
                   skip_empty=True,
                   newlines=True)

    # TODO: test
    def print_postitem_link(self, postitem):
        """Prints the link to the post of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |TextStruct|
        """

        post = postitem.post
        root = self._postdb.root(post)
        if root is None:
            return ('../', post.htmlfilebasename())
        else:
            return (('../', self._postdb.root(post).htmlthreadbasename()),
                    '#post_',
                    post.post_id_str())

    # TODO: test
    def print_postitem_begin(self, postitem):
        """Prints a ``'begin'`` post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        post_id_str = postitem.post.post_id_str()
        return ('\n<div class="postbox">',
                self.print_comment('post ' + post_id_str), '\n')

    # TODO: test
    def print_postitem_end(self, postitem):
        """Prints an ``'end'`` post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        post_id_str = postitem.post.post_id_str()
        return ('</div>',
                self.print_comment('postbox for post ' + post_id_str), '\n')

    # TODO test
    def get_postsummary_fields_main(self, postitem):
        # Unused argument 'postitem' # pylint: disable-msg=W0613
        """Returns the fields of the post summary when the pos position is
        ``"main"``.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** iterable(|PostItemPrinterFun|)
        """

        return (
            self.print_postitem_author,
            self.print_postitem_subject,
            self.print_postitem_tags,
            self.print_postitem_post_id,
            self.print_postitem_parent_post_id,
            self.print_postitem_date,
        )

    # TODO test
    def get_postsummary_fields_flat(self, postitem):
        # Unused argument 'postitem' # pylint: disable-msg=W0613
        """Returns the fields of the post summary when the pos position is
        ``"flat"``.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** iterable(|PostItemPrinterFun|)
        """

        return (
            self.print_postitem_author,
            self.print_postitem_subject,
            self.print_postitem_tags,
            self.print_postitem_post_id,
            self.print_postitem_date,
        )

    def print_postitem_main(self, postitem):
        """Prints a ``'main'`` post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        # This function appends a newline to the HTML text when it is not
        # empty. The condition could be written more nicely if we had a
        # hkutils.is_textstruct_empty function.
        def append_newline(s):
            if s == '' or s == []:
                return s
            else:
                return (s, '\n')

        post_summary_fields = \
            [append_newline(fun(postitem))
             for fun in self.get_postsummary_fields_main(postitem)]

        body = self.print_postitem_body(postitem)
        post_id_str = postitem.post.post_id_str()
        return self.enclose(
                   (post_summary_fields, body),
                   class_='postsummary',
                   id=('post_', post_id_str),
                   newlines=True,
                   closing_comment=True)

    def print_postitem_flat(self, postitem):
        """Prints a ``'flat'`` post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        def td(s):
            return (self.enclose(s, 'td'), '\n')

        post_summary_fields = \
            [td(fun(postitem))
             for fun in self.get_postsummary_fields_flat(postitem)]

        post_summary_str = \
            self.enclose(
                post_summary_fields,
                'tr',
                newlines=True)

        body = self.print_postitem_body(postitem)
        if body is '':
            body_str = ''
        else:
            body_str = \
                self.enclose(
                    self.enclose(
                        body,
                        'td colspan=5',
                        newlines=True),
                    'tr',
                    newlines=True)

        return self.enclose(
                   (post_summary_str, body_str),
                   class_='postsummary',
                   newlines=True)

    # TODO: test
    def print_postitem(self, postitem):
        """Prints the given post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        if postitem.pos == 'begin':
            return self.print_postitem_begin(postitem)
        elif postitem.pos == 'end':
            return self.print_postitem_end(postitem)
        elif postitem.pos == 'main':
            return self.print_postitem_main(postitem)
        elif postitem.pos == 'flat':
            return self.print_postitem_flat(postitem)
        else:
            raise hkutils.HkException, \
                  "Unknown 'pos' in postitem: %s" % (postitem,)

    # Printing and walking several post items

    def augment_postitem(self, postitem):
        """Returns the augmented versions of the given post item.

        The `print_fun` method of the post item is set to the
        :func:`print_postitem` method.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |PostItem|
        """

        postitem = postitem.copy()
        if not hasattr(postitem, 'print_fun'):
            postitem.print_fun = self.print_postitem
        return postitem

    def walk_postitems(self, xpostitems):
        """Walks the augmented versions of the given post items.

        Refer to :func:`augment_postitem` for how the augmentation is done.

        **Argument:**

        - `xpostitems` (iterable(|PostItem|))

        **Returns:** iterable(|PostItem|)
        """

        for postitem in xpostitems:
            yield self.augment_postitem(postitem)

    # TODO: test
    def walk_thread(self, root=None, threadstruct=None):
        """Walks the given thread.

        **Argument:**

        - `root` (|Post| | ``None``) -- The root of the thread to be walked. If
          ``None``, the whole thread structure is walked.
        - `threadstruct` ({(``None`` | |PostId|): |PostId|} | ``None``) -- The
          thread structure to be used. If ``None``, the thread structure of the
          post database will be used.

        **Returns:** iterable(|PostItem|)
        """

        xpostitems = \
            self._postdb.walk_thread(root, threadstruct, yield_main=True)
        return self.walk_postitems(xpostitems)

    # TODO test
    def walk_exp_posts(self, posts):
        """Walks the expanded post set.

        This function walks the expanded post set (``posts.exp()``), but
        prints the posts that are present in the original post set differently
        from those that are present only in the expanded post set. Those that
        are present only in the expanded set (``posts.exp() - posts``) will be
        enclosed in ``'post_inactive'`` span. Other than this, the
        :func:`Generator.print_postitem` method will be used to print both type
        of posts.

        **Argument:**

        - `posts` (|PostSet|)

        **Returns:** iterable(|PostItem|)
        """

        assert(isinstance(posts, hklib.PostSet))

        # roots: roots of posts in `posts`; these threads have to be walked
        roots = posts.expb().collect.is_root()
        roots_list = roots.sorted_list()

        # posts_exp: thread mates of posts in `posts`; these posts have to be
        # printed. The posts in posts_exp that are present also in `posts` will
        # be active, the others will be inactive.
        posts_exp = roots.expf()
        print_fun = self.print_postitem

        for root in roots_list:
            for postitem in self._postdb.walk_thread(root, yield_main=True):
                if (postitem.post not in posts and
                    postitem.pos in ['main', 'flat']):
                    def enclose_inactive(postitem):
                        return self.enclose(print_fun(postitem),
                                            class_='post_inactive',
                                            newlines=True,
                                            closing_comment=True)
                    postitem.print_fun = enclose_inactive
                else:
                    postitem.print_fun = print_fun
                yield postitem

    def print_postitems(self, xpostitems):
        """Prints the given post items using their `print_fun` method.

        **Argument:**

        - `xpostitem` iterable(|PostItem|)

        **Returns:** |HtmlText|
        """

        return [ postitem.print_fun(postitem) for postitem in xpostitems ]

    # Post item modifiers

    # TODO: test
    def set_postitem_attr(self, key, value=True):
        """Returns a function that sets the `key` data attribute of `postitem`
        to the `value`.

        **Argument:**

        - `key` (str)
        - `value` (object)

        **Returns:** |PostItemModifierFun|
        """

        def setter(postitem):
            setattr(postitem, key, value)
            return postitem
        return setter

    # TODO: test
    def reverse_threads(self, xpostitems):
        """Yields the threads in a "smart" reversed order.

        **Argument:**

        - `xpostitems` (iterable(|PostItem|))

        **Returns:** iterable(|PostItem|)

        **Example:**

        Input::

            <PostItem: pos=begin, post_id=my_heap/0, level=0>
              <PostItem: pos=begin, post_id=my_heap/1, level=1>
                <PostItem: pos=begin, post_id=my_heap/2, level=2>
                <PostItem: pos=end, post_id=my_heap/2, level=2>
              <PostItem: pos=end, post_id=my_heap/1, level=1>
              <PostItem: pos=begin, post_id=my_heap/3, level=1>
              <PostItem: pos=end, post_id=my_heap/3, level=1>
            <PostItem: pos=end, post_id=my_heap/0, level=0>
            <PostItem: pos=begin, post_id=my_heap/4, level=0>
            <PostItem: pos=end, post_id=my_heap/4, level=0>

        Output::

            <PostItem: pos=begin, post_id=my_heap/4, level=0>
            <PostItem: pos=end, post_id=my_heap/4, level=0>
            <PostItem: pos=begin, post_id=my_heap/0, level=0>
              <PostItem: pos=begin, post_id=my_heap/1, level=1>
                <PostItem: pos=begin, post_id=my_heap/2, level=2>
                <PostItem: pos=end, post_id=my_heap/2, level=2>
              <PostItem: pos=end, post_id=my_heap/1, level=1>
              <PostItem: pos=begin, post_id=my_heap/3, level=1>
              <PostItem: pos=end, post_id=my_heap/3, level=1>
            <PostItem: pos=end, post_id=my_heap/0, level=0>
        """

        threads = [] # type: [[PostItem]]
        last_thread = [] # type: [PostItem]
        for postitem in xpostitems:
            last_thread.append(postitem)
            if postitem.level == 0 and postitem.pos == 'end':
                threads.append(last_thread)
                last_thread = []
        threads.append(last_thread)
        threads.reverse()
        result = [] # type: [PostItem]
        for thread in threads:
            result += thread
        return result

    # TODO: test
    def enclose_posts(self, class_, posts):
        """Returns a function that encloses the summaries of the given posts
        into the given HTML class.

        **Argument:**

        - `class_` (|HtmlText|)
        - `posts` (|PostSet|)

        **Returns:** |PostItemModifierFun|
        """

        def enclose(postitem):
            post = postitem.post
            if post in posts:
                post_id_str = post.post_id_str()
                old_print_fun = postitem.print_fun
                if postitem.pos == 'main':
                    postitem.print_fun = \
                        lambda postitem:\
                            self.enclose(
                                old_print_fun(postitem),
                                class_=class_,
                                newlines=True,
                                comment=('post ', post_id_str),
                                closing_comment=True)
            return postitem
        return enclose

    # TODO: test
    def enclose_threads(self, class_, posts):
        """Returns a function that encloses the summaries of the given threads
        into the given HTML class.

        **Argument:**

        - `class_` (|HtmlText|)
        - `posts` (|PostSet|)

        **Returns:** |PostItemModifierFun|
        """

        def enclose(postitem):
            post = postitem.post
            if post in posts:
                post_id_str = post.post_id_str()
                old_print_fun = postitem.print_fun
                if postitem.pos == 'begin':
                    postitem.print_fun = \
                        lambda postitem:\
                            ('<span class="', class_, '">',
                             '<!-- post ', post_id_str, ' -->\n',
                            old_print_fun(postitem))
                elif postitem.pos == 'end':
                    postitem.print_fun = \
                        lambda postitem: \
                            (old_print_fun(postitem),
                            '</span>',
                            '<!-- "', class_, '" of post ',
                            post_id_str, ' -->\n')
            return postitem
        return enclose

    # Printing concrete pages

    def print_main_index_page(self):
        """Prints the main index page.

        **Returns:** |HtmlText|
        """

        normal_postitems = self.walk_thread(None)
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

    # TODO: test
    def print_thread_page(self, root):
        """Prints a thread page.

        **Argument:**

        - `root` (|Post|) -- The root of the (sub)thread to be printed.

        **Returns:** |HtmlText|
        """

        xpostitems = self.walk_thread(root)
        xpostitems = \
            itertools.imap(
                self.set_postitem_attr('print_post_body'),
                xpostitems)
        xpostitems = \
            itertools.imap(
                self.set_postitem_attr('print_parent_post_id'),
                xpostitems)
        return self.print_postitems(xpostitems)

    def print_post_page(self, post):
        """Prints a post page.

        **Argument:**

        - `post` (|Post|)

        **Returns:** |HtmlText|
        """

        # We create a thread structure that contains only out post.
        threadst = {None: [post.post_id()]}

        xpostitems = self.walk_thread(threadstruct=threadst)
        xpostitems = \
            itertools.imap(
                self.set_postitem_attr('print_post_body'),
                xpostitems)
        return self.print_postitems(xpostitems)

    # Printing HTML headers and footers

    # TODO: test
    def print_html_header_info(self):
        """Prints the header info.

        An example header info:

        .. code-block:: html

            <!-- Generated by Heapkeeper v0.3 on 2009-10-21 20:58:33 -->

        **Returns:** |HtmlText|
        """

        now = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        info = ('Generated by Heapkeeper v',
                hklib.heapkeeper_version,
                ' on ',
                now)
        return (self.print_comment(info), '\n')

    # TODO: test
    def print_html_head_content(self):
        """Prints the content in the HTML header.

        **Returns:** |HtmlText|
        """

        return \
            ['    <link rel=stylesheet href="%s" type="text/css">\n' % (css,)
             for css in self.options.cssfiles]

    # TODO: test
    def print_html_header(self):
        """Prints the HTML header.

        **Returns:** |HtmlText|
        """

        meta_stuff = ('<meta http-equiv="Content-Type" '
                      'content="text/html;charset=utf-8">')

        content = [(self.print_html_header_info(),
                    '<html>\n'
                    '  <head>\n'
                    '    ', meta_stuff, '\n',
                    '    <title>', self.options.html_title, '</title>\n')]

        content.append(self.print_html_head_content())

        if self.options.html_h1 is None:
            header_title = self.options.html_title
        else:
            header_title = self.options.html_h1

        content.append(
            ('  </head>\n'
             '  <body>\n'
             '    <h1 id="header">', header_title, '</h1>\n\n'))

        return content

    # TODO: test
    def print_html_footer(self):
        """Prints the HTML footer.

        **Returns:** |HtmlText|
        """

        return ('\n'
                '  </body>\n'
                '</html>\n')

    def print_html_page(self, html_body):
        """Puts HTML header and footer around the given HTML body.

        **Argument:**

        - `html_body` (|HtmlText|)

        **Returns:** |HtmlText|
        """

        return (self.print_html_header(),
                html_body,
                self.print_html_footer())

    # General page writer

    # TODO test
    def settle_files_to_copy(self):
        """Copies the files in `self.options.files_to_copy` to the HTML
        directory."""

        for file in self.options.files_to_copy:

            target_file = os.path.join(self._postdb.html_dir(), file)

            # We try to copy the file from one of the heaps used by the post
            # database

            # We have not found the file yet
            file_found = False

            # We iterate the heaps in alphabetical order (to make the algorithm
            # deterministic)
            heaps = sorted(self._postdb._heaps.items())

            # We iterate the heaps and look for the file
            for heap_id, heap_dir in heaps:
                heap_file = os.path.join(heap_dir, file)
                if os.path.exists(heap_file):
                    shutil.copyfile(heap_file, target_file)
                    file_found = True
                    break

            if file_found:
                # File already found and copied
                pass
            elif os.path.exists(file):
                # Copy from the current directory
                shutil.copyfile(file, target_file)
            else:
                hkutils.log('WARNING: file "%s" not found' % (file,))

    # TODO test, doc
    def write_page(self, filename, html_body):

        self.settle_files_to_copy()

        # if the path is relative, put it into html_dir
        if os.path.abspath(filename) != filename:
            filename = os.path.join(self._postdb.html_dir(), filename)

        # creating the directory
        dir = os.path.dirname(filename)
        if not os.path.exists(dir):
            os.mkdir(dir)

        with open(filename, 'w') as f:
            html_page = self.print_html_page(html_body)
            hkutils.write_textstruct(f, html_page)

    # Finding outdated pages

    # TODO: test
    def is_file_newer(self, file1, file2):
        """Returns whether the first file is newer than the second one.

        If any of the files do not exist, it returns ``True``.

        **Arguments:**

        - `file1` (str) -- The name of the first file.
        - `file2` (str) -- The name of the second file.

        **Returns:** bool
        """

        try:
            time1 = os.stat(file1).st_mtime
            time2 = os.stat(file2).st_mtime
            return time1 > time2
        except OSError:
            # a file is missing
            return True

    # TODO: test
    def outdated_thread_pages(self, posts=None):
        """Returns the threads whose pages may be outdated.

        It is not guaranteed that all thread pages are outdated that are
        returned, but it is guaranteed that all thread pages are up-to-date
        that are not returned. If the post is in a cycle, ``False`` is
        returned, because there is no thread page in that case.

        **Arguments:**

        - `posts` (|PostSet|) -- The posts that should be examined. If
          ``None``, all posts are examined.

        **Returns:** |PostSet|
        """

        def may_thread_page_of_post_be_outdated(post):
            # If the post is modified or the post file is newer than the thread
            # page, the thread page is probably outdated.
            root = self._postdb.root(post)

            # The post is in a cycle
            if root is None:
                return False
            else:
                return (post.is_modified() or
                        self.is_file_newer(
                            post.postfilename(),
                            root.htmlthreadfilename()))

        if posts is None:
            posts = self._postdb.all()
        outdated_posts = posts.collect(may_thread_page_of_post_be_outdated)
        outdated_threads = outdated_posts.expb().collect.is_root()

        return outdated_threads

    # TODO: test
    def outdated_post_pages(self, posts=None):
        """Returns the posts whose pages may be outdated.

        It is not guaranteed that all post pages are outdated that are
        returned, but it is guaranteed that all post pages are up-to-date
        that are not returned.

        **Arguments:**

        - `posts` (|PostSet|) -- The posts that should be examined. If
          ``None``, all posts are examined.

        **Returns:** |PostSet|
        """

        def may_post_page_of_post_be_outdated(post):
            # If the post is modified or the post file is newer than the post
            # page, the post page is probably outdated.
            return (post.is_modified() or
                    self.is_file_newer(
                        post.postfilename(),
                        post.htmlfilename()))

        if posts is None:
            posts = self._postdb.all()
        outdated_posts = posts.collect(may_post_page_of_post_be_outdated)
        return outdated_posts

    # Writing concrete pages

    def write_main_index_page(self):
        """Writes the main index page into ``'index.html'``."""

        hkutils.log('Generating index.html...')
        self.options.html_title = 'Main index'
        self.write_page(
            'index/index.html',
            self.print_main_index_page())

    # TODO better test
    def write_thread_pages(self, write_all=False):
        """Writes the thread pages into
        ``'<root_heap_id>/thread_<root_post_index>.html'``.

        **Argument:**

        - `write_all` (bool) -- If ``True``, the function writes all thread
          pages. Otherwise it writes only those whose posts were modified.
        """

        hkutils.log('Generating thread pages...')

        if write_all:
            posts = self._postdb.roots()
        else:
            posts = self.outdated_thread_pages()

        for post in posts:
            self.options.html_title = 'Thread ' + post.post_id_str()
            self.write_page(
                filename=post.htmlthreadbasename(),
                html_body=self.print_thread_page(post))

    # TODO: better test
    def write_post_pages(self, write_all=False):
        """Writes the post pages into ``'<heap_id>/<post_index>.html'``.

        **Argument:**

        - `write_all` (bool) -- If ``True``, the function writes all post
          pages. Otherwise it writes only those whose posts are in cycles and
          were modified.
        """

        hkutils.log('Generating post pages...')

        if write_all:
            posts = self._postdb.roots()
        else:
            posts_in_cycles = self._postdb.cycles()
            posts = self.outdated_post_pages(posts_in_cycles)

        for post in posts:
            self.options.html_title = 'Post ' + post.post_id_str()
            self.write_page(
                filename=post.htmlfilebasename(),
                html_body=self.print_post_page(post))

    # TODO: test
    def write_all(self):
        """Writes the main index page, the thread pages and the post pages."""

        self.write_main_index_page()
        self.write_thread_pages()


class GivenPostsGenerator(Generator):
    """Creates a page that shows the given posts.

    The page will contain the given posts, embedded in their thread structure.
    The posts that are not given but are thread mates of a given post will be
    shown as inactive.
    """

    # TODO: test
    def __init__(self, postdb):
        """Constructor.

        **Arguments:**

        - `postdb` (|PostDB|)
        """

        super(GivenPostsGenerator, self).__init__(postdb)
        self.posts = postdb.postset([])
        self.html_filename = 'given_posts.html'
        self.options.html_title = 'GivenPostsGenerator'

    # TODO: test
    def print_given_posts_page(self):
        """Prints the page that contains the given posts.

        **Returns:** |HtmlText|
        """

        # Getting the posts in the interesting threads
        xpostitems = self.walk_exp_posts(self.posts)

        # Reversing the thread order
        xpostitems = self.reverse_threads(xpostitems)

        # Printing the page
        return self.print_postitems(xpostitems)

    # TODO: test
    def write_given_posts_page(self):
        """Writes the "given post" page."""
        hkutils.log('Generating %s...' % (self.html_filename,))
        self.write_page(
            self.html_filename,
            self.print_given_posts_page())

    # TODO: test
    def write_all(self):
        """Writes the "given post" page."""

        self.write_given_posts_page()

