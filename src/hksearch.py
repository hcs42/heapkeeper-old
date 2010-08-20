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

# Copyright (C) 2010 Csaba Hoch

"""|hksearch| searches in the post database."""


import re

import hklib


def post_matches(post, regexp):
    """Returns whether a regexp can be found in a post.

    The functions tries to find the regexp in the post body, and basically in
    all attributes of the post: author, subject, tags, etc.

    **Argument:**

    - `post` (|Post|)
    - `regexp` (regexp)

    **Returns:** bool
    """

    if (regexp.search(post.author()) or
        regexp.search(post.subject()) or
        regexp.search(post.messid()) or
        regexp.search(post.date_str()) or
        regexp.search(post.parent()) or
        regexp.search(post.post_id_str()) or
        regexp.search(post.body())):
        return True
    for tag in post.tags():
        if regexp.search(tag):
            return True
    return False


def search(term, postset):
    """Returns a subset of the given post set that matches the search term.

    **Arguments:**

    - `term` (str)
    - `postset` (|PostSet|)

    **Returns:** |PostSet|
    """

    patterns = term.split()
    regexps = [re.compile(pattern, (re.MULTILINE | re.IGNORECASE))
               for pattern in patterns]

    def post_matches_any(post):
        """Returns whether the given post matches any regexp in the `regexps`
        list.

        **Argument:**

        - `post` (|Post|)

        **Returns:** bool
        """

        for regexp in regexps:
            if not post_matches(post, regexp):
                return False
        return True

    return postset.collect(post_matches_any)
