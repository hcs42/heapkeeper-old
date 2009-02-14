#!/usr/bin/python

"""Module that manipulates the Heap data structure."""

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
import time
import StringIO
import datetime


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

##### Performance measurement #####

pm_last_time = datetime.datetime.now()
pm_action = ''
def int_time(next_action = ''):
    """Returns the time elapsed since the last call of int_time."""
    global pm_last_time
    global pm_action
    old_action = pm_action
    pm_action = next_action
    now = datetime.datetime.now()
    delta = now - pm_last_time
    delta = delta.seconds + (delta.microseconds)/1000000.0
    pm_last_time = now
    return old_action, delta

def print_time(next_action = ''):
    """Calls int_time and prints the result."""
    pm_action, t = int_time(next_action)
    if pm_action != '':
        print '%.6f %s' % (t, pm_action)
    else:
        print '%.6f' % (t)

##### utility functions and classes #####

STAR = 0

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
        """Returns the tags of the email.

        The returned object should not be modified.
        """

        return self._header['Tag']
    
    # TODO: test unsorted lists and sets as argument
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

    # TODO: test
    def remove_tag(self, tag):
        if self.has_tag(tag):
            self._header['Tag'].remove(tag)
        self.touch()

    def has_tag(self, tag):
        assert(isinstance(tag, str))
        return tag in self._header['Tag']
        
    def flags(self):
        """Returns the flags of the email.

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
        h['Tag'].sort()
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

    def load(self):
        with open(self.postfilename(), 'r') as f:
            self._header, self._body = Post.parse(f)
        self._modified = False
        self._maildb.touch()

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
        self._cycles = None

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
        self._cycles = None

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
        
        See the type of the posts argument at PostSet.__init__.
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

    def prev(self, post):
        """Returns the previous post relative to the given post.
        
        If there is no such post in the database, it returns None
        """

        assert(post in self.all())
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
        """Returns the root of the post.
        
        Warning: if the thread structure contains cycles, calling this
        function may result in an endless loop. Before calling this function,
        the called should check that maildb.has_cycle() == False.
        """

        assert(post in self.all())
        while True:
            prevpost = self.prev(post)
            if prevpost == None:
                return post
            else:
                post = prevpost

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
        PrePost = heapid | int | Post
        PrePostSet = set(PrePest) | PostSet(PrePost) | [PrePost] | PrePost

        When PrePost is an int, it will be converted to a string that should
        represent a heapid.
        Actually, PrePostSet can be any iterable object that iterates over
        PrePost objects.
    """

    def __init__(self, maildb, posts):
        """Constructor.

        Arguments:
        maildb -- Initialises self._maildb.
            Type: MailDB
        posts -- Initialises the set.
            Type: PrePostSet
        """

        super(PostSet, self).__init__(PostSet._to_set(maildb, posts))
        self._maildb = maildb

    def empty_clone(self):
        """Returns an empty PostSet that has the same MailDB as this one."""
        return PostSet(self._maildb, [])

    def copy(self):
        """Copies the object.
        
        The PostSet objects will be different, but the Posts will be the same
        objects.
        """

        return PostSet(self._maildb, self)

    @staticmethod
    def _to_set(maildb, prepostset):
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
            return PostSet._to_set(maildb, [prepostset])
        else:
            result = set()
            for prepost in prepostset:
                # calculating the post for prepost
                if isinstance(prepost, str) or isinstance(prepost, int):
                    # prepost is a heapid
                    post = maildb.post(prepost, True)
                elif isinstance(prepost, Post): # prepost is a Post
                    post = prepost
                else:
                    raise HeapException, \
                          ("Object'type not compatible with Post: %prepost" % \
                           (prepost,))
                result.add(post)
            return result

    def is_set(self, s):
        """The given set equals to the set of contained posts."""
        return set.__eq__(self, PostSet._to_set(self._maildb, s))

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

        result = PostSet(self._maildb, [])
        for post in self:
            # if post is in result, then it has already been processed
            # (and all its consequences has been added to result)
            if post not in result:
                while True:
                    result.add(post)
                    post = self._maildb.prev(post)
                    if post == None:
                        break
        return result

    def expf(self):
        """Expand forward: Returns all consequenses of the PostSet.
        
        Returns: PostSet
        """

        result = PostSet(self._maildb, [])
        for post in self:
            # if post is in result, then it has already been processed
            # (and all its consequences has been added to result)
            if post not in result:
                for post2 in self._maildb.iter_thread(post):
                    result.add(post2)
        return result

    def exp(self):
        return self.expb().expf()

    # Overriding set's methods

    def construct(self, methodname, other):
        """Constructs a new PostSet from self by calling the specified method
        of the set class with the specified arguments."""
        try:
            other = PostSet(self._maildb, other)
        except TypeError:
            return NotImplemented
        result = getattr(set, methodname)(self, other)
        result._maildb = self._maildb
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
        return self.__call__(lambda p: self._postset._maildb.prev(p) == None)

    def __getattr__(self, funname):
        """Returns a function that collects posts whose return value is true
        when their "funname" method is called with the given arguments."""
        def collect_fun(*args, **kw):
            return self.__call__(lambda p: getattr(p, funname)(*args, **kw))
        return collect_fun


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
        post.normalize_subject()

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

