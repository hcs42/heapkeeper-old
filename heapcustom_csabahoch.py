#!/usr/bin/python
# -*- coding: utf-8 -*-

# My (Csaba Hoch) heapcustom.

import heapmanip
import subprocess
import time
import datetime

def sections(maildb):
    ps_all = maildb.all().copy()
    ps_heap = ps_all.collect.has_tag('heap')
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

def format_date(post):
    "post -> str"
    if post.date() == '':
        return None
    else:
        d = time.localtime(heapmanip.calc_timestamp(post.date()))
        return time.strftime('(%Y.%m.%d.)', d)

def read_date(post):
    "post_date -> datetime.datetime"
    return datetime.datetime.fromtimestamp(heapmanip.calc_timestamp(post.date()))

def gen_index(maildb):

    def date_fun(post, section):
        prev = maildb.prev(post)
        if section[2]['flat'] or \
           prev == None or \
           (post.date() != '' and prev.date() != '' and \
            (read_date(post) - read_date(prev) > 
             datetime.timedelta(days=5))):
            return format_date(post)
        else:
            return None

    sections_ = sections(maildb)
    g = heapmanip.Generator(maildb)
    g.index(sections_, write_toc=True, write_date=True,
            shortsubject=True, shorttags=True,
            date_fun=date_fun)

