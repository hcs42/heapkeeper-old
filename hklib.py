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

"""Implements the heap data structure.

**Definiton of pseudo-types:**

.. _hklib_PrePost:

- *PrePost* (heapid | int | |Post|) -- An object that can be converted into
  a |Post|. When it is an *int*, it will be converted to a string that should
  represent a heapid. The *heapid* is converted to a |Post| based on the post
  database.

.. _hklib_PrePostSet:

- *PrePostSet* (set(|PrePost|)) | [|PrePost|] | |PrePost| | |PostSet|) -- An
  object that can be converted into a |PostSet|. Actually, |PrePostSet| can be
  any iterable object that iterates over |PrePost| objects.

.. _hklib_HtmlStr:

- *HtmlStr* (str) -- String that contains HTML.

.. _hklib_DateFun:

- *DateFun* (fun(|Post|, |GeneratorOptions|) -> (str | ``None``)) --
  A function that specifies how to print the dates of the posts. It will be
  called for each post summary that is written into an index page. When it
  returns ``None``, no date will be printed.
"""

from __future__ import with_statement
from imaplib import IMAP4_SSL
import string
import os
import os.path
import shutil
import re
import email
import email.header
import base64
import quopri
import sys
import time
import StringIO
import datetime
import hkutils

heapkeeper_version = '0.3uc'

##### logging #####

log_on = [True]

def set_log(log_):
    log_on[0] = log_

def log(*args):
    if log_on[0]:
        for arg in args:
            sys.stdout.write(arg)
        sys.stdout.write('\n')
        sys.stdout.flush()

##### Constants #####

STAR = 0
NORMAL = 1
CYCLES = 2

##### Post #####

