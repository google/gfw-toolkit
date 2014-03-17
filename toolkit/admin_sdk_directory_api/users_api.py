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
import time

from apiclient import errors as apiclient_errors
from apiclient.discovery import build
from utils import admin_api_tool_errors
from utils import http_utils
from utils import log_utils


_MISSING_FIELD_STUB = '%s field not found in user data.'


def GetFieldFromUser(user, field_name, sub_field_name=None):
  """Safely retrieves a field from a user dictionary object.

  Some User fields are expressed as dictionaries of sub-fields instead of as
  simple values. This method allows retrieval of both field values and
  sub_field values.  In the following sample User record:

    fields: customerId, isAdmin, kind, name
    sub_fields: fullName, givenName, familyName

    {customerId: A03abcde4
     isAdmin: True
     kind: directory#user
     name: {u'fullName': u'George Enlighten', u'givenName': u'George',
            u'familyName': u'Enlighten'}
    }

  Args:
    user: A user object returned from an Apiary service.
    field_name: String field name for an element in a dictionary.
    sub_field_name: Sometimes retrieve a field from an embedded dictionary.

  Returns:
    If the field is present, returns the field contents.
    Otherwise returns template text to warn the user
    that data fields have changed.
  """
  if field_name not in user:
    return _MISSING_FIELD_STUB % field_name
  field_value = user.get(field_name)
  if sub_field_name:
    if not field_value or sub_field_name not in field_value:
      return _MISSING_FIELD_STUB % ('[%s][%s]' % (field_name, sub_field_name))
    return field_value.get(sub_field_name)
  return field_value


