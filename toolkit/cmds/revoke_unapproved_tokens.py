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

"""Revokes unapproved oauth tokens issued for all users in a domain.

This is a multi-step process expected to be scheduled on a repeating basis.

1. Retrieves a fresh list of all domain users.
2. Retrieves a fresh list of existing tokens for each of the users (this may
   be a lengthy operation for large domains.).
3. Revoke unapproved tokens based on a set of rules governed by supplying
   client_id and scope blacklists.

APIs Used:
  Experimental Google Apps 3-legged OAuth Token Management API.
"""

import sys

# setup_path required to allow imports from component dirs (e.g. utils)
# and lib (where the OAuth and Google API Python Client modules reside).
import setup_path  # pylint: disable=unused-import,g-bad-import-order

from utils import admin_api_tool_errors
from utils import cmd_utils
from utils import common_flags
from utils import file_manager
from utils import log_utils
from utils import validators

from utils.token_revoker import TokenRevoker


_CLIENT_BLACKLIST_FILE_NAME = 'client_blacklist.txt'
_SCOPE_BLACKLIST_FILE_NAME = 'scope_blacklist.txt'
FILE_MANAGER = file_manager.FILE_MANAGER


def ForceGatherNewUsersList():
  """Ensure the user list is generated fresh by querying the domain.

  This removes any existing users-list-file so that a current user list will be
  generated.  The current user list will be generated when
  gather_domain_token_stats.py is called by RefreshTokenStats() when it cannot
  locate the USERS_FILE_NAME file.
  """
  FILE_MANAGER.RemoveFile(FILE_MANAGER.USERS_FILE_NAME)


def RefreshTokenStats(flags):
  """Writes a file with all the domain token information.

  Queries each user in the domain and many be lengthy for large domains.

  Args:
    flags: Argparse flags object with apps_domain, resume and first_n.
  """
  arg_list = []
  for flag_value, flag_string in [
      (flags.apps_domain, '--apps_domain=%s' % flags.apps_domain),
      (flags.force, '--force'),
      (flags.verbose, '--verbose')]:
    if flag_value:
      arg_list.append(flag_string)
  try:
    with log_utils.Timer('gather_domain_token_stats.py'):
      cmd_utils.RunPyCmd('gather_domain_token_stats.py', arg_list)
  except admin_api_tool_errors.AdminAPIToolCmdError as e:
    log_utils.LogError('Unable to gather token records.', e)
    sys.exit(1)


def AddFlags(arg_parser):
  """Handle command line flags unique to this script.

  Args:
    arg_parser: object from argparse.ArgumentParser() to accumulate flags.
  """
  common_flags.DefineAppsDomainFlagWithDefault(arg_parser)
  common_flags.DefineForceFlagWithDefaultFalse(
      arg_parser, required=True,
      help_string=('This is a destructive command. Please confirm your intent '
                   'to irreversibly revoke tokens by adding --force.'))
  common_flags.DefineVerboseFlagWithDefaultFalse(arg_parser)

  blacklist_help = ('Name of a text file under ./working/<domain> that lists '
                    'unapproved %ss one to a line.\n  (suggested: %s).')
  arg_parser.add_argument(
      '--client_blacklist_file', '-c', default=None,
      help=blacklist_help % ('client', _CLIENT_BLACKLIST_FILE_NAME),
      type=validators.NoWhitespaceValidatorType())
  arg_parser.add_argument(
      '--scope_blacklist_file', '-s', default=None,
      help=blacklist_help % ('scope', _SCOPE_BLACKLIST_FILE_NAME),
      type=validators.NoWhitespaceValidatorType())
  arg_parser.add_argument(
      '--hide_timing', action='store_true', default=False,
      help='Stop logging the elapsed time of longer functions.')
  arg_parser.add_argument(
      '--use_local_token_stats', action='store_true', default=False,
      help='Avoid regenerating token stats.')
  arg_parser.add_argument(
      '--use_local_users_list', action='store_true', default=False,
      help='Avoid regenerating domain users list.')


def main(argv):
  """A script to gather token data and revoke unapproved tokens issued.

   -In v1: only an 'client_id' blacklist and/or a 'scope' blacklist are
    accepted. Handling of blacklists is straightforward. This utility revokes
    any token issued to an client_id on the client_id black list or with
    a scope found on the scope blacklist.
   -In v2: an client_id white_list may be supplied.  But, the white_list
    may not be supplied if any blacklist is supplied.  It must be alone.
    In handling the white_list, any token to an client_id must also be
    present in the client_id white_list otherwise it is revoked.  As a
    special case, if an client_id white_list is supplied, but it is empty,
    ALL TOKENS WILL BE REVOKED.
   -In v3: combinations of blacklists and white_lists will be allowed.  This
    will allow for three unusual circumstances:
    1) If client_ids are discovered in both white and black lists, the
       utility will fail and take no action. This is considered an unexpected
       error and requires immediate attention.
    2) If an empty white_list is supplied along with non-empty black lists,
       the utility will fail and take no action. This is considered an
       unexpected error and requires immediate attention.
    3) As normal, if a token is found that matches a blacklist it is revoked,
       and tokens found that match the non-empty white_list will remain.  But,
       tokens found that are present neither in a blacklist or white_list
       will cause a WARNING LOG message to be emitted that may be observed.

  Args:
    argv: argument tokens in a list of strings.
  """
  flags = common_flags.ParseFlags(argv,
                                  'Revoke unapproved tokens across a domain.',
                                  AddFlags)
  if not flags.client_blacklist_file and not flags.scope_blacklist_file:
    log_utils.LogError(
        'Either --client_blacklist_file or --scope_blacklist_file must '
        'be supplied.')
    sys.exit(1)

  log_border = 40 * '-'
  log_utils.LogInfo('revoke_unapproved_tokens starting...\n%s' % log_border)
  token_revoker = TokenRevoker(flags)
  if flags.client_blacklist_file:
    token_revoker.LoadClientBlacklist(flags.client_blacklist_file)
  if flags.scope_blacklist_file:
    token_revoker.LoadScopeBlacklist(flags.scope_blacklist_file)
  token_revoker.ExitIfBothBlackListsEmptys()

  if not flags.use_local_users_list:
    ForceGatherNewUsersList()

  # Should normally refresh the token stats - this is for the case where a
  # second pass is desired either for resuming or running a complicated set
  # of rules.
  if not flags.use_local_token_stats:
    RefreshTokenStats(flags)

  token_revoker.RevokeUnapprovedTokens()
  log_utils.LogInfo('revoke_unapproved_tokens done.\n%s' % log_border)
  print 'Revocation details logged to: %s.' % log_utils.GetLogFileName()


if __name__ == '__main__':
  main(sys.argv[1:])
