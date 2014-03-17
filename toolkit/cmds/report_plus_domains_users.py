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

"""Produce reports showing details of Google+ users enrollments.

Makes use of the report_users command. Produces a csv file
that summarize plus domain user profile counts.

Note that the presence of a user in the directory does not
guarantee the presence of a plus domain profile.
"""

import sys

# setup_path required to allow imports from component dirs (e.g. utils)
# and lib (where the OAuth and Google API Python Client modules reside).
import setup_path  # pylint: disable=unused-import,g-bad-import-order

from plus_domains_api import people_api
from utils import admin_api_tool_errors
from utils import auth_helper  # pylint: disable=unused-import
from utils import common_flags
from utils import file_manager
from utils import log_utils
from utils import report_utils
from utils import user_iterator


_PROFILES_FOUND_FILE_NAME = 'plus_profiles_found.json'
_REPORT_USERS_PROFILE_STATE_FILE_NAME = 'report_users_profile_state.csv'
_REPORT_PROFILE_STATUS_HEADER = ['DOMAIN_USERS', 'ACTIVE_GOOGLE+_PROFILES',
                                 'MISSING_PROFILES']


FILE_MANAGER = file_manager.FILE_MANAGER


def _GetProfileStatus(exit_on_fail=True):
  """Reads the snapshot of the profile stats from the Json file.

  Args:
    exit_on_fail: Alternately return the message instead of failing
                  if token file not found.  Used for ui reporting.

  Returns:
    Profile stats in an object (a dictionary).  If cannot find the file
    return a message to show.
  """
  if not FILE_MANAGER.FileExists(_PROFILES_FOUND_FILE_NAME):
    message = 'No profile data.  You cannot --resume.'
    log_utils.LogError(message)
    if exit_on_fail:
      sys.exit(1)
    else:
      return message
  return FILE_MANAGER.ReadJsonFile(_PROFILES_FOUND_FILE_NAME)


def _WriteProfileStatus(profile_status, flags, overwrite_ok=False):
  """Writes the snapshot of the token stats to Json file in progress.

  Args:
    profile_status: An object with the collected profile status.
    flags: Argparse flags object with force.
    overwrite_ok: If True don't check if file exists - else fail if file exists.

  Returns:
    String reflecting the full path of the file created/written.
  """
  filename_path = FILE_MANAGER.BuildFullPathToFileName(
      _PROFILES_FOUND_FILE_NAME)
  overwrite_ok = True if overwrite_ok else flags.force
  if FILE_MANAGER.FileExists(_PROFILES_FOUND_FILE_NAME) and not overwrite_ok:
    log_utils.LogError('Output file (%s) already exists.\nUse --force to '
                       'overwrite, --resume collecting status for an '
                       'interrupted run or --use_local_profile_data to '
                       'profile data.' % filename_path)
    sys.exit(1)
  filename_path = FILE_MANAGER.WriteJsonFile(_PROFILES_FOUND_FILE_NAME,
                                             profile_status,
                                             overwrite_ok=overwrite_ok)
  return filename_path


def _GatherProfileStatus(flags):
  """For each user, determine if they have a Google+ profile.

  Args:
    flags: Argparse flags object with resume.
  """
  profile_status = {}

  if not flags.resume:
    # Early check if file exists and not --force.
    filename_path = _WriteProfileStatus(profile_status, flags)
  else:
    profile_status = _GetProfileStatus()

  http = auth_helper.GetAuthorizedHttp(flags)
  user_api = people_api.PlusDomains(http)

  iterator_purpose = 'plus_report'  # Used to tag iterator progress data.

  # The user list holds a tuple for each user of: email, id, full_name
  # (e.g. 'larry', '112351558298938768732', 'Larry Summon').
  print 'Scanning domain users for %s' % iterator_purpose
  for user in user_iterator.StartUserIterator(http, iterator_purpose, flags):
    user_email, user_id, checkpoint = user  # pylint: disable=unused-variable
    try:
      profile_status[user_email] = user_api.IsDomainUser(user_email)
    except admin_api_tool_errors.AdminAPIToolPlusDomainsError as e:
      # This suggests an unexpected response from the plus domains api.
      # As much detail as possible is provided by the raiser.
      sys.stdout.write('%80s\r' % '')  # Clear the previous entry.
      sys.stdout.flush()
      log_utils.LogError('Unable to get user profile.', e)
      sys.exit(1)

    if checkpoint:
      # Save progress every n users.
      filename_path = _WriteProfileStatus(profile_status, flags,
                                          overwrite_ok=True)
  print 'Domain Profile report written: %s' % filename_path


