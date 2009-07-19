#!/usr/bin/python

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

"""This module starts :mod:`hkshell`, which is Heapkeeper's interactive
shell.

When the ``hkshell`` script is invoked (e.g. by typing ``./hkshell``), it just
executes the :mod:`hk` module, which imports the :mod:`hkshell` module and
invokes the :func:`hkshell.parse_args` and :func:`hkshell.main` functions.
:func:`hkshell.parse_args` parses the command line options.
:func:`hkshell.main` which executes command arguments of ``hkshell``, import
the given customization modules (``hkrc`` by default), and gives the user an
interpreter.
"""

import sys

import hklib
import hkshell

if __name__ == '__main__':

    (cmdl_options, args) = hkshell.parse_args()
    if cmdl_options.version:
        print 'Heapkeeper version %s' % (hklib.heapkeeper_version,)
        sys.exit(0)

    hkshell.main(cmdl_options, args)

