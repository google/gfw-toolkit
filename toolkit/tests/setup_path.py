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

"""Common path adjustment to allow references to shared modules.

This module is imported by executable scripts in order to help the scripts
find library modules that are organized under component directories.

This project is structured as a base directory with components: apixxx, cmds,
third_party and utils.

For clarity, executable scripts in cmds would like to cleanly import modules
that reside in the apixxx, third_party and utils component directories.
In order for this to work the base directory of the source tree must be
included in the PYTHONPATH explicitly.  Then lines such as the following will
succeed in importing component modules:

from utils import auth_helper
...
"""
import os
import sys


# Establish the Application base path as the parent of this file's # directory.
APP_BASE_PATH = os.path.dirname(os.path.dirname(sys.modules[__name__].__file__))
sys.path.insert(0, APP_BASE_PATH)
# For in-place deployments - prefer local ./third_party packages.
if os.path.isdir(os.path.join(APP_BASE_PATH, 'third_party')):
  sys.path.insert(0, os.path.join(APP_BASE_PATH, 'third_party'))

# Attempt to import required packages to help avoid deployment confusion.
try:
  # pylint: disable=g-import-not-at-top, unused-import
  import apiclient
  from apiclient.discovery import build
  import httplib2
  import oauth2client
  from oauth2client.tools import run
  # pylint: enable=g-import-not-at-top, unused-import
except ImportError as e:
  module_package_map = {'apiclient': 'google-api-python-client',
                        'apiclient.discovery': 'google-api-python-client',
                        'oauth2client.tools': 'oauth2client'}
  # The exception message will be of the form: 'No module named xxxxx'
  failed_module = package_name = str(e).split()[-1]
  if failed_module in module_package_map:
    package_name = module_package_map[failed_module]
  print ('Unable to find "%s". You are missing the ./third_party directory or '
         'you need to install the "%s" package.'
         % (failed_module, package_name))
  sys.exit(1)
