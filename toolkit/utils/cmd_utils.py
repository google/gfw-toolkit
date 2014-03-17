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

"""Helper wrappers for invoking other command-line programs.

Uses subprocess and provides common method for invoking the cmd utilities
with some knowledge of common arguments.
"""

import os
import subprocess

import setup_path  # pylint: disable=unused-import,g-bad-import-order

import admin_api_tool_errors
import log_utils


def RunPyCmd(cmd_py, arg_list=None):
  """Helper to run cmd utilities.

  Args:
    cmd_py: String of cmd to run e.g. report_users_csv.py.
    arg_list: List of string args to add to the command line.

  Raises:
    AdminAPIToolCmdError: if the executed command returns nonzero or the
                           command cannot be found.
  """
  cmd_py = os.path.join(setup_path.APP_BASE_PATH, 'cmds', cmd_py)
  if not os.path.isfile(cmd_py):
    raise admin_api_tool_errors.AdminAPIToolCmdError('Cannot find %s' % cmd_py)
  cmd = ['python', cmd_py]
  if arg_list:
    cmd += arg_list
  log_utils.LogDebug(' '.join(cmd))
  return_code = subprocess.call(cmd)
  if return_code:
    raise admin_api_tool_errors.AdminAPIToolCmdError(
        'Execution failed (%d).\n\t%s' % (return_code, ' '.join(cmd)))
