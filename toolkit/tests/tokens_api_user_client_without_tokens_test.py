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


_USER_ID = '0'  # Stub user_id.


# PyLint dislikes the method names Python unittest prefers (testXXX).
# pylint: disable=g-bad-name


@patch('admin_sdk_directory_api.tokens_api.TokensApiWrapper.GetToken')
class TokensApiPrintTokensForUserAndClientIdWithoutTokensTest(
    TokensApiPrintTokensTestBase):
  """Wrapper to test token print code with both user and client_id supplied."""

  def setUp(self):
    """Setup token return data for these tests."""
    super(TokensApiPrintTokensForUserAndClientIdWithoutTokensTest,
          self).setUp()
    self._client_id = 'twitter.com'
    # Token data captured from:
    # ./cmds/ls_tokens_for_user_clientid.py -u usertest1@altostrat.com \
    #                                       -i twitter.com
    self.returned_token_doc = {}

  def testPrintNoTokensFoundMessageForBasicUserAndClientIdWithoutTokens(
      self, mock_get_token_request_fn):
    mock_get_token_request_fn.return_value = self.returned_token_doc
    self._tokens_api.PrintTokenForUserClientId(_USER_ID, self._client_id,
                                               long_list=False)
    self.assertEqual(GetExpectedPrintOutput('PrintTokenForUserClientId.3'),
                     self._new_stdout.print_messages)

  def testPrintNoTokensFoundMessageForLongUserAndClientIdWithoutTokens(
      self, mock_get_token_request_fn):
    mock_get_token_request_fn.return_value = self.returned_token_doc
    self._tokens_api.PrintTokenForUserClientId(_USER_ID, self._client_id,
                                               long_list=True)
    self.assertEqual(GetExpectedPrintOutput('PrintTokenForUserClientId.4'),
                     self._new_stdout.print_messages)


@patch('admin_sdk_directory_api.tokens_api.TokensApiWrapper.ListTokens')
class TokensApiPrintTokensForUserWithoutTokensTest(
    TokensApiPrintTokensTestBase):
  """Wrapper to test token print code with just user supplied."""

  def setUp(self):
    """Setup token return data for these tests."""
    super(TokensApiPrintTokensForUserWithoutTokensTest, self).setUp()
    self.returned_token_doc = {u'items': []}

  def testPrintNoTokensFoundMessageForBasicUserWithoutTokens(
      self, mock_list_tokens_request_fn):
    mock_list_tokens_request_fn.return_value = self.returned_token_doc
    self._tokens_api.PrintTokensForUser(_USER_ID, long_list=False)
    self.assertEqual(GetExpectedPrintOutput('PrintTokensForUser.3'),
                     self._new_stdout.print_messages)

  def testPrintNoTokensFoundMessageForLongUserWithoutTokens(
      self, mock_list_tokens_request_fn):
    mock_list_tokens_request_fn.return_value = self.returned_token_doc
    self._tokens_api.PrintTokensForUser(_USER_ID, long_list=True)
    self.assertEqual(GetExpectedPrintOutput('PrintTokensForUser.3'),
                     self._new_stdout.print_messages)


if __name__ == '__main__':
  unittest.main()
