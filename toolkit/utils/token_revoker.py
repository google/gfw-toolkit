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

"""Class that holds the logic for revoking unapproved tokens based on lists.

Uses black-lists of clients and/or scopes to determine 'unapproved'.
Relies on RefreshTokenStats() to retrieve actual token stats; they are
retrieved with a series of requests and cached in a local file.

Logic to support 'white-lists' and to interpret conflicts between black-lists
and white-lists has been deferred for simplicity.

A recommended pattern of usage is:

  token_revoker = TokenRevoker(flags)

  # Load lists of unapproved clients and scopes.
  if flags.client_blacklist_file:
    token_revoker.LoadClientBlacklist(flags.client_blacklist_file)
  if flags.scope_blacklist_file:
    token_revoker.LoadScopeBlacklist(flags.scope_blacklist_file)
  token_revoker.ExitIfBothBlackListsEmptys()

  # Update the list of domain users to check.
  if not flags.use_local_users_list:
    RefreshDomainUsersList()

  # Update the record of tokens issued.
  if not flags.use_local_token_stats:
    RefreshTokenStats()

  # Determine and revoke the unapproved tokens.
  token_revoker.RevokeUnapprovedTokens()
"""

import sys

# setup_path required to allow imports from component dirs (e.g. utils)
# and lib (where the OAuth and Google API Python Client modules reside).
import setup_path  # pylint: disable=unused-import,g-bad-import-order

from admin_sdk_directory_api import tokens_api
from utils import admin_api_tool_errors
from utils import auth_helper
from utils import file_manager
from utils import log_utils
from utils import token_report_utils


FILE_MANAGER = file_manager.FILE_MANAGER


class TokenRevoker(object):
  """Manages the complexity of the token revocation agasint multiple lists."""

  def __init__(self, flags):
    """Initialize sets which are udpated based on flags.

    Args:
      flags: Argparse flags object with apps_domain, force, hide_timing.
    """
    self._flags = flags
    # Need to store the revocation data in a dictionary because the data
    # may be reexamined in handling for both black and white lists.
    self._tokens_to_revoke = {}  # Populated by checks in this class.
    self._token_data = None  # Read from the token json file.
    self._client_blacklist_set = set()  # Read from file.
    self._scope_blacklist_set = set()  # Read from file.

    self._http = auth_helper.GetAuthorizedHttp(flags)
    self._tokens_api = tokens_api.TokensApiWrapper(self._http)

  def LoadClientBlacklist(self, client_blacklist_file):
    """If supplied, read the client black list file into a set.

    Clients are the domains to whom the tokens have been issued
    (e.g. twitter.com).

    Args:
      client_blacklist_file: String path of the file or None.  None if the
                             command line option not supplied because
                             another method of describing unapproved tokens
                             was used (e.g. scope black list).
    """
    self._client_blacklist_set = (
        FILE_MANAGER.ReadTextFileToSet(client_blacklist_file))

  def LoadScopeBlacklist(self, scope_blacklist_file):
    """If supplied, read the scope black list file into a set.

    Args:
      scope_blacklist_file: String path of the file or None.  None if the
                            command line option not supplied because
                            another method of describing unapproved tokens
                            was used (e.g. client black list).
    """
    self._scope_blacklist_set = (
        FILE_MANAGER.ReadTextFileToSet(scope_blacklist_file))
    # Scopes inconsistently add / - so strip them for our purposes.
    self._scope_blacklist_set = set([s.rstrip('/')
                                     for s in self._scope_blacklist_set])

  def ExitIfBothBlackListsEmptys(self):
    """Look through the lists supplied by command line for the unexpected."""
    if not self._client_blacklist_set and not self._scope_blacklist_set:
      log_utils.LogError('All black lists empty. There is nothing to revoke.')
      sys.exit(1)

  def _IsRevokedByClientBlacklist(self,
                                  scope,  # pylint: disable=unused-argument
                                  client_id):
    """Checks if issued tokens match client_ids listed in client black list.

    By making this a method, this can be expanded to support more complex
    matching such as regex client strings.

    Args:
      scope: String of the scope URI for an issued token - unused.
      client_id: String of the client domain issued the token.
                 May include spaces.

    Returns:
      True if the token is to be revoked by the client black list else False.
    """
    return (self._client_blacklist_set and
            client_id in self._client_blacklist_set)

  def _IsRevokedByScopeBlacklist(self,
                                 scope,
                                 client_id):  # pylint: disable=unused-argument
    """Checks if issued tokens match scopes listed in scope black list.

    By making this a method, this can be expanded to support more complex
    matching such as regex scope strings.

    Args:
      scope: String of the scope URI for an issued token - unused.
      client_id: String of the client domain issued the token.
                 May include spaces.

    Returns:
      True if the token is to be revoked by the scope black list else False.
    """
    if not scope:
      return False
    # Scopes can arbitrarily include a trailing slash so we need to check
    # for both slash-persent and no-slash-present cases.
    candidate_scopes = set([scope.rstrip('/'), scope.rstrip('/') + '/'])
    return self._scope_blacklist_set & candidate_scopes

  def _IdentifyTokensToRevoke(self):
    """Enumerate known tokens and match against revoked clients/scopes.

    Sets self._tokens_to_revoke to a dictionary of the token data to revoke:
      e.g. {u'130316539331.apps.googleusercontent.com':
                set([u'larry@altostrat.com']),
            u'610978662317.apps.googleusercontent.com':
                set([u'larry@altostrat.com'])}
    """
    with log_utils.Timer(
        'Identify tokens', hide_timing=self._flags.hide_timing):
      self._token_data = token_report_utils.GetTokenStats()
      for stat_key, user_list in self._token_data.iteritems():
        scope, client_id = token_report_utils.UnpackStatKey(stat_key)
        for blacklist_filter in [self._IsRevokedByClientBlacklist,
                                 self._IsRevokedByScopeBlacklist]:
          client_ids_revoked = blacklist_filter(scope, client_id)
          if client_ids_revoked:
            user_set = self._tokens_to_revoke.setdefault(client_id, set())
            user_set.update(set(user_list))

  def _RevokeToken(self, user_mail, client_id):
    """Revoke a single token based on client_id and user.

    Failures are logged but execution continues.

    Args:
      user_mail: String email address of the user that authorized the token.
      client_id: String of the client domain issued the token.
                 May include spaces.
    """
    log_utils.LogInfo('Revoking: %s, %s.' % (user_mail, client_id))
    try:
      self._tokens_api.DeleteToken(user_mail, client_id)
    except admin_api_tool_errors.AdminAPIToolTokenRequestError as e:
      log_utils.LogError(
          'Unable to revoke token for user %s and client_id %s.'
          % (user_mail, client_id), e)

  def RevokeUnapprovedTokens(self):
    """Examine each token and match it against rules to determine revocation.

    The black lists (client and scope) are straightforward to handle: tokens
    issued that are matched to a blacklist are revoked.
    """
    self._IdentifyTokensToRevoke()
    if not self._tokens_to_revoke:
      log_utils.LogInfo('No tokens found to revoke')
      return
    log_utils.LogInfo('Tokens found to revoke.  Revoking now...')
    with log_utils.Timer(
        'All _RevokeToken() calls', hide_timing=self._flags.hide_timing):
      for client_id in sorted(self._tokens_to_revoke):
        for user_mail in sorted(self._tokens_to_revoke[client_id]):
          self._RevokeToken(user_mail, client_id)