class Post(object):

    """Represents a posted message on the heap.

    A Post object is in the memory, but usually it represents a file that is in
    the filesystem.

    **Data attributes:**

    - *_header* (``dict(str, (str | [str]))``) -- The header of the post. See
      the contents below.
    - *_body* (``str``) -- The body of the post. The first character of the
      body is not a whitespace. The last character is a newline character, and
      the last but one character is not a whitespace. It does not contain any
      ``\\r`` characters, newlines are stored as ``\\n``. The form of the body
      expressed as a regular expression: ``(\\S|\\S[^\\r]*\\S)\\n``. The
      :func:`set_body` function converts any given string into this format.
    - *_heapid* (``None | str``) -- The identifier of the post.
    - *_postdb* (``None |`` :class:`PostDB` ``)`` -- The post database object
      that contains the post. If *_postdb* is not ``None``, *_heapid* must
      not be ``None`` either.
    - *_modified* (``bool``) -- It is ``False`` if the post file that belongs
      to the post object is up-to-date. It is ``True`` if there is no such file
      or the post has been modified since the last synchronization.

    The *_header* attribute is a dictonary that contains attributes of the post
    such as the subject. The *_header* always contains all the following items:

    - ``'Author'`` (``str``) -- The author of the post.
    - ``'Subject'`` (``str``) -- The subject of the post.
    - ``'Tag'`` (``[str]``) -- The tags of the post.
    - ``'Message-Id'`` (``str``) -- The message id of the post.
    - ``'Parent'`` (``str``) -- The heapid or message id of the parent of
      the post. It should be en empty string when the post has no parent.
    - ``'Date'`` (``str``) -- The date of the post.
    - ``'Flag'`` (``[str]``) -- The flags of the post. Currently there is only
      one flag, the ``delete`` flag.
    """

    # Constructors

    def __init__(self, f, heapid=None, postdb=None):
        """Constructor.

        Arguments:
        f -- A file descriptor from which the header and the body of the post
             will be read. It will not be closed.
        heapid -- See _heapid.
        postdb -- See _postdb.
        """

        assert(not (postdb != None and heapid == None))
        super(Post, self).__init__()
        try:
            self._header, self._body = Post.parse(f)
            self._heapid = heapid
            self._postdb = postdb
            self._datetime = hkutils.NOT_SET
            self._modified = not self.postfile_exists()
        except Exception, e:
            raise hkutils.HkException, \
                  ('Error parsing post "%s"\n%s' % 
                   (getattr(f, 'name', ''), e))

    @staticmethod
    def from_str(s, heapid=None, postdb=None):
        """Creates a Post object from the given string."""
        sio = StringIO.StringIO(s)
        p = Post(sio, heapid, postdb)
        sio.close()
        return p

    @staticmethod
    def from_file(fname, heapid=None, postdb=None):
        """Creates a Post object from a file."""
        with open(fname, 'r') as f:
            return Post(f, heapid, postdb)

    @staticmethod
    def create_empty(heapid=None, postdb=None):
        """Creates an empty Post object."""
        sio = StringIO.StringIO('')
        p = Post(sio, heapid, postdb)
        sio.close()
        return p

    # Modifications

    def touch(self):
        """Should be called each time after the post is modified."""
        self._modified = True
        self._datetime = hkutils.NOT_SET
        if self._postdb != None:
            self._postdb.touch(self)

    def is_modified(self):
        return self._modified

    def add_to_postdb(self, heapid, postdb):
        """Adds the post to the postdb."""
        assert(self._postdb == None)
        self._heapid = heapid
        self._postdb = postdb
        self.touch()

    # Get-set functions

    def heapid(self):
        return self._heapid

    # author field

    def author(self):
        return self._header['Author']

    def set_author(self, author):
        self._header['Author'] = author
        self.touch()

    # subject field

    def real_subject(self):
        return self._header['Subject']

    def subject(self):
        """The subject with the 'Re:' prefix removed."""
        subject = self._header['Subject']
        if re.match('[Rr][Ee]:', subject):
            subject = subject[3:]
        return subject.strip()

    def set_subject(self, subject):
        self._header['Subject'] = subject
        self.touch()

    # message id field

    def messid(self):
        return self._header['Message-Id']

    def set_messid(self, messid):
        self._header['Message-Id'] = messid
        self.touch()

    # parent field

    def parent(self):
        return self._header['Parent']

    def set_parent(self, parent):
        self._header['Parent'] = parent
        self.touch()

    # date field

    def date(self):
        return self._header['Date']

    def set_date(self, date):
        self._header['Date'] = date
        self.touch()

    def timestamp(self):
        """Returns the timestamp of the date of the post.

        If the post does not have a date, 0 is returned.

        Returns: int
        """

        date = self.date()
        return hkutils.calc_timestamp(date) if date != '' else 0

    def datetime(self):
        """Returns the datetime object that describes the date of the post.

        If the post does not have a date, the None object is returned.

        Returns: datetime.datetime | None
        """

        self._recalc_datetime()
        return self._datetime

    def _recalc_datetime(self):

        if self._datetime == hkutils.NOT_SET:
            timestamp = self.timestamp()
            if timestamp == 0:
                self._datetime = None
            else:
                self._datetime = datetime.datetime.fromtimestamp(timestamp)

    def date_str(self):
        """The date converted to a string in local time.
        
        If the post does not have a date, an empty string is returned.
        
        Returns: str
        """

        timestamp = self.timestamp()
        if timestamp == 0:
            return ''
        else:
            return time.strftime('%Y.%m.%d. %H:%M', time.localtime(timestamp))

    def before(self, *dt):
        return datetime.datetime(*dt) > self.datetime()

    def after(self, *dt):
        return datetime.datetime(*dt) <= self.datetime()

    def between(self, dts, dte):
        date = self.datetime()
        return datetime.datetime(*dts) <= date < datetime.datetime(*dte)

    # tag fields

    def tags(self):
        """Returns the tags of the post.

        The returned object should not be modified.
        """

        return self._header['Tag']
    
    def set_tags(self, tags):
        """Sets the given tags as the tags of the post.

        Arguments:
        tags --
            Type: iterable
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
        while line.strip() != '':
            m = re.match('([^:]+): (.*)', line)
            key = m.group(1)
            value = m.group(2)
            line = f.readline()
            while line.strip() != '' and line[0] == ' ':
                line.rstrip('\n')
                value += '\n' + line[1:]
                line = f.readline()
            if key not in headers:
                headers[key] = [value]
            else:
                headers[key].append(value)
        return headers

    @staticmethod
    def create_header(d):
        """Transforms the dict(str, [str]) returned by the parse_header
        function to a str->(str | [str]) dictionary.

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
        h['Tag'].sort()
        h['Flag'].sort()

        if d != {}:
            raise hkutils.HkException, \
                  ('Additional keys: "%s".' % d)
        return h

    def write(self, f):
        """Writes the post to a stream."""

        def write_attr(key, value):
            """Writes an attribute to the output."""
            t = (key, re.sub(r'\n', r'\n ', value))
            f.write('%s: %s\n' % t)

        def write_str(attr):
            """Writes a string attribute to the output."""
            if self._header.get(attr, '') != '':
                write_attr(attr, self._header[attr])

        def write_list(attr):
            """Writes a list attribute to the output."""
            for line in self._header.get(attr, []):
                write_attr(attr, line)

        write_str('Author')
        write_str('Subject')
        write_list('Tag')
        write_str('Message-Id')
        write_str('Parent')
        write_str('Date')
        write_list('Flag')
        f.write('\n')
        f.write(self._body)

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

        with open(self.postfilename(), 'r') as f:
            self._header, self._body = Post.parse(f)
        self._modified = False
        if not silent:
            self._postdb.touch(self)

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

    def __repr__(self):
        return "<post '" + self._heapid + "'>"

    # Misc

    def remove_google_stuff(self):
        r = re.compile(r'--~--~---------~--~----~------------~-------~--~' + \
                       r'----~\n.*?\n' + \
                       r'-~----------~----~----~----~------~----~------~-' + \
                       r'-~---\n', re.DOTALL)
        self.set_body(r.sub('', self.body()))

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
    _next_heapid -- The next free heapid. There is neither a post with this
        heap id nor with any larger heapid.
        Type: int
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
        self._next_heapid = 0
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
        heapids = []

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

                try:
                    heapids.append(int(heapid))
                except ValueError:
                    pass

        next_heapid_0 = max(heapids) + 1 if heapids != [] else 0
        self._next_heapid = max([self._next_heapid, next_heapid_0])
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

    def next_heapid(self):
        """Calculated the next free heapid."""
        next = self._next_heapid
        self._next_heapid += 1
        return str(next)

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

    def add_new_post(self, post):
        """Adds a new post to the postdb.
        
        The heapid of the post will be changed to the next free heapid of the
        postdb."""

        heapid = self.next_heapid()
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
        
        Warning: if the thread structure contains cycles, calling this
        function may result in an endless loop. Before calling this function,
        the called should check that postdb.has_cycle() == False.
        """

        assert(post in self.all())
        while True:
            parentpost = self.parent(post)
            if parentpost == None:
                return post
            else:
                post = parentpost

    def children(self, post):
        """Returns the children of the given post.
        
        If 'post' is None, returns the posts with no parents (i.e. whose
        parent is None).
        
        Arguments:
        post ---
            Type: Post | None

        Returns: [Post]
        """

        assert(post == None or post in self.all())
        
        if post == None:
            children_heapids = self.threadstruct().get(None, [])
        else:
            children_heapids = self.threadstruct().get(post.heapid(), [])
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
        """Returns the list of posts contains by the postset sorted by their
        date."""

        posts = [ (post.timestamp(), post) for post in self ]
        posts.sort()
        return [ post for timestamp, post in posts]

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
        Type: IMAP4_SSL | NoneType
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
        self._server = IMAP4_SSL(host, port)
        self._server.login(username, password)
        log('Connected')

    def close(self):
        """Closes the connection with the IMAP server."""

        self._server.close()
        self._server = None

    def download_email(self, email_index):
        """Downloads an email and returns it as a Post.
        
        Arguments:
        email_index -- The index of the email to download.
            Type: int
        """

        header = self._server.fetch(email_index, '(BODY[HEADER])')[1][0][1]
        text = self._server.fetch(email_index, '(BODY[TEXT])')[1][0][1]
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

        # encodig
        encoding = message['Content-Transfer-Encoding']
        if encoding != None:
            if encoding.lower() == 'base64':
                text = base64.b64decode(text)
            elif encoding.lower() == 'quoted-printable':
                text = quopri.decodestring(text)
        charset = message.get_content_charset()
        text = hkutils.utf8(text, charset)

        text = re.sub(r'\r\n',r'\n',text)
        post = Post.create_empty()
        post.set_author(headers.get('From', ''))
        post.set_subject(headers.get('Subject', ''))
        post.set_messid(headers.get('Message-Id', ''))
        post.set_parent(headers.get('In-Reply-To', ''))
        post.set_date(headers.get('Date', ''))
        post.set_body(text)
        post.remove_google_stuff()
        post.normalize_subject()

        for entry, author_regex in self._config.items('nicknames'):
            [author, regex] = self._config.get('nicknames', entry).split(' ',1)
            if re.search(regex, post.author()) != None:
                post.set_author(author)
                break

        return post

    def download_new(self, lower_value=0):
        """Downloads the new emails from the INBOX of the IMAP server and adds
        them to the post database.

        Arguments:
        lower_value -- Only the email indices that are greater or equal to the
            lower_value are examined.
            Type: int.
        """

        self._server.select("INBOX")[1]
        emails = self._server.search(None, '(ALL)')[1][0].strip()
        if emails != '':
            for email_index in emails.split(' '):
                if int(email_index) >= lower_value:
                    header = self._server.fetch(email_index, \
                             '(BODY[HEADER.FIELDS (MESSAGE-ID)])')[1][0][1]
                    messid = email.message_from_string(header)['Message-Id']
                    # post: the post in the database if already exists
                    post = self._postdb.post_by_messid(messid)
                    if post == None:
                        post = self.download_email(email_index)
                        self._postdb.add_new_post(post)
                        log('Post #%s (#%s in INBOX) downloaded.' % \
                            (post.heapid(), email_index))
                    else:
                        log('Post #%s (#%s in INBOX) found.' % \
                            (post.heapid(), email_index))
        log('Downloading finished.')


##### Html #####

class Html():
    """Creates HTML strings."""

    @staticmethod
    def escape_char(matchobject):
        """Escapes one character based on a match."""
        whole = matchobject.group(0)
        if whole == '<':
            return '&lt;'
        elif whole == '>':
            return '&gt;'
        elif whole == '&':
            return '&amp;'

    @staticmethod
    def escape(text):
        """Escapes the characters of 'text' so that 'text' will appear
        correctly when inserted into HTML."""
        return re.sub(r'[<>&]', Html.escape_char, text)

    @staticmethod
    def doc_header(title, h1, css):
        """An HTML document's beginning."""
        return \
            '<html>\n' \
            '  <head>\n' \
            '    <meta http-equiv="Content-Type" ' \
            'content="text/html;charset=utf-8">\n' \
            '    <title>%s</title>\n' \
            '    <link rel=stylesheet href="%s" type="text/css">\n' \
            '  </head>\n' \
            '  <body>\n' \
            '    <h1 id="header">%s</h1>\n\n' % \
            (title, css, h1)

    @staticmethod
    def doc_footer():
        """An HTML document's end."""
        return \
            '\n' \
            '  </body>\n' \
            '</html>\n'
    
    @staticmethod
    def section_begin(sectionid, sectiontitle):
        """The beginning of a "section" div.
        
        If `sectiontitle` is an empty string, no title is displayed.
        """

        if sectiontitle == '':
            return '<div class="sectionid" id="%s">\n' % (sectionid,)
        else:
            return ('<div class="section">\n'
                    '<span class="sectiontitle" id="%s">%s</span>\n' %
                    (sectionid, sectiontitle))

    @staticmethod
    def section_end():
        """The end of a "section" div."""
        return '</div>\n'

    @staticmethod
    def link(link, content):
        """Creates a link."""
        return '<a href="%s">%s</a>' % (link, content)

    @staticmethod
    def enclose(class_, content, tag='span', newlines=False, id=None):
        """Encloses the given content into a tag.

        A ``"<tag attribs>content</tag>"`` string will be created. An example:

        .. code-block:: html

            <div class="myclass" id="myid">mycontent</div>

        **Arguments:**

        - *class_* (``str | None``) -- The ``class`` of the tag. If ``None``,
          the tag will not have a ``class`` attribute.
        - *content* (``str``) -- The content to be placed between the opening
          and closing tags.
        - *tag* (``str``) -- The name of the tag to be printed.
        - *newlines* (``bool``) -- If ``True``, a newline character will be
          placed after both the opening and the tags.
        - *id* (``str | None``) -- The ``id`` of the tag. If ``None``, the
          tag will not have an ``id`` attribute.
        """

        newline = '\n' if newlines else ''
        classstr = (' class="%s"' % (class_,)) if class_ != None else ''
        idstr = (' id="%s"' % (id,)) if id != None else ''
        return '<%s%s%s>%s%s</%s>%s' % \
               (tag, classstr, idstr, newline, content, tag, newline)

    @staticmethod
    def post_summary(postlink, author, subject, tags, index, date, tag,
                     thread_link=None):
        """Creates a summary for a post."""

        enc = Html.enclose
        link = Html.link
        l = []
        def newline():
            l.append('\n')

        l.append(enc('author', link(postlink, author), tag))
        newline()

        if subject != STAR:
            subject = link(postlink, subject)
        else:
            subject = enc('star', link(postlink, '&mdash;'))
        l.append(enc('subject', subject, tag))
        newline()

        if thread_link is not None:
            l.append(enc('button',
                         link(thread_link, '<img src="thread.png" />')))
            newline()

        if tags != STAR:
            tags = ', '.join(tags)
            tags = link(postlink, '[%s]' % tags)
        else:
            tags = enc('star', link(postlink, '[&mdash;]'))
        l.append(enc('tags', tags, tag))
        newline()

        l.append(enc('index', '&lt;%s&gt;' % link(postlink, index), tag))
        newline()

        if date != None:
            l.append(enc('date', link(postlink, date), tag) + '\n')
        return ''.join(l)

    @staticmethod
    def post_summary_div(link, author, subject, tags, index, date, active,
                         thread_link=None):
        """Creates a summary for a post as a div."""
        class_ = 'postsummary'
        if not active:
            class_ += ' post_inactive'
        return \
            '<div class="postbox">\n' + \
            Html.enclose(
                class_,
                Html.post_summary(
                    link, author, subject, tags, index, date, 'span',
                    thread_link))

    @staticmethod
    def post_summary_table(link, author, subject, tags, index, date, active,
                           thread_link=None):
        """Creates a summary for a post as a row of a table."""
        class_ = 'postsummary'
        if not active:
            class_ += ' post_inactive'
        return \
            '<tr class="%s">' % (class_,) + \
            Html.post_summary(link, author, subject, tags, index, date, 'td')+\
            '</tr>\n'

    @staticmethod
    def thread_post_header(link, author, subject, tags, index, date):
        """Creates a summary for a post as a div, and closes it
        immediately."""
        return \
            '<div class="postbox" id="%s">\n' % (index, ) + \
            Html.enclose(
                'postsummary',
                Html.post_summary(
                    link, author, subject, tags, index, date, 'span')) + \
            '</div>\n'

    @staticmethod
    def list(items, class_=None):
        """Puts the given items into an <ul> list."""
        l = []
        l.append('<ul')
        if class_ != None:
            l.append(' class="%s"' % (class_,))
        l.append('>\n')
        for item in items:
            l.append('  <li>')
            l.append(item)
            l.append('</li>\n')
        l.append('</ul>\n')
        return ''.join(l)


