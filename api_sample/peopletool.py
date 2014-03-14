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

"""Simple ls (show) of a domain user.

Tool to show usage of Google Plus Domains APIs: Google+ User Profile Management.
"""

import argparse
import logging
import os
import sys

lib_dir = os.path.join(os.path.dirname(sys.modules[__name__].__file__),
                       'third_party')
if os.path.isdir(lib_dir):
  sys.path.insert(0, lib_dir)

# pylint: disable=g-import-not-at-top
from apiclient.discovery import build
import apiclient.errors
import auth_helper
import http_utils


def _PrintOneLine(full_name, user_id, plus_user_url):
  """Formats a user print line a little like ls -l.

  Example output:

  Full Name      ID                     Google+ Profile URL
  George User3   000000000298938768732  https://plus.google.com/0123456789012

  Args:
    full_name: first and last name.
    user_id: 21 digit domain id.
    plus_user_url: url to the Google+ user profile.
  """
  # Left justify all but the last as string fields.
  print '%-40s %-22s %s' % (full_name, user_id, plus_user_url)


def _PrintUserHeader():
  """Print user header for ls_user."""
  _PrintOneLine('Full Name', 'ID', 'Google+ Profile URL')


def _PrintOneUser(user):
  """Prints fields from returned user json.

  Args:
    user: user json object returned from the users API list().
  """
  _PrintOneLine(user['displayName'], user['id'], user['url'])


class APIToolPlusDomainsError(Exception):
  """Problem with user provisioning."""
  pass


class PeoplePlusDomains(object):
  """Demonstrates plus domains API."""

  def __init__(self, http):
    """Create our service object with access to plus domains APIs.

    Establishes a people collection that can be used to interrogate profiles.

    Args:
      http: An authorized http interface object.
    """
    self._service = build('plusDomains', 'v1', http=http)
    self._users = self._service.people()

  def GetDomainUserProfile(self, user_email):
    """Retrieve document for a user in an apps domain.

    A common reason to call this is to retrieve the user_id from an email name.

    Args:
      user_email: username to check.

    Returns:
      The user document (available fields listed in _PrintOneUser()).

    Raises:
      APIToolPlusDomainsError: An error retrieving the user. An
                                     example of this is attempting to list
                                     a user from another apps domain.
    """
    request = self._users.get(userId=user_email)
    try:
      return request.execute()
    except apiclient.errors.HttpError as e:  # Missing user raises HttpError.
      if e.resp.status == 404:
        print 'User %s not found.' % user_email
        sys.exit(1)
      error_text = http_utils.ParseHttpResult(e.uri, e.resp, e.content)
      raise APIToolPlusDomainsError(error_text)

  def PrintDomainUserProfile(self, user_email):
    """Print details of a domain user profile.

    Args:
      user_email: user email to find.
    """
    user = self.GetDomainUserProfile(user_email)
    if user:
      _PrintUserHeader()
      _PrintOneUser(user=user)
    else:
      print 'User %s not found.' % user_email


def _ParseFlags(argv):
  """Handle command line flags unique to this script.

  Args:
    argv: holds all the command line flags passed.

  Returns:
    argparser flags object with attributes set based on flag settings.
  """
  argparser = argparse.ArgumentParser(
      description='List user profile from Google+ for an Apps Domain User.',
      parents=[auth_helper.ARG_PARSER])
  argparser.add_argument('--user_email', '-u', required=True,
                         help='User email address [REQUIRED].')
  flags = argparser.parse_args(argv)
  logging.basicConfig(level=flags.logging_level,
                      format='%(asctime)s %(levelname)-8s %(message)s',
                      datefmt='%Y%m%d %H:%M:%S')
  return flags


def main(argv):
  """A script to test Plus Domains APIs: ls (show) user profile."""
  flags = _ParseFlags(argv)
  user_api = PeoplePlusDomains(auth_helper.GetAuthorizedHttp(flags))
  try:
    user_api.PrintDomainUserProfile(flags.user_email)
  except APIToolPlusDomainsError as e:
    print 'Unable to list user profile %s.\n%s' % (flags.user_email, e)
    sys.exit(1)


if __name__ == '__main__':
  main(sys.argv[1:])
