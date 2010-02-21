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

# Copyright (C) 2009-2010 Attila Nagy
# Copyright (C) 2009-2010 Csaba Hoch

"""My (Attis) hkrc."""


import re

import hklib
import hkgen
import hkshell
import hkweb

import hk_issue_tracker

def main():
    hkshell.options.callbacks.gen_indices = gen_indices
    #hkshell.options.callbacks.gen_posts = gen_posts
    hkshell.on('save')
    web = hkweb.start()

def gen_indices(postdb):
    g = MyGenerator(postdb)
    g.write_all()
    g = hk_issue_tracker.Generator(postdb)
    g.write_all()

class MyGenerator(hkgen.Generator):

    def print_main_index_page(self):
        output = []
        postdb = self._postdb
        n = 0
        for title, posts, is_flat in sections(postdb):
            if is_flat:
                postitems = [hklib.PostItem(pos='flat', post=post, level=0)
                             for post in posts.sorted_list()]
            else:
                postitems = self.walk_exp_posts(posts)
            postitems = self.walk_postitems(postitems)
            content = self.print_postitems(postitems)
            n += 1
            output.append(self.section(n - 1, title, content, flat=is_flat))
        return output

def sections(postdb):
    exp = False
    eliminate = True

    # ps_all = all mail
    ps_all = postdb.all().copy()
    # ps_heap = Heap-related (scheduled to go to Hh)
    ps_heap = ps_all.collect.has_tag_from(('heap', 'hh', 'hk'))
    ps_nonheap = ps_all - ps_heap

    # ps_singles = all mail w/o answers
    ps_singles = postdb.roots()
    for post in postdb.all():
        ps_singles -= hklib.PostSet(postdb, [postdb.parent(post)])

    # tidy
    # we agreed that I (Attis) would primarily tidy UMS posts
    # (that means anything that has no Heap-related tags)
    # posts that belong here either:
    # * contain quote introduction (like "xyz wrote:")
    # * contain more quote lines than non-quote (may be OK)
    # * signed (no need for them, esp. quoted signatures)
    # * contain quoted lines, but have no parent or reference
    # * subject starts with lowercase letter (may be OK)
    # * contain obsolete metas
    # * of course we ignore posts already marked as reviewed

    regexp = '\>*\s*2([0-9]+\/)+[0-9]+\s*.*\<[a-z.-]+@[a-z.-]+\>'
    ps_tidy = ps_nonheap.collect.body_contains(regexp)
    ps_tidy |= ps_nonheap.collect.body_contains('wrote:\s*$')
    ps_tidy |= ps_nonheap.collect.body_contains('írta:\s*$')
    ps_tidy |= ps_nonheap.collect(overquoted)
    ps_tidy |= ps_nonheap.collect.body_contains('^\s*Csabi\s*$')
    ps_tidy |= ps_nonheap.collect.body_contains('^\s*Attis\s*$')
    ps_tidy |= ps_nonheap.collect.body_contains('^\s*Josh\s*$')
    ps_unheaded = ps_nonheap.collect(lambda p: not p.parent())
    ps_tidy |= ps_unheaded.collect.body_contains('^>')
    ps_tidy |= ps_nonheap.collect(
        lambda p: p.subject().decode('utf-8')[0] in
            u'abcdefghijklmnopqrstuvwxyzöüóőúéáűí')
    ps_tidy |= ps_nonheap.collect.body_contains('<<<')
    ps_tidy -= ps_all.collect.has_tag('reviewed')
    print '%d posts are problematic.' \
        % len(ps_tidy)

    # we agreed that it would be illegal to reply to an UMS post on Hh
    # so we are looking for Hh posts with non-Hh parents
    ps_illegal = ps_heap.collect(
        lambda p: postdb.parent(p) in ps_nonheap)
    print '%d posts break the UMS—Hh relationship rule.' \
        % len(ps_illegal)

    # todo
    ps_todo = ps_all.collect.has_tag('todo')
    ps_todo |= ps_all.collect.body_contains("^<<<\!*todo")
    ps_todo |= ps_all.collect.body_contains("^\[\!*todo")

    # heap
    if exp:
        ps_heap = ps_heap.exp()
    if eliminate:
        ps_all -= ps_heap

    # programozás
    ps_prog = ps_all.collect.has_tag_from(('Programozás', 'programozás'))
    if exp:
        ps_prog = ps_prog.exp()
    if eliminate:
        ps_all -= ps_prog

    # C és C++ programozás
    ps_ccpp = ps_all.collect.has_tag_from(('c', 'C', 'c++', 'C++'))
    if exp:
        ps_ccpp = ps_ccpp.exp()
    if eliminate:
        ps_all -= ps_ccpp

    # Python programozás
    ps_py = ps_all.collect.has_tag_from(('python', 'Python'))
    if exp:
        ps_py = ps_py.exp()
    if eliminate:
        ps_all -= ps_py

    # politika
    ps_pol = ps_all.collect.has_tag_from(('politika', 'Politika'))
    if exp:
        ps_pol = ps_pol.exp()
    if eliminate:
        ps_all -= ps_pol

    res = [
            ("Illegális Hh—UMS-viszony", ps_illegal, True),
            ("Takarítani", ps_tidy, True),
            ("Tennivalók", ps_todo, True),
            ("Cipősdoboz", ps_singles, True),
            ("Heap", ps_heap, False),
            ("Programozás", ps_prog, False),
            ("C és C++", ps_ccpp, False),
            ("Python", ps_py, False),
            ("Egyéb", ps_all, False)
        ]
    return res

