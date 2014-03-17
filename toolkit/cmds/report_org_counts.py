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

"""Produce reports showing counts of user by org.

Makes use of the report_users command. Produces multiple csv files
that summarize domain user counts by organizational unit.
"""

import sys

# setup_path required to allow imports from component dirs (e.g. utils)
# and lib (where the OAuth and Google API Python Client modules reside).
import setup_path  # pylint: disable=unused-import,g-bad-import-order

from utils import admin_api_tool_errors
from utils import auth_helper  # pylint: disable=unused-import
from utils import cmd_utils
from utils import common_flags
from utils import file_manager
from utils import log_utils
from utils import report_utils


_REPORT_USERS_ORGS_FILE_NAME = '_report_users_orgs.csv.tmp'
_REPORT_ORGS_BY_ACTIVE_FILE_NAME = 'orgs_by_active.csv'
_REPORT_ORGS_BY_OU_FILE_NAME = 'orgs_by_ou.csv'


_REPORT_BY_ACTIVE_HEADER = ['ACTIVE', 'SUSPENDED', 'OU']
_REPORT_BY_ORG_HEADER = ['OU', 'ACTIVE', 'SUSPENDED']
_REPORT_FILTER_FIELDS = ['orgUnitPath', 'suspended']


FILE_MANAGER = file_manager.FILE_MANAGER


def GenerateUserReport(flags):
  """Run the command to create the report file.

  report_users error-exits if the file is found without --force.
  Instead, re-process the existing file in that situation.

  Args:
    flags: Argparse flags object with apps_domain, resume and first_n.
  """
  if FILE_MANAGER.FileExists(_REPORT_USERS_ORGS_FILE_NAME) and not flags.force:
    print 'Showing counts from existing file.'
    return

  print 'Generating new counts...'

  arg_list = [
      '--output_file=%s' % _REPORT_USERS_ORGS_FILE_NAME,
      '--csv_fields=%s' % ','.join(_REPORT_FILTER_FIELDS),
  ]
  for flag_value, flag_string in [
      (flags.apps_domain, '--apps_domain=%s' % flags.apps_domain),
      (flags.force, '--force'),
      (flags.verbose, '--verbose')]:
    if flag_value:
      arg_list.append(flag_string)
  try:
    cmd_utils.RunPyCmd('report_users.py', arg_list)
  except admin_api_tool_errors.AdminAPIToolCmdError as e:
    log_utils.LogError('Unable to generate org data.', e)
    sys.exit(1)


def _ReadAndCountUsersOrgsCSV():
  """Helper to read the users org report for summarizing.

  Always expects to find a header row since that's how we write it.

  Returns:
    Tuple of 2 counters: (#active_users, #suspended_users)
  """
  csv_rows = FILE_MANAGER.ReadCsvFile(_REPORT_USERS_ORGS_FILE_NAME)
  if csv_rows[0] != _REPORT_FILTER_FIELDS:
    log_utils.LogError('Unexpected header in file %s. Try running with '
                       '--force to generate a new file.' %
                       FILE_MANAGER.BuildFullPathToFileName(
                           _REPORT_USERS_ORGS_FILE_NAME))
    sys.exit(1)

  active_user_count = report_utils.Counter()
  suspended_user_count = report_utils.Counter()
  for org, suspended in csv_rows[1:]:
    if suspended == 'True':
      suspended_user_count.Increment(org)
    else:
      active_user_count.Increment(org)
  return active_user_count, suspended_user_count


def SummarizeUserOrgReport():
  """Read the generated csv file and count members in orgs.

  Returns:
    Tuple of 2 lists of tuples (OU, #active, #suspended):
    -List of tuples ordered by #active_users descending
    -List of tuples ordered by OU name alphabetically ascending.

    For example, a simple result (a domain with 1 Org Unit) might be:
    [(929, 0, '/')], [('/', 929, 0)]
  """
  # This is tricky because a domain may be entirely active users, suspended
  # users or (most commonly) a mix of both. Therefore need to handle cases
  # where an entire subdomain is suspended users carefully.
  active_user_counter, suspended_user_counter = _ReadAndCountUsersOrgsCSV()
  # A list of the most common organizations (subdomains) ordered by a count
  # of subdomain members descending.
  list_of_org_data_sorted_by_active_user_descending = []
  for org, active_user_count in active_user_counter.FilterAndSortMostCommon():
    suspended_user_count = suspended_user_counter.data.get(org, 0)
    list_of_org_data_sorted_by_active_user_descending.append(
        (active_user_count, suspended_user_count, org))

  # A list of all organizations (subdomains) ordered by name.
  org_unit_names = set(active_user_counter.data.keys() +
                       suspended_user_counter.data.keys())
  list_of_org_data_sorted_by_org_unit_name_alphabetically = []
  for org in sorted(org_unit_names):
    active_user_count = active_user_counter.data.get(org, 0)
    suspended_user_count = suspended_user_counter.data.get(org, 0)
    list_of_org_data_sorted_by_org_unit_name_alphabetically.append(
        (org, active_user_count, suspended_user_count))
  return (list_of_org_data_sorted_by_active_user_descending,
          list_of_org_data_sorted_by_org_unit_name_alphabetically)


