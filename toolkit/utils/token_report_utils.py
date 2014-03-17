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

"""Common functions used in reporting tokens issued.

Used by both command line tools and ui tools.
"""

import pprint
import sys

# setup_path required to allow imports from component dirs (e.g. utils)
# and lib (where the OAuth and Google API Python Client modules reside).
import setup_path  # pylint: disable=unused-import,g-bad-import-order

import file_manager
import log_utils
import report_utils


_TOKENS_ISSUED_FILE_NAME = 'tokens_issued.json'

FILE_MANAGER = file_manager.FILE_MANAGER


_SCOPE_MAP = {
    'http://docs.google.com/feeds': (
        'Docs (Read/Write, does not require SSL)'),
    'http://docs.googleusercontent.com': (
        'Download PDF and arbitrary files from Docs (Read only, does not '
        'require SSL)'),
    'http://mail.google.com/mail/feed/atom': (
        'Email, new messages (Read only, does not require SSL)'),
    'http://sites.google.com/feeds': (
        'Sites (Read/Write, does not require SSL)'),
    'http://spreadsheets.google.com/feeds': (
        'Spreadsheets (Read/Write, does not require SSL)'),
    'http://www.google.com/calendar/feeds': (
        'Calendar (Read/Write, does not require SSL)'),
    'http://www.google.com/finance/feeds': (
        'Finance (Read Only, does not require SSL)'),
    'http://www.google.com/m8/feeds': (
        'Contacts (Read/Write, does not require SSL)'),
    'https://apps-apis.google.com/a/feeds/calendar/resource': (
        'Calendar Resources (Read/Write)'),
    'https://apps-apis.google.com/a/feeds/calendar/resource/#readonly': (
        'Calendar Resources (Read only)'),
    'https://apps-apis.google.com/a/feeds/emailsettings/2.0': (
        'Email Settings (Read/Write)'),
    'https://apps-apis.google.com/a/feeds/group/#readonly': (
        'Groups Provisioning (Read only)'),
    'https://apps-apis.google.com/a/feeds/groups': (
        'Groups Provisioning'),
    'https://apps-apis.google.com/a/feeds/migration': (
        'Email Migration (Write only)'),
    'https://apps-apis.google.com/a/feeds/nickname/#readonly': (
        'User Nicknames (Read only)'),
    'https://apps-apis.google.com/a/feeds/user': (
        'User Provisioning'),
    'https://apps-apis.google.com/a/feeds/user/#readonly': (
        'User Provisioning (Read only)'),
    'https://docs.google.com/feeds': (
        'Docs (Read/Write)'),
    'https://docs.googleusercontent.com': (
        'Download PDF and arbitrary files from Docs (Read only)'),
    'https://mail.google.com': (
        'Email (Read/Write/Send)'),
    'https://mail.google.com/mail/feed/atom': (
        'Email, new messages (Read only)'),
    'https://sites.google.com/feeds': (
        'Sites  (Read/Write)'),
    'https://spreadsheets.google.com/feeds': (
        'Spreadsheets (Read/Write)'),
    'https://www.google.com/calendar/feeds': (
        'Calendar (Read/Write)'),
    'https://www.google.com/finance/feeds': (
        'Finance (Read Only)'),
    'https://www.google.com/m8/feeds': (
        'Contacts (Read/Write)'),
    'https://www.googleapis.com/auth/apps.groups.migration': (
        'Groups Mail Migration'),
    'https://www.googleapis.com/auth/apps.groups.settings': (
        'Groups Settings'),
    'https://www.googleapis.com/auth/apps.security': (
        '3LO Tokens (read-write)'),
    'https://www.googleapis.com/auth/calendar': (
        'Calendar (Read-Write)'),
    'https://www.googleapis.com/auth/directory.user': (
        'User Provisioning'),
    'https://www.googleapis.com/auth/directory.user.readonly': (
        'User Provisioning (Read only)'),
    'https://www.googleapis.com/auth/tasks': (
        'Tasks (Read/Write)'),
    'https://www.googleapis.com/auth/tasks.readonly': (
        'Tasks (Read Only)'),
    'https://www.googleapis.com/doclist.createnew': (
        'Docs created with this application'),
    'https://www.googleapis.com/doclist.openwith': (
        'Docs opened with this application'),
    }


def LookupScope(scope):
  """Helper to produce a more readable scope line.

  Args:
    scope: String url that reflects the authorized scope of access.

  Returns:
    Line of text with more readable explanation of the scope with the scope.
  """
  readable_scope = _SCOPE_MAP.get(scope.rstrip('/'))
  if readable_scope:
    return '%s [%s]' % (readable_scope, scope)
  return scope


def PackStatKey(client_id, scope):
  """Helper to create a hashable dictionary key that can be json serialized.

  Args:
    client_id: String, possibly with spaces, of the domain issued a token.
    scope: String with no spaces reflecting the scope of access granted.

  Returns:
    Single string key.
  """
  return '%s %s' % (scope, client_id)


def UnpackStatKey(stat_key):
  """Helper to unpack hashable dictionary key that can be json serialized.

  Args:
    stat_key: String key created by PackStatKey().

  Returns:
    Tuple of strings:
    -client_id: String, possibly with spaces, of the domain issued a token.
    -scope: String with no spaces reflecting the scope of access granted.
  """
  return stat_key.split(None, 1)


