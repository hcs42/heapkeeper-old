Documentation and coding conventions
====================================

   *Thus spake the Lord: Thou shalt indent with four spaces. No more, no
   less. Four shall be the number of spaces thou shalt indent, and the
   number of thy indenting shall be four. Eight shalt thou not indent,
   nor either indent thou two, excepting that thou then proceed to four.
   Tabs are right out.*

This file describes the documentation and coding conventions used by the
Heapkeeper project.

You should also read the Style Guide for Python code: :pep:`8`.
However, some recommendations of PEP 8 are overridden by this document.

This is an evolving set of conventions. Most of them were not used from the
beginning, thus there may be some code that does not use certain conventions.
This does not mean that you should not use them.

.. _commit_message_conventions:

Commit messages
"""""""""""""""

A commit message has three parts: a mandatory title and a topic, and an
optional description.

* Title:

    * It should not be more than 50 characters
    * It is generally a good idea to begin the title with a word that describes
      the scope of the change (e.g. the name of a module or a class).
    * Do not put a period after the title.

* Topic:

    * The topic should be preceded by a blank line.
    * The topic should be written between brackets.

* Description:

    * The description should be preceded by a blank line.
    * The description should not contain lines that have more than 79
      characters.
    * If the changes introduce incompatibilities that the users can notice
      (e.g. the format of the config file changes), it is generally worth
      describing them.
    * If it increases readability, it is a good idea to put code objects
      between ````` signs.

Example:

.. code-block:: none

    Doc: improved docstrings

    [development documentation]

    A class and a method have been documented with docstrings. The current
    format shall be used in all docstrings.

    The modified class is MyClass, the modified function is `it`.

Documentation
-------------

These conventions apply both to docstrings and documentation stored in ``rst``
files, since they are both reStructuredText texts.

* Use lines no longer than 79 characters.
* Use US spelling.

Functions
^^^^^^^^^

::

    def add(a, b):
        """Adds `b` to `a`.

        The more lengthy description can go here.

        Note: this is a very complicated function. Use it with care.

        **Arguments:**

        - `a` (int) -- The first number to add.
        - `b` (int) -- The second number to add. This is added to `a`.

        **Returns:** int

        **Example:** ::

            >>> add(1, 2)
            3
        """

        return a + b

Classes
^^^^^^^

::

    class Complex(object):

        """Represents a complex number.

        The more lengthy description can go here.

        **Data attributes:**

        - `re` (float) -- The real part.
        - `im` (float) -- The imaginary part.
        """

        def __init__(self, re=0.0, im=0.0):
            super(Complex, self).__init__()
            self.re = re
            self.im = im

Header levels
^^^^^^^^^^^^^

Use the following underline types in ``*.rst`` files:

.. code-block:: none

    Page title
    ==========

    Section
    -------

    Subsection
    ^^^^^^^^^^

    Subsubsection
    """""""""""""

    Paragraph
    '''''''''

    Subparagraph
    ::::::::::::

Use the following underline types in ``*.py`` files:

.. code-block:: none

    Paragraph
    '''''''''

    Subparagraph
    ::::::::::::

Python code
-----------

General
^^^^^^^

* Use four spaces as one indentation level.
* Use lines no longer than 79 characters.
* Use CamelCaseIdentifiers for class names, identifiers_with_underscore for
  function names and variable names. The only exception is when deriving from
  an existing class with CamelCase function names; in that case the methods of
  the derived class may have CamelCase letters, as well. Constants should be
  written with UPPER_CASE_LETTERS.

Classes
^^^^^^^

* Use only new-style classes, so if there is no other base class, 'object' is
  the base class.
* Always write a 'super' call into the __init__ function.
  (See `"Python's Super is nifty, but you can't use it" by James Knight`__.)
* Use underscore to prefix the private instance variables.
* If there is a function that returns the value of the instance variable, it
  should be called 'stuff' (and not 'get_stuff').
* If there is a function that sets the value of the instance variable, it
  should be called 'set_stuff'.

__ http://fuhm.net/super-harmful/

Yes::

   class A(object):

       def __init__(self):
           super(A, self).__init__()
           self._stuff = 0

       def stuff():
           """Returns stuff."""
           return self._stuff

       def set_stuff(stuff):
           """Sets stuff."""
           self._stuff = stuff

Branches
^^^^^^^^

* When writing a branch based on whether a variable is None or not, use
  explicit comparison.
* When writing a branch based on the value of a Boolean variable, use implicit
  comparison.

Yes::

   # thing is either None or something else
   if thing == None:

No::

   if thing:

Yes::

   # is_happy is a bool
   if is_happy:

No::

   if is_happy == False:

Backslashes at the end of the line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Try to omit backslashes at the and of the lines if possible.

Yes::

   return (this is a very long
           command that does not
           fit into one line)

No::

   return this is a very long \
          command that does not \
          fit into one line

* But be very careful with the ``raise`` statement, because ``"raise x,y"``
  means instantiating class ``x`` with a parameter ``y``, but ``"raise (x,y)"``
  means something else. But you may put parens around ``y``, if it is long.

   Yes::

      raise hkutils.HkException, \
             'We have a problem'

   No::

      raise (hkutils.HkException,
             'We have a problem')

   Yes::

      raise hkutils.HkException, \
            ('We have a problem with %s, which is very serious.' %
             problematic_thing)

Function arguments
^^^^^^^^^^^^^^^^^^

* Don't put extra (more than one) spaces anywhere (except for indentation).

Yes::

   a = f(1, 2, 3)
   b = f(11, 22, 33)
   c = f(111, 222, 333)

No::

   a = f(1,   2,   3)
   b = f(11,  22,   33)
   c = f(111, 222, 333)

Long argument list
^^^^^^^^^^^^^^^^^^

Yes::

   my_function(one_long_argument, another_long_argument,
                a_third_long_argument_that_does_not_fit_into_the_prev_line)

Yes::

   my_function(one_long_argument,
               another_long_argument,
               a_third_long_argument_that_does_not_fit_into_the_prev_line)

No::

   my_function(short_arg,
               short_arg2,
               short_arg3)

Yes::

   my_function(
       one_long_argument,
       another_long_argument,
       a_third_long_argument)

No::

   my_function(
       one_long_argument, another_long_argument,
       a_third_long_argument)

No::

   my_function(one_long_argument,
       another_long_argument,
       a_third_long_argument)

Initializing dictionaries and lists
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* If you break a dictionary into several lines, all entry should go into a
  separate line.
* This does not apply to lists.

Yes::

   d = {'something': 'anything',
        'anything': 'something',
        1:2}

Yes::

   dictionary_with_very_long_name = \
       {'something': 'anything',
        'anything': 'something',
        1:2}

No::

   d = {'something': 'anything', 'anything': 'something',
        1:2}

Yes::

   l = [something_very_very_long_1, something_very_very_long_2,
        something_very_very_long_3, something_very_very_long_4]

Yes::

   l = [something_very_very_long_1,
        something_very_very_long_2,
        something_very_very_long_3,
        something_very_very_long_4]

Yes::

   list_with_very_long_name = \
       [something_very_very_long_1, something_very_very_long_2,
        something_very_very_long_3, something_very_very_long_4]

Yes::

   list_with_very_long_name = \
       [something_very_very_long_1,
        something_very_very_long_2,
        something_very_very_long_3,
        something_very_very_long_4]


``%`` operator
^^^^^^^^^^^^^^

* When you format a string with the % operator and you have only one parameter
  to format, use the tuple syntax.

Yes::

    "%s" % (x,)

No::

    "%s" % x

No::

    "%s" % (x)

The reason is that printing a tuple may lead to surprises. To reduce the
possibility of a bug, always follow this convention, even if you are sure that
the parameter after the ``%`` operator is not a tuple. ::

    >>> x = (1,2)
    >>> "%s" % (x,)
    '(1, 2)'
    >>> "%s" % x
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    TypeError: not all arguments converted during string formatting
    >>> "%s" % (x)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    TypeError: not all arguments converted during string formatting