##### Section #####

class Section(object):
    """Represents a set of posts that should be printed with a title
    according to the specified options.

    This class follows the Options pattern.

    Data attributes:
    title --- The title of the section.
        Type: str
    posts --- The posts that are in the section. If it is a list, the order of
        the posts can matter. (E.g. when printed flatly, the posts will be
        printed in the same order as they are in the list.) If it is the
        CYCLES constant, the posts that are in a cycle in the database will be
        printed.
        Type: [Post] | PostSet | hklib.CYCLES
    is_flat --- If true, the section should be printed flatly, otherwise in a
        threaded structure.
        Type: bool
        Default value: False
    """

    def __init__(self,
                 title=hkutils.NOT_SET,
                 posts=hkutils.NOT_SET,
                 is_flat=False):

        super(Section, self).__init__()
        hkutils.set_dict_items(self, locals())


##### Index #####

class Index(object):
    """Represents a list of sections that should be printed into an HTML file
    according to the specified options.

    This class follows the Options pattern.

    Data attributes:
    sections --- The sections that are contained by the index.
        Type: [Section]
    filename --- The name of the HTML file where the index should be printed.
        It is either an absolute path or it is relative to the HTML dir of the
        post database.
        Type: str
        Default: 'index.html'
    """

    def __init__(self,
                 sections=hkutils.NOT_SET,
                 filename='index.html'):

        super(Index, self).__init__()
        hkutils.set_dict_items(self, locals())


