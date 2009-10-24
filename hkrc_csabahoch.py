# -*- coding: utf-8 -*-

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

"""My (Csaba Hoch) hkrc."""


import datetime
import os
import subprocess
import time

import hkutils
import hklib
import hkgen
import hkcustomlib
import hkshell
import issue_tracker


class MyGenerator(hkgen.Generator):

    def __init__(self, postdb):
        """Constructor.

        **Arguments:**

        - `postdb` (|PostDB|)
        """

        super(MyGenerator, self).__init__(postdb)
        self.options.shortsubject = True
        self.options.shorttags = True

    def print_main_index_page(self):
        """Prints the main index page.

        **Returns:** |HtmlText|
        """

        normal_postitems = self.walk_thread(None)
        normal_postitems = self.reverse_threads(normal_postitems)

        if self._postdb.has_cycle():
            cycle_postitems = self.walk_postitems(self._postdb.walk_cycles())
            return (
                self.section(
                    '0', 'Posts in cycles',
                    self.print_postitems(cycle_postitems),
                    flat=True),
                self.section(
                    '1', 'Other posts',
                    self.print_postitems(normal_postitems)))
        else:
            return self.print_postitems(normal_postitems)


class MyTestGenerator(MyGenerator):

    def __init__(self, postdb):
        """Constructor.

        **Arguments:**

        - `postdb` (|PostDB|)
        """

        super(MyTestGenerator, self).__init__(postdb)

    def should_print_date(self, postitem):
        """Returns ``True`` if the post is flat, has no parent, or its parent
        it more than 3 days older than itself.

        **Arguments:**

        - `postitem` (|PostItem|)

        **Returns:** bool
        """

        post = postitem.post
        parent = self._postdb.parent(post)
        min_diff = datetime.timedelta(days=3)
        if postitem.pos == 'flat' or parent == None:
            return True
        if (post.date() != '' and parent.date() != '' and
            (post.datetime() - parent.datetime() >= min_diff)):
            return True
        return False

    def print_postitem_date(self, postitem):
        """Prints the date of the post item.

        It uses :func:`should_print_date` to decide whether or not the date
        should be printed.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        timestamp = postitem.post.timestamp()
        if timestamp != 0 and self.should_print_date(postitem):
            return hkgen.Generator.format_timestamp(self, timestamp)
        else:
            return ''


def gen_indices(postdb):
    g = issue_tracker.Generator(postdb)
    g.write_all()
    g = MyGenerator(postdb)
    g.write_all()

def gen_indices_fast(postdb):
    g = issue_tracker.Generator(postdb)
    g.calc()
    g.write_issues_sorted_page()
    g = MyGenerator(postdb)
    g.write_thread_pages()

hkshell.options.callbacks.gen_indices = gen_indices

@hkshell.hkshell_cmd()
def R(pps):
    """Mark thread as reviewed."""
    hkshell.aTr(pps, 'reviewed')

def main():
    hkshell.options.callbacks.gen_indices = gen_indices
    hkshell.options.save_on_ctrl_d = False
    hkshell.on('tpp')
    hkshell.on('s')
    hkshell.on('gi')

main()