class UsersApiWrapper(object):
  """Demonstrates a few needed functions of user provisioning."""

  def __init__(self, http):
    """Create our service object with access to Admin SDK APIs.

    Args:
      http: An authorized http interface object.
    """
    self._service = build(serviceName='admin', version='directory_v1',
                          http=http)
    self._users = self._service.users()

  @staticmethod
  def _ShowAllUserFields(user):
    """Show all fields [this can be many] of user data.

    Available fields include (use ls_user -u xxx@mybiz.com -l to see real data):
      agreedToTerms, changePasswordAtNextLogin, creationTime, customerId,
      emails, id, includeInGlobalAddressList, ipWhitelisted, isAdmin,
      isDelegatedAdmin, isMailboxSetup, kind, lastLoginTime,
      name ({'familyName': 'xx', 'fullName': 'yy', 'givenName': 'zz'}),
      nonEditableAliases, orgUnitPath, primaryEmail and suspended.

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
      Tuple reflecting the user: (email, user_id, full_name).
    """
    return (GetFieldFromUser(user, 'primaryEmail'),
            GetFieldFromUser(user, 'id'),
            GetFieldFromUser(user, 'name', sub_field_name='fullName'))

  @staticmethod
  def _ProcessCustomerId(user):
    """Select 'customerId from returned user json.

    Args:
      user: user json object returned from the users API list().

    Returns:
      String user_id for the supplied user.
    """
    return GetFieldFromUser(user, 'customerId')

  @staticmethod
  def _PrintCustomerId(user):
    """Get commonly needed CustomerId from the domain name.

    Args:
      user: user json object returned from the users API list().
    """
    print 'CustomerId for %s:' % GetFieldFromUser(user, 'primaryEmail').split(
        '@')[1]
    print GetFieldFromUser(user, 'customerId')

  @staticmethod
  def _PrintOneLine(email, user_id, full_name):
    """Formats a user print line a little like ls -l.

    Example output:

    Users from domain altostrat.com:
    ID                     Email                                 Full Name
    000000558298938768732  george@altostrat.com                  George Lasta
    000000858699628788601  superadmin@altostrat.com              Super Lastb

    Args:
      email: User email (e.g. myemail@mydomain.com).
      user_id: 21 digit domain id.
      full_name: first and last name.
    """
    # Left justify all but the last as string fields.
    print '%-22s %-40s %s' % (user_id, email, full_name)

  @staticmethod
  def _PrintUserHeader():
    """Print user header for ls_users and ls_user."""
    UsersApiWrapper._PrintOneLine('Email', 'ID', 'Full Name')

  @staticmethod
  def _PrintOneUser(user, long_list=False):
    """Prints select fields from returned user json.

    Available fields include:
      agreedToTerms, changePasswordAtNextLogin, creationTime, customerId,
      emails, id, includeInGlobalAddressList, ipWhitelisted, isAdmin,
      isDelegatedAdmin, isMailboxSetup, kind, lastLoginTime,
      name ({'familyName': 'xx', 'fullName': 'yy', 'givenName': 'zz'}),
      nonEditableAliases, orgUnitPath, primaryEmail and suspended.
    Special handling is needed for:
      emails, name, nonEditableAliases, name: sort for deterministic output.

    Args:
      user: user json object returned from the users API list().
      long_list: if True, print all known user fields.
    """
    UsersApiWrapper._PrintOneLine(GetFieldFromUser(user, 'primaryEmail'),
                                  GetFieldFromUser(user, 'id'),
                                  GetFieldFromUser(user, 'name',
                                                   sub_field_name='fullName'))
    if long_list:
      for field in sorted(user.keys()):
        if field in ('primaryEmail', 'id', 'fullName'):  # already displayed.
          continue
        # For deterministic output, need to pprint container objects like
        # dict. Textwrap is used for the hanging indent.  We use a hanging
        # indent of 7 because 4 spaces is the normal margin and the extra
        # 3 spaces are used for: colon, space and opening brace.
        formatted_text = textwrap.fill(
            pprint.pformat(GetFieldFromUser(user, field)),
            subsequent_indent=(7+len(field)) * ' ', break_on_hyphens=False)
        print '    %s: %s' % (field, formatted_text)

  def _ProcessUserListPage(self, apps_domain, max_page, next_page_token=None,
                           query_filter=None):
    """Helper that handles exceptions retrieving pages of users.

    Args:
      apps_domain: Users apps domain e.g. mybiz.com.
      max_page: Used to optimize paging (1-500).
      next_page_token: Used for ongoing paging of users.
      query_filter: Optinally allow filtering based on many fields.
                    Obvious ones include orgName and orgUnitPath.

    Returns:
      List of users retrieved (one page).
    """
    request = self._users.list(domain=apps_domain, maxResults=max_page,
                               pageToken=next_page_token,
                               query=query_filter)
    backoff = http_utils.Backoff()
    while backoff.Loop():
      try:
        users_list = request.execute()
        return users_list
      except apiclient_errors.HttpError as e:
        if e.resp.status not in http_utils.RETRY_RESPONSE_CODES:
          raise admin_api_tool_errors.AdminAPIToolUserError(
              '%s\nPlease check your domain spelling (%s).' % (
                  http_utils.ParseHttpResult(e.uri, e.resp, e.content),
                  apps_domain))
        log_utils.LogInfo(
            'Possible quota problem retrieving users (%d).' % e.resp.status)
        backoff.Fail()

  def _ProcessDomainUsers(self, apps_domain, process_fn, max_results=None,
                          max_page=100, query_filter=None):
    """Helper to allow multiple, different print functions.

    Args:
      apps_domain: Users apps domain e.g. mybiz.com.
      process_fn: Function to be used against each user object (e.g. print).
      max_results: If not None, stop after this many users.
      max_page: Used to optimize paging (1-500).
      query_filter: Optinally allow filtering based on many fields.
                    Obvious ones include orgName and orgUnitPath.

    Returns:
      Tuple of (result list, count of users retrieved). The result list is
      populated using results from process_fn().
    """
    results = []
    retrieved_count = 0
    next_page_token = None

    if max_page < 1 or max_page > 500:
      max_page = 100  # API default.
    if max_results is not None and max_results < max_page:
      max_page = max_results

    users_list = self._ProcessUserListPage(apps_domain=apps_domain,
                                           max_page=max_page,
                                           query_filter=query_filter)
    while True:
      for user in users_list.get('users', []):
        result = process_fn(user)
        if result:
          results.append(result)
        retrieved_count += 1
        if max_results is not None and retrieved_count >= max_results:
          return results, retrieved_count
      next_page_token = users_list.get('nextPageToken')
      if not next_page_token:
        return results, retrieved_count
      users_list = self._ProcessUserListPage(apps_domain=apps_domain,
                                             max_page=max_page,
                                             query_filter=query_filter,
                                             next_page_token=next_page_token)

  def GetCustomerId(self, apps_domain):
    """Look up the customer_id for a specific apps_domain.

    Other APIs use customer_id as the key to domain-specific
    requests.

    Args:
      apps_domain: Users apps domain e.g. mybiz.com.

    Returns:
      The single customer_id as a string.
    """
    results, _ = self._ProcessDomainUsers(apps_domain=apps_domain,
                                          process_fn=self._ProcessCustomerId,
                                          max_results=1)
    if results:
      return results[0]
    return None  # Only occurs if an authenticated domain has no users.

  def PrintCustomerId(self, apps_domain):
    """Simple lookup of the customerId from the first user.

    Args:
      apps_domain: Users apps domain e.g. mybiz.com.
    """
    self._ProcessDomainUsers(apps_domain=apps_domain,
                             process_fn=self._PrintCustomerId,
                             max_results=1)

  def GetDomainUsers(self, apps_domain, basic=True, max_results=None,
                     max_page=500, query_filter=None):
    """List user details into a data structure.

    Used to serialize a large list of users to a (json) file.

    Args:
      apps_domain: Users apps domain e.g. mybiz.com.
      basic: If True, return a 3-tuple of (email, user_id, full_name) for
             each user, else return the whole user dictionary for each.
      max_results: If not None, stop after this many users.
      max_page: Used to optimize paging (1-500).
      query_filter: Optinally allow filtering based on many fields.
                    Obvious ones include orgName and orgUnitPath.

    Returns:
      List of tuples of user details [(email, id, full_name)...]
    """
    log_utils.LogDebug('GetDomainUsers (%s).' % max_results)
    if basic:
      user_attribute_filter_fn = self._ShowBasicUserFields
    else:
      user_attribute_filter_fn = self._ShowAllUserFields
    results, _ = self._ProcessDomainUsers(apps_domain=apps_domain,
                                          max_results=max_results,
                                          max_page=max_page,
                                          query_filter=query_filter,
                                          process_fn=user_attribute_filter_fn)
    return results

  def PrintDomainUsers(self, apps_domain, max_results=None, max_page=500):
    """Powerful demonstration of ease of user provisioning API.

    If the customer is interested in multiple domains, this might
    be rewritten to use customer=customer_id instead of domain=xxx.

    Args:
      apps_domain: Users apps domain e.g. mybiz.com.
      max_results: If not None, stop after this many users.
      max_page: Used to optimize paging (1-500).
    """
    print 'Users from domain %s:' % apps_domain
    self._PrintUserHeader()
    _, count = self._ProcessDomainUsers(apps_domain=apps_domain,
                                        process_fn=self._PrintOneUser,
                                        max_results=max_results,
                                        max_page=max_page)
    print '%d users found.' % count

  def GetDomainUser(self, user_mail):
    """Retrieve document for a user in an apps domain.

    A common reason to call this is to retrieve the user_id from an email name.

    Args:
      user_mail: username to check.

    Returns:
      The user document (available fields listed in _PrintOneUser()).
    """
    log_utils.LogDebug('GetDomainUser (%s).' % user_mail)
    request = self._users.get(userKey=user_mail)
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
          raise admin_api_tool_errors.AdminAPIToolUserError(
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
    log_utils.LogDebug('IsDomainuser (%s).' % user_mail)
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

  def AddDomainUser(self, first_name, last_name, user_mail, new_password,
                    verify=False):
    """Adds user to the domain.

    Checks if the user already exists.  Users are created by default
    as unsuspended, non-admin users.

    Args:
      first_name: Given first name.
      last_name: Family name.
      user_mail: user_mail to add.
      new_password: Password to set.
      verify: If True, verify user was created.
    """
    log_utils.LogDebug('AddDomainUser (%s).' % user_mail)
    if self.IsDomainUser(user_mail):
      raise admin_api_tool_errors.AdminAPIToolUserError(
          'User %s already exists.' % user_mail)
    body = {
        'primaryEmail': user_mail,
        'name': {'givenName': first_name, 'familyName': last_name},
        'password': new_password
        }
    backoff = http_utils.Backoff()
    while backoff.Loop():
      try:
        self._users.insert(body=body).execute()
        if verify:
          time.sleep(2)  # Seems to be needed for Verify to work consistently.
          if not self.IsDomainUser(user_mail):
            raise admin_api_tool_errors.AdminAPIToolUserError(
                'Problem creating user: %s' % user_mail)
        return
      except apiclient_errors.HttpError as e:
        if e.resp.status not in http_utils.RETRY_RESPONSE_CODES:
          raise admin_api_tool_errors.AdminAPIToolUserError(
              http_utils.ParseHttpResult(e.uri, e.resp, e.content))
        log_utils.LogInfo(
            'Possible quota problem adding user %s (%d). Retrying after '
            'a short wait.' % (user_mail, e.resp.status))
        backoff.Fail()

  def DeleteDomainUser(self, user_mail, verify=False):
    """Deletes user from the domain.

    Checks if the user already exists before attempting delete.

    Args:
      user_mail: user_mail to add.
      verify: If True, verify user was deleted.

    Raises:
      AdminAPIToolUserError: Unable to delete user.
    """
    log_utils.LogDebug('DeleteDomainUser (%s).' % user_mail)
    if not self.IsDomainUser(user_mail):
      raise admin_api_tool_errors.AdminAPIToolUserError(
          'ERROR: user (%s) not a domain member. You may need to check "Enable '
          'provisioning API" in your Domain Settings->User Settings.' % (
              user_mail))
    backoff = http_utils.Backoff()
    while backoff.Loop():
      try:
        self._users.delete(userKey=user_mail).execute()
        if verify:
          time.sleep(2)  # Seems to be needed for Verify to work consistently.
          if self.IsDomainUser(user_mail):
            raise admin_api_tool_errors.AdminAPIToolUserError(
                'Problem deleting user %s.' % user_mail)
        return
      except apiclient_errors.HttpError as e:
        if e.resp.status not in http_utils.RETRY_RESPONSE_CODES:
          raise admin_api_tool_errors.AdminAPIToolUserError(
              http_utils.ParseHttpResult(e.uri, e.resp, e.content))
        log_utils.LogInfo(
            'Possible quota problem deleting user %s (%d). Retrying after '
            'a short wait.' % (user_mail, e.resp.status))
        backoff.Fail()