def _SummarizeProfileStatus():
  """Read the generated profile dictionary file and count users and profiles.

  Returns:
    Tuple of 3 items:
    -Count of the domain users found/checked.
    -Count of the profiles found.
    -The state dictionary with users and state for later written reports.

    An example result would be:
      10, 8, {'john@altostrat.com': True, 'paul@altostrat.com': False}
  """
  domain_profile_status = _GetProfileStatus()
  directory_user_count = len(domain_profile_status.keys())
  user_profiles_count = domain_profile_status.values().count(True)
  return directory_user_count, user_profiles_count, domain_profile_status


def _PrintProfileReport(user_count, profile_count, domain_profile_status,
                        flags):
  """Print profile summary data: counts and users.

  Args:
    user_count: Count of users in the directory for the domain (not Google+).
    profile_count: Count of users with Google+ profiles.
    domain_profile_status: Dictionary of users and state (True|False) if their
                           Google+ profile is present.
    flags: Argparse flags object with show_users.
  """
  print report_utils.BORDER
  format_patterns = []
  for column in _REPORT_PROFILE_STATUS_HEADER:
    format_patterns.append('%%-%ds' % len(column))
  format_string = '  '.join(format_patterns)
  print format_string % tuple(_REPORT_PROFILE_STATUS_HEADER)
  print format_string % (user_count, profile_count,
                         (user_count - profile_count))
  if flags.show_users:
    print '\nDomain user Google+ profile state:'
    for sequence_number, user_email in enumerate(
        sorted(domain_profile_status.keys()), start=1):
      print '%6d. %s: %s' % (sequence_number, user_email,
                             domain_profile_status[user_email])
  print report_utils.BORDER


def _WriteUserProfileState(domain_profile_status, flags):
  """Write the user Google+ email and profile state to a csv file.

  Args:
    domain_profile_status: Dictionary of users and state (True|False) if their
                           Google+ profile is present.
    flags: Argparse flags object with force.
  """
  user_profile_state = []
  for user_email in sorted(domain_profile_status.keys()):
    user_profile_state.append([user_email,
                               domain_profile_status[user_email]])
  try:
    filename_path = FILE_MANAGER.WriteCSVFile(
        _REPORT_USERS_PROFILE_STATE_FILE_NAME, user_profile_state,
        ['User', 'Google+_Profile_State'], overwrite_ok=flags.force)
    print 'Wrote report of users missing Google+ profiles: %s.' % (
        filename_path)
  except admin_api_tool_errors.AdminAPIToolFileError:
    log_utils.LogError('CSV file(s) already exist.\nUse --force to overwrite.')
    sys.exit(1)


def AddFlags(arg_parser):
  """Handle command line flags unique to this script.

  Args:
    arg_parser: object from argparse.ArgumentParser() to accumulate flags.
  """
  common_flags.DefineAppsDomainFlagWithDefault(arg_parser)
  common_flags.DefineForceFlagWithDefaultFalse(arg_parser)
  common_flags.DefineVerboseFlagWithDefaultFalse(arg_parser)

  arg_parser.add_argument('--create_state_report_csv', action='store_true',
                          default=False,
                          help=('Output user email addresses and profile state '
                                'to a csv file.'))
  arg_parser.add_argument('--first_n', type=int, default=0,
                          help='Gather profile status for the first n users.')
  arg_parser.add_argument('--resume', '-r', action='store_true', default=False,
                          help=('Resume if interrupted while gathering '
                                'profiles.'))
  arg_parser.add_argument('--show_users', '-u', action='store_true',
                          default=False,
                          help='Show list of users who are missing profiles.')
  arg_parser.add_argument('--use_local_profile_data', action='store_true',
                          default=False,
                          help='Use local, previously-retrieved profile data.')


def main(argv):
  """Run report_users, parse and print a summary of its results."""
  flags = common_flags.ParseFlags(argv,
                                  'Create report of domain Google+ user info.',
                                  AddFlags)
  if flags.create_state_report_csv:
    FILE_MANAGER.ExitIfCannotOverwriteFile(
        _REPORT_USERS_PROFILE_STATE_FILE_NAME, overwrite_ok=flags.force)
  if not flags.use_local_profile_data:
    _GatherProfileStatus(flags)
  user_count, profile_count, domain_profile_status = _SummarizeProfileStatus()
  _PrintProfileReport(user_count, profile_count, domain_profile_status, flags)
  if flags.create_state_report_csv:
    _WriteUserProfileState(domain_profile_status, flags)


if __name__ == '__main__':
  main(sys.argv[1:])
