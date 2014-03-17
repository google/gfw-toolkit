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

"""Produce reports about domain users.

Uses the Admin SDK Directory API to discover users and their attributes.
Prints output to csv file format.

Use the --csv_fields option to choose fields to emit.  Fields are defined by
the dictionary returned by the Admin SDK Directory API for users.

For example: --csv_fields="primaryEmail,orgUnitPath,suspended"

Fields that are present in all user records include:
  'agreedToTerms', 'changePasswordAtNextLogin', 'creationTime', 'customerId',
  'emails', 'id', 'includeInGlobalAddressList', 'ipWhitelisted', 'isAdmin',
  'isDelegatedAdmin', 'isMailboxSetup', 'kind', 'lastLoginTime', 'name',
  'nonEditableAliases', 'orgUnitPath', 'primaryEmail', 'suspended'

Three fields are treated special:
  'emails': a list of dictionaries is converted to an attribute 'email.primary'
            and subsequently 'email0', 'email1', ...
  'name': a dictionary with multiple names - converted to new attributes:
          'name.familyName', 'name.fullName' and 'name.givenName'.
  'nonEditableAliases': a list of aliases converted to:
                        'alias0', 'alias1', ...

The following are uncommon fields not present in most user records:
  'aliases': a list of alternate aliases.
  'suspensionReason': a string explanation for a suspension.
"""

import sys

# setup_path required to allow imports from component dirs (e.g. utils)
# and lib (where the OAuth and Google API Python Client modules reside).
import setup_path  # pylint: disable=unused-import,g-bad-import-order

from admin_sdk_directory_api import users_api
from utils import admin_api_tool_errors
from utils import auth_helper
from utils import common_flags
from utils import file_manager
from utils import log_utils
from utils import validators


_REPORT_USERS_FILE_NAME = 'report_users.csv'


FILE_MANAGER = file_manager.FILE_MANAGER


class _UserDictionaryParser(object):
  """Utility class to organize parsing of user metadata fields."""

  @staticmethod
  def GetExpectedUserFields():
    """Helper to enumerate the metadata fields we expect to see.

    This list based on interrogating existing user lists and the documentation
    of the user object at this point in time.

    Returns:
      List of the expected fields in alphabetical order.
    """
    return [
        'agreedToTerms', 'aliases', 'changePasswordAtNextLogin', 'creationTime',
        'customerId', 'emails', 'id', 'includeInGlobalAddressList',
        'ipWhitelisted', 'isAdmin', 'isDelegatedAdmin', 'isMailboxSetup',
        'kind', 'lastLoginTime', 'name', 'nonEditableAliases', 'orgUnitPath',
        'primaryEmail', 'suspended', 'suspensionReason']

  @staticmethod
  def FlattenUserEmails(user):
    """Convert user 'emails' field from a container to multiple 'emailX' fields.

    The user object currently allows multiple email addresses to be associated
    (as a list of dictionaries under an 'emails' attribute). Each dictionary
    seems to hold an 'address' attribute and one of the dictionaries has a
    'primary' attribute.

    To allow them to be properly rendered to a csv (one row per user) with
    headers we need to flatten them into a series of fields:
    email.primary, email1, email2, ...

    This code adjusts the user object and adds headers.

    Args:
      user: A user dictionary of fields.

    Returns:
      Set of the headers that were created by the flattening.
    """
    created_headers = set()
    if 'emails' not in user:
      return created_headers
    email_counter = 1  # Start labeling email addresses at 1 (after primary).
    for email_dict in user['emails']:
      if email_dict.get('primary'):
        field = u'email.primary'
      else:
        field = u'email%d' % email_counter
        email_counter += 1
      created_headers.add(field)
      user[field] = email_dict.get('address')
    del user['emails']
    return created_headers

  @staticmethod
  def FlattenUserNames(user):
    """Convert container of 'name' fields to multiple 'name.X' fields.

    The user 'name' dictionary holds multiple fields: familyName, fullName
    and givenName.  To print these fields as part of one row, replace the
    dictionary with a set of like-named fields such as:
    name.familyName, name.fullName, name.givenName.

    Args:
      user: A user dictionary of fields.

    Returns:
      Set of the headers that were created by the flattening.
    """
    created_headers = set()
    for name_field in ['familyName', 'fullName', 'givenName']:
      if name_field in user['name']:
        field = u'name.%s' % name_field
        created_headers.add(field)
        user[field] = user['name'].get(name_field)
    del user['name']
    return created_headers

  @staticmethod
  def FlattenUserAliases(user):
    """Convert container of 'alias' fields to multiple 'aliasX' fields.

    Removing the container to allow all user data to be printed to a single row
    in a report.

    Args:
      user: A user dictionary of fields.

    Returns:
      Set of the headers that were created by the flattening.
    """
    created_headers = set()
    alias_counter = 1
    for alias in user['nonEditableAliases']:
      field = u'alias%d' % alias_counter
      alias_counter += 1
      created_headers.add(field)
      user[field] = alias
    del user['nonEditableAliases']
    return created_headers


