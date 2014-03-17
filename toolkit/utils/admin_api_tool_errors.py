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

"""AdminAPITool errors used to more clearly show error conditions."""


class AdminAPIToolError(Exception):
  """Local exception from this tool."""
  pass


class AdminAPIToolAuthorizationError(AdminAPIToolError):
  """Problem with authorization."""
  pass


class AdminAPIToolCmdError(AdminAPIToolError):
  """Problem with running a command."""
  pass


class AdminAPIToolFileError(AdminAPIToolError):
  """Problem with executing file read or write."""
  pass


class AdminAPIToolJsonError(AdminAPIToolError):
  """Problem with reading/writing json."""
  pass


class AdminAPIToolPlusDomainsError(AdminAPIToolError):
  """Problem with Google+ user profile retrieval."""
  pass


class AdminAPIToolResumeError(AdminAPIToolError):
  """Problem with resuming domain user iteration."""
  pass


class AdminAPIToolTokenRequestError(AdminAPIToolError):
  """Problem with executing Token requests."""
  pass


class AdminAPIToolUserError(AdminAPIToolError):
  """Problem with user (creation/deletion) provisioning."""
  pass


class AdminAPIToolInvalidUserEmailError(AdminAPIToolUserError):
  """Problem with user mail format: should be user@domain.com."""
  pass
