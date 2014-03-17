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

"""Simple add of a domain user (only sets required fields).

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
from utils import validators


def AddFlags(arg_parser):
  """Handle command line flags unique to this script.

  This is unusual in that it requires 4 command line parameters and only
  sets the required user fields.  Many other fields could be exposed and set
  as an extended example.

  Args:
    arg_parser: object from argparse.ArgumentParser() to accumulate flags.
  """
  common_flags.DefineAppsDomainFlagWithDefault(arg_parser)
  common_flags.DefineVerboseFlagWithDefaultFalse(arg_parser)

  arg_parser.add_argument(
      '--user_email', '-u', required=True,
      help='User email address [REQUIRED].',
      type=validators.EmailValidatorType())
  arg_parser.add_argument(
      '--first_name', '-n', required=True,
      help='First name within the domain [REQUIRED].',
      type=validators.NoWhitespaceValidatorType())
  arg_parser.add_argument(
      '--last_name', '-l', required=True,
      help='Last name within the domain [REQUIRED].',
      type=validators.NoWhitespaceValidatorType())
  arg_parser.add_argument(
      '--password', '-p', required=True,
      help='Domain user password [REQUIRED].',
      type=validators.NoWhitespaceValidatorType())


def main(argv):
  """A script to test Admin SDK Directory APIs."""
  flags = common_flags.ParseFlags(argv, 'Add a domain user.', AddFlags)
  http = auth_helper.GetAuthorizedHttp(flags)
  api_wrapper = users_api.UsersApiWrapper(http)
  try:
    api_wrapper.AddDomainUser(flags.first_name, flags.last_name,
                              flags.user_email, flags.password)
  except admin_api_tool_errors.AdminAPIToolUserError as e:
    # Could not add user. Details provided by api wrapper in the e string.
    log_utils.LogError('Unable to add user %s.' % flags.user_email, e)
    sys.exit(1)
  log_utils.LogInfo('User %s added.' % flags.user_email)


if __name__ == '__main__':
  main(sys.argv[1:])