def _FinalizeHeaders(found_fields, headers, flags):
  """Helper to organize the final headers that show in the report.

  The fields discovered in the user objects are kept separate from those
  created in the flattening process in order to allow checking the found
  fields against a list of those expected.  Unexpected fields are identified.

  If the report is a subset of all fields, the headers are trimmed.

  Args:
    found_fields: A set of the fields found in all the user objects.
    headers: A set of the fields created in the flattening helpers.
             Will return with the complete set of fields to be printed.
    flags: Argparse flags object with csv_fields.

  Returns:
    Sorted list of headers.
  """
  # Track known fields to notify user if/when fields change. A few are known
  # but not printed (they are denormalized and replaced below):
  expected_fields = set(_UserDictionaryParser.GetExpectedUserFields())
  if found_fields > expected_fields:
    unexpected_fields = ', '.join(found_fields - expected_fields)
    log_utils.LogWarning(
        'Unexpected user fields noticed: %s.' % unexpected_fields)
  headers |= found_fields
  headers -= set(['emails', 'name', 'nonEditableAliases'])

  # Prune the headers reference object that is used outside this
  # function by using discard() if a subset of fields is desired.
  if flags.csv_fields:
    extra_csv_fields = set(flags.csv_fields) - headers
    if extra_csv_fields:
      print '** Ignoring unknown csv_fields: %s.' % ', '.join(
          sorted(extra_csv_fields))
    for field in list(headers):
      if field not in flags.csv_fields:
        headers.discard(field)
  return sorted(headers)


def ReportDomainUsers(user_list, flags):
  """Report of the domain users and their attributes.

  While the user container is a dictionary, the dictionary is not flat.
  https://developers.google.com/admin-sdk/directory/v1/reference/users#resource
  Because we are printing to a flat csv file we need to denormalize the
  fields that are embedded lists (emails) or dictionaries (name).

  Args:
    user_list: List of dictionaries of users found in the domain.
    flags: Argparse flags object with output_file, force, ...
  """
  if not user_list:
    print 'No users returned.'
    return

  found_fields = set()
  report_headers = set()

  for user in user_list:
    found_fields |= set(user.keys())
    report_headers |= _UserDictionaryParser.FlattenUserEmails(user)
    report_headers |= _UserDictionaryParser.FlattenUserNames(user)
    report_headers |= _UserDictionaryParser.FlattenUserAliases(user)
  sorted_headers = _FinalizeHeaders(found_fields, report_headers, flags)
  csv_data_rows = []
  for user in user_list:
    user_row = []
    for field in sorted_headers:
      user_row.append(user.get(field))
    csv_data_rows.append(user_row)
  filename_path = FILE_MANAGER.WriteCSVFile(flags.output_file, csv_data_rows,
                                            sorted_headers,
                                            overwrite_ok=flags.force)
  print 'Wrote user report: %s.' % filename_path


def AddFlags(arg_parser):
  """Handle command line flags unique to this script.

  Args:
    arg_parser: object from argparse.ArgumentParser() to accumulate flags.
  """
  common_flags.DefineAppsDomainFlagWithDefault(arg_parser)
  common_flags.DefineForceFlagWithDefaultFalse(arg_parser)
  common_flags.DefineVerboseFlagWithDefaultFalse(arg_parser)

  arg_parser.add_argument(
      '--output_file', '-o', default=_REPORT_USERS_FILE_NAME,
      help='Supply a name for the output report file.',
      type=validators.NoWhitespaceValidatorType())
  arg_parser.add_argument(
      '--query_filter',
      help='Optionally filter on a field.',
      type=validators.NoWhitespaceValidatorType())
  arg_parser.add_argument(
      '--csv_fields',
      help='List of fields to emit to csv.',
      type=validators.ListValidatorType())
  arg_parser.add_argument(
      '--first_n', type=int, default=0,
      help='Show the first n users in the list.')


def main(argv):
  """Produce a user report with contents stipulated by flags."""
  flags = common_flags.ParseFlags(argv,
                                  'Create a report of domain user info.',
                                  AddFlags)
  FILE_MANAGER.ExitIfCannotOverwriteFile(flags.output_file,
                                         overwrite_ok=flags.force)
  http = auth_helper.GetAuthorizedHttp(flags)
  api_wrapper = users_api.UsersApiWrapper(http)

  max_results = flags.first_n if flags.first_n > 0 else None
  try:
    user_list = api_wrapper.GetDomainUsers(flags.apps_domain, basic=False,
                                           max_results=max_results,
                                           query_filter=flags.query_filter)
  except admin_api_tool_errors.AdminAPIToolUserError as e:
    log_utils.LogError(
        'Unable to enumerate users from domain %s.' % flags.apps_domain, e)
    sys.exit(1)

  ReportDomainUsers(user_list, flags)


if __name__ == '__main__':
  main(sys.argv[1:])
