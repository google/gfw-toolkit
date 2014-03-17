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

"""Test Admin SDK Directory API.

To see even more detail (output) during tests:
  Set _ENABLE_VERBOSE_LOGGING=True
"""

import unittest

# setup_path required to allow imports from component dirs (e.g. utils)
# and lib (where the OAuth and Google API Python Client modules reside).
import setup_path  # pylint: disable=unused-import,g-bad-import-order

from admin_sdk_directory_api import users_api
from apiary_mocks import MockDirectoryServiceObject
from mock import patch
import test_utils
from test_utils import PrintMocker
from utils import log_utils


_ENABLE_VERBOSE_LOGGING = False  # Set to True to see verbose internal logs.


class DirectoryApiUsersTestBase(unittest.TestCase):
  """Wrapper to test the users methods of the Directory Api."""

  primary_domain = 'primarydomain.com'
  unknown_domain = 'unknowndomain.com'
  primary_customer_id = 'Z01abcde9'

  test_users_manager = test_utils.TEST_USERS_MANAGER

  @patch('admin_sdk_directory_api.users_api.build', autospec=True)
  def setUp(self, mock_ApiclientDiscoveryBuildFn):
    """Setup mocks to simulate Apiary users service exported by the Admin SDK.

    The UsersApiWrapper() object contains the users service object so that
    is mocked next to simulate the back-end provider.  Because Apiary is
    dynamic we have to do this through the build() method.

    Args:
      mock_ApiclientDiscoveryBuildFn: mock object to stub the build function.
    """
    log_utils.SetupLogging(verbose_flag=_ENABLE_VERBOSE_LOGGING)
    mock_ApiclientDiscoveryBuildFn.return_value = (
        MockDirectoryServiceObject())
    self._api_wrapper = users_api.UsersApiWrapper(http=None)
    self._new_stdout = PrintMocker.MockStdOut()

  def tearDown(self):
    """Restore stdout to normal."""
    PrintMocker.RestoreStdOut()
