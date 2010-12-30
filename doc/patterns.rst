Design and code patterns
========================

This page describes design patterns and code patterns that are used in
Heapkeeper.

.. _creating_a_long_string_pattern:

Creating a long string
----------------------

Usage

   When we want to create a long string from many smaller pieces.

Concept

   We append the small pieces to a list, and we join the only in the end.

Code example

   ::

      def create_long_string():
          l = []
          l.append("first part of the string")
          l.append("second part of the string")
          # ...
          return ''.join(l)

Explanation

   Using string concatenation would be much more inefficient, because new
   strings would be created all the time. So don't do this::

      def create_long_string():
          s = ''
          s += "first part of the string"
          s += "second part of the string"
          ...
          return s

Used in

   * :class:`hkgen.BaseGenerator`

.. _lazy_data_calculation_pattern:

Lazy data calculation
---------------------

Usage

   When we want a class to provide data that is calculated from other data that
   is stored by the class.

Concept

   We calculate the data only when needed. An instance variable will store
   either the data, or None if the data is not calculated. The user of the
   class can use simple get-functions to get the data, which will be
   recalculated when needed. The user does not have to be aware of this lazy
   recalculating mechanism.

Code example

   ::

      class MyClass:
          def __init__(self):
              self._data1 = something
              self.touch()

          def touch(self):
              self._data2 = None
              self._data3 = None

          def data2(self):
              self._recalc_data2()
              return self._data2

          def _recalc_data2(self):
              if self._data2 == None:
                  pass
                  # calculating _data2 from _data1

          def data3(self):
              self._recalc_data2()
              return self._data2

          def _recalc_data3(self):
              if self._data3 == None:
                  data2 = self.data2()
                  # calculating _data3 from _data1

          def change_data1(self):
              # change data1
              self.touch()

Explanation

   ``MyClass`` has three instance variables: ``_data1``, ``_data2`` and
   ``_data3``. ``_data1`` is given and modified by the user of the class, or
   calculated from other objects. ``_data2`` and ``_data3``, on the other hand,
   are calculated from ``_data1``. To make the pattern a bit more interesting,
   ``_data3`` is calculated not only from ``_data1``, but also from ``_data2``.

   Our aim is to (re)calculate ``_data2`` and ``_data3`` only if necessary. The
   change_data1 method modifies ``_data1``. We could recalculate ``_data2`` and
   ``_data3`` after changing ``_data1``, but that would be inefficient, because
   maybe the user will change ``_data1`` a lot of times before wanting to
   access ``_data2`` and ``_data3``, and all the recalculatations before the
   last modification would be unnecessary.

   Thus, this pattern uses a system that both ``data2`` and ``_data3`` may be
   valid or invalid (independently). If they are valid, they represent the data
   that was calculated from the current ``_data1``. If they are invalid, they
   should be recalculated. A data structure (``_data2`` or ``_data3``) is
   invalid if it has the value None; otherwise it is valid.

   A logical consequence is that whenever ``_data1`` is changed, all calculated
   data has to be either recalculated or invalidated. The pattern chooses the
   latter solution. There is a function to invalidate all calculated data: the
   ``MyClass.touch`` function. It can also be used for initializing the
   instance variables of the calculated data structures.

   The recalculation is done by the private functions ``_recalc_data1`` and
   ``_recalc_data2``.

Used in

   * :class:`hklib.PostDB`

.. _options_pattern:

Options
-------

Usage

   When we want to handle options dynamically so that we can pass them around
   and they can have default values.

Concept

   We create a class, and instances of that class will represent a
   configuration of the options. One instance variable will represent one
   option.

Code example

   Code that implements an option set::

      class MyOptions(object):

          """Description.

          **Data attributes:**

          - `option1` (int) -- Description.
          - `option2` (str) --- Description. Default value: ``''``.
          """

          def __init__(self,
                       option1=hkutils.NOT_SET,
                       option2=''):

              """Constructor."""

              super(MyOptions, self).__init__()
              hkutils.set_dict_items(self, locals())

   Code that uses it::

      def f(myoptions):
          if myoptions.option1:
              ...

      def g1():
          myoptions = MyOptions()
          myoptions.option1 = 0
          myoptions.option2 = 'something'
          f(myoptions)

      def g2():
          f(MyOptions(option1=0))

Explanation

   One instance of the ``MyOptions`` class represents a configuration of the
   options.

   The options whose default value is ``hkutils.NOT_SET`` do not really have a
   default value. Functions like ``f`` expect that none of the options is
   ``NOT_SET``, so the options whose default value is ``NOT_SET`` should be set
   when functions like ``f`` are called.

Used in

   * :class:`hkgen.GeneratorOptions`
   * :class:`hklib.PostDBEvent`
   * :class:`hkshell.Options`
   * :class:`hkshell.Event`
