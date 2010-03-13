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

"""|hklib| implements the heap data structure.

Pseudo-types
''''''''''''

|hklib| has pseudo-types that are not real Python types, but we use them as
types in the documentation so we can talk about them easily.

.. _hklib_Heapid:

- **Heapid** -- The identifier of a |Post| in |PostDB|.

  Real type: str

.. _hklib_Messageid:

- **Messageid** -- The message identifier of the email from which the |Post|
  was created. Not all post have a message id.

  Real type: str

.. _hklib_PrePost:

- **PrePost** -- An object that can be converted into a |Post|. When it is an
  *int*, it will be converted to a string that should represent a |Heapid|.
  |Heapid| is converted to a |Post| based on the post database.

  Real type: |Heapid| | int | |Post|

.. _hklib_PrePostSet:

- **PrePostSet** -- An object that can be converted into a |PostSet|. Actually,
  |PrePostSet| can be any iterable object that iterates over |PrePost| objects.

  Real type: set(|PrePost|)) | [|PrePost|] | |PrePost| | |PostSet|

.. _hklib_HtmlStr:

- **HtmlStr** -- String that contains HTML.

  Real type: str

.. _hklib_HtmlText:

- **HtmlText** -- Text that contains HTML code.

  Subtype of |TextStruct|.

.. _hklib_LogFun:

- **LogFun(*args)** -- A function that logs the given strings.

   **Arguments:**

   - `*args` ([str]): list of strings to be logged
"""


from __future__ import with_statement

import base64
import datetime
import email
import email.header
import imaplib
import os
import os.path
import quopri
import re
import shutil
import string
import StringIO
import sys
import time

import hkutils


heapkeeper_version = '0.4+'

##### logging #####

def default_log_fun(*args):
    """Default logging function: prints the arguments to the standard output,
    terminated with a newline character.

    **Type:** |LogFun|
    """

    for arg in args:
        sys.stdout.write(arg)
    sys.stdout.write('\n')
    sys.stdout.flush()

# The function to be used for logging.
log_fun = default_log_fun

def set_log(log):
    """Sets the logging function.

    **Arguments:**

    - `log` (bool | |LogFun|) -- If ``False``, logging will be turned off.
      If ``True``, the default logging function will be used. Otherwise the
      specified logging function will be used.
    """

    global log_fun

    if log == True:
        log_fun = default_log_fun
    elif log == False:
        # Do nothing when invoked
        log_fun = lambda *args: None
    else:
        log_fun = log

def log(*args):
    """Logs the given strings.

    This function invokes the logger fuction set by :func:`set_log`.

    **Arguments:**

    - `*args` ([str]) -- List of strings to be logged.
    """

    log_fun(*args)


##### Post #####

# This variable should be put into hklib.Options, but we don't have that yet.
localtime_fun = time.localtime


