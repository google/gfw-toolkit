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
import logging
import sys


# Http response codes to retry - includes quota issues.
# 402: Payment required
# 408: Request timeout
# 503: Service unavailable
# 504: Gateway timeout
RETRY_RESPONSE_CODES = [402, 408, 503, 504]


def _FromJsonString(json_string):
  """Helper to safely attempt a conversion from a json string to an object.

  Args:
    json_string: Presumably properly formatted json string.

  Returns:
    Object reflecting the conversion of the json.
  """
  try:
    return json.loads(json_string)
  except ValueError as e:
    print 'ERROR: response is not valid json: %s\n%s.' % (e, json_string)
    sys.exit(1)


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
  logging.getLogger().debug('----------------------------------------')
  logging.getLogger().debug('status=%d' % response.status)
  logging.getLogger().debug('----------------------------------------')
  logging.getLogger().debug('content=\n%s' % content)
  logging.getLogger().debug('----------------------------------------')

  if response.status in RETRY_RESPONSE_CODES:
    print 'Possible quota problem (%d). %s. You should retry.' % (
        response.status, url)
    sys.exit(1)

  content = _FromJsonString(content)
  if 'error' in content:
    error_text = ['ERROR: status=%d.' % response.status]
    error_text += ['url=%s.' % url]
    # The content:error.message seems to be more useful to users. Retrieve it.
    message = content.get('error', {}).get('message')
    if message:
      error_text += ['message=%s' % message]
    else:
      error_text += ['content=%s' % content]
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
