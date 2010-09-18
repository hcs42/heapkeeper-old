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

# Copyright (C) 2010 Csaba Hoch

"""|hkbodyparser| parses the body of the posts."""


import re


class Segment(object):

    """Represents a segment of the body of a post.

    **Data attributes:**

    - `type` (str) -- The type of the segment. Possible values:

        - ``'normal'``: normal text (quotes, too)
        - ``'link'``: http or ftp links
        - ``'heap_link'``: link to a post on a heap

    - `quote_level` (int) -- The quote level: the numbers of ``'>'`` characters
      in the beginning of the line(s) of the segment.
    - `'is_meta'` (bool) -- Whether the text is meta text or not. (Meta text is
      text written between brackets)
    - `text` (str) -- The (unaltered) text of the segment.
    - `key` (str | ``None``) -- If the segment is a meta text, this is the
      meta key. Otherwise it is ``None``.
    - `value` (str | ``None``) -- If the segment is a meta text, this is the
      meta value. If the segment is a heap link, this is the id of the post.
      Otherwise it is ``None``.
    - `protocol` (str | ``None``) -- If the segment is a link, this is its
      protocol. Otherwise it is ``None.``
    """

    def __init__(self, type='normal', quote_level=0, is_meta=False, text='',
                 key=None, value=None, protocol=None):
        """Constructor.

        **Arguments:**

        - `type` (str)
        - `quote_level` (str)
        - `is_meta` (bool)
        - `text` (str)
        - `key` (str | ``None``)
        - `value` (str | ``None``)
        - `protocol` (str | ``None``)
        """

        self.type = type
        self.quote_level = quote_level
        self.is_meta = is_meta
        self.text = text
        self.key = key
        self.value = value
        self.protocol = protocol

    def __eq__(self, other):
        """Returns whether the segment is equal to another segment.

        **Argument:**

        - `other` (|Segment|)

        **Returns:** bool
        """

        return (self.is_similar(other) and
                self.text == other.text)

    def copy(self):
        """Returns a copy of the segment.

        **Returns:** |Segment|
        """

        result = Segment()
        for key, value in self.__dict__.items():
            setattr(result, key, value)
        return result

    def is_similar(self, other):
        """Returns whether the segment is equal to another segment if we don't
        count their text.

        **Argument:**

        - `other` (|Segment|)

        **Returns:** bool
        """

        # We examine all data members of the segments except for 'text', 'key'
        # and 'value'.

        # Checking that the segments have the same data members. (If they
        # don't, they are not similar.)
        keys = self.__dict__.keys()
        keys_other = other.__dict__.keys()
        if keys != keys_other:
            return False

        # Checking that all attributes except for 'text', 'key' and 'value',
        # have the same values in both segments; if it's not true, the segments
        # are not similar.
        keys.remove('text')
        keys.remove('key')
        keys.remove('value')
        for key in keys:
            if getattr(self, key) != getattr(other, key):
                return False

        # The segments are similar because all check passed.
        return True

    def __str__(self):
        """Converts the segment into a string.

        **Returns:** str
        """

        def attr_str(attr, default, print_repr=False):
            """Convert the given attribute to string.

            **Arguments:**

            - `attr` (str) -- The name of the attribute.
            - `default` (object) -- If the value of the attribute equals to
              `default`, an empty string will be returned.
            - `print_repr` (bool) -- If true, the ``repr`` function will be
              invoked on the value of the attribute.
            """

            value = getattr(self, attr)
            if value == default:
                return ''
            else:
                if print_repr:
                    value = repr(value)
                return '%s=%s, ' % (attr, value)

        return ('<' + self.type + ', ' +
                attr_str('quote_level', 0) +
                attr_str('key', None, print_repr=True) +
                attr_str('value', None, print_repr=True) +
                attr_str('protocol', None) +
                'text=' + repr(self.text) + '>')

    def get_prepost_id_str(self):
        """Returns the prepost id of the heap link.

        **Returns:** str
        """

        # Return the substring after "heap://"
        assert self.type == 'heap_link'
        return self.text[7:]

    def set_prepost_id_str(self, postid_str):
        """Sets the prepost id of the heap link.

        **Argument:**

        - `postid_str` (str)
        """

        assert self.type == 'heap_link'
        self.text = 'heap://' + postid_str


class Body(object):

    """Represents the body of a post.

    **Data attributes:**

    - `segments` ([|Segment|]) -- The segments of the body.
    """

    def __init__(self, segments=None):
        """Constructor.

        **Argument:**

        - `segments` ([|Segment|])
        """

        self.segments = segments if segments is not None else []

    def __str__(self):
        """Converts the segment into a string.

        **Returns:** str
        """

        return ''.join([str(segment) + '\n' for segment in self.segments])

    def body_str(self):
        """Converts the body into string.

        **Returns:** str
        """

        return ''.join([segment.text for segment in self.segments])


##### Parser functions #####


def segment_type_is(type, segments):
    """Returns whether the last item of `segments` exists and has the given
    type.

    **Argument:**

    - `type` (str)
    - `segments` ([|Segment|])

    **Returns:** bool
    """

    return len(segments) > 0 and segments[-1].type == type


