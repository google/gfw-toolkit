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

"""Tool to wrap authentication using oauth2client.

Auth requests need to be serviceable from both command line clients
and AppEngine clients (that cannot write files to save state).
"""

import argparse
import sys

from apiclient.http import set_user_agent
import file_manager
import httplib2
import log_utils
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser as oauth2client_argparser
from oauth2client.tools import run_flow


ARG_PARSER = argparse.ArgumentParser(add_help=False,
                                     parents=[oauth2client_argparser])

# User agent token - pushed into headers for later tracking queries.
_TOOL_USER_AGENT = 'cse-admin-api-tool/%s'

# Name of a file containing information used to identify this application
# and to process OAuth 2.0 authentications.  It includes fields such as
# client_id and client_secret. The file is read (not written) and obtained
# by a domain admin using the API Access tab on the Google APIs Console
# <http://code.google.com/apis/console>
_CLIENT_SECRETS_FILE_NAME = 'client_secrets.json'

# Name of a file that will be created to cache the current access token.
# Contains information used to determine if a refresh is needed.
# This token *is* domain specific so it is contained relative to an apps domain.
_CURRENT_ACCESS_FILE_NAME = 'current_access.dat'

# Default of 5s seems too short for Admin SDK.
_EXTENDED_SOCKET_TIMEOUT_S = 10

# Displayed in the browser if the CLIENT_SECRETS file is missing.
_MISSING_CLIENT_SECRETS_MSG = """
    WARNING: Please configure OAuth 2.0

    To make this tool run you will need to download or populate a file at:

       %s

    with information from your project at the Google Developers Console:
    <https://console.developers.google.com>.
"""

# Scopes are used to describe the needed access level for an API. Possible
# scopes can be discovered within the documentation for the API to be used:
# https://developers.google.com/admin-sdk/directory/v1/reference/users/list#auth
_SCOPES = [
    # For Google+ reads
    'https://www.googleapis.com/auth/plus.profiles.read',
    # For Admin SDK Directory APIs
    'https://www.googleapis.com/auth/directory.user',
    # For 3-legged OAuth
    'https://www.googleapis.com/auth/admin.directory.user.security',
    ]

FILE_MANAGER = file_manager.FILE_MANAGER


def GetCredentials(flags, scope_list):
  """Retrieve saved credentials or create and save credentials using flow.

  Args:
    flags: argparse parsed flags object.
    scope_list: List of strings reflecting desired API access (scope)
                e.g.: ['https://www.googleapis.com/auth/directory.user'].

  Returns:
    An oauth2client Credentials() object.
  """
  client_file_storage = Storage(
      FILE_MANAGER.BuildFullPathToFileName(_CURRENT_ACCESS_FILE_NAME))
  credentials = client_file_storage.get()
  if credentials is None or credentials.invalid:
    client_secrets_path = FILE_MANAGER.BuildFullPathToFileName(
        _CLIENT_SECRETS_FILE_NAME, work_dir=False)
    missing_secrets_msg = _MISSING_CLIENT_SECRETS_MSG % client_secrets_path
    flow_manager = flow_from_clientsecrets(client_secrets_path,
                                           scope=scope_list,
                                           message=missing_secrets_msg)
    credentials = run_flow(flow_manager, client_file_storage, flags)
  if not credentials:
    log_utils.LogError('Unable to retrieve valid credentials.')
    sys.exit(-1)
  return credentials


def GetAuthorizedHttp(flags):
  """Helper to create an http interface object and authorize it.

  Made simple by oauth2client library.  Because http object are NOT
  thread-safe, create a new one every time (assumes being created by multiple
  threads).

  Args:
    flags: argparse parsed flags object.

  Returns:
    Authorized httplib2 http interface object.
  """
  credentials = GetCredentials(flags, _SCOPES)
  try:
    cse_tool_version = _TOOL_USER_AGENT % FILE_MANAGER.ReadAppVersion()
    log_utils.LogDebug('user-agent: %s' % cse_tool_version)
    http = httplib2.Http(timeout=_EXTENDED_SOCKET_TIMEOUT_S)
    set_user_agent(http, cse_tool_version)
    http = credentials.authorize(http)
  except AccessTokenRefreshError:
    log_utils.LogError('The credentials have been revoked or expired, '
                       'please re-run the application to re-authorize')
    sys.exit(1)
  return http
