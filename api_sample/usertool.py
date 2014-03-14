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

"""Tool to exercise Admin SDK - Directory API - Users resource methods."""

import argparse
import logging
import os
import pprint
import sys
import textwrap

lib_dir = os.path.join(os.path.dirname(sys.modules[__name__].__file__),
                       'third_party')
if os.path.isdir(lib_dir):
  sys.path.insert(0, lib_dir)

# pylint: disable=g-import-not-at-top
from apiclient.discovery import build
import apiclient.errors
import auth_helper
import http_utils


def _PrintOneLine(user_email, user_id, full_name):
  """Formats a user print line a little like ls -l.

  Example output:

  Users from domain altostrat.com:
  Email                     ID                     Full Name
  george@altostrat.com      000000058298938768732  George Sum
  superadmin@altostrat.com  000000058699628788601  Super Admin

  Args:
    user_email: User email (e.g. myemail@mydomain.com).
    user_id: 21 digit domain id.
    full_name: first and last name.
  """
  # Left justify all but the last as string fields.
  print '%-40s %-22s %s' % (user_email, user_id, full_name)


def _PrintUserHeader():
  """Print user header for ls_users."""
  _PrintOneLine('Email', 'ID', 'Full Name')


def _PrintOneUser(user, basic=True):
  """Prints fields from returned user json.

  Available fields include:
    agreedToTerms, changePasswordAtNextLogin, creationTime, customerId,
    emails, id, includeInGlobalAddressList, ipWhitelisted, isAdmin,
    isDelegatedAdmin, isMailboxSetup, kind, lastLoginTime,
    name ({'familyName': 'xx', 'fullName': 'yy', 'givenName': 'zz'}),
    nonEditableAliases, orgUnitPath, primaryEmail and suspended.
  Special handling is needed for:
    emails, name, nonEditableAliases, name: sort for deterministic output.

  Args:
    user: user json object returned from the users API list().
    basic: if True, only print 3 common fields otherwise print all fields.
  """
  _PrintOneLine(user['primaryEmail'], user['id'], user['name']['fullName'])
  if basic:
    return
  for field in sorted(user.keys()):
    if field in ('primaryEmail', 'id', 'fullName'):  # already displayed.
      continue
    # For deterministic output, need to pprint container objects like
    # dict. Textwrap is used for the hanging indent.  We use a hanging
    # indent of 7 because 4 spaces is the normal margin and the extra
    # 3 spaces are used for: colon, space and opening brace.
    formatted_text = textwrap.fill(
        pprint.pformat(user.get(field)),
        subsequent_indent=(7+len(field)) * ' ', break_on_hyphens=False)
    print '    %s: %s' % (field, formatted_text)


class APIToolDirectoryUserError(Exception):
  """Problem with the Directory User API."""
  pass


