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
"""


from __future__ import with_statement

import datetime
import itertools
import os
import re

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

        # html_h1 is the same as html_title by default
        self.options.html_h1 = None

        self.options.shortsubject = True
        self.options.shorttags = True

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
    def enclose(self, class_, content, tag='span', newlines=False, id=None,
                comment=None, closing_comment=False):
        """Encloses the given content into a tag.

        **Arguments:**

        - `class_` (|HtmlText| | ``None``) -- The ``class`` of the tag. If
          ``None``, the tag will not have a ``class`` attribute.
        - `content` (|HtmlText|) -- The content to be placed between the
          opening and closing tags.
        - `tag` (|HtmlText|) -- The name of the tag to be printed.
        - `newlines` (bool) -- If ``True``, a newline character will be placed
          after both the opening and the tags.
        - `id` (|HtmlText| | ``None``) -- The ``id`` of the tag. If ``None``,
          the tag will not have an ``id`` attribute.
        - `comment` (|HtmlText| | ``None``) -- Comment that should be written
          after the enclosing tags.
        - `closing_comment` (bool) -- Whether a comment should be written after
          the closing tag about the class of the matching tag.

        **Returns:** |HtmlText|

        **Example:** ::

            >>> generator = hkgen.Generator(postdb())

            >>> text = generator.enclose('chapter', 'mycontent', 'div')
            >>> print hkutils.textstruct_to_str(text)
            <div class="chapter">mycontent</div>

            >>> text = generator.enclose(
            ...            'chapter',
            ...            'mycontent\\n',
            ...            newlines=True,
            ...            id="chap-10",
            ...            comment="Chapter 10",
            ...            closing_comment=True)
            >>> print hkutils.textstruct_to_str(text)
            <span class="chapter" id="chap-10"><!-- Chapter 10 -->
            mycontent
            </span><!-- Chapter 10 --><!-- chapter -->
        """

        if content == '':
            return ''
        newline = '\n' if newlines else ''
        classstr = (' class="', class_, '"') if class_ != None else ''
        idstr = (' id="', id, '"') if id != None else ''
        comment_str = self.print_comment(comment) if comment != None else ''

        if closing_comment and class_ is not None:
            closing_comment_str = self.print_comment(class_)
        else:
            closing_comment_str = ''

        return ('<', tag, classstr, idstr, '>', comment_str, newline,
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

        assert(hkutils.is_textstruct(content))

        if flat:
            content = \
                self.enclose('flatlist', content, tag='table', newlines=True)
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
    def print_postitem_author(self, postitem):
        """Prints the author of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        return self.escape(postitem.post.author())

    # TODO: test
    def print_postitem_subject(self, postitem):
        """Prints the subject of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        post = postitem.post
        parent = self._postdb.parent(post)
        subject = post.subject()
        if self.postitem_is_star_needed(postitem, 'subject'):
            return self.enclose('star',  '&mdash;')
        else:
            return subject

    # TODO: test
    def print_postitem_tags(self, postitem):
        """Prints the tags of the post item.

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
    def print_postitem_threadlink(self, postitem):
        """Prints the thread link of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        post = postitem.post
        if self._postdb.parent(post) is None:
            return self.enclose(
                       'button',
                       self.print_link(
                           post.htmlthreadbasename(),
                           '<img src="thread.png" />'))
        else:
            return ''

    # TODO: test
    def print_postitem_heapid(self, postitem):
        """Prints the heapid of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        return \
            self.print_link(
                self.print_postitem_link(postitem),
                self.escape('<%s>' % (postitem.post.heapid(),)))

    # TODO: test
    def print_postitem_parent_heapid(self, postitem):
        """Prints the heapid of the parent of the post.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        if (hasattr(postitem, 'print_parent_heapid') and
            postitem.print_parent_heapid):

            parent = self._postdb.parent(postitem.post)
            if parent is not None:
                parent_postitem = hklib.PostItem('main', parent)
                return \
                    self.print_link(
                        self.print_postitem_link(parent_postitem),
                        ('&lt;&uarr;',
                         self.escape(parent.heapid()),
                         '&gt;'))
            else:
                return self.escape('<root>')
        else:
            return ''

    # TODO: test
    def print_postitem_date(self, postitem):
        """Prints the date the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        date_str = self.options.date_fun(postitem.post, self.options)
        return ('' if date_str is None else date_str)

    # TODO test
    def print_postitem_body(self, postitem):
        """Prints the body the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        if hasattr(postitem, 'print_post_body') and postitem.print_post_body:
            return self.enclose('postbody',
                                self.escape(postitem.post.body()),
                                tag='pre')
        else:
            return ''

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
            return post.htmlfilebasename()
        else:
            return (self._postdb.root(post).htmlthreadbasename(),
                    '#post_',
                    post.heapid())

    # TODO: test
    def print_postitem_begin(self, postitem):
        """Prints a ``'begin'`` post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        heapid = postitem.post.heapid()
        return ('<div class="postbox">',
                self.print_comment('post ' + heapid), '\n')

    # TODO: test
    def print_postitem_end(self, postitem):
        """Prints an ``'end'`` post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        heapid = postitem.post.heapid()
        return ('</div>',
                self.print_comment('postbox for post ' + heapid), '\n')

    def print_postitem_main(self, postitem):
        """Prints a ``'main'`` post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        def newline():
            content.append('\n')

        def enclose(class_, fun):
            text = fun(postitem)
            if text != '':
                content.append(
                    self.enclose(
                        class_,
                        text))
                newline()

        content = []
        thread_link = self.print_postitem_threadlink(postitem)

        enclose('author', self.print_postitem_author)
        enclose('subject', self.print_postitem_subject)

        content.append(self.print_postitem_threadlink(postitem))
        newline()

        enclose('tags', self.print_postitem_tags)
        enclose('index', self.print_postitem_heapid)
        enclose('parent', self.print_postitem_parent_heapid)
        enclose('date', self.print_postitem_date)

        content.append(
            self.enclose(
                'body',
                self.print_postitem_body(postitem),
                tag='div',
                newlines=True))

        heapid = postitem.post.heapid()
        return self.enclose(
                   class_='postsummary',
                   id=('post_', heapid),
                   newlines=True,
                   content=content,
                   comment=('post ', heapid),
                   closing_comment=True)

    def print_postitem_flat(self, postitem):
        """Prints a ``'flat'`` post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        def newline():
            content.append('\n')

        def enclose(class_, fun):
            text = fun(postitem)
            if text != '':
                columns[0] += 1
                content.append(
                    self.enclose(
                        class_,
                        text,
                        tag='td'))
                newline()

        # We store the number of columns in `columns[0]`.
        columns = [0]

        content = []
        thread_link = self.print_postitem_threadlink(postitem)

        enclose('author', self.print_postitem_author)
        enclose('subject', self.print_postitem_subject)
        enclose('tags', self.print_postitem_tags)
        enclose('index', self.print_postitem_heapid)
        enclose('date', self.print_postitem_date)

        content.append(
            self.enclose(
                tag='tr',
                class_='body',
                newlines=True,
                content=
                    self.enclose(
                        tag=('td colspan=%d' % (columns[0])),
                        class_='body',
                        newlines=True,
                        content=
                            self.print_postitem_body(postitem)))),

        return self.enclose('postsummary', content, tag='tr', newlines=True)

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
        - `threadstruct` ({(``None`` | |Heapid|): |Heapid|} | ``None``) -- The
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
        ae present only in the expanded set (``posts.exp() - posts``) will be
        enclosed in ``'post_inactive'`` span. Other than this, the
        :func:`Generator.print_postitem` method will be used to print both type
        of posts.

        **Argument:**

        - `posts` (|PostSet|)

        **Returns:** iterable(|PostItem|)
        """

        assert(isinstance(posts, hklib.PostSet))

        roots = posts.collect.is_root()
        roots_list = roots.sorted_list()
        posts_exp = roots.expf()
        print_fun = self.print_postitem

        for root in roots_list:
            for postitem in self._postdb.walk_thread(root, yield_main=True):
                if (postitem.post not in posts and
                    postitem.pos in ['main', 'flat']):
                    def enclose_inactive(postitem):
                        return self.enclose('post_inactive',
                                            print_fun(postitem),
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
                heapid = post.heapid()
                old_print_fun = postitem.print_fun
                if postitem.pos == 'main':
                    postitem.print_fun = \
                        lambda postitem:\
                            self.enclose(
                                class_,
                                old_print_fun(postitem),
                                newlines=True,
                                comment=('post ', heapid),
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
                heapid = post.heapid()
                old_print_fun = postitem.print_fun
                if postitem.pos == 'begin':
                    postitem.print_fun = \
                        lambda postitem:\
                            ('<span class="', class_, '">',
                             '<!-- post ', heapid, ' -->\n',
                            old_print_fun(postitem))
                elif postitem.pos == 'end':
                    postitem.print_fun = \
                        lambda postitem: \
                            (old_print_fun(postitem),
                            '</span>',
                            '<!-- "', class_, '" of post ', heapid, ' -->\n')
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
                self.set_postitem_attr('print_parent_heapid'),
                xpostitems)
        return self.print_postitems(xpostitems)

    def print_post_page(self, post):
        """Prints a post page.

        **Argument:**

        - `post` (|Post|)

        **Returns:** |HtmlText|
        """

        # We create a thread structure that contains only out post.
        threadst = {None: [post.heapid()]}

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

        for css in self.options.cssfiles:
             content.append(
                '    <link rel=stylesheet href="%s" type="text/css">\n' %
                (css,))

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

    def settle_files_to_copy(self):
        """Copies the CSS file and other files to the HTML directory if
        needed."""

        if self.options.trycopyfiles:

            for css in self.options.cssfiles:

                # If the CSS file exists, OK
                newcssfile = os.path.join(self._postdb.html_dir(), css)
                if os.path.exists(newcssfile):
                    continue # ok, file exists

                # Try to copy the CSS file from the current directory
                if hkutils.copy_wo(css, newcssfile):
                    continue # ok, copied

                # Try to copy the CSS file from the heap
                cssfile_on_heap = \
                    os.path.join(self._postdb.postfile_dir(), css)
                if hkutils.copy_wo(cssfile_on_heap, newcssfile):
                    continue # ok, copied

                hklib.log('WARNING: CSS file "%s" not found' % (css,))

            if os.path.exists('thread.png'):
                threadpng = os.path.join(self._postdb.html_dir(), 'thread.png')
                hkutils.copy_wo('thread.png', threadpng)

    # TODO test, doc
    def write_page(self, filename, html_body):

        self.settle_files_to_copy()

        # if the path is relative, put it into html_dir
        if os.path.abspath(filename) != filename:
            filename = os.path.join(self._postdb.html_dir(), filename)

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

        hklib.log('Generating index.html...')
        self.options.html_title = 'Main index'
        self.write_page(
            'index.html',
            self.print_main_index_page())

    # TODO better test
    def write_thread_pages(self, write_all=False):
        """Writes the thread pages into ``'thread_<root_heapid>.html'``.

        **Argument:**

        - `write_all` (bool) -- If ``True``, the function writes all thread
          pages. Otherwise it writes only those whose posts were modified.
        """

        hklib.log('Generating thread pages...')

        if write_all:
            posts = self._postdb.roots()
        else:
            posts = self.outdated_thread_pages()

        for post in posts:
            self.options.html_title = 'Thread ' + post.heapid()
            self.write_page(
                filename=post.htmlthreadbasename(),
                html_body=self.print_thread_page(post))

    # TODO: better test
    def write_post_pages(self, write_all=False):
        """Writes the post pages into ``'<heapid>.html'``.

        **Argument:**

        - `write_all` (bool) -- If ``True``, the function writes all post
          pages. Otherwise it writes only those whose posts are in cycles and
          were modified.
        """

        hklib.log('Generating post pages...')

        if write_all:
            posts = self._postdb.roots()
        else:
            posts_in_cycles = self._postdb.cycles()
            posts = self.outdated_post_pages(posts_in_cycles)

        for post in posts:
            self.options.html_title = 'Post ' + post.heapid()
            self.write_page(
                filename=post.htmlfilebasename(),
                html_body=self.print_post_page(post))

    # TODO: test
    def write_all(self):
        """Writes the main index page, the thread pages and the post pages."""

        self.write_main_index_page()
        self.write_thread_pages()
        self.write_post_pages()
