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

""":mod:`hkp_users` implements the "Users" plugin for Heapkeeper.

This plugin displays users' recent activity on hkweb pages.

The plugin can be activated in the following way::

    >>> import hkp_users
    >>> hkp_users.start()

"""


import datetime

import hkutils
import hkweb


def postpage_new_init(self, postdb):
    postpage_old_init(self, postdb)
    self.options.cssfiles.append('plugins/users/static/css/users.css')

def index_new_init(self, postdb):
    index_old_init(self, postdb)
    self.options.cssfiles.append('plugins/users/static/css/users.css')

def print_userlist(self):
    # Unused argument 'self' # pylint: disable=W0613
    last_access = hkweb.last_access
    now = datetime.datetime.now()
    userlist = []
    for user in last_access:
        delta = now - last_access[user]
        if delta < datetime.timedelta(0, 5 * 60):
            userlist.append('<li title="%s ago">%s</li>' %
                            (hkutils.humanize_timedelta(delta), user))
    return ('<div id="userlist">\n', 'Active users:\n',
            '<ul>\n', userlist, '</ul>\n', '</div>\n')

def index_print_additional_header(self):
    return (index_old_print_additional_header(self),
            print_userlist(self))

def postpage_print_additional_header(self, postid):
    return (postpage_old_print_additional_header(self, postid),
            print_userlist(self))

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
