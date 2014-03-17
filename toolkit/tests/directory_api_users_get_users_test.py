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


class DirectoryApiGetUsersTest(DirectoryApiUsersTestBase):
  """Tests api's used by domain-wide commands (enumerating users)."""

  def setUp(self):
    """Need users to simulate user actions."""
    super(DirectoryApiGetUsersTest, self).setUp()
    self._all_user_count = self.test_users_manager.user_count
    self._all_users = self.test_users_manager.GetTestUsers(
        self.primary_domain, max_page=self._all_user_count).get('users')

  def testCanGetDomainUsersWithOneUserLimit(self):
    self.assertEqual(
        self._api_wrapper.GetDomainUsers(self.primary_domain,
                                         basic=False, max_results=1),
        [self._all_users[0]])

  def testCanGetAllDomainUsersWithDefaults(self):
    self.assertEqual(
        self._api_wrapper.GetDomainUsers(self.primary_domain, basic=False),
        self._all_users)

  def testCanGetAllDomainUsersWithSmallPages(self):
    self.assertEqual(
        self._api_wrapper.GetDomainUsers(self.primary_domain, basic=False,
                                         max_page=self._all_user_count/3),
        self._all_users)

  def testCanGetAllDomainUsersWithLargePages(self):
    self.assertEqual(
        self._api_wrapper.GetDomainUsers(self.primary_domain, basic=False,
                                         max_page=self._all_user_count*2),
        self._all_users)

  def testCanGetAllDomainUsersBoundaryPageSizes(self):
    self.assertEqual(
        self._api_wrapper.GetDomainUsers(self.primary_domain, basic=False,
                                         max_page=self._all_user_count-1),
        self._all_users)
    self.assertEqual(
        self._api_wrapper.GetDomainUsers(self.primary_domain, basic=False,
                                         max_page=self._all_user_count),
        self._all_users)
    self.assertEqual(
        self._api_wrapper.GetDomainUsers(self.primary_domain, basic=False,
                                         max_page=self._all_user_count+1),
        self._all_users)

  def testCanGetSpecifiedCountDomainUsers(self):
    for user_count in [1, 4, 5, 10, 11]:  # There are a total 10 test users.
      self.assertEqual(
          self._api_wrapper.GetDomainUsers(self.primary_domain, basic=False,
                                           max_results=user_count),
          self.test_users_manager.GetTestUsers(self.primary_domain,
                                               max_page=user_count,
                                               basic=False).get('users'))

  def testCanGetDomainUsersWithUnknownDomain(self):
    self.assertEqual(
        self._api_wrapper.GetDomainUsers(self.unknown_domain, basic=False), [])


if __name__ == '__main__':
  unittest.main()