##### GeneratorOptions #####

class GeneratorOptions(object):

    """Options that are used by the Generator.

    This class follows the Options pattern.

    TODO: standardize underscore usage.

    Data attributes:
    indices --- The indices to print.
        Type: [Index]
    write_toc --- If True, the index will contain a Table of Contents.
        Type: bool
        Default: False
    shortsubject --- If True, the posts that have the same subject as
        their parent will show a dash instead of their subject.
        Type: bool
        Default: False
    shorttags --- If True, the posts that have the same tags as
        their parent will show a dash instead of their tags.
        Type: bool
        Default: False
    locallinks --- If True, the thread representation will contain
        local links that point to sections within the current page.
        This is useful for thread pages.
        Type: bool
        Default: False
    always_active --- If True, the thread representation will mark all
        posts as active (ie. not grayed). Also useful for thread
        pages.
        Type: bool
        Default: False
    date_fun --- Function that specifies how to print the dates of the
        posts.
        Type: DateFun
        Default: (lambda post, options: None)
    html_title --- The string to print as the <title> of the HTML file.
        Type: str
        Default: 'Heap'
    html_h1 --- The string to print as the title (<h1>) of the HTML file.
        Type: str
        Default: 'Heap'
    cssfile --- The name of the CSS file that should be referenced.
        Type: str
    trycopyfiles --- Copy the CSS file, images and other files into the
        HTML directory if it does not exist. If cssfile is given with an absolute
        path, trycopyfiles should be False.
        Type: bool
        Default: True
    print_thread_of_post --- The thread of the post will be printed into the
        post HTML.
        Type: bool
        Default: False
    section --- The section that is printed at the moment. It is normally not
        set by the user of this module.
        Type: Section
    index --- The index that is printed at the moment. It is normally not
        set by the user of this module.
        Type: Index
    """

    def __init__(self,
                 indices=hkutils.NOT_SET,
                 write_toc=False,
                 shortsubject=False,
                 shorttags=False,
                 locallinks=False,
                 always_active=False,
                 date_fun=lambda post, options: None,
                 html_title='Heap index',
                 html_h1='Heap index',
                 cssfile='heapindex.css',
                 trycopyfiles=True,
                 print_thread_of_post=False,
                 section=hkutils.NOT_SET,
                 index=hkutils.NOT_SET):

        super(GeneratorOptions, self).__init__()
        hkutils.set_dict_items(self, locals())


