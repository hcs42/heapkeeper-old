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

import os
import subprocess
import time
import datetime
import hkutils
import hklib
import hkcustomlib
import hkshell

def has_tag(tags):
    def has_tag_fun(post):
        for tag in tags:
            if post.has_tag(tag):
                return True
        return False
    return has_tag_fun

def indices0(postdb):
    ps_all = postdb.all().copy()

    # heap
    heap_tags = ['heap', 'Heap']
    ps_hk = ps_all.collect(has_tag(heap_tags))
    ps_all -= ps_hk

    # hh
    heap_tags = ['hh', 'Hh', 'HH']
    ps_hh = ps_all.collect(has_tag(heap_tags))
    ps_all -= ps_hh

    # python
    python_tags = ['python', 'Python']
    ps_python = ps_all.collect(has_tag(python_tags))
    ps_all -= ps_python

    # git
    git_tags = ['git', 'Git']
    ps_git = ps_all.collect(has_tag(git_tags))
    ps_all -= ps_git

    # cp
    cp_tags = ['programozás', 'c++', 'C++']
    ps_cp = ps_all.collect(has_tag(cp_tags))
    ps_all -= ps_cp

    # indices
    index_hh = hklib.Index(filename='hh.html')
    index_hh.sections = [hklib.Section("hh", ps_hh)]

    index_ums = hklib.Index(filename='ums.html')
    index_ums.sections = [hklib.Section("Cycles", hklib.CYCLES),
                          hklib.Section("Heapkeeper", ps_hk),
                          hklib.Section("Python", ps_python),
                          hklib.Section("Git", ps_git),
                          hklib.Section("Programozás", ps_cp),
                          hklib.Section("Egyéb", ps_all)]

    return [index_hh, index_ums]
            

def sections1(postdb):
    ps = postdb.postset('1204').exp()
    # sections
    return [("Heap", ps)]

def gen_indices(postdb):

    # Date options
    date_options = hkcustomlib.date_defopts()
    date_options.update({
                         'postdb': postdb,
                         'timedelta': datetime.timedelta(days=5),
                         'date_format': '(%Y.%m.%d. %H:%M:%S)',
                         })
    date_fun = hkcustomlib.create_date_fun(date_options)

    # Generator options

    genopts = hklib.GeneratorOptions()
    genopts.postdb = postdb
    genopts.indices = indices0(postdb)
    genopts.write_toc = False
    genopts.shortsubject = True
    genopts.shorttags = True
    genopts.date_fun = date_fun

    # Generating the index
    hklib.Generator(postdb).gen_indices(genopts)

def gen_posts(postdb, posts):
    date_options = hkcustomlib.date_defopts({'postdb': postdb})
    date_fun = hkcustomlib.create_date_fun(date_options)
    genopts = hklib.GeneratorOptions()
    genopts.postdb = postdb
    genopts.date_fun = date_fun
    genopts.print_thread_of_post = True
    hklib.Generator(postdb).gen_posts(genopts, posts)

@hkshell.hkshell_cmd()
def a():
    hkshell.options.callbacks.gen_indices = gen_indices
    hkshell.options.callbacks.gen_posts = gen_posts
    hkshell.options.callbacks.edit_file = edit_file
    hkshell.options.save_on_ctrl_d = False
    hkshell.on('tpp')
    hkshell.on('s')
    hkshell.on('gi')
    hkshell.on('gp')

def get_content(file):
    return hkutils.file_to_string(file, return_none=True)

def edit_file(file):
    old_content = get_content(file, return_none=True)
    subprocess.call(['vim', '-f', file])
    return get_content(file, return_none=True) != old_content

@hkshell.hkshell_cmd()
def vim():
    def edit_file(file):
        old_content = get_content(file, return_none=True)
        subprocess.call(['vim', '-f', file])
        return get_content(file, return_none=True) != old_content
    hkshell.options.callbacks.edit_file = edit_file

@hkshell.hkshell_cmd()
def gvim():
    def edit_file(file):
        old_content = get_content(file, return_none=True)
        subprocess.call(['gvim', '-f', file])
        return get_content(file, return_none=True) != old_content
    hkshell.options.callbacks.edit_file = edit_file

@hkshell.hkshell_cmd()
def R(pps):
    """Mark thread as reviewed."""
    hkshell.atr(pps, 'r')

if os.path.exists('hcs/pure'):
    hklib.log('Pure mode.')
else:
    hklib.log('Normal mode.')
    a()

