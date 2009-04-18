:mod:`heapmanip` explained
==========================

:class:`heapmanip.MailDB`

This class serves as both an outermost container for all posts
and as a representation of the relationships among them. The
most authentic list of all Post objects on the Heap is internally
MailDB.heapid_to_post.values(). Thus, heapid_to_post can be seen as the
most basic data member of MailDB.

heapid_to_post is a dict that, as the name suggests, assings posts
to heapids. (Mind you, 'heapid_to_post' is to be read as 'heapid =>
post', not as 'assigns heapid to post'.) This dict gets modified only by
_add_post_to_dicts, which itself is called upon by _load_from_disk() (an
offspring of __init__) and add_new_posts(). _load_from_disk() simply
fills up heapid_to_post by looking at the list of .mail files in the
mail directory, creating the Post objects on the fly, while
add_new_posts() adds already created Post objects. The Post object also
needs to be notified that it has been added to a MailDB via
Post.add_to_maildb. add_new_post() does this, but _load_from_disk() can
skip this, as Post.from_file() already includes this action.

heapid_to_post is then used as a source of all heapids, all posts and
of course the post-to-heapid mapping whenever needed; though it is
accessed by convenience functions, namely heapids(), real_posts() and
post(). Not many functions are to access heapid_to_post directly, as
it is a well-guarded implementation detail that the fewer know of, the
safer it is.

Another such dict is messid_to_heapid (messid => heapid). It is
written by _add_post_to_dicts, and read only by post_by_messid.

Values of heapid_to_post also include deleted posts. Deletion, as of
now, is a delicate matter. Removing the .mail file altogether would
result in downloading the deleted post again on the next syncing with
the IMAP server, so the .mail file stays in place for deleted posts,
albeit without any content but a header of two lines, a Message-Id:
(which we still need to match the .mail file to the e-mail in the IMAP
Inbox) and a Flag: deleted line. real_posts() return this untouched
list of all posts, thus including deleted ones. Should you need a list
that excludes these undead posts (and most probably you should), use
post().

If you have followed our trip this far, it is the first time you
encounter evidence a basic principle of MailDB's architecture. I've
already hinted that most of MailDB's data members are all generated
from the two authentic sources, heapid_to_post and messid_to_heapid.
Generating all these data members is expensive, so it is done only
when necessary. The necessity of regenerating is indicated by calling
touch(). This simple method does nothing but discard these generated
data members, the names of which can be found here::

   _posts
   _all
   _threadstruct
   _cycles
   _roots
   _threads

The names are pretty much self-explanatory, the exact structure is
documented in MailDB's docstring. (Here too, maybe in more detail.)

It is important to keep in mind that MailDB takes a lazy approach on
handling these members. If they are needed, and they are not there
(i.e. their value is None), they are produced, but no sooner.
See the :ref:`patterns_lazy_data_calculation` for the design pattern.

_posts is the first of these cached data structures. It gets generated
by _recalc_posts(), and cleared by touch(), of course. _recalc_posts()
generates this list simply via a list comprehension that excludes deleted
posts from the list of all posts (real_posts()).

The only function to call _recalc_posts() is posts(). This is where the
lazy approach mentioned before is applied: though posts() always calls
_recalc_posts(), the latter only performs the calculation if its results
are not cached in _posts.

posts() is a 'public' function, that is, other classes are welcome to
use it.

There is a reason for this. _all is another of those cached data
structure. At first sight, it may seem superfluous; how are "posts" and
"all posts" different? Answer: they are a different type. While _posts
stores a list, _all is of a PostSet type. PostSet is not merely a set
of posts; it also serves as a building unit of Heap -- the level above
Post. For example, you would use a PostSet to specify the posts to be
included in a section of the resulting HTML. More on PostSet later.

The relationship between heapid_to_post.values(), _post is that each
serves as a basis for the generation of the next. However, one may ask
why _posts (or posts()) is needed? It is used externally only once,
where _all (all()) would very probably do the job just as well.

TODO I guess I'll have a word with Csabi on this.

A heap is more than a flat collection of posts. (Proof: a mailing list
is more than a flat collection of messages, and a heap is the extension
of a mailing list.) Posts on the heap are linked into a structure along
the parent-child relationships among them. The resulting structure is
mathematically a forest, that is, a set of trees. (TODO Ask Csabi if
this is correct.)

For now, a given installation of Heapkeeper supports exactly one
heap (the  data structure), with exactly one config file describing one
mail directory, one HTML directory, and one IMAP message store -- hence
one MailDB. So, from now on, I'll be speaking of "the posts in a MailDB"
in the sense of "the posts on a heap". Those sensitive to inexact use
of terminology (respect!), please take note of this before reading on.

The following rules govern the structure of the posts in a MailDB:

* Post 'A' is said to be the parent of post 'B' iff the header of 'A' contains
  a particular type of reference to 'B'. (For the sake of clarity, this is the
  "In-Reply-To:" reference, the taken directly from the terminology of e-mail,
  but the reference here is via a heapid rather than a Message-ID. More on this
  later.)
* Every post may have zero or one parent.
* Every post may have any number of children.
* A post is in the same thread as its parent and its children. (Posts that are
  connected through parent/child relations form a thread.)

TODO Sync this with Csabi's recent hh-post on the revised nomenclature of
thread relations.

With all this made clear, we can now safely dive into the analysis of
the way MailDB represents these relations.

Following the pattern seen with _posts and _all, _threadstruct is a cached
data structure thrown away any time it becomes invalid, and regenerated
again only when needed. You can probably guess the names of the relevant
functions if you've followed this guide closely.

The name of _threadstruct is slightly misleading. This data structure
does not contain the thread structure of the heap explicitely; what
it does is storing a minimalistic structure from which the required
characteristics of the thread structure can be deduced.

_threadstruct is a dictionary. It assigns posts to their parents through
their respective heapids. In other words, indexing this dictionary with
a post's heapid yields a list of the heapids of the children of that
post. Posts without parents are assigned to None.

TODO It is still to be determined whether Heapkeeper would benefit
from a more explicit representation of the thread structure.

Cycles are dangerous to this system. Some functions are written in a
way that they fall in endless loops when the thread structure contains
loops. Examining the way post parent/child relationships are generated,
it is safe to say that a cycle indicates an error. Such a situation can
be caused by:
* Hash collision on the IMAP server when generating Message-ID's. Highly
unlikely; in the case of GMail, it would also probably require a date
wraparound. Beware Y10K!
* Error in the IMAP server when generating Message-ID's. More likely,
still not common.
* Error in Heapkeeper during the parsing, storing or matching of
Message-ID's. A fearsome possibility.
* Corruption of mail files. Since mail files are very often edited by
hand, this is the most probable reason why anyone will ever encounter
a cycle.

(TODO Ask Csabi if he introduced cycle detection code "just in case"
or he actually found cycles during development.)

The generation of _threadstruct, as you have probably guessed, happens
in _recalc_threadstruct().  This function is definitely worth a look.

At 23 lines, it is one of the longest functions in the whole program. It
defines and uses a single-line auxiliary function, add_timestamp. In the
first step, all posts are iterated on. For any post, the heapid of the
parent post is retrieved, and the post is added to a temporary dictionary,
using the parent's heapid as a key. If the key is new in the dictionary,
a new list with the post as a single element is added; otherwise, the list
already present as the value is expanded with the post's heapid. In this
step, the heapids are committed to the temporary array together with the
timestamp of the post. This allows for the sorting of the posts' heapids
in the lists in the next step. Finally, the timestamps are thrown away
using a list comprehension, retaining the chronologically sorted list of
heapids of child posts assigned to the heapid of any parent post, with
the chronologically ordered list of parentless posts assigned to None.

As I said before, this is a rather implicit representation of the
threads. From this dictionary, one can reconstruct the threads by starting
from each parentless thread, and indexing the dictionary with the heapid
obtained in the previous step, branching as needed.

The function iter_thread() is MailDB's built-in facility for traversing
_threadstruct. It is also one of the more complicated parts of the
program.

I have warned a bit earlier about functions intolerant to cycles. These
functions do not fail completely on such thread structures; however,
some posts will be inaccessible. It is this assumption upon which
the generation of _cycles, the list of threads contained in cycles is
based. This leads to some nontrivial but totally acceptable results. See
this example::

   0: 1
   1: 2
   2: 3
   4: 5
   5: 4, 6
   6: 7
   7: 8

Here, we would say that 4 and 5 are in a cycle. From the algorithm's
standpoint, "everything not reachable from roots is in a cycle", posts 4
to 8 are in a cycle. Since cycles mean errors, there is not much sense
in putting effort in recovering the maximum number of messages when
there's a cycle present. There's really not much point in easing the
symptoms that would urge the user to resolve the underlying problem.

From all this, one can probably have a clear insight into the meaning
of the remaining data structures. _cycles contains exactly what the name
implies: a list of all posts that are part of a cycle. The way this list
is compiled is intriguing, and gives the explanation for the peculiar
definition of "in a cycle". _recalc_cycles() starts out from the list
of all posts, then eliminating all posts reachable via iter_thread(). In
the end, only posts unreachable from the roots remain, and these are by
our definition the posts that are in cycles.

(Those familiar to git may find some similarities in concepts
and terminologies here. Just watch the pattern: posts form threads
according to a parent relationship, with some posts getting unreachable
at times. Beware, though: git repositories are represented by DAG's,
while heaps form multiple trees. The most obvious consequence of this
distinction is that threads on a heap never merge the way git branches
do.)

TODO Ask Csabi if the previous paragraph is actually helpful or only
confusing.

_cycles is only used in two places. One is to ensure the call to root()
is safe. The other is to add a special section in the index to contain
posts in cycles.

TODO The former use is a bit zealous. It is perfectly safe to use root()
even if there are cycled loops present, provided the post being examined
is itself root-reachable. I propose an alternative: keep a list (set?) of
posts touched during the search, and if a post is reached that is already
present in the set, return None. (I like to think of this approach as
the snake-game rule: the snake that hits itself dies.)

TODO Consider the time saved by eliminating this data structure.