class Post(object):

    """Represents a posted message on the heap.

    A Post object is in the memory, but usually it represents a file that is in
    the filesystem.

    **Data attributes:**

    - `_header` ({str: (str | [str])}) -- The header of the post. See
      the contents below.
    - `_body` (str) -- The body of the post. The first character of the
      body is not a whitespace. The last character is a newline character, and
      the last but one character is not a whitespace. It does not contain any
      ``\\r`` characters, newlines are stored as ``\\n``. The form of the body
      expressed as a regular expression: ``(\\S|\\S[^\\r]*\\S)\\n``. The
      :func:`set_body` function converts any given string into this format.
    - `_heapid` (|Heapid| | None) -- The identifier of the post.
    - `_postdb` (|PostDB| | None) -- The post database object that contains the
      post. If `_postdb` is not ``None``, `_heapid` must not be ``None``
      either.
    - `_modified` (bool) -- It is ``False`` if the post file that belongs to
      the post object is up-to-date. It is ``True`` if there is no such file or
      the post has been modified since the last synchronization.
    - `_meta_dict` ({str: (str | ``None``)}) -- Dictionary that contains meta
      text from the body.

    The `_header` attribute is a dictonary that contains attributes of the post
    such as the subject. The `_header` always contains all the following items:

    - ``'Author'`` (str) -- The author of the post.
    - ``'Subject'`` (str) -- The subject of the post.
    - ``'Tag'`` ([str]) -- The tags of the post.
    - ``'Message-Id'`` (str) -- The message id of the post.
    - ``'Parent'`` (|Heapid| | |Messageid| | ``''``) -- The heapid or message
      id of the parent of the post. It should be en empty string when the post
      has no parent.
    - ``'Date'`` (str) -- The date of the post.
    - ``'Flag'`` ([str]) -- The flags of the post. Currently there is only one
      flag, the ``delete`` flag.
    """

    # Constructors

    def __init__(self, f, heapid=None, postdb=None):
        """Constructor.

        **Arguments:**

        - `f` (fileobject) -- A file object from which the header and the body
          of the post will be read. It will not be closed.
        - `heapid` (|Heapid| | None) -- Initial value of the `_heapid` data
          attribute.
        - `postdb` (|PostDB| None) -- Initial value of the `_postdb` data
          attribute.
        """

        assert(not (postdb != None and heapid == None))
        super(Post, self).__init__()
        try:
            self._header, self._body = Post.parse(f)
            self._heapid = heapid
            self._postdb = postdb
            self._datetime = hkutils.NOT_SET
            self._modified = not self.postfile_exists()
            self._meta_dict = None
        except Exception, e:
            raise hkutils.HkException, \
                  ('Error parsing post "%s"\n%s' %
                   (getattr(f, 'name', ''), e))

    @staticmethod
    def from_str(s, heapid=None, postdb=None):
        """Creates a |Post| object from the given string.

        **Arguments:**

        - `s` (str) -- String from which the post should be created. It is
          handled like the content of a post file.
        - `heapid` (|Heapid| | None) -- Initial value of the `_heapid` data
          attribute.
        - `postdb` (|PostDB| None) -- Initial value of the `_postdb` data
          attribute.

        **Returns:** |Post|
        """

        sio = StringIO.StringIO(s)
        p = Post(sio, heapid, postdb)
        sio.close()
        return p

    @staticmethod
    def from_file(filename, heapid=None, postdb=None):
        """Creates a |Post| object from a file.

        **Arguments:**

        - `filename` (str) -- The post file from which the post should be
          created.
        - `heapid` (|Heapid| | None) -- Initial value of the `_heapid` data
          attribute.
        - `postdb` (|PostDB| None) -- Initial value of the `_postdb` data
          attribute.

        **Returns:** |Post|
        """

        with open(filename, 'r') as f:
            return Post(f, heapid, postdb)

    @staticmethod
    def create_empty(heapid=None, postdb=None):
        """Creates an empty Post object.

        **Arguments:**

        - `heapid` (|Heapid| | None) -- Initial value of the `_heapid` data
          attribute.
        - `postdb` (|PostDB| None) -- Initial value of the `_postdb` data
          attribute.

        **Returns:** |Post|
        """

        sio = StringIO.StringIO('')
        p = Post(sio, heapid, postdb)
        sio.close()
        return p

    # Modifications

    def touch(self, touch_postdb=True):
        """Should be called each time after the post is modified.

        See also the :ref:`lazy_data_calculation_pattern` pattern.

        **Arguments:**

        - `touch_postdb` (bool) -- Touch the post database.
        """

        self._modified = True
        self._datetime = hkutils.NOT_SET
        self._meta_dict = None
        if self._postdb is not None and touch_postdb:
            self._postdb.touch(self)

    def is_modified(self):
        """Returns whether the post is modified.

        See also the :ref:`lazy_data_calculation_pattern` pattern.
        """

        return self._modified

    def add_to_postdb(self, heapid, postdb):
        """Adds the post to the `postdb`.

        **Arguments:**

        - `heapid` (|Heapid| | None) -- The post will have this heapid in the
          post database.
        - `postdb` (|PostDB| None) -- The post database to which the post
          should be added.
        """

        assert(self._postdb == None)
        self._heapid = heapid
        self._postdb = postdb
        self.touch()

    # Get-set functions

    def heapid(self):
        """Returns the heapid of the post.

        **Returns:** |Heapid|
        """

        return self._heapid

    # author field

    def author(self):
        """Returns the author of the post.

        **Returns:** str
        """

        return self._header['Author']

    def set_author(self, author):
        """Sets the author of the post.

        **Argument:**

        - `author` (str)
        """

        self._header['Author'] = author
        self.touch()

    # subject field

    def real_subject(self):
        """Returns the real subject of the post as it is stored in the post
        file.

        **Returns:** str
        """

        return self._header['Subject']

    def subject(self):
        """The subject with the "Re:" prefix removed.

        **Returns:** str
        """

        subject = self._header['Subject']
        if re.match('[Rr][Ee]:', subject):
            subject = subject[3:]
        return subject.strip()

    def set_subject(self, subject):
        """Sets the ("real") subject of the post.

        **Argument:**

        - `subject` (str)
        """

        self._header['Subject'] = subject
        self.touch()

    # message id field

    def messid(self):
        """Returns the message id of the post.

        **Returns:** str
        """

        return self._header['Message-Id']

    def set_messid(self, messid):
        """Sets the message id of the post.

        **Argument:**

        - `messid` (|Messageid| | ``None``)
        """

        self._header['Message-Id'] = messid
        self.touch()

    # parent field

    def parent(self):
        """Returns the ``Parent`` attribute of the post.

        **Returns:** |Heapid| | |Messageid| | ``''``
        """

        return self._header['Parent']

    def set_parent(self, parent):
        """Sets the ``Parent`` attribute of the post.

        **Argument:**

        - `parent` (|Heapid| | |Messageid| | ``''``)
        """

        self._header['Parent'] = parent
        self.touch()

    # date field

    def date(self):
        """Returns the ``Date`` attribute of the post.

        **Returns:** str
        """

        return self._header['Date']

    def set_date(self, date):
        """Sets the ``Date`` attribute of the post.

        **Argument:**

        - `date` (str)
        """

        self._header['Date'] = date
        self.touch()

    def timestamp(self):
        """Returns the timestamp of the date of the post.

        If the post does not have a date, 0 is returned.

        **Returns:** int
        """

        date = self.date()
        return hkutils.calc_timestamp(date) if date != '' else 0

    def datetime(self):
        """Returns the datetime object that describes the date of the post.

        If the post does not have a date, ``None`` is returned.

        **Returns:** datetime.datetime | ``None``
        """

        self._recalc_datetime()
        return self._datetime

    def _recalc_datetime(self):
        """Recalculates the `_datetime` attribute.

        See also the :ref:`lazy_data_calculation_pattern` pattern.
        """

        if self._datetime == hkutils.NOT_SET:
            timestamp = self.timestamp()
            if timestamp == 0:
                self._datetime = None
            else:
                self._datetime = datetime.datetime.fromtimestamp(timestamp)

    def date_str(self):
        """Returns the date converted to a string in local time.

        ``hkshell.localtime_fun`` is used to calculate the local time.
        If the post does not have a date, an empty string is returned.

        **Returns:** str
        """

        timestamp = self.timestamp()
        if timestamp == 0:
            return ''
        else:
            return time.strftime('%Y.%m.%d. %H:%M', localtime_fun(timestamp))

    def before(self, *dt):
        """Returns ``True`` if the post predates `dt`.

        Returns ``False`` if the post does not have date. Also returns
        ``False`` if the date of the Post is the given date.

        **Returns:** bool

        **Example:** ::

            >>> p(1).before(2010,1,1)
            True
        """

        return (self.datetime() is not None and
                self.datetime() < datetime.datetime(*dt))

    def after(self, *dt):
        """Returns ``True`` if `dt` predates the post.

        Returns ``True`` if the post does not have date. Also returns
        ``True`` if the date of the Post is the given date.

        This function is the exact opposite of :func:`before`: given `p` post
        and a `dt` datetime, exactly one of `p.before(dt)` and `p.after(dt)` is
        ``True``.

        **Returns:** bool
        """

        return (self.datetime() is None or
                datetime.datetime(*dt) <= self.datetime())

    def between(self, dts, dte):
        """Returns ``True`` if the post's date is between `dts` and `dte`.

        ``post.between(dts, dte)`` is equivalent to
        ``post.after(*dts) and post.before(*dte)``.

        **Returns:** bool
        """

        return self.after(*dts) and self.before(*dte)

    # tag fields

    def tags(self):
        """Returns the tags of the post.

        The returned object should not be modified.

        **Returns:** [str]
        """

        return self._header['Tag']

    def set_tags(self, tags):
        """Sets the ``Tag`` attributes of the post.

        **Argument:**

        - `tags` (iterable)
        """

        self._header['Tag'] = sorted(tags)
        self.touch()

    def add_tag(self, tag):
        assert(isinstance(tag, str))
        if not self.has_tag(tag):
            self._header['Tag'].append(tag)
            self._header['Tag'].sort()
        self.touch()

    def remove_tag(self, tag):
        if self.has_tag(tag):
            self._header['Tag'].remove(tag)
        self.touch()

    def has_tag(self, tag):
        assert(isinstance(tag, str))
        return tag in self._header['Tag']

    def has_tag_from(self, taglist):
        for tag in taglist:
            if self.has_tag(tag):
                return True
        return False

    # flag fields

    def flags(self):
        """Returns the flags of the post.

        The returned object should not be modified.
        """

        return self._header['Flag']

    def set_flags(self, flags):
        assert(isinstance(flags, list))
        self._header['Flag'] = sorted(flags)
        self.touch()

    # reference field

    def refs(self):
        """Returns the references of the post.

        The returned object should not be modified.
        """

        return self._header['Reference']

    def set_refs(self, refs):
        assert(isinstance(refs, list))
        self._header['Reference'] = refs
        self.touch()

    # deletion

    def is_deleted(self):
        return 'deleted' in self._header['Flag']

    def delete(self):
        for key, value in self._header.items():
            if key == 'Message-Id':
                pass
            elif isinstance(value, str):
                self._header[key] = ''
            elif isinstance(value, list):
                self._header[key] = []
            else:
                raise hkutils.HkException, \
                      'Unknown type of field: %s' % (value,)
        self._header['Flag'] = ['deleted']
        self._body = ''
        self.touch()

    # meta field

    def meta_dict(self):
        """Returns the dictionary of meta texts in the post body.

        A meta text is a string or a key-value pair in the posts body. It
        should be enclosed within brackets, and nothing else should be in the
        line in which a meta text is. The key and value of the meta text are
        separated with a colon.

        **Returns:** {str: (str | ``None``)}

        **Examples of meta text:** ::

            [priority low]
            [important]
        """

        self._recalc_meta_dict()
        return self._meta_dict

    def _recalc_meta_dict(self):
        """Recalculates the dictionary of meta texts in the post body."""
        if self._meta_dict is None:
            self._meta_dict = {}
            for line in self.body().split('\n'):
                match = re.match(r'\[ *([^ ]*)( (.*))?\]$', line)
                if match:
                    key = match.group(1).strip()
                    value = match.group(3)
                    if value is not None:
                        value = value.strip()
                    self._meta_dict[key] = value

    # body

    def body(self):
        return self._body

    def set_body(self, body):
        self._body = body.strip() + '\n'
        self.touch()

    def body_contains(self, regexp):
        return re.search(regexp, self._body) != None

    # Parsing and printing

    @staticmethod
    def parse(f):
        """Parses f.

        Arguments:
        f -- A file descriptor. It will not be closed.

        Returns a tuple of a header and a body read from f.
        """

        headers = Post.create_header(Post.parse_header(f))
        body = f.read().strip() + '\n'
        return headers, body

    @staticmethod
    def parse_header(f):
        """Parses the header from f.

        Arguments:
        f -- A file descriptor.

        Returns:
        dict(str, [str]).
        """

        headers = {}
        line = f.readline()
        while line not in ['', '\n']:
            m = re.match('([^:]+): (.*)', line)
            key = m.group(1)
            value = m.group(2)
            line = f.readline()
            while line not in ['', '\n'] and line[0] == ' ':
                line = line.rstrip('\n')
                value += '\n' + line[1:]
                line = f.readline()
            if key not in headers:
                headers[key] = [value]
            else:
                headers[key].append(value)
        return headers

    @staticmethod
    def create_header(d):
        """Transforms the {str: [str])} returned by the parse_header
        function to a {str: (str | [str])} dictionary.

        Strings will be assigned to the 'Author', 'Subject', etc. attributes,
        while dictionaries to the 'Tag' and 'Flag' strings. If an attribute is
        not present in the input, an empty string or an empty list will be
        assigned to it. The list that is assigned to 'Flag' is sorted.
        """

        def copy_one(key, alt_key=None):
            try:
                [value] = d.pop(key, [''])
                if alt_key != None and value == '':
                    [value] = d.pop(alt_key, [''])
            except ValueError:
                raise hkutils.HkException, \
                      ('Multiple "%s" keys.' % key)
            h[key] = value

        def copy_list(key):
            h[key] = d.pop(key, [])

        d = d.copy()
        h = {}
        # TODO the alternate keys can be deleted soon
        copy_one('Author', 'From')
        copy_one('Subject')
        copy_list('Tag')
        copy_one('Message-Id')
        copy_one('Parent', 'In-Reply-To')
        copy_one('Date')
        copy_list('Flag')
        copy_list('Reference')
        h['Tag'].sort()
        h['Flag'].sort()

        # Adding additional keys to the _header and print warning about them
        for attr in d.keys():
            log('WARNING: Additional keys: "%s".' % d)
            copy_list(attr)
        return h

    def write(self, f, force_print=set()):
        """Writes the post to a stream.

        **Arguments*:

        - `f` (|Writable|) -- The output stream.
        - `force_print` (set(str)) -- The attributes in this set will be
          printed even if they are empty strings.
        """

        def write_attr(key, value):
            """Writes an attribute to the output."""

            # Remove this attribute from the set of unprinted attributes, since
            # it is being printed now.
            unprinted_attrs.discard(key)

            t = (key, re.sub(r'\n', r'\n ', value))
            f.write('%s: %s\n' % t)

        def write_str(attr):
            """Writes a string attribute to the output."""
            if (self._header.get(attr, '') != '') or (attr in force_print):
                write_attr(attr, self._header[attr])

        def write_list(attr):
            """Writes a list attribute to the output."""
            for line in self._header.get(attr, []):
                write_attr(attr, line)

        unprinted_attrs = set(self._header.keys())

        write_str('Author')
        write_str('Subject')
        write_list('Tag')
        write_str('Message-Id')
        write_str('Parent')
        write_list('Reference')
        write_str('Date')
        write_list('Flag')

        # We print all other attributes that have not been printed yet
        for attr in sorted(unprinted_attrs):
            write_list(attr)

        f.write('\n')
        f.write(self._body)

    def postfile_str(self, force_print=set()):
        """Returns a string that contains the post in post file format.

        **Returns:** str
        """

        sio = StringIO.StringIO()
        self.write(sio, force_print)
        s = sio.getvalue()
        sio.close()
        return s

    def save(self):
        assert(self._postdb != None)
        if self._modified:
            with open(self.postfilename(), 'w') as f:
                self.write(f)
                self._modified = False

    def load(self, silent=False):
        """(Re)loads the Post from the disk.

        Arguments:
        silent --- Do not call postdb.touch.
        """

        # Parsing the post file and returning if it is the same as the post
        # object
        with open(self.postfilename(), 'r') as f:
            header, body = Post.parse(f)
        if header == self._header and body == self._body:
            return

        self._header, self._body = header, body
        self.touch(touch_postdb=(not silent))

    # Filenames

    def postfilename(self):
        """The name of the postfile in which the post is (or can be) stored."""
        assert(self._postdb != None)
        return os.path.join(self._postdb.postfile_dir(), \
                            self._heapid + '.post')

    def htmlfilebasename(self):
        """The base name of the HTML file that can be generated from the
        post."""
        return self._heapid + '.html'

    def htmlfilename(self):
        """The name of the HTML file that can be generated from the post."""
        assert(self._postdb != None)
        return os.path.join(self._postdb.html_dir(), self._heapid + '.html')

    def htmlthreadbasename(self):
        """The base name of the HTML file that can be generated from the
        thread."""
        assert(self._postdb.parent(self) == None)
        return os.path.join('thread_' + self._heapid + '.html')

    def htmlthreadfilename(self):
        """The name of the HTML file that can be generated from the thread."""
        return os.path.join(self._postdb.html_dir(), self.htmlthreadbasename())

    def postfile_exists(self):
        if self._postdb == None:
            return False
        else:
            return os.path.exists(self.postfilename())

    # Python operators

    def __eq__(self, other):
        if isinstance(other, Post):
            return self._header == other._header and \
                   self._body == other._body
        else:
            return False

    def __lt__(self, other):
        """Determines the order of posts.

        The following method should be used to decide whether post1 or post2
        is greater:

        - If both of them have a timestamp and these are not equal, the post
          with the later timestamp is greater.
        - Otherwise the post with the greater heapid is the greater.

        **Arguments:**

        - `other` (|Post|) -- The post to compare this to

        **Returns:** bool
        """

        assert(isinstance(other, Post))
        this_dt = self.datetime()
        other_dt = other.datetime()
        if this_dt and other_dt:
            if this_dt < other_dt:
                return True
            elif this_dt > other_dt:
                return False
        return self.heapid() < other.heapid()

    def __repr__(self):
        return "<post '" + self._heapid + "'>"

    # Misc

    def remove_google_stuff(self):
        # old footer
        r = re.compile(r'--~--~---------~--~----~------------~-------~--~' + \
                       r'----~\n.*?\n' + \
                       r'-~----------~----~----~----~------~----~------~-' + \
                       r'-~---\n', re.DOTALL)
        self.set_body(r.sub('', self.body()))

        # new footer (since November 2009)
        footer_str = \
            (r'^--\s*'
              '^You received this message because you are subscribed to.*')
        footer_re = re.compile(footer_str, re.DOTALL | re.MULTILINE)
        self.set_body(footer_re.sub('', self.body()))
        self.set_body(self.body().strip() + '\n')

    def remove_newlines_from_subject(self):
        """Removes newlines from the subject.

        The newline characters are removed together with the whitspace
        characters surrounding them, and they are replaced with one space.
        """

        r = re.compile(r'\n', re.MULTILINE)
        match = r.search(self.subject())
        if match is None:
            return # not a multiline subject
        else:
            r = re.compile(r'\s*\n\s*', re.MULTILINE)
            new_subject = r.sub(' ', self.subject())
            self.set_subject(new_subject)

    @staticmethod
    def parse_subject(subject):
        """Parses the subject.

        Parses the tags and removes the "Re:" prefix and whitespaces.
        Returns: (subject:str, tags:[str])
        """

        # last_bracket==None  <=>  we are outside of a [tag]
        last_bracket = None
        brackets = []
        i = 0
        while i < len(subject):
            c = subject[i]
            if c == '[' and last_bracket == None:
                last_bracket = i
            elif c == ']' and last_bracket != None:
                brackets.append((last_bracket, i))
                last_bracket = None
            elif c != ' ' and last_bracket == None:
                break
            i += 1

        real_subject = subject[i:]
        if re.match('[Rr]e:', subject):
            subject = subject[3:]
        real_subject = real_subject.strip()

        tags = [ subject[first+1:last].strip() for first, last in brackets ]
        return real_subject, tags

    def normalize_subject(self):
        """Removes the tags from the subject and adds them to the Post as real
        tags.

        Also removes the "Re:" prefix and whitespaces."""

        real_subject, tags = Post.parse_subject(self.subject())
        self.set_subject(real_subject)
        for tag in tags:
            self._header['Tag'].append(tag)


