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

"""Helper methods for tests.

A common issue in testing is retrieving a list of domain users for mocking
back-end services that retrieve users and for verifying that user metadata
is filtered properly.  These functions are used in a few different test
modules.
"""

import json
import operator
import os
import sys

# setup_path required to allow imports from component dirs (e.g. utils)
# and lib (where the OAuth and Google API Python Client modules reside).
import setup_path  # pylint: disable=unused-import,g-bad-import-order


# To gather the user data, insert below debug code in
# users_api.py in the _ProcessUserListPage() method. The data
# retrieved comes from the request.execute() method where the request is
# retrieved by the users.list() invocation.  The responses are 'pages' of
# (upto 500) users with the form:
#
# {u'nextPageToken': u'areallylongstring',
#  u'kind': u'admin#directory#users',
#  u'users': [{}, {}, a list of dictionaries - one for each user]}
#
#        # Test code to collect users from _ProcessUserListPage().
#        # Insert after 'request.execute()' but before 'return users_list'.
#
#        import json
#        import os
#        print '>>>>>%s, %s, %s.' % (apps_domain, max_page, next_page_token)
#        temp_data_file = '/tmp/users_output.json'
#        debug_users_list = []
#        if os.path.isfile(temp_data_file):
#          with open(temp_data_file, 'r') as f:
#            debug_users_list = json.load(f)  # Load existing pages.
#        for user in users_list.get('users', []):
#          debug_users_list.append(user)  # Build the full users list.
#        with open(temp_data_file, 'w') as f:
#          json.dump(debug_users_list, f)  # Dump list as json.
#        # end test code


# Vanilla user template - used for adding new users.
USER_TEMPLATE = {
    'agreedToTerms': True,
    'kind': 'admin#directory#user',
    'name': {
        'fullName': 'FIRST_NAME LAST_NAME',
        'givenName': 'FIRST_NAME',
        'familyName': 'LAST_NAME'
    },
    'nonEditableAliases': [
        'USER_EMAIL@primarydomain.com.test-google-a.com'
    ],
    'ipWhitelisted': False,
    'creationTime': '2013-04-12T21:20:50.000Z',
    'primaryEmail': 'USER_EMAIL@primarydomain.com',
    'changePasswordAtNextLogin': False,
    'isDelegatedAdmin': False,
    'isMailboxSetup': True,
    'isAdmin': False,
    'includeInGlobalAddressList': True,
    'suspended': False,
    'id': '112351558298938768732',
    'lastLoginTime': '2013-08-16T22:01:03.000Z',
    'customerId': 'Z01abcde9',
    'emails': [
        {
            'primary': True,
            'address': 'USER_EMAIL@primarydomain.com'
        },
        {
            'address': 'USER_EMAIL@primarydomain.com.test-google-a.com'
        }
    ],
    'orgUnitPath': '/'
}

# To raise an error as an Apiary Service, the response object would be as
# follows.  The ... is a very large Java call stack.
APIARY_ACCESS_ERROR_CONTENT = """
 "error": {
  "errors": [
   {
    "domain": "global",
    "reason": "forbidden",
    "message": "Not Authorized to access this resource/api",
    "debugInfo": "Not Authorized to access this resource/api ...\n"
   }
  ],
  "code": 403,
  "message": "Not Authorized to access this resource/api"
 }
}"""


class MockErrorResponse(object):
  """Mock response object for including in raised errors."""

  def __init__(self, status, uri):
    self.status = status
    self.uri = uri


def LoadTestJsonFile(json_file_name):
  """Helper to read json files.

  Args:
    json_file_name: Name of a file that exists in the testdata directory.
                    The path will be pre-pended (e.g. my_users.json).
  Returns:
    The object json deserialized.

  Raises:
    IOError: if the file cannot be located or laoded.
    ValueError: if the JSON is improperly formed.
  """
  json_file_path = os.path.join(setup_path.APP_BASE_PATH, 'tests', 'testdata',
                                json_file_name)
  with open(json_file_path, 'r') as f:
    return json.load(f)