def segment_condition(segments, condition):
    """Returns whether the last item of `segments` exists and has the given
    property.

    **Argument:**

    - `segments` ([|Segment|])
    - `condition` (fun(|Segment|) -> bool)

    **Returns:** bool
    """

    return len(segments) > 0 and condition(segments[-1])


def ensure_similar(segment, segments):
    """Ensures that the last element of `segments` is similar to `segment`.

    Returns the new or existing segment that is the last item of `segments`
    and which is similar to `segment`. (See :func:`Segment.is_similar`
    for the definition of similarity.)

    **Argument:**

    - `segment` (|Segment|)
    - `segments` ([|Segment|])

    **Returns:** |Segment|
    """

    if len(segments) == 0 or not segments[-1].is_similar(segment):
        new_segment = segment.copy()
        new_segment.text = ''
        new_segment.key = None
        new_segment.value = None
        segments.append(new_segment)
    return segments[-1]


def calc_quote_level(line):
    """Calculates the quote level of the given line.

    **Argument:**

    - `line` (str)

    **Returns:** (int, str, str)

    - `quote_level` (int) -- The quote level of the line.
    - `quote_str` (str) -- A string that contains the quote signs and the
      optional space after them.
    - `rest_str` (str) -- A string that contains the rest of the line.
    """

    # Calculating the quote level: how many '>' characters are in the
    # beginning of the line? One space after each '>' character is acceptable.
    match = re.match(r'((> ?)*)(.*)$', line)
    quote_str = match.group(1)
    rest_str = match.group(3)
    if quote_str == '':
        quote_level = 0
    else:
        # `quote_level` is the number of '>' characters in `quote_str`
        quote_level = len(['x' for ch in quote_str if ch == '>'])
    return quote_level, quote_str, rest_str


def parse_line_part(text, segments, sample_segment):
    """Parses the part of a line.

    **Argument:**

    - `text` (str) -- The text to be parsed.
    - `segments` ([|Segment|]) -- The segments that are resulted from the
      parsing will be appended to `segments`. Also, the last element of
      `segments` may be modified.
    - `sample_segment` (|Segment|) -- A segment that is similar to the one
      expected here.
    """

    # Nothing to parse, nothing to do
    if text == '':
        return

    urlregexp = r"^(.*)((http|https|ftp|heap)://([^ \t]*))(.*)$"
    match = re.match(urlregexp, text)

    # If the text contains a URL, we first parse the left side of the URL,
    # then the URL, then the right side of the URL.
    if match:

        before = match.group(1)
        address = match.group(2)
        protocol = match.group(3)
        inner_address = match.group(4)
        after = match.group(5)

        # Removing trailing dots
        while address[-1] in '.,;?:()':
            after = address[-1] + after
            address = address[:-1]

        if protocol in ('http', 'https', 'ftp'):
            link_segment = \
                Segment(type='link',
                        text=address,
                        quote_level=sample_segment.quote_level,
                        is_meta=sample_segment.is_meta,
                        protocol=protocol)
        else:
            link_segment = \
                Segment(type='heap_link',
                        text=address,
                        value=inner_address,
                        quote_level=sample_segment.quote_level,
                        is_meta=sample_segment.is_meta)

        parse_line_part(before, segments, sample_segment)
        segments.append(link_segment)
        parse_line_part(after, segments, sample_segment)

        return

    # If the text is a normal text, we append it to the last segment if that
    # is on the same quote level; otherwise we create a new segment.
    segment = ensure_similar(sample_segment, segments)
    segment.text += text