##### PostDBEvent #####

class PostDBEvent(object):
    """Represents an event.

    Data attributes:
    type --- The type of the event. Currently always 'touch'.
        Type: str
    post --- The post which was touched.
        Type: Post | None
    """

    def __init__(self,
                 type=hkutils.NOT_SET,
                 post=None):

        super(PostDBEvent, self).__init__()
        hkutils.set_dict_items(self, locals())

    def __str__(self):
        s = '<PostDBEvent with the following attributes:'
        for attr in ['type', 'post']:
            s += '\n%s = %s' % (attr, getattr(self, attr))
        s += '>'
        return s


##### PostDB #####

class PostDB(object):

    """The post database that stores and handles the posts.

    Data attributes:
    heapid_to_post -- Stores the posts assigned to their heapid-s.
        Type: dict(str, Post)
    messid_to_heapid -- Stores which messid and heapid belong together.
        Type: dict(str, str)
    _postfile_dir -- The directory that contains the post files.
        Type: str
    _html_dir -- The directory that contains the generated HTML files.
        Type: str
    _next_heapid -- A dictionary to assign the next free heapid to prefixes.
        This is part of a caching mechanism. If a prefix is not found here, the
        whole lookup procedure is performed, then the results are added to this
        dictionary. The next free heapid for a prefix is a number for which
        numbers in all other heapids with this prefix are smaller.
        Type: {str: str}
    _posts -- All non-deleted posts.
        Type: None | [Post()]
    _all -- All posts in a PostSet. It can be asked with all().
        Type: None | PostSet.
    _threadstruct -- Assigns the posts to a p post that are replies to p.
        Posts that are not replies to any existing post will be assigned to
        None.
        It can be asked with threadstruct().
        If it is None, then it should be recalculated when needed.
        Type: None | dict(None | heapid, [heapid])
    _cycles -- Posts that are in a cycle in the thread structure.
        These posts will not be iterated by the iter_thread function.
        Type: None | PostSet
    """

    # Constructors

    def __init__(self, postfile_dir, html_dir):
        """Constructor.

        Arguments:
        postfile_dir: Initialises self._postfile_dir.
        html_dir: Initialises self._html_dir.
        """

        super(PostDB, self).__init__()
        self._postfile_dir = postfile_dir
        self._html_dir = html_dir
        self._next_heapid = {}
        self.heapid_to_post = {}
        self.messid_to_heapid = {}
        self.listeners = []

        self._load_from_disk()

    @staticmethod
    def from_config(config):
        """Creates a PostDB with the given configuration.

        If either of post and HTML directories do not exist, it will be
        created, but a warning will be logged.

        Arguments:
        config -- Configuration object. The paths/mail and paths/html options
            will be read.
            Type: ConfigParser
        """

        postfile_dir = config.get('paths', 'mail')
        if not os.path.exists(postfile_dir):
            log('Warning: post directory does not exists: "%s"' %
                (postfile_dir,))
            os.mkdir(postfile_dir)
            log('Post directory has been created.')

        html_dir = config.get('paths', 'html')
        if not os.path.exists(html_dir):
            log('Warning: HTML directory does not exists: "%s"' %
                (html_dir,))
            os.mkdir(html_dir)
            log('HTML directory has been created.')

        return PostDB(postfile_dir, html_dir)

    def _load_from_disk(self):
        """Loading the database from the disk."""

        # We need the original_heapid_to_post when reloading the post database.
        original_heapid_to_post = self.heapid_to_post

        self.heapid_to_post = {}
        self.messid_to_heapid = {}

        for file in os.listdir(self._postfile_dir):
            if file.endswith('.post'):
                heapid = file[:-5]
                absname = os.path.join(self._postfile_dir, file)

                # We try to obtain the post which has the heapid 'heapid'. If
                # such a post exists (i.e. original_heapid_to_post contains
                # 'heapid'), the post should be reloaded from the disk. This
                # way, if someone has a reference to post object, they will
                # refer to the reloaded posts. If there is no post with
                # 'heapid', a new Post object should be created.
                post = original_heapid_to_post.get(heapid, None)
                if post == None:
                    post = Post.from_file(absname, heapid, self)
                else:
                    post.load(silent=True)
                self._add_post_to_dicts(post)

        self._next_heapid = {}
        self.touch()

    # Modifications

    def notify_listeners(self, event):
        for listener in self.listeners:
            listener(event)

    def touch(self, post=None):
        """If something in the database changes, this function should be
        called.

        If a post in the database is changed, this function will be invoked
        automatically, so there is no need to call it again.
        """

        self._posts = None
        self._all = None
        self._threadstruct = None
        self._cycles = None
        self._roots = None
        self._threads = None
        if post != None:
            self.notify_listeners(PostDBEvent(type='touch', post=post))

    # Get-set functions

    def heapids(self):
        return self.heapid_to_post.keys()

    def next_heapid(self, prefix=''):
        """Return the next heapid with the form ``prefix + int``.

        The "next" here means the heapid with smallest number which is larger
        than all numbers present in all other heapids with the given prefix.

        This function uses a caching mechanism to avoid iterating over all
        posts on each calling. This cache is the `_next_heapid` data member,
        a dictionary where the keys are the prefixes. The empty prefix is
        always cached, while other prefixes are cached after the first lookup.

        **Arguments**:

        - `prefix` (str) -- The prefix of the new heapid.

        **Returns**: str
        """

        cache = self._next_heapid

        if cache.has_key(prefix):
            next = cache[prefix]
            cache[prefix] += 1
            return prefix + str(next)
        else:
            matches = filter(lambda x: x.startswith(prefix), self.heapids())
            numbers = []
            for match in matches:
                number_str = match[len(prefix):]
                try:
                    numbers.append(int(number_str))
                except ValueError:
                    pass
            try:
                next_number = max(numbers) + 1
            except ValueError:
                next_number = 1
            cache[prefix] = next_number + 1
            return prefix + str(next_number)

    def posts(self):
        """Returns the list of all posts that are not deleted.

        The object returned by this function should not be modified.
        """

        self._recalc_posts()
        return self._posts

    def postset(self, posts):
        """Creates a PostSet that will contain the specified posts.

        See the type of the posts argument at :func:`PostSet.__init__`.
        """

        return PostSet(self, posts)

    def _recalc_posts(self):
        """Recalculates the _posts variable if needed."""
        if self._posts == None:
            self._posts = \
                [ p for p in self.real_posts() if not p.is_deleted() ]

    def real_posts(self):
        """Returns the list of all posts, even the deleted ones."""
        return self.heapid_to_post.values()

    def post(self, heapid, raiseException=False):
        """Returns the post specified by its heapid.

        The raiseException argument specifies what should happen it the post is
        not found. If raiseException is false, None will be returned, otherwise
        a KeyError exception will be raised.
        """

        if isinstance(heapid, int):
            heapid = str(heapid)
        if raiseException:
            return self.heapid_to_post[heapid]
        else:
            return self.heapid_to_post.get(heapid)

    def post_by_messid(self, messid):
        try:
            return self.post(self.messid_to_heapid[messid])
        except KeyError:
            return None

    # Save, reload

    def save(self):
        """Saves all the posts that needs to be saved."""
        for post in self.heapid_to_post.values():
            post.save()

    def reload(self):
        """Reloads the database from the disk.

        The unsaved changes will be abandoned.
        """

        self._load_from_disk()

    # New posts

    def add_new_post(self, post, heapid=None, prefix=''):
        """Adds a new post to the postdb.

        The heapid of the post will be changed to the next free heapid of the
        postdb.

        **Arguments:**

        - `post` (|Post|) -- The post to be added to the database.
        - `heapid` (str | ``None``) -- The post should have this heapid.
          If ``None``, the post should get the next free heapid that starts
          with `prefix`.
        - `prefix` (str) -- If `heapid` is ``None``, the post should get the
          next free heapid that starts with `prefix`.
        """

        if heapid == None:
            heapid = self.next_heapid(prefix=prefix)
        post.add_to_postdb(heapid, self)
        self._add_post_to_dicts(post)
        return post

    def _add_post_to_dicts(self, post):
        """Adds the post to the heapid_to_post and messid_to_heapid
        dictionaries. """
        heapid = post.heapid()
        self.heapid_to_post[heapid] = post
        if post.messid() != '':
            self.messid_to_heapid[post.messid()] = heapid

    # All posts

    def all(self):
        """Returns the PostSet of all posts that are not deleted.

        The object returned by this function should not be modified.
        On the other hand, the posts contained by it can be modified.
        """

        self._recalc_all()
        return self._all

    def _recalc_all(self):
        if self._all == None:
            self._all = PostSet(self, self.posts())

    # Thread structure

    def threadstruct(self):
        """Returns the calculated _threadstruct.

        The object returned by this function should not be modified.
        """

        self._recalc_threadstruct()
        return self._threadstruct

    def parent(self, post):
        """Returns the parent of the given post.

        If there is no such post in the database, it returns None
        """

        assert(post in self.all())
        postparent = post.parent()

        if postparent == '':
            return None

        else:

            # try to get the parentpost by messid
            parentpost = self.post_by_messid(postparent)

            # try to get the parentpost by heapid
            if parentpost == None:
                parentpost = self.post(postparent)

            # deleted posts do not count
            if parentpost != None and parentpost.is_deleted():
                parentpost = None

            return parentpost

    def root(self, post):
        """Returns the root of the post.

        **Argument:**

        - `post` (|Post|)

        **Returns:** |Post| | ``None`` -- ``None`` is returned when the post
        is in a cycle.
        """

        assert(post in self.all())
        posts = set([post])
        while True:
            parentpost = self.parent(post)
            if parentpost == None:
                return post
            elif parentpost in posts:
                return None # we found a cycle
            else:
                posts.add(parentpost)
                post = parentpost

    def children(self, post, threadstruct=None):
        """Returns the children of the given post.

        If 'post' is None, returns the posts with no parents (i.e. whose
        parent is None).

        Arguments:
        post ---
            Type: Post | None
        threadstruct ---

        Returns: [Post]
        """

        assert(post == None or post in self.all())

        if threadstruct is None:
            threadstruct = self.threadstruct()

        if post == None:
            children_heapids = threadstruct.get(None, [])
        else:
            children_heapids = threadstruct.get(post.heapid(), [])

        # This assertion can catch nasty bugs when the thread structure
        # contains a string as a value instead of a list.
        assert(isinstance(children_heapids, list))

        return [ self.post(heapid) for heapid in children_heapids ]

    def _recalc_threadstruct(self):
        """Recalculates the _threadstruct variable if needed."""

        if self._threadstruct == None:

            def add_timestamp(post):
                """Creates a (timestamp, heapid) pair from the post."""
                return (post.timestamp(), post.heapid())

            threads = {None: []} # dict(heapid, [answered:(timestamp, heapid)])
            for post in self.posts():
                parentpost = self.parent(post)
                parent_heapid = \
                    parentpost.heapid() if parentpost != None else None
                if parent_heapid in threads:
                    threads[parent_heapid].append(add_timestamp(post))
                else:
                    threads[parent_heapid] = [add_timestamp(post)]
            t = {}
            for heapid in threads:
                threads[heapid].sort()
                t[heapid] = \
                    [ heapid2 for timestamp, heapid2 in threads[heapid] ]
            self._threadstruct = t

    def iter_thread(self, post, threadstruct=None):
        """Iterates over a thread.

        The first element of the thread will be the post (except when the post
        is None, which will not be yielded). All the consequenses of post will
        be yielded in a preorder way. An example:
            1 <- 2 <- 3
              <- 4
            5
        The posts will be yielded in the following order: 1, 2, 3, 4, 5.

        The posts can be modified during the iteration.
        """

        assert(post in self.all() or post == None)
        if post != None:
            yield post
        heapid = post.heapid() if post != None else None
        if threadstruct == None:
            threadstruct = self.threadstruct()
        for ch_heapid in threadstruct.get(heapid, []):
            for post2 in self.iter_thread(self.post(ch_heapid), threadstruct):
                yield post2

    def walk_thread(self, root, threadstruct=None, yield_main=False):
        """Walks a thread and yields its posts.

        **Argument:**

        - `root` (|Post| | ``None``) -- The root of the thread to be walked. If
          ``None``, the whole thread structure is walked.
        - `threadstruct` ({(``None`` | |Heapid|): |Heapid|} | ``None``) -- The
          thread structure to be used. If ``None``, the thread structure of the
          post database will be used.

        **Returns:** iterable(|PostItem|)

        `walk_thread` walks the thread indicated by `root` with deep walk and
        yields |PostItem| objects. A post item contains a post and some
        additional information.

        The post item contains the post's position, which can be ``begin`` or
        ``end``. Each post is yielded twice during the walk. When the deep walk
        enters the subthread of a post, the post is yielded with ``begin``
        position. When the deep walk leaves its subthread, it is yielded with
        ``end`` position.

        The post item also contains the level of the post. The level of the
        root post is 0, the level of its children is 1, etc. When the `root`
        argument is ``None`` and the whole database is walked, the level of all
        root posts is 0.

        **Example:**

        The thread structure walked::

            0 <- 1 <- 2
              <- 3
            4

        The post items yielded (indentation is there only to help the human
        reader)::

            <PostItem: pos=begin, heapid='0', level=0>
              <PostItem: pos=begin, heapid='1', level=1>
                <PostItem: pos=begin, heapid='2', level=2>
                <PostItem: pos=end, heapid='2', level=2>
              <PostItem: pos=end, heapid='1', level=1>
              <PostItem: pos=begin, heapid='3', level=1>
              <PostItem: pos=end, heapid='3', level=1>
            <PostItem: pos=end, heapid='0', level=0>
            <PostItem: pos=begin, heapid='4', level=0>
            <PostItem: pos=end, heapid='4', level=0>
        """

        # `stack` is initialized with "beginning" `PostItem`s (i.e.
        # ``item.pos == 'begin'``).
        # During the execution of the loop:
        #  - the stack is popped,
        #  - whatever we got, we yield it,
        #  - if it is a beginning `PostItem`, we push the matching ending
        #    `PostItem`
        #  - then push a beginning `PostItem` for all the children of the
        #    popped item's post
        # This means that we will yield the ending `PostItem` once all the
        # children (and their children etc.) are processed.

        assert(root in self.all() or root == None)

        if root is None:
            roots = [ PostItem(pos='begin', post=root, level=0)
                      for root in self.children(None, threadstruct) ]
            stack = list(reversed(roots))
        else:
            stack = [ PostItem(pos='begin', post=root, level=0) ]

        while len(stack) > 0:

            postitem = stack.pop()
            yield postitem

            if postitem.pos == 'begin':

                if yield_main:
                    postitem_main = postitem.copy()
                    postitem_main.pos = 'main'
                    yield postitem_main

                # pushing the closing pair of postitem into the stack
                postitem_end = postitem.copy()
                postitem_end.pos = 'end'
                stack.append(postitem_end)

                # pushing the children of the post into the stack
                new_level = postitem.level + 1
                child_postitems = \
                    [ PostItem(pos='begin', post=child, level=new_level)
                      for child in self.children(postitem.post, threadstruct) ]
                stack += reversed(child_postitems)

    def cycles(self):
        """Returns the posts that are in a cycle of the thread structure.

        Returns: PostSet
        """

        self._recalc_cycles()
        return self._cycles

    def has_cycle(self):
        """Returns whether there is a cycle in the thread structure."""
        return len(self.cycles()) != 0

    def _recalc_cycles(self):
        if self._cycles == None:
            self._cycles = self.all().copy()
            # A post is in a cycle <=> it cannot be accessed by iter_thread
            for post in self.iter_thread(None):
                self._cycles.remove(post)

    def walk_cycles(self):
        """Walks and yields post items for the posts in cycles.

        The ``pos`` attribute of the post items will be ``'flat'``. The
        ``level`` attribute will be 0.

        **Returns:** iterable(|PostItem|)
        """

        for post in self.cycles().sorted_list():
            yield PostItem(pos='flat', post=post, level=0)

    def roots(self):
        self._recalc_roots()
        return self._roots

    def _recalc_roots(self):
        if self._roots == None:
            self._roots = [ self.post(heapid)
                            for heapid in self.threadstruct()[None] ]

    def threads(self):
        self._recalc_threads()
        return self._threads

    def _recalc_threads(self):
        if self._threads == None:
            self._threads = {}
            for root in self.roots():
                self._threads[root] = self.postset(root).expf()

    # Filenames

    def postfile_dir(self):
        return self._postfile_dir

    def html_dir(self):
        return self._html_dir


