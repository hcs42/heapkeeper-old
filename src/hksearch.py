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


##### Regular expressions #####

# This functions shall be used instead of calling the re module directly. This
# will ensure that the same regexp options will be used everywhere.

regexp_options = (re.MULTILINE | re.IGNORECASE | re.UNICODE)

def matches(pattern, s):
    """Returns whether a string matches (contains) a pattern.

    **Arguments:**

    - `pattern` (str)
    - `s` (str)

    **Returns:** bool
    """

    return bool(re.search(pattern, s, regexp_options))

def matches_any(pattern, strings):
    """Returns whether a string matches (contains) any of the patterns.

    **Arguments:**

    - `pattern` (str)
    - `strings` (iterable(str))

    **Returns:** bool
    """

    for s in strings:
        if matches(pattern, s):
            return True
    return False


##### Targets #####

def whole_target_matches(post, pattern):
    """Returns whether the post matches the pattern.

    This function will return true if the pattern is contained anywhere in the
    post (subject, body, tags, etc.)

    **Arguments:**

    - `post` (|Post|)
    - `pattern` (str)

    **Returns:** bool
    """

    fields = \
        (post.author(),
         post.subject(),
         post.messid(),
         post.date_str(),
         post.parent(),
         post.post_id_str(),
         post.body())
    return \
        (matches_any(pattern, fields) or
         matches_any(pattern, post.tags()))

def date_match(target_type, post, pattern):
    """Returns whether the post matches the given date.

    See how dates are matches agaist the posts in the documentation of
    :func:`hklib.Post.before` and :func:`hklib.Post.after`.

    **Arguments:**

    - `target_type` (str): Either 'before' or 'after'.
    - `post` (|Post|)
    - `pattern` (str): The description of the date as described in
      :func:`hkutils.parse_date`.

    **Returns:** bool
    """

    dt_args = hkutils.parse_date(pattern)
    try:
        return getattr(post, target_type)(*dt_args)
    except Exception, e:
        msg = 'Incorrect date: %s\n%s' % (repr(pattern), str(e))
        raise hkutils.HkException(msg)

target_types = \
    {'whole': whole_target_matches,
     'heap': lambda post, pattern: matches(pattern, post.heap_id()),
     'author': lambda post, pattern: matches(pattern, post.author()),
     'subject': lambda post, pattern: matches(pattern, post.subject()),
     'tag': lambda post, pattern: matches_any(pattern, post.tags()),
     'message-id': lambda post, pattern: matches(pattern, post.messid()),
     'body': lambda post, pattern: matches(pattern, post.body()),
     'before': lambda post, pattern: date_match('before', post, pattern),
     'after': lambda post, pattern: date_match('after', post, pattern)}

def add_target_type(name, fun):
    """Adds a new target type.

    **Arguments:**

    - `name` (str) -- The name of the target type.
    - `fun` (fun(|Post|, str) -> bool) -- The function that decides whether a
      post matches a pattern.
    """

    target_types[name] = fun


##### search #####

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
        new_pattern = None

        # If str_target has the form of "<target_type>:<str>", then we will put
        # (<target_type>, <regexp for str>) into `new_target`
        for target_type in target_types.keys():
            if str_target.startswith(target_type + ':'):
                # We found the target type of the current target
                new_target_type = target_type
                new_pattern = str_target[(len(target_type) + 1):]
                break

        # Otherwise the target should be searched in the whole post
        if new_target_type is None:
            new_target_type = 'whole'
            new_pattern = str_target

        # If the pattern starts with a '-' sign, the effect of the search
        # should be negated (i.e. posts that don't match the pattern should
        # be found)
        if new_pattern.startswith('-'):
            new_pattern = new_pattern[1:]
            new_is_positive = False
        else:
            new_is_positive = True

        targets.append((new_target_type, new_pattern, new_is_positive))

    def post_matches_any(post):
        """Returns whether the given post matches any regexp in the `targets`
        list.

        **Argument:**

        - `post` (|Post|)

        **Returns:** bool
        """

        for (target_type, pattern, positive) in targets:
            matches = target_types[target_type](post, pattern)

            # (matches != positive) <=>
            # (matches and not positive) or (not matches and positive) =>
            # this post should not be in the search result
            if matches != positive:
                return False

        return True

    return postset.collect(post_matches_any)
