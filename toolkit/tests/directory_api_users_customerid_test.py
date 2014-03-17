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
from test_utils import GetExpectedPrintOutput


class DirectoryApiUsersCustomerIdTest(DirectoryApiUsersTestBase):
  """Tests api's used by ls_customer_id.py."""

  def testCanGetCustomerIdWithValidDomain(self):
    self.assertEqual(
        self.primary_customer_id,
        self._api_wrapper.GetCustomerId(self.primary_domain))

  def testCustomerIdWithUnknownDomainIsNone(self):
    self.assertIsNone(self._api_wrapper.GetCustomerId(self.unknown_domain))


class DirectoryApiPrintUsersCustomerIdStdoutTest(DirectoryApiUsersTestBase):
  """Tests api's used by ls_customer_id.py."""

  def testPrintCustomerIdWithValidDomainHasExpectedOutput(self):
    self._api_wrapper.PrintCustomerId(self.primary_domain)
    self.assertEqual(GetExpectedPrintOutput('PrintCustomerId.1'),
                     self._new_stdout.print_messages)


if __name__ == '__main__':
  unittest.main()
