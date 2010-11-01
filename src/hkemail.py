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
# Copyright (C) 2009-2010 Attila Nagy

"""|hkemail| downloads emails and converts them into posts."""


import base64
import email
import email.header
import getpass
import imaplib
import itertools
import quopri
import re

import hkutils
import hklib


# TODO test
class EmailDownloader(object):

    """A EmailDownloader object can be used to connect to the server and
    download new posts.

    **Data attributes:**

    - `_postdb` (|PostDB|) -- The post database.
    - `_config` (|ConfigDict|) -- The configuration object.
    - `_server` (imaplib.IMAP4_SSL | ``None``) -- The object that represents
      the IMAP server.

    **Reading:**

    - RFC2822 -- Internet Message Format
    - RFC3501 -- Internet Message Access Protocol - Version 4rev1
    - http://en.wikipedia.org/wiki/MIME#Multipart_messages
    """

    def __init__(self, postdb, config, heap_id):
        """Constructor.

        **Arguments:**

        - `_postdb` (|PostDB|) -- The post database.
        - `_config` (|ConfigDict|) -- The configuration object.
        - `_heap_id` (|HeapId|) -- The id of the heap which will be used.
        """

        super(EmailDownloader, self).__init__()
        self._postdb = postdb
        self._config = config
        self._heap_id = heap_id
        self._server = None

    def connect(self):
        """Connects to the IMAP server."""

        hkutils.log('Reading settings...')

        # Try to get the server configuration specific to the heap
        server = self._config['heaps'][self._heap_id].get('server')

        # If that does not exist, get the generic server configuration
        if server is None:
            server = self._config['server']

        host = server['host']
        port = server['port']
        username = server['username']
        password = server.get('password')
        # if imaps is omitted, default to True iff port is 993
        imaps = server.get('imaps', (port == 993))

        # If no password was specified, ask it from the user
        if password is None:
            prompt = 'Password for %s@%s: ' % (username, host)
            password = getpass.getpass()

        hkutils.log('Connecting...')
        if imaps:
            self._server = imaplib.IMAP4_SSL(host, port)
        else:
            self._server = imaplib.IMAP4(host, port)
        self._server.login(username, password)
        hkutils.log('Connected')

    def close(self):
        """Closes the connection with the IMAP server."""

        self._server.close()
        self._server = None

    @staticmethod
    def parse_email(header, text):
        """Creates strings from an already downloaded email header and
        body part.

        **Arguments:**

        - `header` (str) -- The header of the email.
        - `text` (str) -- The body of the email.

        **Returns:** (str, str)
        """

        message = email.message_from_string(header + text)

        def normalize_str(s):
            s = re.sub(r'\r\n', r'\n', s) # Windows EOL
            s = re.sub(r'\xc2\xa0', ' ', s) # Non-breaking space
            return s

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
                value = normalize_str(value)
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
                    ('multipart/mixed',
                     'multipart/alternative',
                     'multipart/signed',
                     'multipart/related')):
                    hkutils.log('WARNING: unknown type of multipart '
                                'message: %s\n%s' %
                                (content_type, header + text))
                message = message.get_payload(0)
            else:
                if content_type != 'text/plain':
                    hkutils.log('WARNING: content type is not text/plain: '
                                '%s\n%s' %
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
            if encoding.lower() in ('7bit', '8bit', 'binary'):
                pass # no conversion needed
            elif encoding.lower() == 'base64':
                text = base64.b64decode(text)
            elif encoding.lower() == 'quoted-printable':
                text = quopri.decodestring(text)
            else:
                hkutils.log('WARNING: Unknown encoding, skipping decoding: '
                            '%s\n'
                            'text:\n%s\n' % (encoding, text))
        charset = message.get_content_charset()
        text = hkutils.utf8(text, charset)
        text = normalize_str(text)

        return headers, text

    def create_post_from_email(self, header, text):
        """Create a Post from an already downloaded email header and
        body part.

        **Arguments:**

        - `header` (str) -- The header of the email.
        - `text` (str) -- The body of the email.

        **Returns:** (str, str)
        """

        headers, text = self.parse_email(header, text)
        post = hklib.Post.create_empty()
        post.set_author(headers.get('From', ''))
        post.set_subject(headers.get('Subject', ''))
        post.set_messid(headers.get('Message-Id', ''))
        post.set_parent(headers.get('In-Reply-To', ''))
        post.set_date(headers.get('Date', ''))
        post.set_body(text)
        post.remove_google_stuff()
        post.remove_newlines_from_subject()
        post.normalize_subject()

        # If the author has a nickname, we set it
        r = re.compile('[-._A-Za-z0-9]+@[-._A-Za-z0-9]+')
        match = r.search(post.author())
        if match is not None:
            author_address = match.group(0)
        else:
            author_address = ''

        # We try to read the nickname from the
        # heaps/<heap id>/nicknames/<author address> configuration item
        heap_config = self._config['heaps'][self._heap_id]
        author_nick = heap_config['nicknames'].get(author_address)

        # We try to read the nickname from the nicknames/<author address>
        # configuration item
        if author_nick is None:
            author_nick = self._config['nicknames'].get(author_address)

        if author_nick is not None:
            post.set_author(author_nick)
        else:
            hkutils.log("WARNING: author's nickname not found: %s" %
                        (post.author()))

        return post

    def imap_compact(self, messnum_strs):
        """Expresses a list of message numbers in the shortest
        possible form using IMAP sequence notation.

        **Arguments:**

        - `messnum_strs` ([str]) -- An ordered list of message number strings.

        **Returns:** [str] -- A list of message numbers and sequence
        notations.

        **Example:** ::

            >>> email_downloader.imap_compact((1, 2, 3, 5, 6, 7, 42))
            ['1:3', '5:7', '42']
        """

        # Convert sequence of strings into sequence of ints
        messnums = [int(messnum_str) for messnum_str in messnum_strs]

        result = []
        # Iterate over consecutive sequences
        for _, group_iter in itertools.groupby(enumerate(messnums),
                                               lambda (i, x): i - x):
            group = list(group_iter)
            start = str(group[0][1])
            end = str(group[-1][1])
            result.append(start + (':' + end if len(group) > 1 else ''))
        return result

    def fragment_list(self, strings, maxlen=500):
        """Breaks a list of strings into a list of lists of strings where
        the concatenated length of individual lists does not exceed a
        given maximum.

        **Arguments:**

        - `strings` ([str]) -- The list of strings to be fragmented.
        - `maxlen` (int) -- The maximum length of individual lists.

        **Returns:** [[str]]

        **Example:** ::

            >>> email_downloader.fragment_list(
                    ('lo', 'rem', 'ip', 'sum', 'dolor', 'sit'),
                    maxlen=10)
            [['lo', 'rem', 'ip'], ['sum', 'dolor'], ['sit']]
        """

        fragments = []
        current_fragment = []
        length_now = 0
        for string in strings:
            if length_now + len(string) + 1 > maxlen:
                fragments.append(current_fragment)
                current_fragment = [string]
                length_now = len(string) + 1
            else:
                current_fragment.append(string)
                length_now += len(string) + 1
        fragments.append(current_fragment)
        return fragments

    def download_new(self, lower_value=0, detailed_log=False):
        """Downloads the new emails from the INBOX of the IMAP server and adds
        them to the post database.

        **Arguments:**

        - `lower_value` (int) -- Only the email indices that are greater or
          equal to `lower_value` are examined.
        - `detailed_log` (bool) -- If ``True``, every email found or downloaded
          is reported.

        **Returns:** |PostSet| -- A set of the new posts.
        """

        assert self._postdb.has_heap_id(self._heap_id)
        self._server.select("INBOX")

        # Stage 1: checking for matching IDs
        # Note: this is probably unnecessary

        if lower_value == 0:
            imap_crit = 'ALL'
        else:
            imap_crit = '(%d:*)' % (lower_value,)
        result = self._server.search(None, imap_crit)[1][0].strip()
        if result == '':
            hkutils.log('No messages to download.')
            return
        emails = result.split(' ')

        # The list has to be compacted to keep the IMAP command short.
        # Plus we fragment the list into pieces not longer than
        # a given amount that can be safely handled by all IMAP servers
        # (this is now 500).
        sequences = self.imap_compact(emails)
        fragments = self.fragment_list(sequences)

        # Stage 2: checking which messages we don't already have
        # We do this because it can save a lot of time and bandwidth

        hkutils.log('Checking...')

        messids = []
        for fragment in fragments:
            fragment_imap = ','.join(fragment)
            param = '(BODY[HEADER.FIELDS (MESSAGE-ID)])'
            result = self._server.fetch(fragment_imap, param)[1]
            raw_messids = [result[2 * i][1] for i in range(len(result) / 2)]
            # using the email lib to parse Message-Id headers
            messids.extend([email.message_from_string(s)['Message-Id']
                            for s in raw_messids])

        # Assembling a list of new messages
        download_list = []
        for index, messid in zip(emails, messids):
            post = self._postdb.post_by_messid(messid)
            if post == None:
                download_list.append(index)
            elif detailed_log:
                hkutils.log('Post #%s (#%s in INBOX) found.' %
                            (post.post_index(), int(index) + lower_value))

        # Stage 3: actually downloading the needed messages

        new_msg_count = len(download_list)
        if new_msg_count == 0:
            hkutils.log('No new messages.')
            return
        else:
            hkutils.log('%d new message%s found.' %
                        (new_msg_count, hkutils.plural(new_msg_count)))

        hkutils.log('Downloading...')

        # Compact & fragment this list too to keep IMAP commands short
        sequences = self.imap_compact(download_list)
        fragments = self.fragment_list(sequences)

        downloaded_msg_count = 0
        for fragment in fragments:
            fragment_imap = ','.join(fragment)
            new_posts = []

            result = self._server.fetch(fragment_imap,
                                        '(BODY[TEXT] BODY[HEADER])')[1]
            # `result` is formatted like this:
            #
            #    [ # First email:
            #
            #      # result[0]:
            #      ('1 (BODY[TEXT] {123}',
            #       'This is the body of the first result...'),
            #
            #      # result[1]:
            #      (' BODY[HEADER] {456}',
            #       'Headers-Of: first-email...'),
            #
            #      # result[2]:
            #      ')'
            #
            #      # Second email:
            #
            #      # result[3]:
            #      ('2 (BODY[TEXT] {789}',
            #       'This is the body of the second result...'),
            #      ... ]
            #
            # The final ')' element causes a single email to be represented
            # by 3 elements in the list of results.

            for i in range(len(result) / 3):
                number_str = result[i * 3][0]
                number = number_str[0:number_str.index(' ')]
                text = result[i * 3][1]
                header = result[i * 3 + 1][1]
                # Catch "Exception" # pylint: disable=W0703
                try:
                    post = self.create_post_from_email(header, text)
                    self._postdb.add_new_post(post, self._heap_id)
                    new_posts.append(post)
                except Exception, e:
                    hkutils.log('Error while downloading: %s' % e)
                    downloaded_msg_count += 1
                    continue
                if detailed_log:
                    hkutils.log('Post #%s (#%s in INBOX) downloaded.' %
                                (post.post_index(), number))
                downloaded_msg_count += 1

        hkutils.log('%d new message%s downloaded.' %
                    (downloaded_msg_count,
                     hkutils.plural(downloaded_msg_count)))

        if new_msg_count != downloaded_msg_count:
            hkutils.log('WARNING: number of new (%d) and'
                        'downloaded (%d) messages not equal!' %
                        (new_msg_count, downloaded_msg_count))

        return hklib.PostSet(self._postdb, new_posts)