def overquoted(post):
    all = 0
    quoted = 0
    for line in post.body().splitlines():
        all += 1
        if re.search('^\s*\>', line):
            quoted += 1
    return 100 * quoted / all > 70

@hkshell.hkshell_cmd()
def et(pps):
    """Tidy up a whole thread."""
    roots = []
    for post in hklib.PostSet(hkshell.postdb(), pps):
        roots.append(hkshell.postdb().root(post))
    for root in roots:
        for post in hkshell.postdb().iter_thread(root):
            hkshell.e(post.post_id())
    hkshell.g()

@hkshell.hkshell_cmd()
def lsr(pps):
    """Print a whole thread, ie. recursive ls."""
    hkshell.ls(hkshell.ps(pps).exp(), show_tags=True)

def review_status(root):
    """Returns the review status of a thread specified by its root."""
    ps = hkshell.ps(root).expf()
    has_reviewed = False
    has_unreviewed = False
    for p in ps:
        if p.has_tag('reviewed'):
            has_reviewed = True
        else:
            has_unreviewed = True
        if has_reviewed and has_unreviewed:
            return 'some'
    assert has_reviewed or has_unreviewed
    if not has_reviewed:
        return 'no'
    else:
        return 'all'

@hkshell.hkshell_cmd()
def statrev(base=None):
    """Prints some statistics on the review status of the Heap."""
    if base is None:
        base = hkshell.postdb().all()
    assert isinstance(base, hklib.PostSet)

    threads = base.expb().collect.is_root()
    n_threads = len(threads)
    n_posts = len(base)
    n_reviewed = len(base.collect.has_tag('reviewed'))
    p_reviewed = float(n_reviewed) / n_posts * 100
    counter = {'all': 0, 'some': 0, 'no': 0}

    for thread in threads:
        counter[review_status(thread)] += 1

    print 'Number of threads: %d' % (n_threads,)
    for status in counter.keys():
        n = counter[status]
        p = float(n) / n_threads * 100
        print 'Threads with %s posts reviewed: %d (%0.2f %%)' % \
            (status, n, p)
    print '\nNumber of posts: %d' % (n_posts,)
    print 'Reviewed posts: %d (%0.2f %%)' % (n_reviewed, p_reviewed)

