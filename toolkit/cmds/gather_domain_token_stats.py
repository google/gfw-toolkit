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

"""Gather token information for a whole domain and show some stats.

This may be a large task given many domains > 20k users.  Therefore,
this script requires some form of perisistence.  Likely, this script
will get interrupted by quota constraints and need to be resumed
so progress should be tracked.

Overall, enough data should be collected to show 3 primary stats:
  1. List the domains the are most frequently issued tokens.
  2. List the users most frequently authorizing token access.
  3. Show a map of users to client_ids (to allow for revocation).

Tool to show usage of Admin SDK Directory APIs.

APIs Used:
  Admin SDK Directory API: user management
  Experimental Google Apps 3-legged OAuth Token Management API.
"""

import sys

# setup_path required to allow imports from component dirs (e.g. utils)
# and lib (where the OAuth and Google API Python Client modules reside).
import setup_path  # pylint: disable=unused-import,g-bad-import-order

from admin_sdk_directory_api import tokens_api
from utils import admin_api_tool_errors
from utils import auth_helper
from utils import common_flags
from utils import log_utils
from utils import token_report_utils
from utils import user_iterator


def AddFlags(arg_parser):
  """Handle command line flags unique to this script.

  Args:
    arg_parser: object from argparse.ArgumentParser() to accumulate flags.
  """
  common_flags.DefineAppsDomainFlagWithDefault(arg_parser)
  common_flags.DefineForceFlagWithDefaultFalse(arg_parser)
  common_flags.DefineVerboseFlagWithDefaultFalse(arg_parser)

  arg_parser.add_argument('--first_n', type=int, default=0,
                          help=('Gather tokens for the first n users in the '
                                'domain.'))
  arg_parser.add_argument('--resume', '-r', action='store_true', default=False,
                          help='Resume an interrupted gather command.')


def main(argv):
  """A script to test Apps Security APIs: summarizing oauth2 tokens."""
  flags = common_flags.ParseFlags(argv,
                                  'Gather token status for entire domain.',
                                  AddFlags)
  # Tracks stats for each domain-scope:
  # {
  #   (scope1, domain1): [user1, user2, ...],
  #   (scope2, domain1): [user1, user3, ...],
  #   (scope1, domain2): [user4, user5, ...],
  #   (scope3, domain3): [user6, user7, ...],
  # }
  # Issue domains (e.g.twitter.com) are the domains to whom the token was
  # issued and scopes reflect the data accessed.
  #
  # This is simple to minimize memory footprint.  Later processing of this data
  # structure will report most frequent: issue domains, scopes and users.
  token_stats = {}

  if not flags.resume:
    # Early check if file exists and not --force.
    filename_path = token_report_utils.WriteTokensIssuedJson(token_stats,
                                                             flags.force)
  else:
    token_stats = token_report_utils.GetTokenStats()

  http = auth_helper.GetAuthorizedHttp(flags)
  apps_security_api = tokens_api.TokensApiWrapper(http)

  iterator_purpose = 'collection'  # Used to tag iterator progress data.

  # The user list holds a tuple for each user of: email, id, full_name
  # (e.g. 'larry', '112351558298938768732', 'Larry Summon').
  print 'Scanning domain users for %s' % iterator_purpose
  for user in user_iterator.StartUserIterator(http, iterator_purpose, flags):
    user_email, user_id, checkpoint = user
    try:
      token_list = apps_security_api.GetTokensForUser(user_id)
    except admin_api_tool_errors.AdminAPIToolTokenRequestError as e:
      # This suggests an unexpected response from the apps security api.
      # As much detail as possible is provided by the raiser.
      sys.stdout.write('%80s\r' % '')  # Clear the previous entry.
      sys.stdout.flush()
      log_utils.LogError('Unable to get user tokens.', e)
      sys.exit(1)

    for token in token_list:
      # Save lists of users with tokens.
      for scope in token['scopes']:
        stat_key = token_report_utils.PackStatKey(token['clientId'], scope)
        token_stats.setdefault(stat_key, [])
        token_stats[stat_key].append(user_email)

    if checkpoint:
      # Save progress every n users.
      filename_path = token_report_utils.WriteTokensIssuedJson(
          token_stats, overwrite_ok=True)
  print 'Token report written: %s' % filename_path


if __name__ == '__main__':
  main(sys.argv[1:])
