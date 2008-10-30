#!/usr/bin/python

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

##### global variables #####

log_on = True

def set_log(log_):
    log_on = log_

def log(str):
    if log_on:
        print str

config = ConfigParser.ConfigParser()
config.read('heap.cfg')

##### utility functions #####

def file_to_string(file_name):
    """Reads a file's content to a string."""
    f = open(file_name)
    s = f.read()
    f.close()
    return s

def string_to_file(s,file_name):
    """Writes a string to a file."""
    f = open(file_name,'w')
    f.write(s)
    f.close()

def utf8(s, charset):
    if charset != None:
        return s.decode(charset).encode('utf-8')
    else:
        return s

##### Mail #####

class Mail(object):

    def __init__(self, heapid):
        super(Mail, self).__init__()
        self._heapid = heapid
        #_up_to_date: the mailfile is up-to-date
        self._up_to_date = self.mailfile_exists()
        self._headers = None
        self._body = None

    def get_headers(self):
        if self._headers == None:
            with open(self.get_mailfile()) as f:
                self._headers = Mail.read_headers(f)
        return self._headers

    def set_headers(self, headers):
        self._headers = headers
        self._up_to_date = False

    def get_body(self):
        if self._body == None:
            with open(self.get_mailfile()) as f:
                Mail.read_headers(f) # only read, don't store
                self._body = f.read()
        return self._body
    
    def set_body(self, body):
        self._body = body.strip()+'\n'
        self._up_to_date = False

    def get_heapid(self):
        return self._heapid

    def get_author(self):
        try:
            return self.get_headers()['From']
        except KeyError:
            return ''

    def set_author(self, author):
        self.get_headers()['From'] = author
        self._up_to_date = False

    def get_subject(self):
        try:
            return self.get_headers()['Subject']
        except KeyError:
            return ''

    def get_messid(self):
        try:
            return self.get_headers()['Message-Id']
        except KeyError:
            return None

    def get_inreplyto(self):
        try:
            return self.get_headers()['In-Reply-To']
        except KeyError:
            return None

    def get_date(self):
        try:
            return self.get_headers()['Date']
        except KeyError:
            return ''

    def get_deleted(self):
        try:
            return self.get_headers()['Flags'] == 'deleted' # TODO: ugly
        except KeyError:
            return False

    def set_deleted(self, deleted):
        self.get_headers()['Flags'] = 'deleted' # TODO: ugly
        self._up_to_date = False

    @staticmethod
    def read_headers(f):
        headers = {}
        line = f.readline()
        while line not in ['', '\n']:
            m = re.match('([^:]+): (.*)', line)
            key = m.group(1)
            value = m.group(2)
            line = f.readline()
            while line not in ['', '\n'] and line[0] == ' ':
                value += '\n' + line[1:-1]
                line = f.readline()
            headers[key] = value
        return headers

    def save(self):
        if not self._up_to_date:
            mailfile = self.get_mailfile()
            headers = self.get_headers()
            body = self.get_body()
            with open(mailfile, 'w') as f:
                if self.get_deleted():
                    f.write('Message-Id: %s\n' % self.get_messid())
                    f.write('Flags: deleted\n')
                else:
                    for attr in ['From', 'Subject', 'Message-Id', 'In-Reply-To', 'Date', 'Flags']:
                        if attr in headers:
                            f.write('%s: %s\n' % (attr, re.sub(r'\n', r'\n ', headers[attr])))
                    f.write('\n')
                    f.write(body)
            self._up_to_date = True

    def remove_google_stuff(self):
        body = self.get_body()
        r = re.compile(r'--~--~---------~--~----~------------~-------~--~----~\n.*?\n' \
                        '-~----------~----~----~----~------~----~------~--~---\n', re.DOTALL)
        self.set_body(r.sub('', body))

    def get_mailfile(self):
        return os.path.join(config.get('paths','mail'), self._heapid + '.mail')

    def get_htmlfile(self):
        return os.path.join(config.get('paths','html'), self._heapid + '.html')

    def mailfile_exists(self):
        return os.path.exists(self.get_mailfile())


class MailDB(object):

    def __init__(self):
        super(MailDB, self).__init__()
        self.heapid_to_mail = {}
        self.messid_to_heapid = {}
        heapids = []
        if not os.path.exists(config.get('paths','mail')):
            os.mkdir(config.get('paths','mail'))
        for file in os.listdir(config.get('paths','mail')):
            if file[-5:] == '.mail':
                heapid = file[:-5]
                self._add_mail_to_dicts(Mail(heapid), heapid)
                try:
                    heapids.append(int(heapid))
                except ValueError:
                    pass
        self._next_heapid = max(heapids) + 1

    def get_heapids(self):
        return self.heapid_to_mail.keys()

    def next_heapid(self):
        next = self._next_heapid
        self._next_heapid += 1
        return str(next)

    def get_mails(self):
        return self.heapid_to_mail.values()

    def get_mail(self, heapid):
        try:
            return self.heapid_to_mail[heapid]
        except KeyError:
            return None

    def get_mail_by_messid(self, messid):
        try:
            return self.get_mail(self.messid_to_heapid[messid])
        except KeyError:
            return None

    def save(self):
        for mail in self.heapid_to_mail.values():
            mail.save()

    def create_new_mail(self):
        heapid = self.next_heapid()
        mail = Mail(heapid)
        self.heapid_to_mail[heapid] = mail
        return mail

    def index_mail(self, mail):
        self.messid_to_heapid[mail.get_messid()] = mail.get_heapid()

    def _add_mail_to_dicts(self, mail, heapid=None):
        if heapid == None:
            heapid = mail.get_heapid()
        self.heapid_to_mail[heapid] = mail
        self.messid_to_heapid[mail.get_messid()] = heapid

    def add_timestamp(self, mail):
        heapid = mail.get_heapid()
        date = mail.get_date()
        if date == '':
            return (0, heapid)
        else:
            tz = email.utils.parsedate_tz(date)
            timestamp = email.utils.mktime_tz(tz)
            return (timestamp, heapid)

    def get_threads(self):
        threads = {} # heapid -> [answered::(timestamp, heapid)]
        for mail in self.get_mails():
            if not mail.get_deleted():
                prev = mail.get_inreplyto()
                prev_heapid = None
                if prev != None:
                    if prev in self.messid_to_heapid:
                        prev_heapid = self.messid_to_heapid[prev]
                    elif prev in self.heapid_to_mail:
                        prev_heapid = prev
                if prev_heapid in threads:
                    threads[prev_heapid].append(self.add_timestamp(mail))
                else:
                    threads[prev_heapid] = [self.add_timestamp(mail)]
        t = {}
        for heapid in threads:
            threads[heapid].sort(sort_with_timestamp)
            t[heapid] = [ heapid2 for timestamp, heapid2 in threads[heapid] ]
        return t