html_footer = """\
  </body>
</html>
"""

html_section_begin = """\
<div class="section">
<span class="sectiontitle" id=%s>%s</span>
"""

html_section_end = """\
</div>
"""

def html_link(link, content):
    return '<a href="%s">%s</a>' % (link, content)

def html_span(class_, content):
    return '<span class="%s">%s</span>' % (class_, content)

def html_one_mail(link, author, subject, tags, index, date):

    s = '<div class="mail">\n'
    s += html_span('author', html_link(link, author)) + '\n'

    if subject != STAR:
        subject = html_link(link, subject)
    else:
        subject = html_span('star', html_link(link, '&mdash;'))
    s += html_span('subject', subject) + '\n'

    if tags != STAR:
        tags = ', '.join(tags)
        s += html_span('tags', '[%s]' % html_link(link, tags)) + '\n'
    else:
        s += html_span('tags_star', '[%s]' % html_link(link, '&mdash;')) + '\n'

    s += html_span('index', '&lt;%s&gt;' % html_link(link, index)) + '\n'
    if date != None:
        s += html_span('timestamp', html_link(link, date)) + '\n'
    return s

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

    def index_html(self, sections=None, write_toc=True, write_date=True,
                   shortsubject=False, shorttags=False, date_fun=None):
        """Creates the index HTML file.
        
        The created file is named 'index.html' and is placed in the html_dir
        directory.
        
        Arguments:
        sections = None | [(str, PrePostSet)]
        """
        
        if sections == None:
            sections = [('All posts', self._maildb.all(),{})]
        else:
            #sections3 = []
            #for section in sections:
            #    try:
            #        sectionname, sectionset, sectionflags = section
            #    except ValueError:
            #        sectionname, sectionset = section
            #        sectionflags = {}
            #    section3.append((sectionname, sectionset, sectionflags))
            #sections = sections3

            #for i in range(sections):
            #    if len(section) == 2:
            #        sectionname, sectionset = sections[i]
            #        sections[i] = sectionname, sectionset, {}

            for i in range(len(sections)):
                try:
                    sectionname, sectionset = sections[i]
                    sections[i] = sectionname, sectionset, {}
                except:
                    pass
                sections[i][2].setdefault('flat', False)

        def write_toc_fun():
            f.write("<div><ul>")
            if self._maildb.has_cycle():
                f.write('<li><a href="#posts_in_cycles">' +
                        'Posts in cycles</a></li>\n')
            for i, (sectiontitle, section, sectionopts) in enumerate(sections):
                f.write('<li><a href="#%d">%s</a></li>\n' % (i, sectiontitle))
            f.write("</ul></div>\n")
        
        def write_post(post, subject, tags):
                author = re.sub('<.*?>','', post.author())
                if write_date:
                    if date_fun == None:
                        date_str = post.date_str()
                    else:
                        date_str = date_fun(post)
                    if date_str != None:
                        date_html = ("&nbsp; (%s)" % date_str) 
                    else:
                        date_html = ''
                else:
                    date_html = ''

                f.write(html_one_mail(post.htmlfilebasename(),
                                      quote_html(author),
                                      subject,
                                      tags,
                                      post.heapid(),
                                      date_html))

        def write_thread(heapid, indent, parentsubject, parenttags):
            """Writes a post and all its followers into the output."""

            if heapid != None:
                post = self._maildb.heapid_to_post[heapid]
                real_subject = post.subject()
                if shortsubject and parentsubject == real_subject:
                    subject = STAR
                else:
                    subject = quote_html(real_subject)

                real_tags = post.tags()
                if shorttags and parenttags == real_tags:
                    tags = STAR
                else:
                    tags = real_tags

                write_post(post, subject, tags)

            else:
                real_subject = None
                real_tags = None

            if heapid in threadst:
                for heapid2 in threadst[heapid]:
                    write_thread(heapid2, indent+1, real_subject, real_tags)
            if heapid != None:
                f.write("</div>\n")

        threadst = self._maildb.threadstruct()
        filename = os.path.join(self._maildb.html_dir(), 'index.html')
        with open(filename, 'w') as f:
            f.write(html_header % ('Heap Index', 'heapindex.css', 'UMS Heap'))
            roots = [ self._maildb.post(heapid) for heapid in threadst[None] ]
            threads = [ self._maildb.postset(root).expf() for root in roots ]
            first = True
            if write_toc:
                write_toc_fun()
            for i, (sectiontitle, section, sectionopts) in enumerate(sections):
                f.write(html_section_begin % (str(i), sectiontitle))

                if not sectionopts['flat']:
                    for root, thread in zip(roots, threads):
                        if not (thread & section).is_set([]):
                            write_thread(root.heapid(), 1, None, None)
                else:
                    for post in section:
                        write_post(post, post.subject(), post.tags())
                        f.write('</div>')

                f.write(html_section_end)
            if self._maildb.has_cycle():
                f.write(html_section_begin % ('posts_in_cycles',
                                              'Posts in cycles'))
                for post in self._maildb.cycles():
                    subject = quote_html(post.subject())
                    write_post(post, subject, post.tags())
                    f.write("</div>\n")
                f.write(html_section_end)
            f.write(html_footer)
        log('HTML generated.')

