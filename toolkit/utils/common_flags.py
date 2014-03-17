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

"""Common flags functions used by all the command-line-interface scripts.

All the command-line-interface scripts (ls_customer_id, ls_tokens_for_user,
ls_tokens_for_user_clientid, ls_users, revoke_tokens_for_user_clientid)
require a Google Apps domain name (apps_domain).

Optionally, each may enable a --verbose option to show more output messages.
"""

import argparse

# setup_path required to allow imports from component dirs (e.g. utils)
# and lib (where the OAuth and Google API Python Client modules reside).
import setup_path  # pylint: disable=unused-import,g-bad-import-order

import auth_helper
import file_manager
import log_utils
import validators


FILE_MANAGER = file_manager.FILE_MANAGER


def DefineAppsDomainFlagWithDefault(arg_parser, required=False):
  """Defines common --apps_domain flag used on most command line commands.

  Args:
    arg_parser: object from argparse.ArgumentParser() to accumulate flags.
    required: If False uses the default from the default_domain file.
  """
  default_domain = FILE_MANAGER.ReadDefaultDomain() if not required else ''
  arg_parser.add_argument(
      '--apps_domain', '-a', required=required, default=default_domain,
      type=validators.AppsDomainValidatorType(),
      help='Google Apps Domain Name (e.g. altostrat.com) [REQUIRED].')


def DefineForceFlagWithDefaultFalse(arg_parser, required=False,
                                    help_string=None):
  """Defines common --force flag used on many command line commands.

  Args:
    arg_parser: object from argparse.ArgumentParser() to accumulate flags.
    required: Enforces required -f on some commands.
    help_string: String to use for help (to override default).
  """
  if not help_string:
    help_string = 'Confirm (force) that file overwrite is ok.'
  arg_parser.add_argument(
      '--force', '-f', action='store_true', default=False, required=required,
      help=help_string)


def DefineVerboseFlagWithDefaultFalse(arg_parser):
  """Defines common --verbose flag used on many command line commands.

  Args:
    arg_parser: object from argparse.ArgumentParser() to accumulate flags.
  """
  arg_parser.add_argument(
      '--verbose', '-v', action='store_true', default=False,
      help='Show expanded output.')


def ParseFlags(argv, description, add_flags_fn=None):
  """Common command-line flags parsing (e.g. for apps domain and verbose).

  Allows custom added flags using add_flags_fn and also initializes logging
  using the common --verbose flag.

  Args:
    argv: List of strings passed from main().
    description: String passed to parser constructor for help.
    add_flags_fn: If present, function that adds custom flags.

  Returns:
    Argparse parsed flags object with flag attributes.
  """
  arg_parser = argparse.ArgumentParser(description=description,
                                       parents=[auth_helper.ARG_PARSER])
  if add_flags_fn:
    add_flags_fn(arg_parser)
  flags = arg_parser.parse_args(argv)

  log_utils.SetupLogging(flags.verbose)
  if hasattr(flags, 'apps_domain') and flags.apps_domain:
    FILE_MANAGER.AddWorkDirectory(flags.apps_domain)
  return flags
