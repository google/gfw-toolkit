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

"""Utility validator functions for command line flags."""

import argparse
import re

import setup_path  # pylint: disable=unused-import,g-bad-import-order

import admin_api_tool_errors


# '.' and '-' are valid in domain names and email addresses.
VALID_APPS_DOMAIN_RE = r'^[\w.-]+\.[\w]+$'
VALID_EMAIL_RE = r'^([\w.-]+)@([\w.-]+\.[\w]+)$'
VALID_NOWHITESPACE_RE = r'^[\S]+$'


class ListValidatorType(object):
  """Simple class to split command line option strings into lists."""

  def __call__(self, arg_string):
    arg_string = arg_string.strip()
    if not arg_string:
      return []
    return arg_string.split(',')


class RegexValidatorType(object):
  """Performs regular expression match on value.

  Raises:
    argparse.ArgumentTypeError() if validation fails to match.
  """

  def __init__(self, match_pattern, error_message):
    self._pattern_re = re.compile(match_pattern)
    self._error_message = error_message
    if not self._error_message:
      self._error_message = 'Must match pattern %s.' % match_pattern

  def __call__(self, arg_string):
    arg_string = arg_string.strip()
    if not self._pattern_re.search(arg_string):
      raise argparse.ArgumentTypeError(self._error_message)
    return arg_string


class AppsDomainValidatorType(RegexValidatorType):
  """Ensures a command-line flag is a valid apps domain string."""

  def __init__(self):
    """Customize validator for Google Apps Domain name strings."""
    super(AppsDomainValidatorType, self).__init__(
        match_pattern=VALID_APPS_DOMAIN_RE,
        error_message='Must be a non-empty string of form: altostrat.com.')


class EmailValidatorType(RegexValidatorType):
  """Ensures a command-line flag is a valid apps domain string."""

  def __init__(self):
    """Customize validator for Email addresses."""
    super(EmailValidatorType, self).__init__(
        match_pattern=VALID_EMAIL_RE,
        error_message=('Must be a non-empty string of form: '
                       'youremail@altostrat.com.'))


class NoWhitespaceValidatorType(RegexValidatorType):
  """Ensures a command-line flag is a non-whitespace string."""

  def __init__(self):
    """Customize validator for no whitespace."""
    super(NoWhitespaceValidatorType, self).__init__(
        match_pattern=VALID_NOWHITESPACE_RE,
        error_message='Must be a non-whitespace string.')


def GetEmailParts(user_email):
  """Helper to retrieve the domain from an email address.

  Args:
    user_email: String with a properly formatted email address.

  Returns:
    A tuple of strings: (user_name, domain_name) parsed from the email address.

  Raises:
    AdminAPIToolInvalidUserEmailError: If mail address is improperly formatted.
  """
  result = re.compile(VALID_EMAIL_RE).match(user_email)
  if not result:
    raise admin_api_tool_errors.AdminAPIToolInvalidUserEmailError(
        'Email address (%s) must be of form: user@altostrat.com' % user_email)
  return result.group(1, 2)
