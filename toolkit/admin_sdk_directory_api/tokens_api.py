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

"""Tool to enable access to apps security APIs for oauth token management.

Relies on Admin SDK Tokens API.

Example requests and responses for the Admin SDK Tokens APIs can be reviewed
in the API_NOTES file.
"""

from operator import itemgetter  # for sorting

from apiclient import errors as apiclient_errors
from apiclient.discovery import build
from utils import admin_api_tool_errors
from utils import file_manager
from utils import http_utils
from utils import log_utils
from utils import token_report_utils


FILE_MANAGER = file_manager.FILE_MANAGER


class TokensApiWrapper(object):
  """Expose the methods of 3-legged OAuth management."""

  def __init__(self, http):
    """Create our service object with access to the apps security APIs.

    Args:
      http: An authorized http interface object.
    """
    self._service = build(serviceName='admin', version='directory_v1',
                          http=http)
    self._tokens = self._service.tokens()

  def _IssueTokensRequestForUser(self, request):
    """Create and issue a tokens request authorized by the user.

    The request will reflect one of a get(), list() or delete() command. The
    operation can be inspected by looking at request.methodId for one of:
    u'directory.tokens.list', u'directory.tokens.get' or
    u'directory.tokens.delete'.

    Args:
      request: Google API service request object from a get(), list() or
               delete() invocation.

    Returns:
      A dictionary (called a json document in references) with a member 'items'
      which is a list of tokens.
    """
    backoff = http_utils.Backoff()
    while backoff.Loop():
      try:
        return request.execute()
      except apiclient_errors.HttpError as e:
        # 404 is returned from get when no tokens for client_id exist.
        # This is normal and should not be presented to the user as an error.
        if request.method != 'DELETE' and e.resp.status == 404:
          return {}
        if e.resp.status not in http_utils.RETRY_RESPONSE_CODES:
          raise admin_api_tool_errors.AdminAPIToolUserError(
              '%s\nPlease check your domain spelling.'
              % http_utils.ParseHttpResult(e.uri, e.resp, e.content))
        log_utils.LogInfo('Possible quota problem with %s tokens (%d).' %
                          (request.methodId, e.resp.status))
        backoff.Fail()

  def DeleteToken(self, user_mail, client_id):
    """Deletes 1 token for a user and client.

    Args:
      user_mail: email address for the user e.g. xxx@yyy.com.
      client_id: domain authorized (e.g. xxx.apps.googleusercontent.com).

    Returns:
      A dictionary (called a json document in references) with a member 'items'
      which is a list of tokens.
    """
    return self._IssueTokensRequestForUser(
        self._tokens.delete(clientId=client_id, userKey=user_mail))

  def GetToken(self, user_mail, client_id):
    """Retrieves 1 token for a user and client.

    Args:
      user_mail: email address for the user e.g. xxx@yyy.com.
      client_id: domain authorized (e.g. xxx.apps.googleusercontent.com).

    Returns:
      A dictionary (called a json document in references) with a member 'items'
      which is a list of tokens.
    """
    return self._IssueTokensRequestForUser(
        self._tokens.get(clientId=client_id, userKey=user_mail))

  def ListTokens(self, user_mail):
    """Retrieves a list of tokens for a user.

    Args:
      user_mail: email address for the user e.g. xxx@yyy.com.

    Returns:
      A dictionary (called a json document in references) with a member 'items'
      which is a list of tokens.
    """
    return self._IssueTokensRequestForUser(self._tokens.list(userKey=user_mail))

  @staticmethod
  def _PrintOneLine(client_id, display_text=None, scopes=None):
    """Justify and print one line of token data.

    40 character wide columns are arbitrarily chosen.  It's a half
    of a standard 80-char console screen so seems commonly usable.

    Args:
      client_id: Domain authorized with the token (e.g. twitter.com).
      display_text: Human readable domain - sometimes same as the client_id.
      scopes: List of authorized scopes of access.
    """
    col_width = 40
    fmt = '%%-%ss' % col_width
    values = [client_id]
    if display_text:
      fmt = '%s %s' % (fmt, fmt)
      # apps.googleusercontent.com has very long client_ids...wrap them.
      if len(client_id) > col_width:
        fmt += '\n  %s'
        values = [client_id[:col_width], display_text,
                  client_id[col_width:]]
      else:
        values.append(display_text)
    print fmt % tuple(values)
    if not scopes:
      return
    for scope in sorted(scopes):
      print '    %s' % token_report_utils.LookupScope(scope)

  @staticmethod
  def _PrintOneToken(token, long_list=False):
    """Prints select fields from returned token json.

    Args:
      token: token object retrieved from Apps Security APIs.
      long_list: if True then print additional fields.
    """
    if long_list:
      TokensApiWrapper._PrintOneLine(client_id=token['clientId'],
                                     display_text=token['displayText'],
                                     scopes=token['scopes'])
    else:
      TokensApiWrapper._PrintOneLine(client_id=token['clientId'],
                                     display_text=token['displayText'])

  def GetTokensForUser(self, user_mail):
    """Get the list of tokens issued by a user.

    Args:
      user_mail: email address for the user e.g. xxx@yyy.com.

    Returns:
      A list of tokens authorized by user_mail.
    """
    token_doc = self.ListTokens(user_mail=user_mail)
    if not token_doc:
      raise admin_api_tool_errors.AdminAPIToolTokenRequestError(
          'ERROR: Unexpected response: no document returned.')
    if 'items' in token_doc:
      return sorted(token_doc['items'], key=itemgetter('clientId'))
    return []

  def PrintTokensForUser(self, user_mail, long_list=False):
    """Simple print of token document for a given customer/user.

    Args:
      user_mail: email address for the user e.g. xxx@yyy.com.
      long_list: boolean, if True then print more output columns.
    """
    token_list = self.GetTokensForUser(user_mail)
    if token_list:
      TokensApiWrapper._PrintOneLine(client_id='Client ID',
                                     display_text='Display Text')
      for token in token_list:
        TokensApiWrapper._PrintOneToken(token=token, long_list=long_list)
    else:
      print 'No tokens found for that user.'

  def PrintTokenForUserClientId(self, user_mail, client_id, long_list=False):
    """Simple print of token document for given customer/user/client_id.

    Args:
      user_mail: email address for the user e.g. xxx@yyy.com.
      client_id: domain authorized (e.g. xxx.apps.googleusercontent.com).
      long_list: boolean, if True then print more output columns.
    """
    token_doc = self.GetToken(user_mail=user_mail, client_id=client_id)
    if token_doc:
      TokensApiWrapper._PrintOneLine(client_id='Client ID',
                                     display_text='Display Text')
      TokensApiWrapper._PrintOneToken(token=token_doc, long_list=long_list)
    else:
      print 'No tokens found for that user and client_id.'
