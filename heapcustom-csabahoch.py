#!/usr/bin/python
# -*- coding: utf-8 -*-

# My (Csaba Hoch) heapcustom.

import heapmanip
import subprocess
import time

def sections(maildb):
    ps_all = maildb.all().copy()
    ps_heap = ps_all.collect.has_tag('heap').exp()
    ps_all -= ps_heap
    ps_cp = ps_all.collect.has_tag('programozás')
    ps_cp |= ps_all.collect.has_tag('c++')
    ps_cp |= ps_all.collect.has_tag('C++')
    ps_cp |= ps_all.collect.has_tag('python')
    ps_cp |= ps_all.collect.has_tag('Python')
    ps_cp = ps_cp.exp()
    ps_all -= ps_cp
    return [("Heap", ps_heap),
            ("Programozás", ps_cp),
            ("Egyéb", ps_all)]

def gen_index_html(maildb):

    def date_fun(post):
        if maildb.prev(post) == None:
            date_local = time.localtime(heapmanip.calc_timestamp(post.date()))
            return time.strftime('%Y.%m.%d.', date_local)
        else:
            return None

    sections_ = sections(maildb)
    g = heapmanip.Generator(maildb)
    g.index_html(sections_, write_toc=True, write_date=True,
                 shortsubject=True, shorttags=True,
                 date_fun=date_fun)

