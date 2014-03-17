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

"""Produce user reports from the domain token stats file.

The domain token stats file reflects tokens issued by Google Apps users
that allow external domains (e.g. twitter.com) access to some user data.
This file is produced by running gather_domain_token_stats.

This file produces output user reports that are useful in identifying users
in anticipation of revoking tokens.
"""

import sys

# setup_path required to allow imports from component dirs (e.g. utils)
# and lib (where the OAuth and Google API Python Client modules reside).
import setup_path  # pylint: disable=unused-import,g-bad-import-order

from utils import common_flags
from utils import file_manager
from utils import token_report_utils
from utils.report_utils import BORDER
from utils.report_utils import PrintReportLine
from utils.report_utils import SEPARATOR
from utils.report_utils import WrapReportText


_CLIENT_ID_REPORT_FILE_NAME = 'top_client_ids.csv'
_SCOPES_REPORT_FILE_NAME = 'top_scopes.csv'


FILE_MANAGER = file_manager.FILE_MANAGER


def ReportCommonClientIDs(client_id_summary, flags):
  """Report the domains that were most frequently issued tokens.

  Args:
    client_id_summary: TokenStats object with client_id as primary.
    flags: Argparse flags object with console, long_list, show_users.
  """
  client_counter = client_id_summary.CalculateRankings()
  csv_header = ['NUM_USERS', 'CLIENT_ID']
  if flags.console:
    PrintReportLine('\n%s' % BORDER)
    PrintReportLine('MOST COMMON CLIENT IDs:')
    PrintReportLine(BORDER)
    PrintReportLine('%s' % '\t'.join(csv_header), indent=True)
    for client_id, user_count in (
        client_counter.FilterAndSortMostCommon(flags.top_n)):
      PrintReportLine('%d:\t%s' % (user_count, client_id), indent=True)
      if flags.long_list:
        for token in client_id_summary.GetTokenList(client_id):
          scope_set, user_set = token
          printable_scopes = [token_report_utils.LookupScope(s)
                              for s in sorted(scope_set)]
          PrintReportLine('%2d: %s' % (len(user_set), printable_scopes[0]),
                          indent=True, indent_level=2)
          for scope in printable_scopes[1:]:
            PrintReportLine(scope, indent=True, indent_level=3)
          if flags.show_users:
            users_string = ', '.join(sorted(user_set))
            PrintReportLine(SEPARATOR, indent=True, indent_level=3)
            PrintReportLine(WrapReportText(users_string))

  if flags.csv:
    # Swap client_id and user_count for printing.
    csv_rows = [
        (v, k) for k, v in client_counter.FilterAndSortMostCommon(flags.top_n)]
    filename_path = FILE_MANAGER.WriteCSVFile(_CLIENT_ID_REPORT_FILE_NAME,
                                              csv_rows, csv_header,
                                              overwrite_ok=flags.force)
    print 'Wrote common client ids report: %s.' % filename_path


def ReportCommonScopes(scope_summary, flags):
  """Report the scopes that were most frequently used issuing tokens.

  Args:
    scope_summary: TokenStats object with scope as primary.
    flags: Argparse flags object with console, long_list, show_users.
  """
  scope_counter = scope_summary.CalculateRankings()
  csv_header = ['NUM_USERS', 'SCOPE']
  if flags.console:
    PrintReportLine('\n%s' % BORDER)
    PrintReportLine('MOST COMMON SCOPES:')
    PrintReportLine(BORDER)
    PrintReportLine('%s' % '\t'.join(csv_header), indent=True)
    for scope, user_count in scope_counter.FilterAndSortMostCommon(flags.top_n):
      PrintReportLine(
          '%d:\t%s' % (user_count, token_report_utils.LookupScope(scope)),
          indent=True)
      if flags.long_list:
        for token in scope_summary.GetTokenList(scope):
          client_id_set, user_set = token
          sorted_domains = sorted(client_id_set)
          PrintReportLine('%2d: %s' % (len(user_set), sorted_domains[0]),
                          indent=True, indent_level=2)
          for client_id in sorted_domains[1:]:
            PrintReportLine(client_id, indent=True, indent_level=3)
          if flags.show_users:
            users_string = ', '.join(sorted(user_set))
            PrintReportLine(SEPARATOR, indent=True, indent_level=3)
            PrintReportLine(WrapReportText(users_string))

  if flags.csv:
    # Swap scope and user_count for printing.
    csv_rows = [
        (v, k) for k, v in scope_counter.FilterAndSortMostCommon(flags.top_n)]
    filename_path = FILE_MANAGER.WriteCSVFile(_SCOPES_REPORT_FILE_NAME,
                                              csv_rows, csv_header,
                                              overwrite_ok=flags.force)
    print 'Wrote common scopes report: %s.' % filename_path


def AddFlags(arg_parser):
  """Handle command line flags unique to this script.

  Args:
    arg_parser: object from argparse.ArgumentParser() to accumulate flags.
  """
  common_flags.DefineAppsDomainFlagWithDefault(arg_parser)
  common_flags.DefineForceFlagWithDefaultFalse(arg_parser)
  common_flags.DefineVerboseFlagWithDefaultFalse(arg_parser)

  arg_parser.add_argument('--console', action='store_true', default=True,
                          help='Print output on console.')
  arg_parser.add_argument('--csv', action='store_true', default=False,
                          help='Output results to a csv file.')
  arg_parser.add_argument('--long_list', '-l', action='store_true',
                          default=False,
                          help='Show details of client_ids and scopes.')
  arg_parser.add_argument('--show_users', '-u', action='store_true',
                          default=False,
                          help='Show details of users (enables --long_list).')
  arg_parser.add_argument('--top_n', type=int, default=0,
                          help='Show top n elements in each report.')


def main(argv):
  """A script to test Apps Security APIs: summarizing oauth2 tokens."""
  flags = common_flags.ParseFlags(argv,
                                  'Create report of domain token info.',
                                  AddFlags)
  if flags.show_users:
    flags.long_list = True
  client_id_summary, scope_summary = token_report_utils.SummarizeTokenStats(
      token_report_utils.GetTokenStats())
  ReportCommonClientIDs(client_id_summary, flags)
  ReportCommonScopes(scope_summary, flags)


if __name__ == '__main__':
  main(sys.argv[1:])