##### Generator #####

class Generator(object):

    """A Generator object can generate various HTML strings and files from the
    post database.
    
    Currently it can generate two kinds of HTML files: index pages and post
    pages.
    
    The methods that start with ``gen_`` prefix write into files, the other
    methods mostly return HTML strings.

    **Attributes:**

    - *_postdb* (``PostDB``) -- The post database.

    **Used patterns:**

    - :ref:`creating_a_long_string_pattern`
    """

    def __init__(self, postdb):
        """Constructor.

        **Arguments:**

        - *postdb* (:class:`PostDB`) -- Initializes ``self._postdb``.
        """

        super(Generator, self).__init__()
        self._postdb = postdb
    
    def settle_files_to_copy(self, options):
        """Copies the CSS file and other files to the HTML directory if needed."""

        if options.trycopyfiles:
            newcssfile = os.path.join(self._postdb.html_dir(), options.cssfile)
            hkutils.copy_wo(options.cssfile, newcssfile)
            if os.path.exists('thread.png'):
                threadpng = os.path.join(self._postdb.html_dir(), 'thread.png')
                hkutils.copy_wo('thread.png', threadpng)

    def post(self, post, options):
        """Converts the post into HTML.

        **Arguments:**

        - *post* (:class:`Post`)
        - *options* (:class:`GeneratorOptions`)
        
        **Returns:** ``HtmlStr``
        """

        l = []
        h1 = Html.escape(post.author()) + ': ' + \
             Html.escape(post.subject())
        l.append(Html.doc_header(h1, h1, options.cssfile))

        l2 = []
        try:
            first = True
            for index in options.indices:
                if not first:
                    l2.append('<br/>\n')
                first = False
                l2.append(Html.link(index.filename,
                                   'Back to ' + index.filename))
        except AttributeError:
            l2.append(Html.link('index.html', 'Back to the index'))

        l2.append('\n')
        l2.append(Html.enclose('index', Html.escape('<%s>' % (post.heapid(),))))
        l2.append('\n')

        l.append(
            Html.enclose(
                tag='div',
                class_=None,
                id='subheader',
                content=''.join(l2),
                newlines=True))

        # date
        date_str = options.date_fun(post, options)
        if date_str != None:
            l.append(Html.enclose('date', date_str))
            l.append('\n')

        # thread
        if options.print_thread_of_post:
            section = Section(title='Thread', posts=[post])
            options.section = section
            thread = \
                self.summarize_thread(self._postdb.root(post), options)
            del options.section
            l.append(thread)

        l.append(Html.enclose('postbody', Html.escape(post.body()), tag='pre'))

        l.append(Html.doc_footer())
        return ''.join(l)
 
    def summarize_thread(self, post, options):
        """Converts the summaries of posts in a thread into HTML.
        
        Warning: if the given post is in a cycle, this function will go into
        an endless loop.

        **Arguments:**

        - *post* (:class:`Post`)
        - *options* (:class:`GeneratorOptions`)

        **Returns:** ``HtmlStr``
        """

        # stack will contain heapids and strings.
        # A heapid may be a string or None.
        # If stack contains several items during the execution of the loop, the
        # loop will do the following.
        # It goes through all items in reversed order and does the following
        # to all items:
        #  - if the item is a string, puts it into 'strings'
        #  - if item is a heapid, then:
        #      - if heapid is not None, puts the summary of the post that has
        #        the heapid into 'strings'
        #      - puts the summary of the the post's all children into 'strings'
        root = post
        stack = [post]
        threadstruct = self._postdb.threadstruct()
        strings = []
        
        while len(stack) > 0:
            item = stack.pop()

            if isinstance(item, str):
                strings.append(item)

            else:
                if item != None:
                    post = item
                    parent = self._postdb.parent(post)
                    subject = post.subject()
                    if (options.shortsubject and parent != None and
                        subject == parent.subject()):
                        subject_to_print = STAR
                    else:
                        subject_to_print = Html.escape(subject)

                    tags = post.tags()
                    if (options.shorttags and parent != None and
                        tags == parent.tags()):
                        tags_to_print = STAR
                    else:
                        tags_to_print = tags

                    if post == root:
                        thread_link = root.htmlthreadbasename()
                    else:
                        thread_link = None

                    strings.append(
                        self.post_summary(post, options, subject_to_print,
                                          tags_to_print, thread_link))

                    stack.append(self.post_summary_end())
                stack += reversed(self._postdb.children(item))
        return ''.join(strings)

    def full_thread(self, thread, options):
        """Converts the whole thread into HTML.

        **Arguments:**

        - *thread* (:class:`Post`)
        - *options* (:class:`GeneratorOptions`)
        
        **Returns:** ``HtmlStr``

        **Notes:**
        Don't forget that a thread is identified by its root post.
        """
        assert(thread._postdb.root(thread) == thread)

        l = []
        h1 = Html.escape(thread.author()) + ': ' + \
             Html.escape(thread.subject())
        l.append(Html.doc_header(h1, h1, 'heapindex.css'))

        l2 = []
        try:
            first = True
            for index in options.indices:
                if not first:
                    l2.append('<br/>\n')
                first = False
                l2.append(Html.link(index.filename,
                                   'Back to ' + index.filename))
        except AttributeError:
            l2.append(Html.link('index.html', 'Back to the index'))

        l2.append('\n')
        l2.append(Html.enclose('index', Html.escape('<%s>' % (thread.heapid(),))))
        l2.append('\n')

        l.append(
            Html.enclose(
                tag='div',
                class_=None,
                id='subheader',
                content=''.join(l2),
                newlines=True))

        # date
        date_str = options.date_fun(thread, options)
        if date_str != None:
            l.append(Html.enclose('date', date_str))
            l.append('\n')

        # thread
        if options.print_thread_of_post:
            section = Section(title='Thread', posts=[thread])
            options.section = section
            options.locallinks = True
            options.always_active = True
            thread_summary = \
                self.summarize_thread(thread, options)
            del options.section
            l.append(thread_summary)

        # bodies
        for curr_post in thread._postdb.iter_thread(thread):
            l.append(Html.thread_post_header(curr_post.htmlfilebasename(),
                                             Html.escape(curr_post.author()), 
                                             Html.escape(curr_post.subject()),
                                             curr_post.tags(),
                                             curr_post.heapid(),
                                             options.date_fun(curr_post,
                                                              options)))
            l.append(Html.enclose('postbody',
                                  Html.escape(curr_post.body()), tag='pre'))

        l.append(Html.doc_footer())
        return ''.join(l)

    def index_toc(self, sections, options):
        """Creates a table of contents.
        
        Each section will be one item in the table of contents.

        **Arguments:**
        
        - *sections* (``[`` :class:`Section` ``]``)
        - *options* (:class:`GeneratorOptions`)
        
        **Returns:** ``HtmlStr``
        """

        items = []
        for i, section in enumerate(sections):
            if section.title != '':
                items.append(Html.link("#section_%s" % (i,), section.title))
        return Html.list(items, 'tableofcontents')
        
    def post_summary(self, post, options, subject=NORMAL, tags=NORMAL,
                     thread_link=None):
        """Creates a summary for the post.
        
        **Arguments:**

        - *post* (:class:`Post`)
        - *options* (:class:`GeneratorOptions`)

        **Returns:** ``HtmlStr``
        """

        # Author
        author = Html.escape(post.author())

        # Subject
        if subject == NORMAL:
            subject = Html.escape(post.subject())

        # Tags
        if tags == NORMAL:
            tags = post.tags()

        # Date
        date_str = options.date_fun(post, options)

        section = options.section
        if options.always_active or section.posts == CYCLES:
            active = True
        else:
            active = post in section.posts

        if options.locallinks:
            link = '#' + post.heapid()
        else:
            link = post.htmlfilebasename()

        args = (link, author, subject, tags, post.heapid(),
                date_str, active, thread_link)

        if section.is_flat: 
            return Html.post_summary_table(*args)
        else:
            return Html.post_summary_div(*args)

    def post_summary_end(self):
        """Returns an HTML string that closes the HTML returned by
        :func:`post_summary`.
        
        **Returns:** ``HtmlStr``
        """

        return '</div>\n'

    def thread(self, post, options):
        """Converts the summaries of posts in a thread into HTML.
        
        Warning: if the given post is in a cycle, this function will go into
        an endless loop.

        **Arguments:**

        - *post* (``None |`` :class:`Post`) -- The root of the thread to be
          printed.
        - *options* (:class:`GeneratorOptions`)

        **Returns:** ``HtmlStr``
        """

        # stack will contain heapids and strings.
        # A heapid may be a string or None.
        # If stack contains several items during the execution of the loop, the
        # loop will do the following.
        # It goes through all items in reversed order and does the following
        # to all items:
        #  - if the item is a string, puts it into 'strings'
        #  - if item is a heapid, then:
        #      - if heapid is not None, puts the summary of the post that has
        #        the heapid into 'strings'
        #      - puts the summary of the the post's all children into 'strings'
        root = post
        stack = [post]
        threadstruct = self._postdb.threadstruct()
        strings = []

        while len(stack) > 0:
            item = stack.pop()

            if isinstance(item, str):
                strings.append(item)

            else:
                if item != None:
                    post = item
                    parent = self._postdb.parent(post)
                    subject = post.subject()
                    if (options.shortsubject and parent != None and
                        subject == parent.subject()):
                        subject_to_print = STAR
                    else:
                        subject_to_print = Html.escape(subject)

                    tags = post.tags()
                    if (options.shorttags and parent != None and
                        tags == parent.tags()):
                        tags_to_print = STAR
                    else:
                        tags_to_print = tags

                    if post == root:
                        thread_link = root.htmlthreadbasename()
                    else:
                        thread_link = None

                    strings.append(
                        self.post_summary(post, options, subject_to_print,
                                          tags_to_print, thread_link))

                    stack.append(self.post_summary_end())
                stack += reversed(self._postdb.children(item))
        return ''.join(strings)

    def section(self, sectionid, options):
        """Converts a section into HTML.

        When the section is not flat, the section will be printed in a threaded
        structure. The order of the posts whose parent is the same is
        determined by their order in the thread structure.

        When the section is flat, the ``posts`` attribute of the section
        specifies the order the posts. If ``posts`` is a list, the order of the
        list will be kept. If it is a :class:`PostSet`, the posts will be
        sorted by their date.

        **Arguments:**

        - *sectionid* (``int``) -- The identifier of the section.
        - *options* (:class:`GeneratorOptions`)

        **Returns:** ``HtmlStr``
        """

        l = []
        roots = self._postdb.roots()
        threads = self._postdb.threads()
        section = options.section


        l.append(Html.section_begin('section_%s' % (sectionid,),section.title))

        posts = section.posts

        if posts == CYCLES:
            posts = options.postdb.cycles()
            is_flat = True
        else:
            is_flat = section.is_flat

        if is_flat:
            l.append('<table class="flatlist">\n')
            if isinstance(posts, PostSet):
                posts = posts.sorted_list()
            for post in posts:
                l.append(self.post_summary(post, options))
            l.append('</table>\n')
        else:
            if isinstance(posts, list):
                posts = set(posts)
            for root in roots:
                thread = threads[root]
                if not (thread & posts).is_set([]):
                    # if section contains at least part of the thread
                    l.append(self.thread(root, options))
        l.append(Html.section_end())

        return ''.join(l)
    
    def gen_indices(self, options):
        """Creates the index pages.
        
        **Arguments:**

        - *options* (:class:`GeneratorOptions`)
        """

        hkutils.check(
            options,
            ['indices', 'write_toc', 'shortsubject', 'shorttags', 'date_fun',
             'html_title', 'html_h1', 'cssfile', 'trycopyfiles'])

        self.settle_files_to_copy(options)
        threadst = self._postdb.threadstruct()
        for index in options.indices:
            options.index = index
            filename = os.path.join(self._postdb.html_dir(),
                                    index.filename)
            try:
                with open(filename, 'w') as f:
                    doc_header = Html.doc_header(options.html_title,
                                                 options.html_h1,
                                                 options.cssfile)
                    f.write(doc_header)
                    if options.write_toc:
                        f.write(self.index_toc(index.sections, options))
                    for i, section in enumerate(index.sections):
                        options.section = section
                        f.write(self.section(i, options))
                        del options.section
                    f.write(Html.doc_footer())
            except IOError:
                log('IOError during index generation.')
                return
            del options.index
        
        log('Indices generated.')

    def gen_posts(self, options, posts=None):
        """Creates a post page for each post that is not deleted.
        
        **Arguments:**

        - *options* (:class:`GeneratorOptions`)
        - *posts* (:class:`Post` | ``None``) -- the posts whose post page
          should be generated. If ``None``, the post page of all posts will be
          generated.
        """

        hkutils.check(
            options,
            ['date_fun', 'html_title', 'html_h1', 'cssfile', 'trycopyfiles',
             'print_thread_of_post'])

        self.settle_files_to_copy(options)
        if posts == None:
            posts = self._postdb.all()
        for post in posts:
            try:
                with open(post.htmlfilename(), 'w') as f:
                    f.write(self.post(post, options))
            except IOError:
                log('IOError during post HTML generation.')
                return
        
        log('Post HTMLs generated.')

    def gen_threads(self, options):
        """Creates a thread page for each thread.
        
        **Arguments:**

        - *options* (:class:`GeneratorOptions`)
        """

        hkutils.check(
            options,
            ['date_fun', 'html_title', 'html_h1', 'cssfile', 'trycopyfiles',
             'print_thread_of_post'])

        self.settle_files_to_copy(options)
        for thread in self._postdb.roots():
            try:
                with open(thread.htmlthreadfilename(), 'w') as f:
                    f.write(self.full_thread(thread, options))
            except IOError:
                log('IOError during thread HTML generation.')
                return
        
        log('Thread HTMLs generated.')