def get_heap_time_bounds(base=None):
    """Returns the timestamps of the first and last post in the heap
    or a post set as a tuple of two `datetime.datetime` objects."""
    if base is None:
        base = hkshell.postdb().all()
    assert isinstance(base, hklib.PostSet)

    lall = list(base.collect(lambda x: x.datetime() is not None))
    lall.sort()
    first = lall[0].datetime()
    last = lall[-1].datetime()
    return (first, last)

def get_heap_timeunits(unit='month'):
    """Yields tuples of lower and upper timestamps for time units of
    a given length covering.

    Time units may be 'day's, 'month's, 'year's.

    TODO: Support 'week's."""

    def next_day(dt):
        assert isinstance(dt, datetime.datetime)
        n_dt = dt + datetime.timedelta(days=1)
        return datetime.datetime(n_dt.year, n_dt.month, n_dt.day)

    def next_year(dt):
        assert isinstance(dt, datetime.datetime)
        return datetime.datetime(dt.year+1, 1, 1)

    def next_month(dt):
        # months are slightly more tricky
        assert isinstance(dt, datetime.datetime)
        month = dt.month + 1
        year = dt.year
        while month > 12:
            month -= 12
            year += 1
        return datetime.datetime(year, month, 1)

    next_unit_dict = {
            'day': next_day,
            'month': next_month,
            'year': next_year
        }
    next_unit = next_unit_dict[unit]

    first, last = get_heap_time_bounds()
    lower_bound = first
    upper_bound = next_unit(first)
    if upper_bound > last:
        # the whole interval fits into one unit!
        yield (first, last)
    else:
        while upper_bound < last:
            yield (lower_bound, upper_bound)
            lower_bound = upper_bound
            upper_bound = next_unit(upper_bound)
            if upper_bound > last:
                yield (lower_bound, last)

@hkshell.hkshell_cmd()
def size(post, pure=True):
    counter = 0
    lines = post.body().split('\n')
    for line in lines:
        if pure:
            if len(line) == 0 or line[0] == '>':
                continue
        counter += len(line.decode('utf-8'))
    return counter

@hkshell.hkshell_cmd()
def statcontrib(base=None):
    """Prints some statistics on contribution to the Heap."""
    if base is None:
        base = hkshell.postdb().all()
    assert isinstance(base, hklib.PostSet)

    n_posts = len(base)
    first, last = get_heap_time_bounds(base)
    n_days = (last - first).days

    print 'Number of posts: %d' % (n_posts,)
    print 'Time elapsed: %d days' % (n_days,)
    avg_ppd = float(n_posts) / n_days
    print 'Average posts per day: %0.3f\n' % (avg_ppd,)

    names = ('anyone', 'Csabi', 'Josh', 'Attis')
    for name in names:
        if name == 'anyone':
            posts = base
        else:
            posts = base.collect(lambda p: p.author() == name)
        count = len(posts)
        ratio = float(count) / n_posts * 100
        avg_ppd = float(count) / n_days
        print 'Posts by %s: %d (%0.2f %%, %0.3f posts per day)' \
            % (name, count, ratio, avg_ppd)

        size_pure = 0
        size_full = 0
        for p in posts:
            size_pure += size(p,pure=True)
            size_full += size(p,pure=False)
        avg_cpp = float(size_pure) / count
        avg_cpd = float(size_pure) / n_days
        percent_quote = float(size_full - size_pure) / size_pure * 100
        print 'Characters in all posts: %d' % (size_full,)
        print 'Pure characters (excl. quotes): %d' % (size_pure,)
        print 'Average pure characters per post: %0.2f' % (avg_cpp,)
        print 'Average pure characters per day: %0.2f' % (avg_cpd,)
        print 'Percent of quotes: %0.2f %%\n' % (percent_quote,)

@hkshell.hkshell_cmd()
def statmill(base=None):
    """Prints statistics on contribution to the Heap.

    In the past, I have done similar statistics. I plan to do this
    every time the number of posts mod 1000 becomes 0."""

    # note: soon these should be separate heaps
    all = hkshell.postdb().all()
    heap = all.collect.has_tag_from(('hh', 'heap', 'hk'))
    nonheap = all - heap

    print '== Statistics for the whole Heap ==\n'
    statcontrib(all)
    print '== Statistics for the Heapkeeper Heap ==\n'
    statcontrib(heap)
    print '== Statistics for the UMS Heap ==\n'
    statcontrib(nonheap)

