#!/usr/bin/python

"""Manipulates the Heap data structure.

Usage:

    python heapmanip.py download_mail
    python heapmanip.py generate_html
    python heapmanip.py rename_thread _heapid_ _new_subject_

A config file has to be created in the current directory with the name
"heap.cfg". An example config file:

    [server]
    host=imap.gmail.com
    port=993
    username=our.heap@gmail.com
    password=examplepassword

    [paths]
    mail=mail
    html=html

    [nicknames]
    1=Somebody somebody@gmail.com
    2=Somebody_else somebody.else@else.com
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
import email.utils
import sys
import ConfigParser
import time
import StringIO


##### global variables #####

log_on = [True]

def set_log(log_):
    log_on[0] = log_

def log(str):
    if log_on[0]:
        print str


##### utility functions and classes #####

def file_to_string(file_name):
    """Reads a file's content into a string."""
    f = open(file_name)
    s = f.read()
    f.close()
    return s

def string_to_file(s, file_name):
    """Writes a string to a file."""
    f = open(file_name,'w')
    f.write(s)
    f.close()

def utf8(s, charset):
    """Encodes the given string in the charset into utf-8.

    If the charset is None, the original string will be returned.
    """
    if charset != None:
        return s.decode(charset).encode('utf-8')
    else:
        return s

def calc_timestamp(date):
    """Calculates a timestamp from a date.

    The date argument should conform to RFC 2822.
    The timestamp will be an UTC timestamp.
    """
    return email.utils.mktime_tz(email.utils.parsedate_tz(date))

class HeapException(Exception):

    """A very simple exception class used by this module."""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


##### Post #####

