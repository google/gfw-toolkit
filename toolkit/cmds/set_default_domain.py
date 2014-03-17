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

"""Create a file that caches the Apps Domain and CustomerId for future use.

Creates a file (default_domain) that is consumed by the other command line
scripts.  It will contain the actual domain name and a unique customer_id
that is retrieved from an API query.

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
  common_flags.DefineAppsDomainFlagWithDefault(arg_parser, required=True)
  common_flags.DefineForceFlagWithDefaultFalse(arg_parser)
  common_flags.DefineVerboseFlagWithDefaultFalse(arg_parser)


def main(argv):
  """Save the domain to a file to avoid constantly passing a flag."""
  flags = common_flags.ParseFlags(argv, 'Save default domain for all commands.',
                                  AddFlags)

  # Fail if the defaults file exists. Better than waiting for write to check.
  FILE_MANAGER.ExitIfCannotOverwriteFile(FILE_MANAGER.DEFAULT_DOMAIN_FILE_NAME,
                                         work_dir=False,
                                         overwrite_ok=flags.force)
  http = auth_helper.GetAuthorizedHttp(flags)
  api_wrapper = users_api.UsersApiWrapper(http)
  try:
    customer_id = api_wrapper.GetCustomerId(flags.apps_domain)
  except admin_api_tool_errors.AdminAPIToolUserError as e:
    log_utils.LogError(
        'Unable to retrieve customer_id for domain %s.' % flags.apps_domain, e)
    sys.exit(1)
  filename_path = FILE_MANAGER.WriteDefaults(flags.apps_domain, customer_id,
                                             flags.force)
  print 'Default domain stored in %s.' % filename_path


if __name__ == '__main__':
  main(sys.argv[1:])