main()

# ----------- DEAD CODE ---------------
# No code beyond this point. The commented lines were obsoleted by the
# Generator overhaul (and the creation of hkgen). Functionality
# implemented here (custom date_fun, monthly indices) should eventually
# find their way to the new customized generator, MyGenerator.

#def date_fun(post, options):
#    root = post._postdb.root(post)
#    if hasattr(options, 'section'):
#        section = options.section
#        if section.is_flat or \
#           root == post:
#            return format_date(post)
#    if post.date() != '' and root.date() != '':
#        diff = read_date(post) - read_date(root)
#        if diff.days > 0:
#            return '(+%d days)' % diff.days
#        elif diff.seconds > 3600:
#            return '(+%d hours)' % (diff.seconds / 3600)
#        elif diff.seconds > 60:
#            return '(+%d minutes)' % (diff.seconds / 60)
#        else:
#            return None
#    else:
#        return "(nincs dátum!)"
#def get_date_limits(postdb):
#    "Gets the datetime of the earliest and newest posts in postdb."
#    start_date, end_date = None, None
#    for post in postdb.roots():
#        if start_date == None:
#            start_date = read_date(post)
#        if end_date == None:
#            end_date = read_date(post)
#        else:
#            if start_date > read_date(post):
#                start_date = read_date(post)
#            if end_date < read_date(post):
#                end_date = read_date(post)
#    return (start_date, end_date)
#
#def get_month(year, month):
#    months = ['január', 'február', 'március', 'április', 'május',
#              'június', 'július', 'augusztus', 'szeptember', 'október',
#              'november', 'december']
#    return "%d %s" % (year, months[month - 1])
#
#def get_posts_in_month(postdb, year, month):
#    next_month = month + 1
#    next_year = year
#    if next_month == 13:
#        next_year += 1
#        next_month = 1
#    return postdb.postset([post._heapid for post in postdb.roots() \
#        if post.date() != '' \
#            and read_date(post) > datetime.datetime(year, month, 1) \
#            and read_date(post) < \
#                datetime.datetime(next_year, next_month, 1)])
#
#def do_monthly(postdb):
#    start_date, end_date = get_date_limits(postdb)
#    curr_year, curr_month = start_date.year, start_date.month
#    monthlist = []
#    while datetime.datetime(curr_year, curr_month,1) < end_date:
#        monthlist.append((get_month(curr_year, curr_month), \
#            get_posts_in_month(postdb, curr_year, curr_month)))
#        curr_month += 1
#        if curr_month == 13:
#            curr_year += 1
#            curr_month = 1
#    return [hklib.Section(*month) for month in monthlist]
#
#def format_date(post):
#    "post -> str"
#    if post.date() == '':
#        return "(no date)"
#    else:
#        d = time.localtime(hkutils.calc_timestamp(post.date()))
#        return "(" + time.strftime('%Y.%m.%d.', d) + ')'
#
#def read_date(post):
#    "post_date -> datetime.datetime"
#    if post.date():
#        return datetime.datetime.fromtimestamp(
#                hkutils.calc_timestamp(post.date())
#            )
#    else:
#        return None
#
#def gen_posts(postdb, posts):
#    # Generator options
#    date_options = hkcustomlib.date_defopts()
#    date_options.update({'postdb': postdb,
#                         'timedelta': datetime.timedelta(days=0)})
#    date_fun = hkcustomlib.create_date_fun(date_options)
#
#    genopts = hklib.GeneratorOptions()
#    genopts.postdb = postdb
#    genopts.write_toc = True
#    genopts.print_thread_of_post = True
#    genopts.date_fun = date_fun
#
#    # Generating the posts
#    hklib.Generator(postdb).gen_posts(genopts, posts)