def PrintOrgCounts(orgs_by_active, orgs_by_ou):
  """Print org groups with related counts of users.

  Args:
    orgs_by_active: List of tuples (#active, #suspended, org) order by #active.
    orgs_by_ou: List of tuples (org, #active, #suspended) ordered by ou.
  """
  print report_utils.BORDER
  # Order by #active descending.
  print ','.join(_REPORT_BY_ACTIVE_HEADER)
  for active, suspended, org in orgs_by_active:
    print '%d,%d,%s' % (active, suspended, org)
  print report_utils.BORDER
  # Order by OU ascending.
  print ','.join(_REPORT_BY_ORG_HEADER)
  for org, active, suspended in orgs_by_ou:
    print '%s,%d,%d' % (org, active, suspended)
  print report_utils.BORDER


def WriteOrgCounts(orgs_by_active, orgs_by_ou, flags):
  """Write org counts to two csv files for later use.

  Args:
    orgs_by_active: List of tuples (#active, #suspended, org) order by #active.
    orgs_by_ou: List of tuples (org, #active, #suspended) ordered by ou.
    flags: Argparse flags object with apps_domain, resume and first_n.
  """
  try:
    filename_path = FILE_MANAGER.WriteCSVFile(_REPORT_ORGS_BY_ACTIVE_FILE_NAME,
                                              orgs_by_active,
                                              _REPORT_BY_ACTIVE_HEADER,
                                              overwrite_ok=flags.force)
    print 'Wrote report of org users sorted by active user count: %s.' % (
        filename_path)
    filename_path = FILE_MANAGER.WriteCSVFile(_REPORT_ORGS_BY_OU_FILE_NAME,
                                              orgs_by_ou,
                                              _REPORT_BY_ORG_HEADER,
                                              overwrite_ok=flags.force)
    print 'Wrote report of org users sorted by org-unt count: %s.' % (
        filename_path)
  except admin_api_tool_errors.AdminAPIToolFileError:
    log_utils.LogError('CSV file(s) already exist. Use --force to overwrite.')
    sys.exit(1)


def AddFlags(arg_parser):
  """Handle command line flags unique to this script.

  Args:
    arg_parser: object from argparse.ArgumentParser() to accumulate flags.
  """
  common_flags.DefineAppsDomainFlagWithDefault(arg_parser)
  common_flags.DefineForceFlagWithDefaultFalse(arg_parser)
  common_flags.DefineVerboseFlagWithDefaultFalse(arg_parser)

  arg_parser.add_argument('--csv', action='store_true', default=False,
                          help='Output results to a csv file.')


def main(argv):
  """Run report_users, parse and print a summary of its results."""
  flags = common_flags.ParseFlags(argv, 'Create a report of org counts.',
                                  AddFlags)
  if flags.csv:
    FILE_MANAGER.ExitIfCannotOverwriteFile(_REPORT_ORGS_BY_ACTIVE_FILE_NAME,
                                           overwrite_ok=flags.force)
    FILE_MANAGER.ExitIfCannotOverwriteFile(_REPORT_ORGS_BY_OU_FILE_NAME,
                                           overwrite_ok=flags.force)
  GenerateUserReport(flags)
  orgs_by_active, orgs_by_ou = SummarizeUserOrgReport()
  PrintOrgCounts(orgs_by_active, orgs_by_ou)
  if flags.csv:
    WriteOrgCounts(orgs_by_active, orgs_by_ou, flags)


if __name__ == '__main__':
  main(sys.argv[1:])
