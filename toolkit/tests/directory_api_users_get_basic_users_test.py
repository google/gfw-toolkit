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


class DirectoryApiGetBasicUsersTest(DirectoryApiUsersTestBase):
  """Tests api's used by ls_users.py.

  Test basic user output (basic==tuple vs non-basic=the_whole_dict).
  """

  def setUp(self):
    """Need users to simulate user actions."""
    super(DirectoryApiGetBasicUsersTest, self).setUp()
    self._all_user_count = self.test_users_manager.user_count
    self._all_users_basic = self.test_users_manager.GetTestUsers(
        self.primary_domain, max_page=self._all_user_count, basic=True).get(
            'users')

  def testCanGetBasicDomainUsersWithDefaults(self):
    self.assertEqual(
        self._api_wrapper.GetDomainUsers(self.primary_domain, basic=True),
        self._all_users_basic)

  def testCanGetBasicDomainUsersWithSmallPages(self):
    self.assertEqual(
        self._api_wrapper.GetDomainUsers(self.primary_domain, basic=True,
                                         max_page=self._all_user_count/3),
        self._all_users_basic)

  def testCanGetBasicDomainUsersWithUnknownDomain(self):
    self.assertEqual(
        self._api_wrapper.GetDomainUsers(self.unknown_domain, basic=True), [])


if __name__ == '__main__':
  unittest.main()
