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

"""Test Admin SDK Directory API."""

import unittest

from directory_api_users_test_base import DirectoryApiUsersTestBase
from utils import admin_api_tool_errors


class DirectoryApiDeleteUserTest(DirectoryApiUsersTestBase):
  """Tests api's used by rm_user.py."""

  def setUp(self):
    """Need users to simulate user actions."""
    super(DirectoryApiDeleteUserTest, self).setUp()
    self._user_email = 'nratchitt@%s' % self.primary_domain
    self._unknown_user_email = 'zzzzz@%s' % self.primary_domain
    self._unknown_user_email = 'nratchitt@%s' % self.unknown_domain
    self._first_name = 'Nurse'
    self._last_name = 'Ratchitt'
    self._password = 'Google123'
    self.test_users_manager.AddTestUser(self._first_name, self._last_name,
                                        self._user_email)

  def tearDown(self):
    """Clean up simulated users."""
    self.test_users_manager.DeleteTestUser(self._user_email)

  def testCanDeleteExistingDomainUser(self):
    self.assertIsNone(
        self._api_wrapper.DeleteDomainUser(self._user_email, verify=True))

  def testDeleteUnknownDomainUserRaises(self):
    self.assertRaises(
        admin_api_tool_errors.AdminAPIToolUserError,
        self._api_wrapper.DeleteDomainUser, self._unknown_user_email,
        verify=True)


if __name__ == '__main__':
  unittest.main()
