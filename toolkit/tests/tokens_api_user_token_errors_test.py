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

"""Test apps security token API."""

import unittest

from mock import patch
from test_utils import GetExpectedPrintOutput
from tokens_api_test_base import TokensApiPrintTokensTestBase
from utils.admin_api_tool_errors import AdminAPIToolTokenRequestError


_USER_ID = '0'  # Stub user_id.


# PyLint dislikes the method names Python unittest prefers (testXXX).
# pylint: disable=g-bad-name


@patch('admin_sdk_directory_api.tokens_api.TokensApiWrapper.ListTokens')
class TokensApiPrintTokensForUserWithTokenErrorTest(
    TokensApiPrintTokensTestBase):
  """Wrapper to test token print code with just user supplied."""

  def testPrintTokensForUserWithTokenDocEmptyRaisesError(
      self, mock_list_tokens_request_fn):
    mock_list_tokens_request_fn.return_value = {}
    self.assertRaises(
        AdminAPIToolTokenRequestError,
        self._tokens_api.PrintTokensForUser, _USER_ID, long_list=False)

  def testPrintNoTokensFoundMessageForWhenTokenDocNoItemsError(
      self, mock_list_tokens_request_fn):
    mock_list_tokens_request_fn.return_value = {'unexpected': 'notempty'}
    self._tokens_api.PrintTokensForUser(_USER_ID, long_list=True)
    self.assertEqual(GetExpectedPrintOutput('PrintTokensForUser.3'),
                     self._new_stdout.print_messages)


if __name__ == '__main__':
  unittest.main()
