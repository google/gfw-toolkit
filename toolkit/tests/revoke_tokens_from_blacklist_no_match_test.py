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

"""Test revoke_unapproved_tokens command - uses the Admin SDK token API."""

import unittest

from mock import patch

import revoke_tokens_command_test_base as test_base


@patch('utils.token_report_utils.GetTokenStats')
@patch('utils.token_revoker.TokenRevoker._RevokeToken')
@patch('utils.log_utils.LogInfo')
class RevokeUnapprovedTokensCommandTestBlacklistNoMatchTests(
    test_base.RevokeUnapprovedTokensCommandTestBase):
  """Test revoke_unapproved_tokens.py with black lists."""

  def testRevokeUnapprovedTokensWithOneElementDomainBlacklistNoMatch(
      self, mock_loginfo_fn,  # pylint: disable=unused-argument
      mock_revoketoken_fn, mock_readtokensjson_fn):
    mock_readtokensjson_fn.return_value = self._parsed_tokens
    self._token_revoker._client_blacklist_set = set(['notwitter.com'])
    self._token_revoker.RevokeUnapprovedTokens()
    self.assertFalse(mock_revoketoken_fn.called)

  def testRevokeUnapprovedTokensWithMultiElementDomainBlacklistNoMatch(
      self, mock_loginfo_fn,  # pylint: disable=unused-argument
      mock_revoketoken_fn, mock_readtokensjson_fn):
    mock_readtokensjson_fn.return_value = self._parsed_tokens
    self._token_revoker._client_blacklist_set = set(['notwitter.com',
                                                     'nomadeuptest1.com'])
    self._token_revoker.RevokeUnapprovedTokens()
    self.assertFalse(mock_revoketoken_fn.called)

  def testRevokeUnapprovedTokensWithOneElementScopeBlacklistNoMatch(
      self, mock_loginfo_fn,  # pylint: disable=unused-argument
      mock_revoketoken_fn, mock_readtokensjson_fn):
    mock_readtokensjson_fn.return_value = self._parsed_tokens
    self._token_revoker._scope_blacklist_set = set([
        'https://www.googleapis.com/auth/appengine.admin'])
    self._token_revoker.RevokeUnapprovedTokens()
    self.assertFalse(mock_revoketoken_fn.called)

  def testRevokeUnapprovedTokensWithMultiElementScopeBlacklistNoMatch(
      self, mock_loginfo_fn,  # pylint: disable=unused-argument
      mock_revoketoken_fn, mock_readtokensjson_fn):
    mock_readtokensjson_fn.return_value = self._parsed_tokens
    self._token_revoker._scope_blacklist_set = set([
        'https://www.googleapis.com/auth/appengine.admin',
        'https://www.googleapis.com/auth/appengine.pretend.admin'])
    self._token_revoker.RevokeUnapprovedTokens()
    self.assertFalse(mock_revoketoken_fn.called)


if __name__ == '__main__':
  unittest.main()