class PostItem(object):

    """Represents a post when performing walk on posts.

    Used for example by |PostDB.walk_thread|. For information about what
    exactly the values of the data attributes will be during a walk, please
    read the documenation of the function that performs the walk.

    **Data attributes:**

    - `pos` (str) -- The position of the post item. Possible values:
      ``'begin'``, ``'end'``, ``'flat'``.
    - `post` (Post) -- The post represented by the post item.
    - `level` (int) -- The level of the post.
    """

    def __init__(self, pos, post, level=0):
        """Constructor.

        **Arguments:**

        - `pos` (str) -- Initializes the `pos` data attribute.
        - `post` (Post) -- Initializes the `post` data attribute.
        - `level` (int) -- Initializes the `level` data attribute.
        """

        assert(pos in ['begin', 'end', 'main', 'flat'])
        self.pos = pos
        self.post = post
        self.level = level

    def copy(self):
        """Creates a shallow copy of the post item."""
        p = PostItem(pos=self.pos,
                     post=self.post,
                     level=self.level)
        p.__dict__ = self.__dict__.copy()
        return p

    def __str__(self):
        """Returns the string representation of the PostItem.

        **Returns:** str

        Example: ``<PostItem: pos=begin, heapid='42', level=0>``
        """

        if self.post.heapid() is None:
            heapid_str = None
        else:
            heapid_str = "'%s'" % (self.post.heapid(),)

        s = ('<PostItem: pos=%s, heapid=%s, level=%d' %
             (self.pos, heapid_str, self.level))
        attrs = self.__dict__.copy()
        del attrs['pos']
        del attrs['post']
        del attrs['level']

        for attr, value in attrs.items():
             s += ', %s=%s' % (attr, value)

        s += '>'
        return s

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


