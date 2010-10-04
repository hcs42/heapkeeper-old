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

import hkweb


# messages is the list of message lines. thread_lock is a dict that
# assigns locks to waiting threads. session_pos is a dict that assigns
# their current position in the message list to sessions.
messages = []
thread_lock = {}
session_pos = {}


class SendChatMessage:
    # "Class has no __init__ method" # pylint: disable-msg=W0232

    @hkweb.auth
    def POST(self):
        line = webpy.input()['l']
        user = getattr(self, 'user', '???')
        messages.append((user, line))
        for thread in thread_lock:
            thread_lock[thread].set()
        return "Line '%s' accepted." % line

class PollChatMessage:
    # "Class has no __init__ method" # pylint: disable-msg=W0232

    @hkweb.auth
    def GET(self, session_id):
        webpy.header('Content-type', 'text/html')
        thread_id = str(threading.current_thread())
        if session_id not in session_pos:
            session_pos[session_id] = 0
        if session_pos[session_id] == len(messages):
            thread_lock[thread_id] = threading.Event()
            thread_lock[thread_id].clear()
            thread_lock[thread_id].wait()
        while session_pos[session_id] < len(messages):
            msg_author, msg_text = messages[session_pos[session_id]]
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

postpage_old_init = hkweb.PostPageGenerator.__init__
index_old_init = hkweb.IndexGenerator.__init__

def postpage_new_init(self, postdb):
    postpage_old_init(self, postdb)
    self.js_files.append('/plugins/chat/static/js/hkp_chat.js')
    self.options.cssfiles.append('plugins/chat/static/css/chat.css')

def index_new_init(self, postdb):
    index_old_init(self, postdb)
    self.js_files = ['/external/jquery.js',
                     '/plugins/chat/static/js/hkp_chat.js']
    self.options.cssfiles.append('plugins/chat/static/css/chat.css')

def add_chat(self):
    # Unused argument 'self' # pylint: disable-msg=W0613
    return ('<div id="chatbox">\n',
            """
                <div id="chatmessages"></div>
                <input id="chattextinput"></input>
            """,
            '</div>\n')

def index_print_main(self):
    js_links = \
            [('<script type="text/javascript" src="%s"></script>\n' %
              (js_file,)) for js_file in self.js_files]
    return (self.print_searchbar(),
            add_chat(self),
            self.print_main_index_page(),
            js_links)

def postpage_print_main(self, postid):
    return (self.print_searchbar(),
            add_chat(self),
            self.print_post_page(postid))

def start():
    """Starts the plugin."""

    hkweb.IndexGenerator.__init__ = index_new_init
    hkweb.PostPageGenerator.__init__ = postpage_new_init

    hkweb.IndexGenerator.print_main = index_print_main
    hkweb.PostPageGenerator.print_main = postpage_print_main

    hkweb.insert_urls(('/chat-send', SendChatMessage))
    hkweb.insert_urls(('/chat-poll/(.*)', PollChatMessage))
