#!/usr/bin/python

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

# global variables
mail_dir = 'mail'

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

def get_next_mailfile():
    """Returns a filename with a *.mail form, such that there is no file with
    that name."""
    i = 1
    while i != 0:
        filename = os.path.join(mail_dir,('%d.mail' % i))
        if os.path.exists(filename):
            i += 1
        else:
            i = 0
    return filename

def cut(s):
    return re.sub('[\n\r].*', '', s)

def utf8(s, charset):
    if charset != None:
        return s.decode(charset).encode('utf-8')
    else:
        return s

def remove_google_stuff(text):
    r = re.compile(r'--~--~---------~--~----~------------~-------~--~----~\n.*?\n-~----------~----~----~----~------~----~------~--~---\n', re.DOTALL)
    return r.sub('', text)

def download_email(server, email_index, output_file):
    """Writes the email with the given index to given file."""

    header = server.fetch(email_index, '(BODY[HEADER])')[1][0][1]
    text = server.fetch(email_index, '(BODY[TEXT])')[1][0][1]
    message = email.message_from_string(header+text)
    output = ""
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
            value = re.sub(r'\n',r'\n ',value)
            output += attr + ': ' + value + '\n'

   
    encoding = message['Content-Transfer-Encoding']
    if encoding != None:
        if encoding.lower() == 'base64':
            text = base64.b64decode(text)
        elif encoding.lower() == 'quoted-printable':
            text = quopri.decodestring(text)
    charset = message.get_content_charset()
    text = utf8(text, charset)

    text = re.sub(r'\r\n',r'\n',text)
    text = remove_google_stuff(text)
    output += '\n' + text
    string_to_file(output, output_file)


def get_setting(name):
    return file_to_string(name).strip()

def get_email_file(email_index):
    return os.path.join(mail_dir, "%d.mail" % email_index)

def email_exists(email_index):
    return os.path.exists(get_email_file(email_index))

def connect(log = True):
    if log:
        print 'Reading settings...'
    host = get_setting('host')
    port = int(get_setting('port'))
    username = get_setting('username')
    password = get_setting('pw')

    if log:
        print 'Connecting...'
    server = IMAP4_SSL(host, port)
    server.login(username, password)

    if log:
        print 'Connected'

    return server

def read_mailfiles():
    emails_i = {} # mailfile -> headers
    emails_m = {} # message_id -> mailfile

    for email_file in os.listdir(mail_dir):
        if email_file[-5:] == '.mail':
            f = open(os.path.join(mail_dir,email_file))
            headers = read_headers(f)
            f.close()
            emails_i[email_file] = headers
            emails_m[headers['Message-Id']] = email_file

    return emails_i, emails_m

def download_emails(log = True):

    if not os.path.exists(mail_dir):
        os.mkdir(mail_dir)
    emails_i, emails_m = read_mailfiles()

    server = connect(log)
    server.select("INBOX")[1]
    emails = server.search(None, '(ALL)')[1][0]


    emails = emails.strip()
    if emails != '':
        for email_index in emails.split(' '):
            header = server.fetch(email_index, '(BODY[HEADER.FIELDS (MESSAGE-ID)])')[1][0][1]
            message_id = email.message_from_string(header)['Message-Id']
            if message_id not in emails_m:
                mailfile = get_next_mailfile()
                if log:
                    print 'Downloading mail #%s.' % mailfile
                download_email(server, email_index, mailfile)
            else:
                mailfile = emails_m[message_id]
                if log:
                    print 'Mail #%s found.' % strip_mailfile(mailfile)

    server.close()
    if log:
        print 'Downloading finished.'

def mysort(x,y):
    if x[0] > y[0]:
        return 1
    elif x[0] == y[0]:
        return 0
    else:
        return -1

def read_headers(f):
    headers = {}
    line = f.readline()
    while line != '\n':
        m = re.match('([^:]+): (.*)', line)
        key = m.group(1)
        value = m.group(2)
        line = f.readline()
        while line != '\n' and line[0] == ' ':
            value += '\n' + line[1:-1]
            line = f.readline()
        headers[key] = value
    return headers

def add_timestamp(email_file, emails_i):
    date = emails_i[email_file].get('Date')
    if date == None:
        return (0, email_file)
    else:
        tz = email.utils.parsedate_tz(date)
        timestamp = email.utils.mktime_tz(tz)
        return (timestamp, email_file)

def strip_mailfile(email_file):
    return email_file[:-5]

def email_txt_file(email_file):
    return email_file[:-5]+'.txt'

html_header = """\
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
    <title>Heap Index</title>
    <link rel=stylesheet href="heapindex.css" type="text/css">
  </head>
  <body>
    <h1 id="header">UMS Heap</h1>

"""

html_footer = """
  </body>
</html>
"""

html_one_mail = """\
<div class="mail">
<a href="mail/%s">
<span class="subject">%s</span>
<span class="index">&lt;%s&gt;</span>
<span class="author">"%s"</span>
<span class="timestamp">%s</span>
</a>
"""

def generate_html():
    emails_i, emails_m = read_mailfiles()
    answers = {} # email_file -> [answered::(timestamp, email_file)]

    for email_file, headers in emails_i.items():
        # prev_mid: PREVious Message ID
        # prev_ei: PREVious Email Index
        prev_mid = headers.get('In-Reply-To')
        if prev_mid != None and prev_mid in emails_m:
            prev_ei = emails_m[prev_mid]
        else:
            prev_ei = 0
        if prev_ei in answers:
            answers[prev_ei].append(add_timestamp(email_file, emails_i))
        else:
            answers[prev_ei] = [add_timestamp(email_file, emails_i)]

    def write_thread(answers, email_file, f, indent):
        if email_file != 0:

            # copying *.mail -> *.txt
            email_file_new = email_txt_file(email_file)
            email_file_full = os.path.join(mail_dir, email_file)
            email_file_new_full = os.path.join(mail_dir, email_file_new)
#            if not os.path.exists(email_file_new_full):
            shutil.copyfile(email_file_full, email_file_new_full)

            index = strip_mailfile(email_file)
            # writing into mail.html
            headers = emails_i[email_file]
            subject = headers['Subject'] if 'Subject' in headers else ''
            date_str =  ("&nbsp; (%s)" % headers['Date']) if 'Date' in headers else ''
            author = re.sub('<.*?>','',headers['From'])
            f.write(html_one_mail % \
                    (email_file_new, subject, index, author, date_str))

            #f.write('%s <a href="%s/%s">%s</a>&nbsp;&nbsp;<i>%s</i>%s<br>\n' % \
            #        ('&nbsp;&nbsp;' * indent * 4, mail_dir, email_file_new, \
            #        subject, author, date_str))
        if email_file in answers:
            answers[email_file].sort(mysort)
            for timestamp, email_file_2 in answers[email_file]:
                write_thread(answers, email_file_2, f, indent+1)
        f.write("</div>\n")

    f = open('mail.html','w')
    f.write(html_header)
    write_thread(answers, 0, f, 0)
    f.write(html_footer)
    f.close()

if __name__ == '__main__':
    download_emails()

