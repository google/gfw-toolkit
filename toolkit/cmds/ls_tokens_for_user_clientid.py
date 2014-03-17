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

"""Show the oauth token issued to an application on behalf of a user.

A 'clientId' (e.g. twitter.com) is the identifier of an application that
requests access to some Apps Domain resources.

APIs Used:
  Experimental Google Apps 3-legged OAuth Token Management API.
"""

import sys

# setup_path required to allow imports from component dirs (e.g. utils)
# and lib (where the OAuth and Google API Python Client modules reside).
import setup_path  # pylint: disable=unused-import,g-bad-import-order

from admin_sdk_directory_api import tokens_api
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
  common_flags.DefineVerboseFlagWithDefaultFalse(arg_parser)

  arg_parser.add_argument(
      '--long_list', '-l', action='store_true', default=False,
      help='Show more columns of output.')
  arg_parser.add_argument(
      '--client_id', '-c', required=True,
      help=('Client ID to which the token was issued (e.g. twitter.com) '
            '[REQUIRED].'),
      type=validators.NoWhitespaceValidatorType())
  arg_parser.add_argument(
      '--user_email', '-u', required=True,
      help='User email address [REQUIRED].',
      type=validators.EmailValidatorType())


def main(argv):
  """A script to test Apps Security APIs."""
  flags = common_flags.ParseFlags(argv,
                                  'List token info about a user and client.',
                                  AddFlags)
  http = auth_helper.GetAuthorizedHttp(flags)
  user_api = users_api.UsersApiWrapper(http)
  if not user_api.IsDomainUser(flags.user_email):
    print 'User %s not found.' % flags.user_email
    sys.exit(1)
  apps_security_api = tokens_api.TokensApiWrapper(http)
  try:
    apps_security_api.PrintTokenForUserClientId(flags.user_email,
                                                flags.client_id,
                                                flags.long_list)
  except admin_api_tool_errors.AdminAPIToolTokenRequestError as e:
    log_utils.LogError(
        'Unable to retrieve tokens for user %s.' % flags.user_email, e)
    sys.exit(1)


if __name__ == '__main__':
  main(sys.argv[1:])
