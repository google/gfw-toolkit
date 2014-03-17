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

"""Test revoke_unapproved_tokens command - uses the Admin SDK token API.

To see even more detail (output) during tests:
  Set _ENABLE_VERBOSE_LOGGING=True
"""

import argparse
import unittest

# setup_path required to allow imports from component dirs (e.g. utils)
# and lib (where the OAuth and Google API Python Client modules reside).
import setup_path  # pylint: disable=unused-import,g-bad-import-order

from apiary_mocks import MockDirectoryServiceObject
from mock import patch
from test_utils import LoadTestJsonFile
from utils import log_utils
from utils.token_revoker import TokenRevoker


_ENABLE_VERBOSE_LOGGING = False  # Set to True to see verbose internal logs.

_TEST_DOMAIN = 'primarydomain.com'
_PARSED_TOKEN_FILE_NAME = '%s_parsed_tokendata.json' % _TEST_DOMAIN


def _SetupMockArgParseFlags():
  """Mock a flag used in TokenRevoker(). Hides printed output.

  Returns:
    argparse flags object.
  """
  arg_parser = argparse.ArgumentParser()
  arg_parser.add_argument('--hide_timing', action='store_true', default=True,
                          help=('Stop logging the elapsed time of longer '
                                'functions.'))
  return arg_parser.parse_args([])


class RevokeUnapprovedTokensCommandTestBase(unittest.TestCase):
  """Base class for token printing test classes."""

  @patch('admin_sdk_directory_api.tokens_api.build', autospec=True)
  @patch('utils.auth_helper.GetAuthorizedHttp')
  def setUp(self, mock_GetAuthorizedHttp_Fn, mock_ApiclientDiscoveryBuildFn):
    """Setup mocks to simulate Apiary token returns from Apps Security.

    We avoid mocking details because we wrapped the Apiary services in an
    api layer that can be mocked easily.

    We patch the LogInfo method because that inhibits log output messages
    from emitting during tests that confuse interactive test users.

    Args:
      mock_GetAuthorizedHttp_Fn: mock object to avoid getting auth flow.
      mock_ApiclientDiscoveryBuildFn: mock object to stub the build function.
    """
    log_utils.SetupLogging(verbose_flag=_ENABLE_VERBOSE_LOGGING)
    mock_GetAuthorizedHttp_Fn.return_value = None
    mock_ApiclientDiscoveryBuildFn.return_value = (
        MockDirectoryServiceObject())
    self._token_revoker = TokenRevoker(_SetupMockArgParseFlags())
    self._parsed_tokens = LoadTestJsonFile(_PARSED_TOKEN_FILE_NAME)
