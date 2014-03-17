#!/usr/bin/python
#
# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Common functions used in reporting.

Used by both command line tools and ui tools.
"""

from operator import itemgetter
import pprint
import textwrap


DISPLAY_WIDTH = 80
TAB_WIDTH = 4
BORDER = DISPLAY_WIDTH * '-'
SEPARATOR = (DISPLAY_WIDTH / 2) * '-'

# Only need is for wrapping with 3-level indenting.
wrapper = textwrap.TextWrapper(width=DISPLAY_WIDTH,
                               initial_indent=3 * TAB_WIDTH * ' ',
                               subsequent_indent=3 * TAB_WIDTH * ' ')


def PrintReportLine(text, indent=False, indent_level=1):
  """Helper to allow report string formatting (e.g. set tabs to 4 spaces).

  Args:
    text: String text to print.
    indent: If True, indent the line.
    indent_level: If indent, indent this many tabs.
  """
  if indent:
    fmt = '%s%%s' % (indent_level * '\t')
  else:
    fmt = '%s'
  print str(fmt % text).expandtabs(TAB_WIDTH)


def WrapReportText(text):
  """Helper to allow report string wrapping (e.g. wrap and indent).

  Actually invokes textwrap.fill() which returns a string instead of a list.
  We always double-indent our wrapped blocks.

  Args:
    text: String text to be wrapped.

  Returns:
    String of wrapped and indented text.
  """
  return wrapper.fill(text)


class Counter(object):
  """Replaces Collections.Counter when Python 2.7 is not available."""

  def __init__(self):
    """Establish internal data structures for counting."""
    self._counter = {}

  def DebugPrint(self):
    """For debugging show the data structure."""
    pprint.pprint(self._counter)

  def Increment(self, counter_key, counter_increment=1):
    """Increment a key.

    Args:
      counter_key: String key that will collect a count.
      counter_increment: Int to increment the count; usually 1.
    """
    self._counter.setdefault(counter_key, 0)
    self._counter[counter_key] += counter_increment

  @property
  def data(self):
    """Give access to the dictionary for retrieving keys/values."""
    return self._counter

  def FilterAndSortMostCommon(self, top_n=None):
    """Determine the top_n keys with highest counts in order descending.

    Args:
      top_n: Int count of the number of keys of interest. If None, list all.

    Returns:
      List of 2-tuples (key, count) in descending order.
    """
    results = [(k, v) for k, v in self._counter.iteritems()]
    if not top_n:
      top_n = len(results)
    return sorted(results, key=itemgetter(1), reverse=True)[:top_n]
