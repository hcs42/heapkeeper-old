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


def sections(maildb):
    ps_all = maildb.all().copy()

    # heap
    heap_tags = ['heap', 'Heap']
    ps_heap = ps_all.collect(has_tag(heap_tags))
    ps_all -= ps_heap

    # cp
    cp_tags = ['programozás', 'c++', 'C++', 'python', 'Python']
    ps_cp = ps_all.collect(has_tag(cp_tags))
    ps_all -= ps_cp

    # sections
    return [("Heap", ps_heap),
            ("Programozás", ps_cp),
            ("Egyéb", ps_all)]

def gen_index(maildb):

    # Date options
    date_options = heapcustomlib.date_defopts())
    date_fun = heapcustomlib.create_date_fun(date_options)

    # Generator options
    sections_ = sections(maildb)
    gen_options = heapcustomlib.generator_defopts()
    gen_options.update({'sections': sections_,
                    'write_toc': True,
                    'write_date': True,
                    'shortsubject': True,
                    'shorttags': True,
                    'date_fun': date_fun})

    # Generating the index
    heapmanip.Generator(maildb).index(gen_options)
