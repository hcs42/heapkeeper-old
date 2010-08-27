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

import hkutils
import hklib


def post_matches(post, target_type, target_content):
    """Returns whether a target can be found in a post.

    **Arguments:**

    - `post` (|Post|)
    - `target_type` (str) -- This parameter specifies the type of the target.
      Currently it means where the target should be searched for. It is one of
      the following strings: ``'whole'``, ``'heap'``, ``'author'``,
      ``'subject'``, ``'tag'``, ``'message-id'``, ``'body'``. ``'whole'`` means
      that the whole post (all attributes and body included) are searched for;
      ``'heap'`` means that the name of the heap is examined; etc.
    - `target_content` (str | regexp) -- This parameter is considered to be a
      regular expression and it is search in the strings specified by the
      `target_type` parameter.

    **Returns:** bool
    """

    t = target_content

    if target_type == 'whole':
        if (re.search(t, post.author()) or
            re.search(t, post.subject()) or
            re.search(t, post.messid()) or
            re.search(t, post.date_str()) or
            re.search(t, post.parent()) or
            re.search(t, post.post_id_str()) or
            re.search(t, post.body())):
            return True
        for tag in post.tags():
            if re.search(t, tag):
                return True
        return False
    elif target_type == 'heap':
        return bool(re.search(t, post.heap_id()))
    elif target_type == 'author':
        return bool(re.search(t, post.author()))
    elif target_type == 'subject':
        return bool(re.search(t, post.subject()))
    elif target_type == 'tag':
        for tag in post.tags():
            if re.search(t, tag):
                return True
    elif target_type == 'message-id':
        return bool(re.search(t, post.messid()))
    elif target_type == 'body':
        return bool(re.search(t, post.body()))
    else:
        msg = 'Unknown target type: %s'
        raise hkutils.HkException(msg % repr(target_type))


def search(term, postset):
    """Returns a subset of the given post set that satisfies all search targets
    in the given search term.

    **Arguments:**

    - `term` (str)
    - `postset` (|PostSet|)

    **Returns:** |PostSet|
    """

    # StrTarget examples: 'cont.*ent', 'heap:myheap'
    # Target examples: ('regexp', 'cont.*ent'), ('heap', 'myheap')

    str_targets = term.split() # [StrTarget]
    targets = [] # [Target]
    for str_target in str_targets:
        new_target_type = None
        new_target_content = None

        # If str_target has the form of "<target_type>:<str>", then we will put
        # (<target_type>, <regexp for str>) into `new_target`
        for target_type in ('heap', 'author', 'subject', 'tag', 'message-id',
                            'body'):
            if str_target.startswith(target_type + ':'):
                # We found the target type of the current target
                new_target_type = target_type
                new_target_content = str_target[(len(target_type) + 1):]
                break

        # Otherwise the target should be searched in the whole post
        if new_target_type is None:
            new_target_type = 'whole'
            new_target_content = str_target

        regexp = re.compile(new_target_content, (re.MULTILINE | re.IGNORECASE))
        targets.append((new_target_type, regexp))

    def post_matches_any(post):
        """Returns whether the given post matches any regexp in the `regexps`
        list.

        **Argument:**

        - `post` (|Post|)

        **Returns:** bool
        """

        for (target_type, target_content) in targets:
            if not post_matches(post, target_type, target_content):
                return False
        return True

    return postset.collect(post_matches_any)
