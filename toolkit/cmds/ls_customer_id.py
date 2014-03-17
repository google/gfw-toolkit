#!/usr/bin/python
#
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

"""Show the customer_id of an Apps Domain.

Tool to show usage of Admin SDK Directory APIs.

APIs Used:
  Admin SDK Directory API: user management
"""

import sys

# setup_path required to allow imports from component dirs (e.g. utils)
# and lib (where the OAuth and Google API Python Client modules reside).
import setup_path  # pylint: disable=unused-import,g-bad-import-order

from admin_sdk_directory_api import users_api
from utils import admin_api_tool_errors
from utils import auth_helper
from utils import common_flags
from utils import log_utils


def AddFlags(arg_parser):
  """Handle command line flags unique to this script.

  Args:
    arg_parser: object from argparse.ArgumentParser() to accumulate flags.
  """
  common_flags.DefineAppsDomainFlagWithDefault(arg_parser)
  common_flags.DefineVerboseFlagWithDefaultFalse(arg_parser)


def main(argv):
  """Retrieve and print the customer_id for a given apps domain."""
  flags = common_flags.ParseFlags(argv, 'List the Google Apps Customer ID.',
                                  AddFlags)
  http = auth_helper.GetAuthorizedHttp(flags)
  api_wrapper = users_api.UsersApiWrapper(http)
  try:
    api_wrapper.PrintCustomerId(flags.apps_domain)
  except admin_api_tool_errors.AdminAPIToolUserError as e:
    log_utils.LogError('Unable to enumerate one user.', e)
    sys.exit(1)


if __name__ == '__main__':
  main(sys.argv[1:])
