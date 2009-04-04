#!/usr/bin/python
# -*- coding: utf-8 -*-

# My (Csaba Hoch) heapcustom.

import heapmanip
import heapcustomlib
import subprocess
import time
import datetime

def has_tag(tags):
    def has_tag_fun(post):
        for tag in tags:
            if post.has_tag(tag):
                return True
        return False
    return has_tag_fun

def indices0(maildb):
    ps_all = maildb.all().copy()

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
    index_hm = heapmanip.Index(filename='hm.html')
    index_hm.sections = [heapmanip.Section("Heap", ps_heap)]

    index_hh = heapmanip.Index(filename='hh.html')
    index_hh.sections = [heapmanip.Section("hh", ps_hh)]

    index_ums = heapmanip.Index(filename='ums.html')
    index_ums.sections = [heapmanip.Section("Cycles", heapmanip.CYCLES),
                          heapmanip.Section("Programozás", ps_cp),
                          heapmanip.Section("Egyéb", ps_all)]

    return [index_hm, index_hh, index_ums]
            

def sections1(maildb):
    ps = maildb.postset('1204').exp()
    # sections
    return [("Heap", ps)]

def gen_indices(maildb):

    # Date options
    date_options = heapcustomlib.date_defopts()
    date_options.update({
                         'maildb': maildb,
                         'timedelta': datetime.timedelta(days=5),
                         'date_format': '(%Y.%m.%d. %H:%M:%S)',
                         })
    date_fun = heapcustomlib.create_date_fun(date_options)

    # Generator options

    genopts = heapmanip.GeneratorOptions()
    genopts.maildb = maildb
    genopts.indices = indices0(maildb)
    genopts.write_toc = True
    genopts.shortsubject = True
    genopts.shorttags = True
    genopts.date_fun = date_fun

    # Generating the index
    heapmanip.Generator(maildb).gen_indices(genopts)

def gen_posts(maildb):
    date_options = heapcustomlib.date_defopts({'maildb': maildb})
    date_fun = heapcustomlib.create_date_fun(date_options)
    genopts = heapmanip.GeneratorOptions()
    genopts.maildb = maildb
    genopts.print_thread_of_post = True
    heapmanip.Generator(maildb).gen_posts(genopts)

def main(handlers):
    pass
    