class TokenStats(object):
  """Accumulates stats on Client Ids and Scopes for reporting.

  Primarily needs to allow for the following 2 ordered lists:
  -Rank the client_ids according to tokens (users) issued descending.
  -Rank the scopes according to tokens (users) issued descending.

  Additionally, reports will want to allow the following detail drilldown:
  -Show the scopes issued to each client_id.
  -Show the client_ids issued tokens for each scope.
  """

  def __init__(self):
    """Establish internal data structures for accumulation.

    This data structure can be used to report a summary keyed on either
    client_id or scope.  Therefore, the key will be referred to as
    'primary' since it may be either client_ids or scopes. If client_id
    is the 'primary', the 'scope' will be the secondary.

    The primary data structure will be a dictionary.  The key for each
    dictionary element will be the 'primary' string.  The value for each
    dictionary element will be a list of 2-tuple of:
      (set(secondaries), set(users)).
    Each list-element reflects a set of users who granted tokens with access
    described by the set of scopes to an client_id.
    """
    self._access_token_map = {}

  def DebugPrint(self):
    """For debugging show the data structure."""
    pprint.pprint(self._access_token_map)

  def AddToken(self, primary, secondary, users):
    """Add data to the primary key.

    Creates the key if if does not exist.  If the user_set is equal to an
    existing user_set, adds the secondary to the existing secondary list
    otherwise creates a new list element with the new secondary and user list.

    Args:
      primary: String describing the client_id or scope url.
      secondary: String describing the client_id or scope url.
      users: List of users.
    """
    primary_list = self._access_token_map.setdefault(primary, [])
    user_set = set(users)
    found = False
    for secondary_set, secondary_user_set in primary_list:
      if user_set == secondary_user_set:
        found = True
        secondary_set.add(secondary)
    if not found:
      primary_list.append((set([secondary]), user_set))

  def CalculateRankings(self):
    """Run the data and fill a counter with user counts on primary key.

    This counter used in reporting rankings based on user counts.

    Returns:
      Counter object with keys of client_id or scope and counts of users
      in each.
    """
    results = report_utils.Counter()
    for primary_key, token_list in self._access_token_map.iteritems():
      primary_user_set = set()
      for _, secondary_user_set in token_list:
        primary_user_set |= secondary_user_set
      results.Increment(primary_key, len(primary_user_set))
    return results

  def GetTokenList(self, primary):
    """Retrieve the token list (value) for the primary key.

    Args:
      primary: String describing the client_id or scope url.

    Returns:
      List of tokens for the primary key. Each token is a 2-tuple of
      -secondary_set
      -user_set
    """
    token_list = self._access_token_map.get(primary, [])
    if token_list:
      token_list = sorted(token_list, key=lambda x: len(x[1]), reverse=True)
    return token_list


def SummarizeTokenStats(token_data):
  """Helper to populate summary data for client_ids and scopes.

  Args:
    token_data: Dictionary deserialized from a json file created by
           gather_domain_token_stats().

  Returns:
    Tuple of TokenStats objects:
    -A TokenStats with client_id as primary and scope as secondary.
    -A TokenStats with scope as primary and client_id as secondary.
  """
  client_id_summary_data = TokenStats()
  scope_summary_data = TokenStats()

  for stat_key, user_list in token_data.iteritems():
    scope, client_id = UnpackStatKey(stat_key)
    client_id_summary_data.AddToken(client_id, scope, user_list)
    scope_summary_data.AddToken(scope, client_id, user_list)

  return client_id_summary_data, scope_summary_data


def GetUsersInDomain(token_data, target_client_id):
  """Helper to retrieve the users who authorized tokens to an client_id.

  Args:
    token_data: Dictionary deserialized from a json file created by
                gather_domain_token_stats().
    target_client_id: String, possibly with spaces, a domain issued a token.

  Returns:
    A counter that includes the list of domains and #users authorizing to each.
  """
  user_list = set()

  for stat_key, stat_user_list in token_data.iteritems():
    _, client_id = UnpackStatKey(stat_key)
    if client_id == target_client_id:
      user_list |= set(stat_user_list)

  return sorted(user_list)


def GetTokenStats(exit_on_fail=True):
  """Reads the snapshot of the token stats from the Json file.

  Args:
    exit_on_fail: Alternately return the message instead of failing
                  if token file not found.  Used for ui reporting.

  Returns:
    Token stats in an object (a dictionary).  If cannot find the file
    return a message to show.
  """
  if not FILE_MANAGER.FileExists(_TOKENS_ISSUED_FILE_NAME):
    message = 'No token data. You must run gather_domain_token_stats first.'
    log_utils.LogError(message)
    if exit_on_fail:
      sys.exit(1)
    else:
      return message
  return FILE_MANAGER.ReadJsonFile(_TOKENS_ISSUED_FILE_NAME)


def WriteTokensIssuedJson(token_stats, overwrite_ok=False):
  """Writes the snapshot of the token stats to Json file in progress.

  Args:
    token_stats: An object with the collected token stats.
    overwrite_ok: If True don't check if file exists - else fail if file exists.

  Returns:
    String reflecting the full path of the file created/written.
  """
  filename_path = FILE_MANAGER.BuildFullPathToFileName(_TOKENS_ISSUED_FILE_NAME)
  if FILE_MANAGER.FileExists(_TOKENS_ISSUED_FILE_NAME) and not overwrite_ok:
    log_utils.LogError('Output file (%s) already exists. Use --force to '
                       'overwrite or --resume to continue an interrupted '
                       'run.' % filename_path)
    sys.exit(1)
  filename_path = FILE_MANAGER.WriteJsonFile(_TOKENS_ISSUED_FILE_NAME,
                                             token_stats,
                                             overwrite_ok=overwrite_ok)
  return filename_path