class UserDirectory(object):
  """Interacts with the Admin Directory API users collection."""

  def __init__(self, http):
    """Create service object with access to cloud directory APIs.

    Establishes a users collection that can be used to interrogate domain users.

    Args:
      http: An authorized http interface object.
    """
    self._service = build('admin', 'directory_v1', http=http)
    self._users = self._service.users()

  def _ProcessUserListPage(self, apps_domain, max_page, next_page_token=None):
    """Helper that handles exceptions retrieving pages of users.

    Args:
      apps_domain: Users apps domain e.g. mybiz.com.
      max_page: Used to optimize paging (1-500).
      next_page_token: Used for ongoing paging of users.

    Returns:
      List of users retrieved (one page).
    """
    request = self._users.list(domain=apps_domain, maxResults=max_page,
                               pageToken=next_page_token)
    try:
      users_list = request.execute()
      return users_list
    except apiclient.errors.HttpError as e:
      error_text = http_utils.ParseHttpResult(e.uri, e.resp, e.content)
      raise APIToolDirectoryUserError(error_text)

  def _ProcessDomainUsers(self, apps_domain, process_fn, max_results=None,
                          max_page=100):
    """Helper to allow multiple, different print functions.

    Args:
      apps_domain: Users apps domain e.g. mybiz.com.
      process_fn: Function to be used against each user object (e.g. print).
      max_results: If not None, stop after this many users.
      max_page: Used to optimize paging (1-500).

    Returns:
      Tuple of (result list, count of users retrieved). The result list is
      populated using results from process_fn().
    """
    results = []
    retrieved_count = 0
    next_page_token = None

    if max_page < 1 or max_page > 500:
      max_page = 100  # API default.
    if max_results is not None and max_results < max_page:
      max_page = max_results

    users_list = self._ProcessUserListPage(apps_domain=apps_domain,
                                           max_page=max_page)
    while True:
      for user in users_list.get('users', []):
        result = process_fn(user)
        if result:
          results.append(result)
        retrieved_count += 1
        if max_results is not None and retrieved_count >= max_results:
          return results, retrieved_count
      next_page_token = users_list.get('nextPageToken')
      if not next_page_token:
        return results, retrieved_count
      users_list = self._ProcessUserListPage(apps_domain=apps_domain,
                                             max_page=max_page,
                                             next_page_token=next_page_token)

  def AddDomainUser(self, first_name, last_name, user_email, new_password):
    """Adds user to the domain.

    Users are created by default as unsuspended, non-admin users.

    Args:
      first_name: Given first name.
      last_name: Family name.
      user_email: user_email to add.
      new_password: Password to set.
    """
    body = {
        'primaryEmail': user_email,
        'name': {'givenName': first_name, 'familyName': last_name},
        'password': new_password
        }
    request = self._users.insert(body=body)
    try:
      request.execute()
      return
    except apiclient.errors.HttpError as e:
      error_text = http_utils.ParseHttpResult(e.uri, e.resp, e.content)
      raise APIToolDirectoryUserError(error_text)

  def DeleteDomainUser(self, user_email):
    """Deletes user from the domain.

    Args:
      user_email: user_email to add.

    Raises:
      APIToolDirectoryUserError: Unable to delete user.
    """
    request = self._users.delete(userKey=user_email)
    try:
      request.execute()
      return
    except apiclient.errors.HttpError as e:  # Missing user raises HttpError.
      if e.resp.status == 404:
        print 'User %s not found.' % user_email
        sys.exit(1)
      error_text = http_utils.ParseHttpResult(e.uri, e.resp, e.content)
      raise APIToolDirectoryUserError(error_text)

  def GetDomainUser(self, user_email):
    """Retrieve document for a user in an apps domain.

    A common reason to call this is to retrieve the user_id from an email name.

    Args:
      user_email: username to check.

    Returns:
      The user document (available fields listed in _PrintOneUser()).

    Raises:
      APIToolDirectoryUserError: An error retrieving the user. An
                                       example of this is attempting to list
                                       a user from another apps domain.
    """
    request = self._users.get(userKey=user_email)
    try:
      return request.execute()
    except apiclient.errors.HttpError as e:  # Missing user raises HttpError.
      if e.resp.status == 404:
        print 'User %s not found.' % user_email
        if '@' not in user_email:
          print 'The user_email should be formatted as user@domain.com.'
        sys.exit(1)
      error_text = http_utils.ParseHttpResult(e.uri, e.resp, e.content)
      raise APIToolDirectoryUserError(error_text)

  def PrintDomainUser(self, user_email):
    """Print details of a domain user.

    Args:
      user_email: user email to find.
    """
    user = self.GetDomainUser(user_email)
    if user:
      _PrintUserHeader()
      _PrintOneUser(user=user, basic=False)
    else:
      print 'User %s not found.' % user_email

  def PrintDomainUsers(self, apps_domain, max_results=None, max_page=500):
    """Powerful demonstration of ease of Directory User API.

    Args:
      apps_domain: Users apps domain e.g. mybiz.com.
      max_results: If not None, stop after this many users.
      max_page: Used to optimize paging (1-500).
    """
    print 'Users from domain %s:' % apps_domain
    _PrintUserHeader()
    _, count = self._ProcessDomainUsers(apps_domain=apps_domain,
                                        process_fn=_PrintOneUser,
                                        max_results=max_results,
                                        max_page=max_page)
    print '%d users found.' % count


def AddUserCommand(flags, user_api):
  """Wrapper to invoke add_user against Admin SDK Cloud Directory.

  Args:
    flags: argparse parsed command line flags.
    user_api: authenticated Admin SDK users collection object.
  """
  try:
    user_api.AddDomainUser(flags.first_name, flags.last_name,
                           flags.user_email, flags.password)
  except APIToolDirectoryUserError as e:
    # Could not add user. Details provided by api wrapper in the e string.
    print 'Unable to add user %s.\n%s' % (flags.user_email, e)
    sys.exit(1)
  print 'User %s added.' % flags.user_email


def SetupAddUserParser(cmd_subparsers):
  """Create subparser for AddUser command.

  Args:
    cmd_subparsers: argparse subparsers object from add_subparsers().
  """
  parser_add_user = cmd_subparsers.add_parser(
      'add_user',
      help='Add user to the Domain Cloud Directory.')
  parser_add_user.add_argument(
      '--user_email', '-u', required=True,
      help='User email address [REQUIRED].')
  parser_add_user.add_argument(
      '--first_name', '-n', required=True,
      help='First name within the domain [REQUIRED].')
  parser_add_user.add_argument(
      '--last_name', '-l', required=True,
      help='Last name within the domain [REQUIRED].')
  parser_add_user.add_argument(
      '--password', '-p', required=True,
      help='Password [REQUIRED].')
  parser_add_user.set_defaults(subcommand=AddUserCommand)