def parse_line(line, line_index, segments, lines, variables):
    """Parses a line.

    **Argument:**

    - `line` (str) -- The line to be parsed. Does not contain the ending
      linefeed.
    - `segments` ([|Segment|]) -- The segments parsed so far. This will be
      modified: the new segments will be appended to this list, and the last
      element of the list may be modified. The ending linefeed will be
      appended to the segment that will be the last in `segments`.
    - `variables` ({str: object}) -- Variables created and used by this
      function.
    """

    # If the current line is the continuation of a raw block...
    end_of_raw_block = variables.get('end_of_raw_block')
    if end_of_raw_block is not None:
        assert line_index <= end_of_raw_block
        segments[-1].text += line + '\n'

        # If this is the last line of the raw block, delete the
        # `end_of_raw_block` variable
        if line_index == end_of_raw_block:
            del variables['end_of_raw_block']
        return

    # If the current line is the continuation of a meta text...
    if segment_condition(segments, lambda segment: segment.is_meta):
        meta_segment = segments[-1]
        # ...and the meta text is closed
        if (len(line) > 0) and (line[-1] == ']'):
            variables['main_meta_segment'].value += line[:-1].rstrip()
            parse_line_part(line[:-1], segments, meta_segment)
            segment = ensure_similar(meta_segment, segments)
            segments[-1].text += ']'
            normal_segment = Segment(text='\n')
            segments.append(normal_segment)
        # ...and the meta text will still be continued
        else:
            variables['main_meta_segment'].value += line + '\n'
            parse_line_part(line, segments, meta_segment)
            segments[-1].text += '\n'
        return

    # If this is the beginning of a meta text...
    if (len(line) > 0) and (line[0] == '[') and (']' not in line[1:-1]):

        # ...which is a one-liner
        if line[-1] == ']':
            one_liner = True
            content = line[1:-1]
        # ...which will be continued
        else:
            one_liner = False
            content = line[1:]

        match = re.match(r'( *[^ \t]*)(.*)', content)
        assert match
        meta_segment = Segment(is_meta=True)
        key_text = match.group(1)
        value_text = match.group(2)
        meta_segment.key = key_text.strip()
        value = value_text.strip()
        meta_segment.value = value

        # The "[" and the key_text is added to `meta_segment`; the rest (which
        # is `value_text`) will be handled by parse_line_part
        meta_segment.text = '[' + key_text
        if one_liner:
            segments += [meta_segment]
            parse_line_part(value_text, segments, meta_segment)
            segment = ensure_similar(meta_segment, segments)
            segments[-1].text += ']'
            normal_segment = Segment(text='\n')
            segments += [normal_segment]
        else:
            variables['main_meta_segment'] = meta_segment
            meta_segment.value += '\n'
            segments += [meta_segment]
            parse_line_part(value_text, segments, meta_segment)
            if segments[-1].type != 'normal':
                normal_segment = Segment(is_meta=True)
                segments.append(normal_segment)
            segments[-1].text += '\n'
        return

    quote_level, quote_str, rest_str = calc_quote_level(line)

    # If this is the beginning of a raw block...
    if (len(rest_str) > 0) and (rest_str[0] in ' \t'):

        # Check that the previous line allows us to make this line a raw line
        # (if the previous line is on the same quote level and is not a raw
        # line, then this line cannot be a raw line either)
        if line_index == 0:
            prev_line_ok = True
        else:
            prev_line = lines[line_index - 1]
            prev_quote_level, prev_quote_str, prev_rest_str = \
                calc_quote_level(prev_line)
            if prev_quote_level != quote_level:
                prev_line_ok = True
            elif prev_rest_str == '':
                prev_line_ok = True
            else:
                prev_line_ok = False

        if prev_line_ok:

            # Check whether there is a line in the following paragraph that
            # does not start with whitespace
            i = line_index + 1
            lines_count = len(lines)
            end_of_raw_block = None # no raw block
            while True:

                # The body has ended and we haven't found a
                # non-whitespace-starting line
                if (i == lines_count):
                    end_of_raw_block = lines_count - 1
                    break

                i_quote_level, i_quote_str, i_rest_str = \
                    calc_quote_level(lines[i])

                # The quote level changed, so the last line of the raw block is
                # the previous line
                if i_quote_level != quote_level:
                    end_of_raw_block = i - 1
                    break

                # If we find an empty line, that line could be the end of the
                # raw block. Later we may find another line and set
                # `end_of_raw_block` then accordingly.
                if i_rest_str == '':
                    end_of_raw_block = i - 1
                    i += 1
                    continue

                # If we find a line that cannot be in a raw block, we stop the
                # loop.
                if i_rest_str[0] not in ' \t':
                    break

                i += 1

            if end_of_raw_block is not None:

                raw_segment = Segment(type='raw',
                                      quote_level=quote_level,
                                      text=line+'\n')
                segments.append(raw_segment)

                # If this is a multiline raw block, we store the index of its
                # last line in `variables`
                if end_of_raw_block != line_index:
                    variables['end_of_raw_block'] = end_of_raw_block
                return

    # If this is a normal text line
    if quote_level > 0:
        segment = ensure_similar(Segment(quote_level=quote_level), segments)
        segment.text += quote_str

    # `rest`: text after the quote signs
    sample_segment = Segment(quote_level=quote_level)
    parse_line_part(rest_str, segments, sample_segment)
    segment = ensure_similar(Segment(quote_level=quote_level), segments)
    segment.text += '\n'


def parse(body_str):
    """Parses the body of a post.

    All trailing white spaces are removed. If we disregard trailing white
    spaces, the contacenation of the text of the returned segments will be
    equal to `body_str`, i.e. the following equality will hold::

        re.subn(r'[ \\t]+\\n', r'\\n', body_str)[0] ==
        ''.join([segment.text for segment in parse(body_str).segments])

    **Argument:**

    - `body_str` (str)

    **Returns:** |Body|
    """

    lines = body_str.split('\n')

    # If the last character of `body_str` is \n, an extra empty string will
    # be present in `lines`. Now we remove it.
    if len(lines) >=1 and lines[-1] == '':
        del lines[-1]

    # segments ([Segment]) -- The list of segments. The parser functions
    # manipulate the end of this list.
    segments = []
    variables = {}
    for index, line in enumerate(lines):
        parse_line(line.rstrip(), index, segments, lines, variables)

    return Body(segments=segments)
