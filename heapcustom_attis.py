# -*- coding: utf-8 -*-

# This file is part of Heapmanipulator.
#
# Heapmanipulator is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Heapmanipulator is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Heapmanipulator.  If not, see <http://www.gnu.org/licenses/>.

# Copyright (C) 2009 Attila Nagy
# Copyright (C) 2009 Csaba Hoch

"""My (Attis) heapcustom."""

import heapmanip
import heapcustomlib
import heaplib
import subprocess
import time
import datetime

def sections(maildb):
    exp = False
    eliminate = False

    # ps_all = összes levél
    ps_all = maildb.all().copy()

    # todo
    ps_todo = ps_all.collect.has_tag('todo')
    ps_todo |= ps_all.collect.body_contains("^<<<\!*todo")

    # heap
    ps_heap = ps_all.collect.has_tag('heap')
    if exp:
        ps_heap = ps_heap.exp()
    if eliminate:
        ps_all -= ps_heap

    # programozás
    ps_prog = ps_all.collect.has_tag('programozás')
    ps_prog |= ps_all.collect.has_tag('Programozás')
    if exp:
        ps_prog = ps_prog.exp()
    if eliminate:
        ps_all -= ps_prog

    # C és C++ programozás
    ps_ccpp = ps_all.collect.has_tag('c')
    ps_ccpp |= ps_all.collect.has_tag('C')
    ps_ccpp |= ps_all.collect.has_tag('c++')
    ps_ccpp |= ps_all.collect.has_tag('C++')
    if exp:
        ps_ccpp = ps_ccpp.exp()
    if eliminate:
        ps_all -= ps_ccpp

    # Python programozás
    ps_py = ps_all.collect.has_tag('python')
    ps_py |= ps_all.collect.has_tag('Python')
    if exp:
        ps_py = ps_py.exp()
    if eliminate:
        ps_all -= ps_py

    # politika
    ps_pol = ps_all.collect.has_tag('politika')
    ps_pol |= ps_all.collect.has_tag('Politika')
    if exp:
        ps_pol = ps_pol.exp()
    if eliminate:
        ps_all -= ps_pol

    res = [ heapmanip.Section("Todo", ps_todo, {'flat': True}),
            heapmanip.Section("Heap", ps_heap),
            heapmanip.Section("Programozás", ps_prog),
            heapmanip.Section("C és C++", ps_ccpp),
            heapmanip.Section("Python", ps_py),
            heapmanip.Section("Egyéb", ps_all)]
#    monthly = do_monthly(maildb)
#    if monthly != None:
#        res.extend(monthly)
    return res

def get_date_limits(maildb):
    "Gets the datetime of the earliest and newest posts in maildb."
    start_date, end_date = None, None
    for post in maildb.roots():
        if start_date == None:
            start_date = read_date(post)
        if end_date == None:
            end_date = read_date(post)
        else:
            if start_date > read_date(post):
                start_date = read_date(post)
            if end_date < read_date(post):
                end_date = read_date(post)
    return (start_date, end_date)

def get_month(year, month):
    months = ['január', 'február', 'március', 'április', 'május', 'június', 'július', \
        'augusztus', 'szeptember', 'október', 'november', 'december'] 
    return "%d %s" % (year, months[month - 1])

def get_posts_in_month(maildb, year, month):
    next_month = month + 1
    next_year = year
    if next_month == 13:
        next_year += 1
        next_month = 1
    return maildb.postset([post._heapid for post in maildb.roots() \
        if post.date() != '' \
            and read_date(post) > datetime.datetime(year, month, 1) \
            and read_date(post) < datetime.datetime(next_year, next_month, 1)])

def do_monthly(maildb):
    start_date, end_date = get_date_limits(maildb)
    curr_year, curr_month = start_date.year, start_date.month
    monthlist = []
    while datetime.datetime(curr_year, curr_month,1) < end_date:
        monthlist.append((get_month(curr_year, curr_month), \
            get_posts_in_month(maildb, curr_year, curr_month)))
        curr_month += 1
        if curr_month == 13:
            curr_year += 1
            curr_month = 1
    return [heapmanip.Section(*month) for month in monthlist]

def format_date(post):
    "post -> str"
    if post.date() == '':
        return "(nincs dátum!)"
    else:
        d = time.localtime(heaplib.calc_timestamp(post.date()))
        return "(" + time.strftime('%Y.%m.%d.', d) + ')'

def read_date(post):
    "post_date -> datetime.datetime"
    if post.date():
        return datetime.datetime.fromtimestamp(
                heaplib.calc_timestamp(post.date())
            )
    else:
        return None

def gen_indices(maildb):

    # Date options
    date_options = heapcustomlib.date_defopts()
    date_options.update({'maildb': maildb,
                         'timedelta': datetime.timedelta(days=5)})
    date_fun = heapcustomlib.create_date_fun(date_options)

    # Generator options
    genopts = heapmanip.GeneratorOptions()
    genopts.maildb = maildb
#    genopts.indices = [heapmanip.Index(sections(maildb)), heapmanip.Index(do_monthly(maildb),"monthly.html")]
    # new idea is:
    # - add static main index,
    # - do_montly() and store its results,
    # - iterate on months, add one new index per month, one section per index

    genopts.indices = [heapmanip.Index(sections(maildb))]
    months = do_monthly(maildb)
    for n in range(0, len(months)):
        genopts.indices.append(heapmanip.Index([months[n]],
                               "month_" + str(n + 1) + ".html"))

    genopts.write_toc = True
    genopts.shortsubject = True
    genopts.shorttags = True
    genopts.date_fun = date_fun

    # Generating the index
    heapmanip.Generator(maildb).gen_indices(genopts)

def gen_posts(maildb):
    # Generator options
    genopts = heapmanip.GeneratorOptions()
    genopts.maildb = maildb
    genopts.write_toc = True
    genopts.print_thread_of_post = True
#    genopts.indices = [heapmanip.Index(sections(maildb)), heapmanip.Index(do_monthly(maildb),"monthly.html")]
    genopts.indices = [heapmanip.Index(sections(maildb))]
    n = 0
    for month in do_monthly(maildb):
        genopts.indices.append(heapmanip.Index(month, str(n) + "html"))
        n += 1

    # Generating the posts
    heapmanip.Generator(maildb).gen_posts(genopts)

