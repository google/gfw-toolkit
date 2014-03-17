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


class DirectoryApiPrintUserStdoutTest(DirectoryApiUsersTestBase):
  """Tests ls_user.py -l."""

  def setUp(self):
    """Need users to simulate user actions."""
    super(DirectoryApiPrintUserStdoutTest, self).setUp()
    self._test_user = 'george@%s' % self.primary_domain
    self._unknown_test_user = 'nogeorge@%s' % self.primary_domain

  def testPrintKnownDomainUserHasExpectedOutput(self):
    self._api_wrapper.PrintDomainUser(self._test_user)
    self.assertEqual(GetExpectedPrintOutput('PrintDomainUser.1'),
                     self._new_stdout.print_messages)

  def testLongPrintKnownDomainUserHasExpectedOutput(self):
    self._api_wrapper.PrintDomainUser(self._test_user, long_list=True)
    self.assertEqual(GetExpectedPrintOutput('PrintDomainUser.2'),
                     self._new_stdout.print_messages)

  def testPrintUnknownDomainUserHasExpectedOutput(self):
    self._api_wrapper.PrintDomainUser(self._unknown_test_user)
    self.assertEqual(GetExpectedPrintOutput('PrintDomainUser.3'),
                     self._new_stdout.print_messages)

  def testLongPrintUnknownDomainUserHasExpectedOutput(self):
    self._api_wrapper.PrintDomainUser(self._unknown_test_user, long_list=True)
    self.assertEqual(GetExpectedPrintOutput('PrintDomainUser.4'),
                     self._new_stdout.print_messages)


if __name__ == '__main__':
  unittest.main()