def LsUserCommand(flags, user_api):
  """Wrapper to invoke ls_user against Admin SDK Cloud Directory.

  Args:
    flags: argparse parsed command line flags.
    user_api: authenticated Admin SDK users collection object.
  """
  try:
    user_api.PrintDomainUser(flags.user_email)
  except APIToolDirectoryUserError as e:
    print 'Unable to list user %s.\n%s' % (flags.user_email, e)
    sys.exit(1)


def SetupLsUserParser(cmd_subparsers):
  """Create subparser for AddUser command.

  Args:
    cmd_subparsers: argparse subparsers object from add_subparsers().
  """
  parser_ls_user = cmd_subparsers.add_parser(
      'ls_user',
      help='List user attributes from the Domain Cloud Directory.')
  parser_ls_user.add_argument(
      '--user_email', '-u', required=True,
      help='User email address [REQUIRED].')
  parser_ls_user.set_defaults(subcommand=LsUserCommand)


def LsUsersCommand(flags, user_api):
  """Wrapper to invoke ls_users against Admin SDK Cloud Directory.

  Args:
    flags: argparse parsed command line flags.
    user_api: authenticated Admin SDK users collection object.
  """
  max_results = flags.first_n if flags.first_n > 0 else None
  try:
    user_api.PrintDomainUsers(flags.apps_domain, max_results=max_results)
  except APIToolDirectoryUserError as e:
    print 'Unable to list user for %s.\n%s' % (flags.apps_domain, e)
    sys.exit(1)


def SetupLsUsersParser(cmd_subparsers):
  """Create subparser for AddUser command.

  Args:
    cmd_subparsers: argparse subparsers object from add_subparsers().
  """
  parser_ls_users = cmd_subparsers.add_parser(
      'ls_users',
      help='List users from the Domain Cloud Directory.')
  parser_ls_users.add_argument(
      '--apps_domain', '-a', required=True,
      help='Google Apps Domain Name (e.g. altostrat.com) [REQUIRED].')
  parser_ls_users.add_argument(
      '--first_n', type=int,
      help='Show the first n users in the list.')
  parser_ls_users.set_defaults(subcommand=LsUsersCommand)


def RmUserCommand(flags, user_api):
  """Wrapper to invoke rm_user against Admin SDK Cloud Directory.

  Args:
    flags: argparse parsed command line flags.
    user_api: authenticated Admin SDK users collection object.
  """
  try:
    user_api.DeleteDomainUser(flags.user_email)
  except APIToolDirectoryUserError as e:
    print 'Unable to rm user %s.\n%s' % (flags.user_email, e)
    sys.exit(1)
  print 'User %s successfully removed.' % flags.user_email


def SetupRmUserParser(cmd_subparsers):
  """Create subparser for AddUser command.

  Args:
    cmd_subparsers: argparse subparsers object from add_subparsers().
  """
  parser_rm_user = cmd_subparsers.add_parser(
      'rm_user',
      help='Remove user from the Domain Cloud Directory.')
  parser_rm_user.add_argument(
      '--user_email', '-u', required=True,
      help='User email address [REQUIRED].')
  parser_rm_user.set_defaults(subcommand=RmUserCommand)


def _ParseFlags(argv):
  """Handle command line flags unique to this script.

  Args:
    argv: holds all the command line flags passed.

  Returns:
    argparser flags object with attributes set based on flag settings.
  """
  argparser = argparse.ArgumentParser(
      description='Exercise Admin SDK Directory Users API.',
      parents=[auth_helper.ARG_PARSER])
  cmd_subparsers = argparser.add_subparsers()

  SetupAddUserParser(cmd_subparsers)
  SetupLsUserParser(cmd_subparsers)
  SetupLsUsersParser(cmd_subparsers)
  SetupRmUserParser(cmd_subparsers)

  flags = argparser.parse_args(argv)
  logging.basicConfig(level=flags.logging_level,
                      format='%(asctime)s %(levelname)-8s %(message)s',
                      datefmt='%Y%m%d %H:%M:%S')
  return flags


def main(argv):
  """A script to show Admin SDK Directory APIs."""
  flags = _ParseFlags(argv)
  user_api = UserDirectory(auth_helper.GetAuthorizedHttp(flags))
  flags.subcommand(flags, user_api)


if __name__ == '__main__':
  main(sys.argv[1:])