class Post(object):

    """Represents a posted message.

    A Post object is in the memory, but usually it represents a file that is in
    the filesystem.

    Data attributes:
    _header -- The header of the post.
        Type: dict(str, (str | [str])).
    _body -- The body of the post. The first character of the body is not a
        whitespace. The last character is a newline character, and the but one
        character is not a whitespace. It does not contain any '\\r'
        characters, newlines are stored as '\\n'.
        In regexp: (|\\S|\\S[^\\r]*\\S)\\n
        The set_body function converts any given string into this format.
        Type: str.
    _heapid -- The identifier of the post.
        Type: NoneType | str.
    _maildb -- The MailDB object that contains the post.
        If _maildb is None, _heapid must not be None.
        Type: NoneType | MailDB.
    _modified -- It is false if the file on the disk that represents the post
        is up-to-date. It is true if there is no such file or the post
        has been modified since the last synchronization.
        Type: bool.
    """

    # Constructors

    def __init__(self, f, heapid=None, maildb=None):
        """Constructor.

        Arguments:
        f -- A file descriptor from which the header and the body of the post
             will be read. It will not be closed.
        heapid -- See _heapid.
        maildb -- See _maildb.
        """

        assert(not (maildb != None and heapid == None))
        super(Post, self).__init__()
        self._header, self._body = Post.parse(f)
        self._heapid = heapid
        self._maildb = maildb
        self._modified = not self.postfile_exists()

    @staticmethod
    def from_str(s, heapid=None, maildb=None):
        """Creates a Post object from the given string."""
        sio = StringIO.StringIO(s)
        p = Post(sio, heapid, maildb)
        sio.close()
        return p

    @staticmethod
    def from_file(fname, heapid=None, maildb=None):
        """Creates a Post object from a file."""
        with open(fname, 'r') as f:
            return Post(f, heapid, maildb)

    @staticmethod
    def create_empty(heapid=None, maildb=None):
        """Creates an empty Post object."""
        sio = StringIO.StringIO('')
        p = Post(sio, heapid, maildb)
        sio.close()
        return p

    # Modifications

    def touch(self):
        """Should be called each time after the post is modified."""
        self._modified = True
        if self._maildb != None:
            self._maildb.touch()

    def is_modified(self):
        return self._modified

    def add_to_maildb(self, heapid, maildb):
        """Adds the post to the maildb."""
        assert(self._maildb == None)
        self._heapid = heapid
        self._maildb = maildb
        self.touch()

    # Get-set functions

    def heapid(self):
        return self._heapid

    def author(self):
        return self._header['From']

    def set_author(self, author):
        self._header['From'] = author
        self.touch()

    def real_subject(self):
        return self._header['Subject']

    def subject(self):
        """The subject with the 'Re:' prefix removed."""
        subject = self._header['Subject']
        if re.match('[Rr]e:', subject):
            subject = subject[3:]
        return subject.strip()

    def set_subject(self, subject):
        self._header['Subject'] = subject
        self.touch()

    def messid(self):
        return self._header['Message-Id']

    def set_messid(self, messid):
        self._header['Message-Id'] = messid
        self.touch()

    def inreplyto(self):
        return self._header['In-Reply-To']

    def set_inreplyto(self, inreplyto):
        self._header['In-Reply-To'] = inreplyto
        self.touch()

    def date(self):
        return self._header['Date']

    def set_date(self, date):
        self._header['Date'] = date
        self.touch()

    def date_str(self):
        """The date converted to a string in local time."""
        date = self.date()
        if date == '':
            return ''
        else:
            date_local = time.localtime(calc_timestamp(date))
            return time.strftime('%Y.%m.%d. %H:%M', date_local)

    def tags(self):
        # The list is copied so that the original cannot be modified by the
        # caller.
        return self._header['Tag'][:]
    
    def tags_iter(self):
        """Iterator that iterates on the tags."""
        return self._header['Tag'].__iter__()

    def set_tags(self, tags):
        self._header['Tag'] = tags
        self.touch()
        
    def flags(self):
        # The list is copied so that the original cannot be modified by the
        # caller.
        return self._header['Flag'][:]

    def set_flags(self, flags):
        assert(isinstance(flags, list))
        self._header['Flag'] = sorted(flags)
        self.touch()
        
    def is_deleted(self):
        return 'deleted' in self._header['Flag']

    def delete(self):
        self._header = {'Message-Id': self.messid(), 
                         'Flag': ['deleted']}
        self.touch()

    def body(self):
        return self._body

    def set_body(self, body):
        self._body = body.strip() + '\n'
        self.touch()

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

        Strings will be assigned to the 'From', 'Subject', etc. attributes,
        while dictionaries to the 'Tag' and 'Flag' strings. If an attribute is
        not present in the input, an empty string or an empty list will be
        assigned to it. The list that is assigned to 'Flag' is sorted.
        """

        def copy_one(key):
            try:
                [value] = d.pop(key, [''])
            except ValueError:
                raise HeapException, ('Multiple "%s" keys.' % key)
            h[key] = value

        def copy_list(key):
            h[key] = d.pop(key, [])
            
        d = d.copy()
        h = {}
        copy_one('From')
        copy_one('Subject')
        copy_list('Tag')
        copy_one('Message-Id')
        copy_one('In-Reply-To')
        copy_one('Date')
        copy_list('Flag')
        h['Flag'].sort()

        # compatibility code for the "Flags" attribute {
        flags = d.pop('Flags', None)
        if flags == ['deleted']:
            h['Flag'].append('deleted')
        elif flags == None:
            pass
        else:
            raise HeapException, ('Unknown "Flags" tag: "%s"' % (flags,))
        # }

        if d != {}:
            raise HeapException, ('Additional keys: "%s".' % d)
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

        write_str('From')
        write_str('Subject')
        write_list('Tag')
        write_str('Message-Id')
        write_str('In-Reply-To')
        write_str('Date')
        write_list('Flag')
        f.write('\n')
        f.write(self._body)

    def save(self):
        assert(self._maildb != None)
        if self._modified:
            with open(self.postfilename(), 'w') as f:
                self.write(f)
                self._modified = False

    # Filenames

    def postfilename(self):
        """The name of the postfile in which the post is (or can be) stored."""
        assert(self._maildb != None)
        return os.path.join(self._maildb.postfile_dir(), \
                            self._heapid + '.mail')

    def htmlfilebasename(self):
        """The base name of the HTML file that can be generated from the
        post."""
        return self._heapid + '.html'

    def htmlfilename(self):
        """The name of the HTML file that can be generated from the post."""
        assert(self._maildb != None)
        return os.path.join(self._maildb.html_dir(), self._heapid + '.html')

    def postfile_exists(self):
        if self._maildb == None:
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

    # Misc

    def remove_google_stuff(self):
        r = re.compile(r'--~--~---------~--~----~------------~-------~--~' + \
                       r'----~\n.*?\n' + \
                       r'-~----------~----~----~----~------~----~------~-' + \
                       r'-~---\n', re.DOTALL)
        self.set_body(r.sub('', self.body()))


##### MailDB #####

class MailDB(object):

    """The mail database that stores and handles the posts.

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
        Type: [Post()]
    _all -- All posts in a PostSet. It can be asked with all().
        Type: PostSet.
    _threadstruct -- Assigns the posts to a p post that are replies to p.
        It can be asked with threadstruct().
        If it is None, then it should be recalculated when needed.
        Type: dict(heapid, [heapid])
    """

    # Constructors

    def __init__(self, postfile_dir, html_dir):
        """Constructor.

        Arguments:
        postfile_dir: Initialises self._postfile_dir.
        html_dir: Initialises self._html_dir.
        """

        super(MailDB, self).__init__()
        self._postfile_dir = postfile_dir
        self._html_dir = html_dir
        self._init()

    @staticmethod
    def from_config(config):
        """Creates a MailDB with the given configuration.

        Arguments:
        config -- Configuration object. The paths/mail and paths/html options
            will be read.
            Type: ConfigParser
        """
        
        postfile_dir = config.get('paths', 'mail')
        html_dir = config.get('paths', 'html')
        return MailDB(postfile_dir, html_dir)

    def _init(self):
        """Initialisation."""

        self.heapid_to_post = {}
        self.messid_to_heapid = {}
        heapids = []
        if not os.path.exists(self._postfile_dir):
            os.mkdir(self._postfile_dir)
        for file in os.listdir(self._postfile_dir):
            if file.endswith('.mail'):
                heapid = file[:-5]
                absname = os.path.join(self._postfile_dir, file)
                self._add_post_to_dicts(Post.from_file(absname, heapid, self))
                try:
                    heapids.append(int(heapid))
                except ValueError:
                    pass
        self._next_heapid = max(heapids) + 1 if heapids != [] else 0
        self._posts = None
        self._all = None
        self._threadstruct = None

    # Modifications

    def touch(self):
        """If something in the database changes, this function should be
        called.
        
        If a post in the database is changed, this function will be invoked
        automatically, so there is no need to call it again.
        """

        self._posts = None
        self._all = None
        self._threadstruct = None

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
    
    def _recalc_posts(self):
        """Recalculates the _posts variable if needed."""
        if self._posts == None:
            self._posts = \
                [ p for p in self.real_posts() if not p.is_deleted() ]

    def real_posts(self):
        """Returns the list of all posts, even the deleted ones."""
        return self.heapid_to_post.values()

    def post(self, heapid):
        try:
            return self.heapid_to_post[heapid]
        except KeyError:
            return None

    def post_by_messid(self, messid):
        try:
            return self.post(self.messid_to_heapid[messid])
        except KeyError:
            return None

    # Save

    def save(self):
        """Saves all the posts that needs to be saved."""
        for post in self.heapid_to_post.values():
            post.save()

    # New posts

    def add_new_post(self, post):
        """Adds a new post to the maildb.
        
        The heapid of the post will be changed to the next free heapid of the
        maildb."""

        heapid = self.next_heapid()
        post.add_to_maildb(heapid, self)
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
        """

        self._recalc_all()
        return self._all

    def _recalc_all(self):
        if self._all == None:
            self._all = PostSet(self, self.posts())

    # Thread structure

    def threadstruct(self):
        """Returns the calculated _threadstruct.
        
        The object returned by this function should not be modified."""

        self._recalc_threadstruct()
        return self._threadstruct

    def prev(self, post):
        """Returns the previous post relative to the given post."""

        assert(post in self.posts())
        inreplyto = post.inreplyto()

        if inreplyto == '':
            return None
        
        else:

            # try to get the prev_post by messid
            prev_post = self.post_by_messid(inreplyto)

            # try to get the prev_post by heapid
            if prev_post == None:
                prev_post = self.post(inreplyto)

            # deleted posts do not count
            if prev_post != None and prev_post.is_deleted():
                prev_post = None

            return prev_post

    def root(self, post):
        """Returns the root of the post."""

        assert(post in self.posts())
        prev_post = self.prev(post)
        if prev_post == None:
            return post
        else:
            return self.root(prev_post)

    def _recalc_threadstruct(self):
        """Recalculates the _threadstruct variable if needed."""

        if self._threadstruct == None:

            def add_timestamp(post):
                """Creates a (timestamp, heapid) pair from the post."""
                heapid = post.heapid()
                date = post.date()
                timestamp = calc_timestamp(date) if date != '' else 0
                return (timestamp, heapid)

            threads = {None: []} # dict(heapid, [answered:(timestamp, heapid)])
            for post in self.posts():
                prev_post = self.prev(post)
                prev_heapid = prev_post.heapid() if prev_post != None else None
                if prev_heapid in threads:
                    threads[prev_heapid].append(add_timestamp(post))
                else:
                    threads[prev_heapid] = [add_timestamp(post)]
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

        assert(post in self.posts() or post == None)
        if post != None:
            yield post
        heapid = post.heapid() if post != None else None
        if threadstruct == None:
            threadstruct = self.threadstruct()
        for ch_heapid in threadstruct.get(heapid, []):
            for post2 in self.iter_thread(self.post(ch_heapid), threadstruct):
                yield post2

    # Filenames

    def postfile_dir(self):
        return self._postfile_dir

    def html_dir(self):
        return self._html_dir