##### PostSet #####

class PostSet(set):

    """A set of posts.

    Data attributes:
    _postdb -- Mail database.
        Type: PostDB
    """

    def __init__(self, postdb, posts):
        """Constructor.

        Arguments:
        postdb -- Initialises self._postdb.
            Type: PostDB
        posts -- Initialises the set.
            Type: PrePostSet
        """

        super(PostSet, self).__init__(PostSet._to_set(postdb, posts))
        self._postdb = postdb

    def empty_clone(self):
        """Returns an empty PostSet that has the same PostDB as this one."""
        return PostSet(self._postdb, [])

    def copy(self):
        """Copies the object.

        The PostSet objects will be different, but the Posts will be the same
        objects.
        """

        return PostSet(self._postdb, self)

    @staticmethod
    def _to_set(postdb, prepostset):
        """Converts a PrePostSet object to a set of Posts.

        Arguments:
        prepostset -- The PrePostSet to be converted.
            Type: PrePostSet

        Returns: set(Post)
        """

        if isinstance(prepostset, PostSet):
            return prepostset
        elif isinstance(prepostset, str) or \
             isinstance(prepostset, int) or \
             isinstance(prepostset, Post):
            return PostSet._to_set(postdb, [prepostset])
        else:
            result = set()
            for prepost in prepostset:
                # calculating the post for prepost
                if isinstance(prepost, str) or isinstance(prepost, int):
                    # prepost is a heapid
                    post = postdb.post(prepost, True)
                elif isinstance(prepost, Post): # prepost is a Post
                    post = prepost
                elif prepost == None: # prepost is None
                    continue
                else:
                    raise hkutils.HkException, \
                          ("Object type not compatible with Post: %s" % \
                           (prepost,))
                result.add(post)
            return result

    def is_set(self, s):
        """The given set equals to the set of contained posts."""
        return set.__eq__(self, PostSet._to_set(self._postdb, s))

    def __getattr__(self, funname):
        if funname == 'forall':
            return PostSetForallDelegate(self)
        if funname == 'collect':
            return PostSetCollectDelegate(self)
        else:
            raise AttributeError, \
                  ("'PostSet' object has no attribute '%s'" % funname)

    def expb(self):
        """Expand backwards: returns all causes of the posts in PostSet.

        Returns: PostSet
        """

        result = PostSet(self._postdb, [])
        for post in self:
            # if post is in result, then it has already been processed
            # (and all its consequences has been added to result)
            if post not in result:
                while True:
                    result.add(post)
                    post = self._postdb.parent(post)
                    if post == None:
                        break
        return result

    def expf(self):
        """Expand forward: Returns all consequenses of the PostSet.

        Returns: PostSet
        """

        result = PostSet(self._postdb, [])
        for post in self:
            # if post is in result, then it has already been processed
            # (and all its consequences has been added to result)
            if post not in result:
                for post2 in self._postdb.iter_thread(post):
                    result.add(post2)
        return result

    def exp(self):
        return self.expb().expf()

    def sorted_list(self):
        """Returns the sorted list of posts contained in the postset.

        **Returns:** ``[Post]`` - the sorted list
        """

        posts = list(self)
        posts.sort()
        return posts

    # Overriding set's methods

    def construct(self, methodname, other):
        """Constructs a new PostSet from self by calling the specified method
        of the set class with the specified arguments."""
        try:
            other = PostSet(self._postdb, other)
        except TypeError:
            return NotImplemented
        result = getattr(set, methodname)(self, other)
        result._postdb = self._postdb
        return result

    def __and__(self, other):
        return self.construct('__and__', other)

    def __eq__(self, other):
        if isinstance(other, PostSet):
            return set.__eq__(self, other)
        else:
            return False

    def __ne__(self, other):
        return not self == other

    def __or__(self, other):
        return self.construct('__or__', other)

    def __sub__(self, other):
        return self.construct('__sub__', other)

    def __xor__(self, other):
        return self.construct('__xor__', other)

    def difference(self, other):
        return self.construct('difference', other)

    def intersection(self, other):
        return self.construct('intersection', other)

    def symmetric_difference(self, other):
        return self.construct('symmetric_difference', other)

    def union(self, other):
        return self.construct('union', other)

    def __rand__(self, other):
        return self.construct('__rand__', other)

    def __ror__(self, other):
        return self.construct('__ror__', other)

    def __rsub__(self, other):
        return self.construct('__rsub__', other)

    def __rxor__(self, other):
        return self.construct('__rxor__', other)

    # Methods inherited from set.
    #
    # These functions does not have to be overriden, because they do not
    # construct a new PostSet object (as opposed to most of the overriden
    # functions).
    #
    # __contains__(...)
    # __iand__(...)
    # __ior__(...)
    # __isub__(...)
    # __ixor__(...)
    # __iter__(...)
    # __len__(...)
    # add(...)
    # clear(...)
    # difference_update(...)
    # discard(...)
    # intersection_update(...)
    # issubset(...)
    # issuperset(...)
    # pop(...)
    # remove(...)
    # symmetric_difference_update(...)
    # update(...)

    #  Methods inherited from set which should not be used (yet?)
    #
    # TODO: These method should be reviewed whether they should be inherited,
    # overriden or removed.
    #
    # __cmp__(...)
    # __ge__(...)
    # __getattribute__(...)
    # __gt__(...)
    # __hash__(...)
    # __le__(...)
    # __lt__(...)
    # __reduce__(...)
    # __repr__(...)


