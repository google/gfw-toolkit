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

"""Utils for http response and content handling.

Used for common cracking of the content document returned from a request.
"""

import json
import random
import time
import urllib

import log_utils
from utils import admin_api_tool_errors


# Http response codes to retry - includes quota issues.
# 402: Payment required
# 408: Request timeout
# 503: Service unavailable
# 504: Gateway timeout
RETRY_RESPONSE_CODES = [402, 408, 503, 504]

BACKOFF_MAX_RETRIES = 8  # Last retry is 2**8 = 256s


class Backoff(object):
  """Exponential Backoff class used in conjunction with requests.

  Implements an exponential backoff algorithm.  Instantiate and call loop() each
  time through the loop, and each time a request fails call fail() which will
  delay an appropriate amount of time.
  """

  def __init__(self, maxretries=BACKOFF_MAX_RETRIES):
    self.retry = 0
    self.maxretries = maxretries

  def Loop(self):
    return self.retry < self.maxretries

  def Fail(self):
    self.retry += 1
    # Add small randomness to avoid races between threads.
    delay_s = (2 ** self.retry) + (random.randint(0, 1000) / 1000)
    log_utils.LogInfo('Waiting for %ds and retrying...' % delay_s)
    time.sleep(delay_s)


def FromJsonString(json_string):
  """Helper to safely attempt a conversion from a json string to an object.

  Args:
    json_string: Presumably properly formatted json string.

  Returns:
    Object reflecting the conversion of the json.

  Raises:
    AdminAPIToolJsonError: pinpoints the location of the error.
  """
  try:
    document_object = json.loads(json_string)
  except ValueError as e:
    raise admin_api_tool_errors.AdminAPIToolJsonError(
        'ERROR: response is not valid json: %s\n%s.' % (e, json_string))
  return document_object


def ParseHttpResult(url, response, content):
  """Helper to more clearly find and return error messages.

  Args:
    url: full url including https:// for the RESTful API command.
    response: response with headers from http.
    content: content from the url (unzipped if necessary).

  Returns:
    If error text is discovered, returns a string with the error text
    otherwise returns an object containing the content.
  """
  log_utils.LogDebug('----------------------------------------')
  log_utils.LogDebug('status=%d' % response.status)
  log_utils.LogDebug('----------------------------------------')
  log_utils.LogDebug('content=\n%s' % content)
  log_utils.LogDebug('----------------------------------------')
  content = FromJsonString(content)
  if 'error' in content:
    error_text = ['ERROR: status=%d.' % response.status]
    error_text += ['url=%s.' % url]
    # The content:error.message seems to be more useful to users. Retrieve it.
    message = content.get('error', {}).get('message')
    if message:
      error_text += ['message=%s.' % message]
    else:
      error_text += ['content=%s.' % content]
    # The provisioning API is not available if the box is not checked.
    if (response.status == 403 and
        message == 'Domain cannot use apis.'):
      error_text = [message, 'You should check "Enable provisioning API" '
                    'in your Domain Settings->User Settings.']
    # When requesting tokens for a specific client_id, if no tokens
    # are found, the API server responds with an unexpected 500 error.
    # Notice that specific case and fail a little more gracefully.
    elif (response.status == 500 and
          message == 'No tokens exist for the specified client id'):
      error_text = [message]
    return '\n'.join(error_text)
  return content


def SafeEncode(token):
  """Safely encode a token to be used in an url.

  The simple case is this converts spaces in url parameters properly to %20.

  Args:
    token: A string value to convert to an url-safe token.

  Returns:
    The converted string.
  """
  return urllib.quote(token)