##### PostSet #####

class PostSet(set):

    """A set of posts.

    Data attributes:
    _maildb -- Mail database.
        Type: MailDB
    
    Types:
        PrePostSet = set(Post) | PostSet(Post) | [Post] | Post
    """

    def __init__(self, maildb, posts):
        """Constructor.

        Arguments:
        maildb -- Initialises self._maildb.
            Type: MailDB
        posts -- Initialises the set.
            Type: PrePostSet
        """

        super(PostSet, self).__init__(PostSet.to_set(posts))
        self._maildb = maildb

    @staticmethod
    def to_set(s):
        """Converts a PreSet object to a set."""
        if isinstance(s, set):
            return s
        elif isinstance(s, list) or isinstance(s, tuple):
            return set(s)
        elif isinstance(s, Post):
            return set([s])
        else:
            raise HeapException, \
                  ("Object's type not compatible with MailSet: %s" % (s,))

    def is_set(self, s):
        """The given set equals to the set of contained posts."""
        return set.__eq__(self, PostSet.to_set(s))

    def __eq__(self, s):
        if isinstance(s, PostSet):
            return set.__eq__(self, s)
        else:
            return False

    def forall(self):
        return PostSetDelegate(self)

    def __getattr__(self, funname):
        if funname == 'fa':
            return self.forall()
        else:
            raise AttributeError, \
                  ("'PostSet' object has no attribute '%s'" % funname)

    def expf(self):
        """Returns all consequenses of the PostSet.
        
        Returns: PostSet
        """

        result = set()
        for post in self:
            # if post is in result, then it has already been processed
            # (and all its consequences has been added to result)
            if post not in result:
                for post2 in self._maildb.iter_thread(post):
                    result.add(post2)
        return PostSet(self._maildb, result)

