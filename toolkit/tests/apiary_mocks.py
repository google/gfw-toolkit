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

"""Helper mocks for tests.

Common apiary mocks used by tests.
"""

from apiclient.errors import HttpError
from mock import Mock
import test_utils
from test_utils import APIARY_ACCESS_ERROR_CONTENT


TEST_USERS_MANAGER = test_utils.TEST_USERS_MANAGER


class MockExecutableRequestUser(object):
  """Request object that returns a user."""

  def __init__(self, user_key):
    self._user_key = user_key

  def execute(self):  # pylint: disable=g-bad-name
    return TEST_USERS_MANAGER.GetTestUser(self._user_key)


class MockExecutableRequestUserList(object):
  """Request object that returns a user list."""

  def __init__(self, domain, max_results, page_token, query=None):
    self._domain = domain
    self._max_results = max_results
    self._page_token = int(page_token) if page_token is not None else None
    self._query = query

  def execute(self):  # pylint: disable=g-bad-name
    start_index = self._page_token if self._page_token is not None else 0
    return TEST_USERS_MANAGER.GetTestUsers(
        self._domain, max_page=self._max_results, start_index=start_index,
        query=self._query)


class MockExecutableRequestUserInsert(object):
  """Request object that simulates user add/insert."""

  def __init__(self, user_email, first_name, last_name, password):
    self._user_email = user_email
    self._first_name = first_name
    self._last_name = last_name
    self._password = password

  def execute(self):  # pylint: disable=g-bad-name
    response = TEST_USERS_MANAGER.AddTestUser(self._first_name, self._last_name,
                                              self._user_email)
    if response:
      return  HttpError(response, APIARY_ACCESS_ERROR_CONTENT)


class MockExecutableRequestUserDelete(object):
  """Request object that simulates user delete."""

  def __init__(self, user_email):
    self._user_email = user_email

  def execute(self):  # pylint: disable=g-bad-name
    TEST_USERS_MANAGER.DeleteTestUser(self._user_email)


class MockUsersObject(object):
  """Simulates apiary directory 'users' interface."""

  def list(self, domain, maxResults, pageToken,  # pylint: disable=invalid-name
           query=None):  # pylint: disable=g-bad-name,invalid-name
    return MockExecutableRequestUserList(domain, maxResults, pageToken, query)

  def get(self, userKey):  # pylint: disable=g-bad-name
    return MockExecutableRequestUser(userKey)  # pylint: disable=g-bad-name

  def insert(self, body):  # pylint: disable=g-bad-name
    return MockExecutableRequestUserInsert(body['primaryEmail'],
                                           body['name']['givenName'],
                                           body['name']['familyName'],
                                           body['password'])

  def delete(self, userKey):  # pylint: disable=g-bad-name
    return MockExecutableRequestUserDelete(userKey)


class MockDirectoryServiceObject(Mock):
  """Simulates apiary directory service."""

  def users(self):  # pylint: disable=g-bad-name
    return MockUsersObject()
