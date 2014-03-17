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

"""Simple rm/delete of a domain user.

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

  Args:
    arg_parser: object from argparse.ArgumentParser() to accumulate flags.
  """
  common_flags.DefineAppsDomainFlagWithDefault(arg_parser)
  common_flags.DefineForceFlagWithDefaultFalse(arg_parser, required=True)
  common_flags.DefineVerboseFlagWithDefaultFalse(arg_parser)

  arg_parser.add_argument(
      '--user_email', '-u', required=True,
      help='User email address [REQUIRED].',
      type=validators.EmailValidatorType())


def main(argv):
  """A script to test Admin SDK Directory APIs: delete."""
  flags = common_flags.ParseFlags(argv, 'Remove a domain user.', AddFlags)
  http = auth_helper.GetAuthorizedHttp(flags)
  api_wrapper = users_api.UsersApiWrapper(http)
  try:
    api_wrapper.DeleteDomainUser(flags.user_email)
  except admin_api_tool_errors.AdminAPIToolUserError as e:
    log_utils.LogError('Unable to rm user %s.' % flags.user_email, e)
    sys.exit(1)
  log_utils.LogInfo('User %s successfully removed.' % flags.user_email)


if __name__ == '__main__':
  main(sys.argv[1:])
