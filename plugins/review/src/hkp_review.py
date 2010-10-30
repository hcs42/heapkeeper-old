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

""":mod:`hkp_review` implements the "Review" plugin for Heapkeeper.

This plugin helps to set threads to "reviewed".

It defines a |hkshell| command (`r()` by default) that adds "reviewed" tag to
the given thread and commits all modifications to the post database. (It is
supposed that git is used for version controlling the post database.) The
plugin commits all modificaions because reviewing a thread may include
modifying other posts. The commit message will be generated from the subject of
the root post of thre thread.

The plugin also adds a "Set to reviewed" button to each thread page which calls
`r()` with that post as an argument.

The plugin can be activated in the following way::

    >>> import hkp_review
    >>> hkp_review.start()

"""


import hkutils
import hkshell
import hkweb
import tempfile
import os


def set_to_reviewed(prepost=None):
    """Sets the given thread to reviewed and commits all changes to the heap in
    which the thread is.

    **Argument:**

    - `prepost` (|PrePost| | ``None``) -- If all touched post are within one
      thread, this parameter may be ``None``, in which case Heapkeeper will
      find this thread.
    """

    if prepost is None:
        modified = hkshell.postdb().all().collect.is_modified()
        roots = modified.expb().collect.is_root()
        if len(roots) == 0:
            hkutils.log(
                'No modified posts. No action. Use the r(<post id>) format.')
            return
        elif len(roots) > 1:
            hkutils.log('More than one modified threads. No action.')
            return

        post = roots.pop()
        hkutils.log('Thread: ' + post.post_id_str())
    else:
        post = hkshell.p(prepost)
        if hkshell.postdb().parent(post) is not None:
            hkutils.log('The post is not a root. No action.')
            return

    # Saving the modifications
    hkshell.aTr(post, 'reviewed')
    hkshell.s()

    # Calculating the subject to be mentioned in the commit message
    subject = post.subject()
    if len(subject) > 33:
        subject = subject[:30] + '...'

    # Writing the commit message into a temp file
    f, filename = tempfile.mkstemp()
    os.write(f, 'Review: "' + subject + '" thread\n'
                '\n'
                '[review]\n')
    os.close(f)

    # Commiting the change in git
    heap_dir = hkshell.postdb()._heaps[post.heap_id()]
    oldcwd = os.getcwd()
    try:
        os.chdir(heap_dir)
        hkutils.call(['git', 'commit', '-aF', filename])
    finally:
        os.chdir(oldcwd)
        os.remove(filename)


class SetPostReviewed(hkweb.AjaxServer):
    """Sets the given post to reviewed.

    Served URL: ``/set-post-reviewed/<heap>/<post index>``"""

    def __init__(self):
        hkweb.AjaxServer.__init__(self)

    def execute(self, post_id, args):
        # Unused argument 'postitem' # pylint: disable=W0613
        """Sets the post to reviewed.

        **Argument:**

        - `args` ({})

        **Returns:** {'error': str} | {}
        """

        post = self._postdb.post(post_id)
        if post is None:
            return {'error': 'No such post: "%s"' % (post_id,)}

        set_to_reviewed(post)
        return {}


def start(review_command_name='r'):
    """Starts the plugin.

    **Argument:**

    - `review_command_name` (str) -- The name of the |hkshell| command that
      shall be defined.
    """

    hkshell.register_cmd(review_command_name, set_to_reviewed)
    hkweb.insert_urls(['/set-post-reviewed/(.*)',
                       'hkp_review.SetPostReviewed'])

    old_init = hkweb.PostPageGenerator.__init__

    def __init__(self, postdb):

        # __init__ method from base class 'PostPageGenerator' is not called
        # pylint: disable=W0231
        old_init(self, postdb)

        self.js_files.append('/plugins/review/static/js/hkp_review.js')

    hkweb.PostPageGenerator.__init__ = __init__