class PostSetDelegate(object):

    """A delegate of posts.
    
    If a method is called on a PostSetDelegate object, it will forward the call
    to the posts it represents.

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

        super(PostSetDelegate, self).__init__()
        self._postset = postset

    def __getattr__(self, funname):
        def forall_fun(*args, **kw):
            for post in self._postset:
                getattr(post, funname)(*args, **kw)
        return forall_fun

##### Server #####

class Server(object):
    
    """A Server object can be used to connect to the server and download new
    posts.
    
    Data attributes:
    _maildb -- The mail database..
        Type: MailDB
    _config -- The configuration.
        Type: ConfigParser
    _server -- The object that represents the IMAP server.
        Type: IMAP4_SSL | NoneType
    """

    def __init__(self, maildb, config):
        """Constructor.

        Arguments:
        maildb: Initialises self._maildb.
        config: Initialises self._config.
        """

        super(Server, self).__init__()
        self._maildb = maildb
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
                    value += utf8(v[0], v[1])
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
        text = utf8(text, charset)

        text = re.sub(r'\r\n',r'\n',text)
        post = Post.create_empty()
        post.set_author(headers.get('From', ''))
        post.set_subject(headers.get('Subject', ''))
        post.set_messid(headers.get('Message-Id', ''))
        post.set_inreplyto(headers.get('In-Reply-To', ''))
        post.set_date(headers.get('Date', ''))
        post.set_body(text)
        post.remove_google_stuff()

        for entry, author_regex in self._config.items('nicknames'):
            [author, regex] = self._config.get('nicknames', entry).split(' ',1)
            if re.search(regex, post.author()) != None:
                post.set_author(author)
                break

        return post

    def download_new(self, lower_value=0):
        """Downloads the new emails from the INBOX of the IMAP server and adds
        them to the mail database.

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
                    post = self._maildb.post_by_messid(messid)
                    if post == None:
                        post = self.download_email(email_index)
                        self._maildb.add_new_post(post)
                        log('Post #%s (#%s in INBOX) downloaded.' % \
                            (post.heapid(), email_index))
                    else:
                        log('Post #%s (#%s in INBOX) found.' % \
                            (post.heapid(), email_index))
        log('Downloading finished.')


##### Generator #####