class TestUsersManager(object):
  """Helper class to efficiently load list of users and then support paging."""

  def __init__(self, primary_domain):
    self.primary_domain = primary_domain
    self.all_test_users = LoadTestJsonFile('%s_users.json' % primary_domain)
    self.all_test_users = sorted(self.all_test_users,
                                 key=operator.itemgetter('primaryEmail'))

  @property
  def user_count(self):
    return len(self.all_test_users)

  def _FilterTestUsers(self, query, user_list):
    """Filters a subset of the user list.

    Args:
      query: A String filter query. e.g. 'email:u*'.
      user_list: A list of dictionaries of users.

    Returns:
      List of all found test users or an empty list.
    """
    filter_key, filter_value = query.split(':')
    key_translations = {'email': 'primaryEmail'}
    if filter_key in key_translations:
      filter_key = key_translations[filter_key]
    filter_value = filter_value.rstrip('*')
    return [u for u in user_list if u.get(filter_key).startswith(filter_value)]

  def _GetAllTestUsers(self, apps_domain):
    """Load all the test users once for the whole test.

    Allows safe access to test data.

    Args:
      apps_domain: Used to verify supplied domain matches test data apps domain.

    Returns:
      List of all found test users or an empty list.
    """
    if apps_domain == self.primary_domain:
      return self.all_test_users
    return []

  def AddTestUser(self, first_name, last_name, user_email):
    """For simulating adding users that can be queried and deleted.

    Args:
      first_name: String with the users first name.
      last_name: String with the users last name.
      user_email: String with the users email (key).

    Returns:
      user_email if the user already exists, else None.
    """
    stub_email = 'USER_EMAIL@primarydomain.com'
    _, user_email_domain = user_email.split('@')
    if user_email_domain != 'primarydomain.com':
      url = ('https://www.googleapis.com/admin/directory/v1/users/%s'
             '?alt=json.' % user_email)
      return MockErrorResponse(403, url)
    new_user = USER_TEMPLATE.copy()
    new_user['name']['fullName'] = '%s %s' % (first_name, last_name)
    new_user['name']['givenName'] = first_name
    new_user['name']['familyName'] = last_name
    new_user['nonEditableAliases'][0].replace(stub_email, user_email)
    new_user['primaryEmail'] = user_email
    for email_entry in new_user['emails']:
      email_entry['address'] = email_entry['address'].replace(stub_email,
                                                              user_email)
    self.all_test_users.append(new_user)
    return None

  def DeleteTestUser(self, user_email):
    """For simulating deleting users that can be queried."""
    candidate = -1
    for user_index in range(self.user_count):
      user = self.all_test_users[user_index]
      if user['primaryEmail'] == user_email:
        candidate = user_index
        break
    if candidate == -1:
      print 'UNABLE to locate test user: %s to delete.' % user_email
    else:
      del self.all_test_users[candidate]

  def _MakeBasicUser(self, user):
    """Helper function to translate a full user dict to a basic tuple.

    This is used to lighten up on carrying around the full user metadata when
    all that is frequently desired is the users: email, id and name.

    Args:
      user: Full dictionary of a single user's metadata from Admin SDK.

    Returns:
      Tuple of user attributes: (primaryEmail, id, fullName).
    """
    return user['primaryEmail'], user['id'], user['name']['fullName']

  def GetTestUsers(self, apps_domain, max_page=500, start_index=0,
                   query=None, basic=False):
    """Helper to retrieve the test data from a very large json data file.

    This is how we simulate paging users similar to the service.  This
    retrieves one page of data just like the service interface does.

    Args:
      apps_domain: String domain expected.
      max_page: Number that sets the page size; the way existing list() works.
      start_index: Used for paging when start_index > 0.
      query: A String filter query. e.g. 'email:u*'.
      basic: Matches 'basic' arg in api - produces basic tuples not full dict.

    Returns:
      A list of user dictionaries.
    """
    test_users = self._GetAllTestUsers(apps_domain)
    if query:
      test_users = self._FilterTestUsers(query, test_users)
    test_user_count = len(test_users)
    if test_users or start_index < test_user_count:
      test_users_page = test_users[start_index:(start_index+max_page)]
      if basic:
        test_users_page = [self._MakeBasicUser(u) for u in test_users_page]
      next_page_token = start_index + min(max_page, len(test_users_page))
      if next_page_token >= test_user_count:
        next_page_token = None  # Terminal condition when we hit end of list.
      return {u'nextPageToken': next_page_token,
              u'kind': u'admin#directory#users', u'users': test_users_page}
    else:
      return {u'nextPageToken': None,
              u'kind': u'admin#directory#users', u'users': []}

  def GetTestUser(self, user_key):
    """Helper to retrieve a specific test user.

    Args:
      user_key: the email address of the user to retrieve.

    Returns:
      A dictionary of data for the specified user.
    """
    apps_domain = user_key.split('@')[1]
    for user in self._GetAllTestUsers(apps_domain):
      if user.get('primaryEmail') == user_key:
        return user
    return None


# Singleton users manager for multiple modules.
TEST_USERS_MANAGER = TestUsersManager('primarydomain.com')


def GetExpectedPrintOutput(test_key):
  """Helper to retrieve expected print output for unit tests that print.

  Args:
    test_key: A unique key identifying the test output that is requested.

  Returns:
    A string (with newlines) that reflects the expected print output.
  """
  return LoadTestJsonFile(
      'primarydomain.com_expected_print_output.json')[test_key]


class PrintMocker(object):
  """Class to mock/stub out stdout - allowing print output to be compared."""

  old_stdout = None  # Stash stdout and restore it after test.

  def __init__(self):
    self._print_messages = []  # Stack up output messages here.

  @property
  def print_messages(self):
    """Allow tests to retrieve the messages for comparisions."""
    return ''.join(self._print_messages)

  def ClearMessages(self):
    """Reset the message buffer between tests."""
    self._print_messages = []

  def flush(self):  # pylint: disable=g-bad-name
    """This method required to fully mock stdout."""
    pass

  def write(self, message):  # pylint: disable=g-bad-name
    """The is the required method used by print()."""
    self._print_messages.append(message)

  @staticmethod
  def MockStdOut():
    """Helper to make mocking print output (stdout) easy. Initializes stdout.

    Expected code sequence:

    new_stdout = PrintMocker.MockStdOut()
    ...test code...
    assertEqual(test_utils.GetExpectedPrintOuput(...),
                new_stdout.print_messages)
    PrintMocker.RestoreStdOut()

    Returns:
      The new stdout so that it's message buffer may be checked.
    """
    PrintMocker.old_stdout = sys.stdout
    new_stdout = PrintMocker()
    sys.stdout = new_stdout
    return new_stdout

  @staticmethod
  def RestoreStdOut():
    """Helper to make mocking print output (stdout) easy. Restores stdout."""
    sys.stdout = PrintMocker.old_stdout
