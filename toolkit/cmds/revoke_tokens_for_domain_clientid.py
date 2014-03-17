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

"""Revokes the oauth tokens issued to an application for all users in a domain.

Tool to show usage of 3-legged oauth APIs.

APIs Used:
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
from utils import validators


PREFIX = 'revocation'


def AddFlags(arg_parser):
  """Handle command line flags unique to this script.

  Args:
    arg_parser: object from argparse.ArgumentParser() to accumulate flags.
  """
  common_flags.DefineAppsDomainFlagWithDefault(arg_parser)
  common_flags.DefineVerboseFlagWithDefaultFalse(arg_parser)

  arg_parser.add_argument(
      '--client_id', '-c', required=True,
      help=('Client ID to which the token was issued (e.g. twitter.com) '
            '[REQUIRED].'),
      type=validators.NoWhitespaceValidatorType())
  arg_parser.add_argument(
      '--first_n', type=int, default=0,
      help='Revoke tokens for the first n users in the domain.')
  arg_parser.add_argument(
      '--resume', '-r', action='store_true', default=False,
      help='Resume an interrupted gather command.')
  arg_parser.add_argument(
      '--use_local_token_stats', action='store_true', default=False,
      help=('Only attempt to revoke tokens listed in the local stats file '
            'created by a previous run of gather_domain_token_stats.'))


def main(argv):
  """A script to test Apps Security APIs: revoking oauth2 tokens."""
  flags = common_flags.ParseFlags(argv, 'Revoke tokens issued for a client id.',
                                  AddFlags)
  log_border = (40 * '-')
  log_utils.LogInfo('revoke_tokens_for_domain_clientid starting...\n%s'
                    % log_border)

  if flags.use_local_token_stats:
    stats_user_list = token_report_utils.GetUsersInDomain(
        token_report_utils.GetTokenStats(), flags.client_id)
  else:
    stats_user_list = []  # List of users with a token for an issue domain

  http = auth_helper.GetAuthorizedHttp(flags)
  apps_security_api = tokens_api.TokensApiWrapper(http)

  # The user list holds a tuple for each user of: email, id, full_name
  # (e.g. 'larry@altostrat.com', '000000000098938768732', 'Larry Summon').
  print 'Scanning domain users for %s...' % PREFIX
  for user in user_iterator.StartUserIterator(http, PREFIX, flags):
    user_email, _, _ = user
    # Skip revocation attempts if tokens not found in the latest report.
    if flags.use_local_token_stats and user_email not in stats_user_list:
      continue

    try:
      # NOTE: attempting to revoke a non-existent token causes no
      #       discernible output (no failure message or fail status).
      apps_security_api.DeleteToken(user_email, flags.client_id)
    except admin_api_tool_errors.AdminAPIToolTokenRequestError as e:
      # This suggests an unexpected response from the apps security api.
      # As much detail as possible is provided by the raiser.
      sys.stdout.write('%80s\r' % '')  # Clear the previous entry.
      sys.stdout.flush()
      log_utils.LogError(
          'Unable to revoke token for user %s and client_id %s.'
          % (user, flags.client_id), e)
      sys.exit(1)
    # If attempting to revoke tokens for the whole domain, do not print
    # confirmation because we're not sure which users actually had the tokens.
    if flags.use_local_token_stats:
      log_utils.LogInfo(
          'Successfully revoked token for user %s for client_id %s.'
          % (user_email, flags.client_id))
  log_utils.LogInfo('revoke_tokens_for_domain_clientid done.\n%s' % log_border)
  print 'Revocation details logged to: %s.' % log_utils.GetLogFileName()
  if not flags.use_local_token_stats:
    print 'NOTE: To save time, revocation is attempted for all domain users '
    print '      without checking in advance if a token was granted.  Because '
    print '      revocation returns no indication of actual token revocation, '
    print '      the actual clients of tokens revoked are not logged. If it '
    print '      is required to log the actual client ids of revoked tokens, '
    print '      run the gather token stats command and use '
    print '      --use_local_token_stats with this command. '


if __name__ == '__main__':
  main(sys.argv[1:])