html_header = """\
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
    <title>%s</title>
    <link rel=stylesheet href="%s" type="text/css">
  </head>
  <body>
    <h1 id="header">%s</h1>

"""

html_footer = """
  </body>
</html>
"""

html_one_mail = """\
<div class="mail">
<a href="%s">
<span class="subject">%s</span>
<span class="index">&lt;%s&gt;</span>
<span class="author">%s</span>
<span class="timestamp">%s</span>
</a>
"""

def sub_html(matchobject):
    whole = matchobject.group(0)
    if whole == '<':
        return '&lt;'
    elif whole == '>':
        return '&gt;'
    elif whole == '&':
        return '&amp;'

def quote_html(text):
    return re.sub(r'[<>&]', sub_html, text)

class Generator(object):

    """A Generator object can generate HTML from the posts.
    
    It can generate an index page that contains all posts, and an HTML file
    for each post.

    Data attributes:
    _maildb -- The mail database.
        Type: MailDB
    """

    def __init__(self, maildb):
        """Constructor

        Arguments:
        maildb -- Initialises self._maildb.
            Type: MailDB
        """

        super(Generator, self).__init__()
        self._maildb = maildb

    def posts_to_html(self):
        """Creates an HTML file for each post that are not deleted."""
        for post in self._maildb.posts():
            with open(post.htmlfilename(), 'w') as f:
                h1 = quote_html(post.author()) + ': ' + \
                     quote_html(post.subject())
                f.write(html_header % (h1, 'heapindex.css', h1))
                f.write('(' + post.date_str() + ')')
                f.write('<pre>')
                f.write(quote_html(post.body()))
                f.write('</pre>')
                f.write(html_footer)

    def index_html(self):
        """Creates the index HTML file.
        
        The created file is named 'index.html' and is placed in the html_dir
        directory."""

        def write_thread(heapid, indent):
            """Writes a post and all its followers into the output."""
            if heapid != None:
                post = self._maildb.heapid_to_post[heapid]
                author = re.sub('<.*?>','', post.author())
                date_str = ("&nbsp; (%s)" % post.date_str()) 
                f.write(html_one_mail % (post.htmlfilebasename(), \
                                         quote_html(post.subject()), \
                                         post.heapid(), \
                                         quote_html(author), \
                                         date_str))
            if heapid in threadst:
                for heapid2 in threadst[heapid]:
                    write_thread(heapid2, indent+1)
            if heapid != None:
                f.write("</div>\n")

        threadst = self._maildb.threadstruct()
        filename = os.path.join(self._maildb.html_dir(), 'index.html')
        with open(filename, 'w') as f:
            f.write(html_header % ('Heap Index', 'heapindex.css', 'UMS Heap'))
            write_thread(None, 0)
            f.write(html_footer)
        log('HTML generated.')


##### Interface functions #####

def read_config():
    """Reads and returns the configuration object."""

    config = ConfigParser.ConfigParser()
    config.read('heap.cfg')
    return config

def read_maildb():
    return MailDB.from_config(read_config())

def download_mail(from_ = 0):
    config = read_config()
    maildb = MailDB.from_config(config)
    server = Server(maildb, config)
    server.connect()
    server.download_new(int(from_))
    server.close()
    maildb.save()

def generate_html():
    maildb = read_maildb()
    g = Generator(maildb)
    g.index_html()
    g.posts_to_html()

def delete_mail(*heapids):
    l = list(heapids)
    maildb = read_maildb()
    for heapid in l:
        maildb.post(heapid).delete()
    maildb.save()

def change_nick(author_regex, new_author):
    maildb = read_maildb()
    author_regex = re.compile(author_regex)
    for heapid in maildb.heapids():
        mail = maildb.post(heapid)
        if author_regex.search(mail.author()) != None:
            mail.set_author(new_author)
    maildb.save()

def rename_thread_core(maildb, threadst, heapid, new_subject):
    maildb.post(heapid).set_subject(new_subject)
    if heapid in threadst:
        for heapid2 in threadst[heapid]:
            rename_thread_core(maildb, threadst, heapid2, new_subject)

def rename_thread(heapid, new_subject):
    """Renames the subject of a post and all of its following posts."""
    maildb = read_maildb()
    threadst = maildb.threadstruct()
    rename_thread_core(maildb, threadst, heapid, new_subject)
    maildb.save()

if __name__ == '__main__':
    argv = sys.argv[1:]
    if argv == [] or argv[0] in ['-h', '-help', '--help']:
        print __doc__
    else:
        funname = argv.pop(0)
        getattr(sys.modules[__name__], funname)(*argv)

