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

"""Show a list of users in an Apps Domain.

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
from utils import file_manager
from utils import log_utils


FILE_MANAGER = file_manager.FILE_MANAGER


def AddFlags(arg_parser):
  """Handle command line flags unique to this script.

  Args:
    arg_parser: object from argparse.ArgumentParser() to accumulate flags.
  """
  common_flags.DefineAppsDomainFlagWithDefault(arg_parser)
  common_flags.DefineForceFlagWithDefaultFalse(arg_parser)
  common_flags.DefineVerboseFlagWithDefaultFalse(arg_parser)

  arg_parser.add_argument('--json', action='store_true', default=False,
                          help='Output results to a json file.')
  arg_parser.add_argument('--first_n', type=int, default=0,
                          help='Show the first n users in the list.')


def main(argv):
  """A script to test Admin SDK Directory APIs."""
  flags = common_flags.ParseFlags(argv, 'List domain users.', AddFlags)
  if flags.json:
    FILE_MANAGER.ExitIfCannotOverwriteFile(FILE_MANAGER.USERS_FILE_NAME,
                                           overwrite_ok=flags.force)

  http = auth_helper.GetAuthorizedHttp(flags)
  api_wrapper = users_api.UsersApiWrapper(http)

  max_results = flags.first_n if flags.first_n > 0 else None
  try:
    if flags.json:
      user_list = api_wrapper.GetDomainUsers(flags.apps_domain,
                                             max_results=max_results)
    else:
      api_wrapper.PrintDomainUsers(flags.apps_domain,
                                   max_results=max_results)
  except admin_api_tool_errors.AdminAPIToolUserError as e:
    log_utils.LogError(
        'Unable to enumerate users from domain %s.' % flags.apps_domain, e)
    sys.exit(1)

  if flags.json:
    try:
      filename_path = FILE_MANAGER.WriteJsonFile(FILE_MANAGER.USERS_FILE_NAME,
                                                 user_list,
                                                 overwrite_ok=flags.force)
    except admin_api_tool_errors.AdminAPIToolFileError as e:
      # This usually means the file already exists and --force not supplied.
      log_utils.LogError('Unable to write the domain users file.', e)
      sys.exit(1)
    print 'Users list written to %s.' % filename_path


if __name__ == '__main__':
  main(sys.argv[1:])
