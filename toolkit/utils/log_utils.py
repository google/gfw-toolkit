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

"""Common logging setup and utility functions."""

import logging
import os
import tempfile
import time


# There are messages emitted by libraries using INFO (20) and WARNING (30)
# that we supress. They can be observed using our --verbose. Add classes of
# our app messages that are observed while still hiding INFO and WARNING.
APPINFO = 35  # Higher than WARNING but lower than ERROR.
APPWARNING = 36  # Higher than APPINFO but lower than ERROR.


def GetLogFileName():
  """Helper to produce the log file name."""
  return os.path.join(tempfile.gettempdir(), 'cse_api_tool.log')


def SetupLogging(verbose_flag):
  """Initialize logging and handle --verbose option.

  Since apiclient discovery uses INFO level (20) for noisy logging of
  URLS, we define a level 35 APPINFO level for normal app info logging.

  Args:
    verbose_flag: command line verbose flag.

  Returns:
    Initialized logger.
  """
  logging.addLevelName(APPINFO, 'APPINFO')
  logging.addLevelName(APPWARNING, 'APPWARNING')
  if verbose_flag:
    logging_level = logging.DEBUG
    print 'Showing VERBOSE output.'
  else:
    logging_level = APPINFO

  # Setup logging handler to file of DEBUG+ messages. Messages include
  # timestamp and messages append to the logfile.
  logging.basicConfig(level=logging_level,
                      format='%(asctime)s %(levelname)-8s %(message)s',
                      datefmt='%Y%m%d %H:%M:%S',
                      filename=GetLogFileName(),
                      filemode='a')

  # Setup logging handler to console of INFO+ messages.
  # Use them as PRINT messages.
  console_handler = logging.StreamHandler()
  console_handler.setLevel(logging_level)
  # Set a format which is simpler for console use (no time/date prefix).
  # We do not use multiple-area logging so we do not:
  # a) supply a area-string when acquiring a logger
  # b) show an area-string %(name) in our formatters
  # c) set a global logger since logging.getLogger('') retrieves the same
  #    instance across modules.
  console_formatter = logging.Formatter('%(levelname)-8s %(message)s')
  # tell the handler to use this format
  console_handler.setFormatter(console_formatter)
  # add the handler to the root logger
  logger = logging.getLogger('')
  logger.addHandler(console_handler)


def LogDebug(msg):
  """Utility function to log debug messages to users.

  Should be used for detailed output that is only useful when working to
  understand unexpected behaviors.

  Args:
    msg: String with the message to print/log.
  """
  logging.getLogger('').debug(msg)


def LogInfo(msg):
  """Utility function to log normal messages to users.

  Should be used for normal output that will be shown and logged to file.

  Args:
    msg: String with the message to print/log.
  """
  logging.getLogger('').log(APPINFO, msg)


def LogWarning(msg):
  """Utility function to log warning messages to users.

  Should be used for warning output that will be shown and logged to file.

  Args:
    msg: String with the message to print/log.
  """
  logging.getLogger('').log(APPWARNING, msg)


def LogError(msg, error_exception=None):
  """Utility function to log errors to screen and log file.

  Helps ensure common message-formatting.

  Args:
    msg: String with the message to print/log.
    error_exception: If used in an except, pass e to show exception string in
                     a consistent format.
  """
  if error_exception:
    logging.getLogger('').error('%s\n\t(%s)', msg, error_exception)
  else:
    logging.getLogger('').error(msg)


class Timer(object):
  """Simple timer class for timing commands.

  Conveniently used as a context manager:

    from utils.log_utils import Timer

    with Timer() as t:
      // do some timable operation
      MyDbWork()
    print 'Elapsed db work: %s.' % t.secs
  """

  def __init__(self, log_tag=None, hide_timing=False):
    """Allow a tag to auto label the elapsed messages.

    Args:
      log_tag: If supplied, an elapsed message will be logged.
      hide_timing: Allow users to disable messages dynamically.
    """
    self._log_tag = log_tag
    self._hide_timing = hide_timing

  def __enter__(self):
    self._start = time.time()
    return self

  def __exit__(self, *args):
    self._end = time.time()
    self.secs = self._end - self._start
    if not self._hide_timing and self._log_tag:
      LogInfo('[timing]Elapsed time for %s: %f s' % (self._log_tag, self.secs))