class PostSetForallDelegate(object):

    """A delegate of posts.

    If a method is called on a PostSetForallDelegate object, it will forward
    the call to the posts it represents.
    A PostSetForallDelegate object can be asked from a PostSet via its "forall"
    attribute.

    Data attributes:
    _postset -- The PostSet which is represented.
        Type: PostSet
    """

    def __init__(self, postset):
        """Constructor.

        Arguments:
        postset -- Initialises _postset.
            Type: PostSet
        """

        super(PostSetForallDelegate, self).__init__()
        self._postset = postset

    def __call__(self, forallfun):
        """Performs forallfun on each post."""
        for post in self._postset:
            forallfun(post)

    def __getattr__(self, funname):
        """Returns a function that calls the "funname" method of all the posts
        in postset when called with the given arguments."""
        def forall_fun(*args, **kw):
            for post in self._postset:
                getattr(post, funname)(*args, **kw)
        return forall_fun


class PostSetCollectDelegate(object):

    """A delegate of posts.

    It can be used to collect posts with a specified property from a PostSet.
    A PostSetCollectDelegate object can be asked from a PostSet via its
    "collect" attribute.

    Collecting posts can be done in three ways:

    1. The PostSetCollectDelegate class has some functions that collect
       specific posts.

       The following example collects the posts that are roots of a thread
       ("collect" is a PostSetCollectDelegate object):

           ps = collect.is_root()

    2. If a method is called on a PostSetCollectDelegate object which is not
       a method of the PostSetCollectDelegate class, the object will invoke the
       given method with the given arguments on all the posts of the postset,
       and returns those in a new postset whose method returned true.

       An example that collects the posts that has 'mytag' tag:

            ps = collect.has_tag('mytag')

    3. The user can call the PostSetCollectDelegate object with any function as
       an argument that gets a Post and returns a boolean.

       An example that collects the posts that has 'mytag' tag but does not
       have 'other_tag' tag:

            ps = collect(lambda p: p.has_tag('mytag') and \\
                                   not p.has_tag('other_tag'))

    Data attributes:
    _postset -- The PostSet which is represented.
        Type: PostSet
    """

    def __init__(self, postset):
        """Constructor.

        Arguments:
        postset -- Initialises _postset.
            Type: PostSet
        """

        super(PostSetCollectDelegate, self).__init__()
        self._postset = postset

    def __call__(self, filterfun):
        """Returns posts with which filterfun returns true."""
        result = self._postset.empty_clone()
        for post in self._postset:
            post_true = filterfun(post)
            assert(isinstance(post_true, bool))
            if post_true:
                result.add(post)
        return result

    def is_root(self):
        """Returns the posts that are roots of a thread."""
        return self.__call__(lambda p: self._postset._postdb.parent(p) == None)

    def __getattr__(self, funname):
        """Returns a function that collects posts whose return value is true
        when their "funname" method is called with the given arguments."""
        def collect_fun(*args, **kw):
            return self.__call__(lambda p: getattr(p, funname)(*args, **kw))
        return collect_fun


