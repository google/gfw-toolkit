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


class DirectoryApiGetUserTest(DirectoryApiUsersTestBase):
  """Tests api's used by domain-wide commands (enumerating users)."""

  def setUp(self):
    """Need users to simulate user actions."""
    super(DirectoryApiGetUserTest, self).setUp()
    self._test_user = 'george@%s' % self.primary_domain
    self._unknown_test_user = 'nogeorge@%s' % self.primary_domain

  def testCanGetKnownDomainUser(self):
    self.assertEqual(
        self.test_users_manager.GetTestUser(self._test_user),
        self._api_wrapper.GetDomainUser(self._test_user))

  def testCannotGetDomainUserWithUnknownUser(self):
    self.assertIsNone(
        self._api_wrapper.GetDomainUser(self._unknown_test_user))

  def testIsDomainUserForKnownUser(self):
    self.assertTrue(self._api_wrapper.IsDomainUser(self._test_user))

  def testIsDomainUserForUnknownUser(self):
    self.assertFalse(
        self._api_wrapper.IsDomainUser(self._unknown_test_user))


if __name__ == '__main__':
  unittest.main()
