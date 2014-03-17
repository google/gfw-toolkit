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

"""Tool to show a pattern of easy access to an API.

Relies on the google-api-python-client and its embedded oauth2client.
See the README for more details on google-api-python-client.
"""

import pprint
import textwrap

from admin_sdk_directory_api import users_api
from apiclient import errors as apiclient_errors
from apiclient.discovery import build
from utils import admin_api_tool_errors
from utils import http_utils
from utils import log_utils


class PlusDomains(object):
  """Demonstrates a few needed functions of user provisioning."""

  def __init__(self, http):
    """Create our service object with access to Admin SDK Directory APIs.

    Args:
      http: An authorized http interface object.
    """
    self._service = build('plusDomains', 'v1', http=http)
    self._users = self._service.people()

  @staticmethod
  def _ShowAllUserFields(user):
    """Show all fields [this can be many] of user data.

    Available fields include (use ls_user -u xxx@mybiz.com -l to see real data):
      birthday, displayName, etag, gender, id, image, isPlusUser, kind,
      name ({'familyName': 'xx', 'givenName': 'yy'}), objectType, url,
      verified.

    Args:
      user: user json object returned from the users API list().

    Returns:
      Dictionary of the entire user metadata.
    """
    return user

  @staticmethod
  def _ShowBasicUserFields(user):
    """Select and show only 3 basic fields from returned user json.

    Args:
      user: user json object returned from the users API list().

    Returns:
      Tuple reflecting the user: (display_name, user_id, user_url).
    """
    return (users_api.GetFieldFromUser(user, 'displayName'),
            users_api.GetFieldFromUser(user, 'id'),
            users_api.GetFieldFromUser(user, 'url'))

  @staticmethod
  def _PrintOneLine(display_name, user_id, user_url):
    """Formats a user print line a little like ls -l.

    Example output:

    Users from domain altostrat.com:
    ID                     Display Name                          User Url
    000000000098938768732  George Lasta                          https://...

    A real user url has the format:
      https://plus.google.com/000000058298938768732

    Args:
      display_name: first and last name [This can be different than the users
                                         directory name].
      user_id: 21 digit domain id.
      user_url: x character url to the profile.
    """
    # Left justify all but the last as string fields.
    print '%-22s %-40s %s' % (user_id, display_name, user_url)

  @staticmethod
  def _PrintUserHeader():
    """Print user header for ls_users and ls_user."""
    PlusDomains._PrintOneLine('Display Name', 'ID', 'User Url')

  @staticmethod
  def _PrintOneUser(user, long_list=False):
    """Prints select fields from returned user json.

    Available fields include:
      birthday, displayName, etag, gender, id, image, isPlusUser, kind,
      name ({'familyName': 'xx', 'givenName': 'yy'}), objectType, url,
      verified.
    Special handling is needed for:
      name: sort for deterministic output.
      image: handle multiple images.

    Args:
      user: user json object returned from the users API list().
      long_list: if True, print all known user fields.
    """
    PlusDomains._PrintOneLine(users_api.GetFieldFromUser(user, 'displayName'),
                              users_api.GetFieldFromUser(user, 'id'),
                              users_api.GetFieldFromUser(user, 'url'))
    if long_list:
      for field in sorted(user.keys()):
        if field in ('displayName', 'id', 'url'):  # already displayed.
          continue
        # For deterministic output, need to pprint container objects like
        # dict. Textwrap is used for the hanging indent.  We use a hanging
        # indent of 7 because 4 spaces is the normal margin and the extra
        # 3 spaces are used for: colon, space and opening brace.
        formatted_text = textwrap.fill(
            pprint.pformat(users_api.GetFieldFromUser(user, field)),
            subsequent_indent=(7+len(field)) * ' ', break_on_hyphens=False)
        print '    %s: %s' % (field, formatted_text)

  def GetDomainUser(self, user_mail):
    """Retrieve document for a user in an apps domain.

    A common reason to call this is to retrieve the user_id from an email name.

    Args:
      user_mail: username to check.

    Returns:
      The user document (available fields listed in _PrintOneUser()).
    """
    log_utils.LogDebug('GetDomainUser --plus_domains (%s).' % user_mail)
    request = self._users.get(userId=user_mail)
    backoff = http_utils.Backoff()
    while backoff.Loop():
      try:
        return request.execute()
      except apiclient_errors.HttpError as e:  # Missing user raises HttpError.
        if e.resp.status not in http_utils.RETRY_RESPONSE_CODES:
          error_text = http_utils.ParseHttpResult(e.uri, e.resp, e.content)
          if error_text.startswith('ERROR: status=404'):
            # User not found is reflected by 404 - resource not found.
            return None
          elif error_text.startswith('ERROR: status=403'):
            missing_user_message = (
                'message=The operation is not allowed because the requested '
                'people are not part of the domain.')
            if missing_user_message in error_text:
              return None
          raise admin_api_tool_errors.AdminAPIToolPlusDomainsError(
              'User %s not found: %s' % (user_mail, error_text))
        log_utils.LogInfo(
            'Possible quota problem retrieving user %s (%d). Retrying after '
            'a short wait.' % (user_mail, e.resp.status))
        backoff.Fail()

  def IsDomainUser(self, user_mail):
    """Check if domain users exists.

    Args:
      user_mail: user email to check.

    Returns:
      True if user exists else False.
    """
    log_utils.LogDebug('IsDomainuser --plus_domains (%s).' % user_mail)
    return self.GetDomainUser(user_mail) is not None

  def PrintDomainUser(self, user_mail, long_list=False):
    """Print basic details of a domain user.

    Used by a command line utility to possible check if a user exists.
    If used with --long_list, all user details are printed.

    Args:
      user_mail: user email to find.
      long_list: If True, print added user fields.
    """
    user = self.GetDomainUser(user_mail)
    if user:
      self._PrintUserHeader()
      self._PrintOneUser(user=user, long_list=long_list)
    else:
      print 'User %s not found.' % user_mail