class Server(object):

    def __init__(self, maildb):
        super(Server, self).__init__()
        self.maildb = maildb

    @staticmethod
    def get_setting(name):
        return file_to_string(name).strip()

    def connect(self):
        log('Reading settings...')
        
        host = config.get('server', 'host')
        port = int(config.get('server', 'port'))
        username = config.get('server', 'username')
        password = config.get('server', 'password')

        log('Connecting...')
        self.server = IMAP4_SSL(host, port)
        self.server.login(username, password)

        log('Connected')
        return self.server

    def close(self):
        self.server.close()

    def download_email(self, email_index, mail):

        header = self.server.fetch(email_index, '(BODY[HEADER])')[1][0][1]
        text = self.server.fetch(email_index, '(BODY[TEXT])')[1][0][1]
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
        mail.set_headers(headers)
        mail.set_body(text)
        mail.remove_google_stuff()

        for entry, author_regex in config.items('nicknames'):
            [author, regex] = config.get('nicknames', entry).split(' ',1)
            if re.match(regex, mail.get_author()):
                mail.set_author(author)
                break

    def download_new(self, lower_value=0):
        self.server.select("INBOX")[1]
        emails = self.server.search(None, '(ALL)')[1][0].strip()
        if emails != '':
            for email_index in emails.split(' '):
                if int(email_index) >= lower_value:
                    header = self.server.fetch(email_index, '(BODY[HEADER.FIELDS (MESSAGE-ID)])')[1][0][1]
                    messid = email.message_from_string(header)['Message-Id']
                    # mail: the mail in the database if already exists
                    mail = self.maildb.get_mail_by_messid(messid)
                    if mail == None:
                        mail = self.maildb.create_new_mail()
                        log('Downloading mail #%s.' % mail.get_heapid())
                        self.download_email(email_index, mail)
                        self.maildb.index_mail(mail)
                    else:
                        log('Mail #%s found.' % mail.get_heapid())
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

def sort_with_timestamp(x, y):
    if x[0] > y[0]:
        return 1
    elif x[0] == y[0]:
        return 0
    else:
        return -1

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

    def __init__(self, maildb):
        super(Generator, self).__init__()
        self.maildb = maildb

    def mail_to_html(self):
        for mail in self.maildb.get_mails():
            if not mail.get_deleted():
                with open(mail.get_htmlfile(), 'w') as f:
                    h1 = quote_html(mail.get_author()) + ': ' + quote_html(mail.get_subject())
                    f.write(html_header % (h1, 'heapindex.css', h1))
                    f.write('<pre>')
                    f.write(quote_html(mail.get_body()))
                    f.write('</pre>')
                    f.write(html_footer)

    def db_to_html(self):
        threads = self.maildb.get_threads()
        with open('mail.html','w') as f:
            f.write(html_header % ('Heap Index', 'heapindex.css', 'UMS Heap'))
            self.write_thread(threads, None, f, 0)
            f.write(html_footer)
        log('HTML generated.')

    def write_thread(self, threads, heapid, f, indent):
        if heapid != None:
            mail = self.maildb.heapid_to_mail[heapid]
            date = mail.get_date()
            if date != '':
                date = ("&nbsp; (%s)" % date) 
            from_ = re.sub('<.*?>','', mail.get_author())
            f.write(html_one_mail % (mail.get_htmlfile(), \
                                     quote_html(mail.get_subject()), \
                                     mail.get_heapid(), \
                                     quote_html(from_), \
                                     date))

        if heapid in threads:
            for heapid2 in threads[heapid]:
                self.write_thread(threads, heapid2, f, indent+1)

        if heapid != None:
            f.write("</div>\n")

##### Interface functions #####

def download_mail(from_ = 0):
    maildb = MailDB()
    server = Server(maildb)
    server.connect()
    server.download_new(int(from_))
    server.close()
    maildb.save()

def generate_html():
    maildb = MailDB()
    g = Generator(maildb)
    g.db_to_html()
    g.mail_to_html()

def delete_mail(*heapids):
    l = list(heapids)
    maildb = MailDB()
    for heapid in l:
        maildb.get_mail(heapid).set_deleted(True)
    maildb.save()

def change_nick(author_regex, new_author):
    author_regex = re.compile(author_regex)
    maildb = MailDB()
    for heapid in maildb.get_heapids():
        mail = maildb.get_mail(heapid)
        if author_regex.match(mail.get_author()):
            mail.set_author(new_author)
    maildb.save()

if __name__ == '__main__':
    argv = sys.argv[1:]
    if argv == []:
        download_mail()
        generate_html()
    else:
        funname = argv.pop(0)
        getattr(sys.modules[__name__], funname)(*argv)

