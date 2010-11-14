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

# Copyright (C) 2010 Attila Nagy

""":mod:`hkp_chat` implements real-time chat in hkweb.

This plugin implements real-time chat (instant messaging) in hkweb.

The plugin can be activated in the following way::

    >>> import hkp_chat
    >>> hkp_chat.start()

"""


import re
import threading
import web as webpy

import hkshell
import hkweb


# messages is the list of message lines. thread_lock is a dict that
# assigns locks to waiting threads. session_pos is a dict that assigns
# their current position in the message list to sessions.
messages = []
thread_lock = {}
session_pos = {}


class SendChatMessage:
    # "Class has no __init__ method" # pylint: disable=W0232

    @hkweb.auth
    def POST(self):
        line = webpy.input()['l']
        channel = webpy.input()['channel']
        user = getattr(self, 'user', '???')
        messages.append((channel, user, line))
        for thread in thread_lock:
            thread_lock[thread].set()
        return "Line '%s' accepted in channel '%s'." % (line, channel)

class PollChatMessage:
    # "Class has no __init__ method" # pylint: disable=W0232

    @hkweb.auth
    def GET(self, session_id):
        webpy.header('Content-type', 'text/html')
        channel = webpy.input()['channel']
        thread_id = str(threading.current_thread())
        if session_id not in session_pos:
            session_pos[session_id] = 0
        if session_pos[session_id] == len(messages):
            thread_lock[thread_id] = threading.Event()
            thread_lock[thread_id].clear()
            thread_lock[thread_id].wait()
        while session_pos[session_id] < len(messages):
            msg_channel, msg_author, msg_text = \
                messages[session_pos[session_id]]
            if msg_channel != channel:
                session_pos[session_id] += 1
                continue
            esc_msg = re.sub(r'[<>&]',
                          lambda m: {'<': '&lt;',
                                     '>': '&gt;',
                                     '&': '&amp;'}[m.group(0)],
                          msg_text)
            yield """<div class="chatmessage">
                <span class="chatmessagename">%s</span>
                <span class="chatmessagetext">%s</span>
            </div>""" % (msg_author, esc_msg)
            session_pos[session_id] += 1


def postpage_new_init(self, postdb):
    postpage_old_init(self, postdb)
    self.js_files.append('/plugins/chat/static/js/hkp_chat.js')
    self.options.cssfiles.append('plugins/chat/static/css/chat.css')

def index_new_init(self, postdb):
    index_old_init(self, postdb)
    self.js_files.append('/plugins/chat/static/js/hkp_chat.js')
    self.options.cssfiles.append('plugins/chat/static/css/chat.css')

def print_chat(self):
    # Unused argument 'self' # pylint: disable=W0613
    return ('<div id="chatbox">\n',
            """
                <div id="chatmessages"></div>
                <input id="chattextinput"></input>
            """,
            '</div>\n')

def threadid_js(post_id=None):
    if post_id is None:
        thread_id = ''
    else:
        thread_id = hkshell.postdb().root(hkshell.p(post_id)).post_id_str()
    return ("""<script type="text/javascript">var thread_id='%s';</script>""" %
            thread_id)

#def index_print_main(self):
#    #js_links = \
#    #        [('<script type="text/javascript" src="%s"></script>\n' %
#    #          (js_file,)) for js_file in self.js_files]
#    return (self.print_searchbar(),
#            print_additional(self),
#            self.print_main_index_page(),
#            threadid_js(),
#            print_js_links)

def postpage_print_additional_header(self, info):
    return (postpage_old_print_additional_header(self, info),
            threadid_js(info['postid']),
            print_chat(self))

def index_print_additional_header(self, info):
    return (index_old_print_additional_header(self, info),
            threadid_js(),
            print_chat(self))

def start():
    """Starts the plugin."""

    global postpage_old_init
    global index_old_init
    global postpage_old_print_additional_header
    global index_old_print_additional_header

    postpage_old_init = hkweb.PostPageGenerator.__init__
    index_old_init = hkweb.IndexGenerator.__init__
    postpage_old_print_additional_header = \
        hkweb.PostPageGenerator.print_additional_header
    index_old_print_additional_header = \
        hkweb.IndexGenerator.print_additional_header

    hkweb.IndexGenerator.__init__ = index_new_init
    hkweb.PostPageGenerator.__init__ = postpage_new_init
    hkweb.IndexGenerator.print_additional_header = \
        index_print_additional_header
    hkweb.PostPageGenerator.print_additional_header = \
        postpage_print_additional_header

    hkweb.insert_urls(('/chat-send', SendChatMessage))
    hkweb.insert_urls(('/chat-poll/(.*)', PollChatMessage))