##### EmailDownloader #####

class EmailDownloader(object):

    """A EmailDownloader object can be used to connect to the server and
    download new posts.

    Data attributes:
    _postdb -- The post database..
        Type: PostDB
    _config -- The configuration.
        Type: ConfigParser
    _server -- The object that represents the IMAP server.
        Type: imaplib.IMAP4_SSL | NoneType

    **Reading:**

    - RFC2822 - Internet Message Format
    - RFC3501 - INTERNET MESSAGE ACCESS PROTOCOL - VERSION 4rev1
    - http://en.wikipedia.org/wiki/MIME#Multipart_messages
    """

    def __init__(self, postdb, config):
        """Constructor.

        Arguments:
        postdb: Initialises self._postdb.
        config: Initialises self._config.
        """

        super(EmailDownloader, self).__init__()
        self._postdb = postdb
        self._config = config
        self._server = None

    def connect(self):
        """Connects to the IMAP server."""

        log('Reading settings...')
        host = self._config.get('server', 'host')
        port = int(self._config.get('server', 'port'))
        username = self._config.get('server', 'username')
        password = self._config.get('server', 'password')
        log('Connecting...')
        self._server = imaplib.IMAP4_SSL(host, port)
        self._server.login(username, password)
        log('Connected')

    def close(self):
        """Closes the connection with the IMAP server."""

        self._server.close()
        self._server = None

    @staticmethod
    def parse_email(header, text):
        """Creates strings from an already downloaded email header and
        body part.

        Arguments:
        header -- The header of the email.
            Type: string
        text -- The body of the email.
            Type: string
        """

        message = email.message_from_string(header + text)

        # processing the header
        headers = {}
        for attr in ['From', 'Subject', 'Message-Id', 'In-Reply-To', 'Date']:
            value = message[attr]
            if value != None:
                # valuelist::[(string, encoding)]
                valuelist = email.header.decode_header(value)
                value = ''
                first = True
                for v in valuelist:
                    if first:
                        first = False
                    else:
                        value += ' '
                    value += hkutils.utf8(v[0], v[1])
                value = re.sub(r'\r\n',r'\n',value)
                headers[attr] = value

        # We find the first leaf of the "message tree", where the multipart
        # messages are the branches and the non-multipart messages are the
        # leaves. This leaf should has the content type text/plain. When the
        # loop is finished, the `message` variable will point to the leaf that
        # is interesting to Heapkeeper.
        #
        # See also http://en.wikipedia.org/wiki/MIME#Multipart_messages
        while True:
            content_type = message.get_content_type()
            if message.is_multipart():
                if (content_type not in
                    ('multipart/mixed', 'multipart/alternative')):
                    log('WARNING: unknown type of multipart message: %s\n%s' %
                        (content_type, header + text))
                message = message.get_payload(0)
            else:
                if content_type != 'text/plain':
                    log('WARNING: content type is not text/plain: %s\n%s' %
                        (content_type, header + text))
                break

        # encoding
        encoding = message['Content-Transfer-Encoding']
        text = message.get_payload()
        if type(text) is not str:
            raise hkutils.HkException(
                '`text` is not a string but the following object: %s\n' %
                (str(text),))
        if encoding != None:
            if encoding.lower() == '7bit':
                pass # no conversion needed
            elif encoding.lower() == 'base64':
                text = base64.b64decode(text)
            elif encoding.lower() == 'quoted-printable':
                text = quopri.decodestring(text)
            else:
                log('WARNING: Unknown encoding, skipping decoding: %s\n'
                    'text:\n%s\n' % (encoding, text))
        charset = message.get_content_charset()
        text = hkutils.utf8(text, charset)
        text = re.sub(r'\r\n',r'\n',text)

        return headers, text

    def create_post_from_email(self, header, text):
        """Create a Post from an already downloaded email header and
        body part.

        Arguments:
        header -- The header of the email.
            Type: string
        text -- The body of the email.
            Type: string
        """

        headers, text = self.parse_email(header, text)
        post = Post.create_empty()
        post.set_author(headers.get('From', ''))
        post.set_subject(headers.get('Subject', ''))
        post.set_messid(headers.get('Message-Id', ''))
        post.set_parent(headers.get('In-Reply-To', ''))
        post.set_date(headers.get('Date', ''))
        post.set_body(text)
        post.remove_google_stuff()
        post.remove_newlines_from_subject()
        post.normalize_subject()

        if self._config.has_section('nicknames'):
            for entry, author_regex in self._config.items('nicknames'):
                [author, regex] = \
                    self._config.get('nicknames', entry).split(' ',1)
                if re.search(regex, post.author()) != None:
                    post.set_author(author)
                    break

        return post

    def download_new(self, lower_value=0, detailed_log=False):
        """Downloads the new emails from the INBOX of the IMAP server and adds
        them to the post database.

        **Arguments:**

        - `lower_value` (int): only the email indices that are greater or equal
          to `lower_value` are examined.
        - `detailed_log` (bool): if ``True``, every email found or downloaded
          is reported.

        **Returns:** |PostSet| -- a set of the new posts
        """

        self._server.select("INBOX")
        result = self._server.search(None, '(ALL)')[1][0].strip()
        if result == '':
            log('Message box is empty.')
            return
        all_emails = result.split(' ')

        emails = [ em for em in all_emails if int(em) >= lower_value ]
        emails_imap = ','.join(emails)

        log('Checking...')

        result = self._server.fetch(emails_imap,
                                    '(BODY[HEADER.FIELDS (MESSAGE-ID)])')[1]
        raw_messids = [ result[2 * i][1] for i in range(len(emails)) ]
        messids = [ email.message_from_string(s)['Message-Id']
                    for s in raw_messids ]

        # assembling a list of new messages
        download_list = []
        for index, messid in zip(emails, messids):
            post = self._postdb.post_by_messid(messid)
            if post == None:
                download_list.append(index)
            elif detailed_log:
                log('Post #%s (#%s in INBOX) found.' %
                    (post.heapid(), int(index) + lower_value))
        download_imap = ','.join(download_list)
        num_new = len(download_list)

        if num_new == 0:
            log('No new messages.')
            return
        else:
            log('%d new message%s found.' %
                (num_new, hkutils.plural(num_new)))

        log('Downloading...')

        new_posts = []

        result = self._server.fetch(download_imap,
                                    '(BODY[TEXT] BODY[HEADER])')[1]
        for i in range(num_new):
            text = result[i * 3][1]
            header = result[i * 3 + 1][1]
            post = self.create_post_from_email(header, text)
            self._postdb.add_new_post(post)
            new_posts.append(post)
            if detailed_log:
                log('Post #%s (#%s in INBOX) downloaded.' %
                    (post.heapid(), download_list[i]))

        log('%d new message%s downloaded.' %
            (num_new, hkutils.plural(num_new)))

        return PostSet(self._postdb, new_posts)


##### GeneratorOptions #####

class GeneratorOptions(object):

    """Options that are used by |Generator|.

    This class follows the Options pattern.

    TODO: standardize underscore usage.

    **Data attributes:**

    shortsubject --- If True, the posts that have the same subject as
        their parent will show a dash instead of their subject.
        Type: bool
        Default: False
    shorttags --- If True, the posts that have the same tags as
        their parent will show a dash instead of their tags.
        Type: bool
        Default: False
    html_title --- The string to print as the <title> of the HTML file.
        Type: str
        Default: 'Heap index'
    html_h1 --- The string to print as the title (<h1>) of the HTML file.
        Type: str
        Default: 'Heap index'
    cssfiles --- The name of the CSS files that should be referenced.
        Type: str
    files_to_copy --- List of files that should be copied from the heap's
        directory or from the current directory to the HTML directory.
        Type: [str]
        Default: []
    """

    def __init__(self,
                 shortsubject=False,
                 shorttags=False,
                 html_title='Heap index',
                 html_h1='Heap index',
                 cssfiles=['heapindex.css'],
                 files_to_copy=['heapindex.css']):

        super(GeneratorOptions, self).__init__()
        hkutils.set_dict_items(self, locals())
