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


def print_userlist(generator):
    # Unused argument  # pylint: disable=W0613
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

def start():
    """Starts the plugin."""

    # Adding code to the init method of the Generator classes
    def init2(self, postdb):
        # unused argument # pylint: disable=W0613
        self.options.cssfiles.append('plugins/users/static/css/users.css')
    hkutils.append_fun_to_method(hkweb.IndexGenerator, 'init', init2)
    hkutils.append_fun_to_method(hkweb.PostPageGenerator, 'init', init2)

    # Adding code to the print_additional_header method of the Generator
    # classes
    def print_additional_header2(self, info):
        # unused argument # pylint: disable=W0613
        return print_userlist(self)
    hkutils.append_fun_to_method(
        hkweb.IndexGenerator,
        'print_additional_header',
        fun=print_additional_header2,
        resultfun=lambda r1, r2: (r1, r2))
    hkutils.append_fun_to_method(
        hkweb.PostPageGeneratorGenerator,
        'print_additional_header',
        fun=print_additional_header2,
        resultfun=lambda r1, r2: (r1, r2))
