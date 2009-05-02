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

import subprocess
import time
import datetime
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
    ps_heap = ps_all.collect(has_tag(heap_tags))
    ps_all -= ps_heap

    # hh
    heap_tags = ['hh', 'Hh', 'HH']
    ps_hh = ps_all.collect(has_tag(heap_tags))
    ps_all -= ps_hh

    # cp
    cp_tags = ['programozás', 'c++', 'C++', 'python', 'Python']
    ps_cp = ps_all.collect(has_tag(cp_tags))
    ps_all -= ps_cp

    # sections
    index_hm = hklib.Index(filename='hm.html')
    index_hm.sections = [hklib.Section("Heap", ps_heap)]

    index_hh = hklib.Index(filename='hh.html')
    index_hh.sections = [hklib.Section("hh", ps_hh)]

    index_ums = hklib.Index(filename='ums.html')
    index_ums.sections = [hklib.Section("Cycles", hklib.CYCLES),
                          hklib.Section("Programozás", ps_cp),
                          hklib.Section("Egyéb", ps_all)]

    return [index_hm, index_hh, index_ums]
            

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
    genopts.write_toc = True
    genopts.shortsubject = True
    genopts.shorttags = True
    genopts.date_fun = date_fun

    # Generating the index
    hklib.Generator(postdb).gen_indices(genopts)

def gen_posts(postdb):
    date_options = hkcustomlib.date_defopts({'postdb': postdb})
    date_fun = hkcustomlib.create_date_fun(date_options)
    genopts = hklib.GeneratorOptions()
    genopts.postdb = postdb
    genopts.print_thread_of_post = True
    hklib.Generator(postdb).gen_posts(genopts)

hkshell.options.callbacks.gen_indices = gen_indices
hkshell.options.callbacks.gen_posts = gen_posts
hkshell.on('tpp')

@hkshell.shell_cmd
def mycmd():
    print 'Hi, this is my command.'
