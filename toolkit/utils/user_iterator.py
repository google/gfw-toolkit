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

"""Resumable domain user iterator - cycle through domain users reliably.

Allows a domain user utility (e.g. gather... or revoke...) to handle some
operation on a set of users, get interrupted, and then resume.

This is needed for working with large sets of users (e.g.> 20k users)
efficiently.
"""

import sys

# setup_path required to allow imports from component dirs (e.g. utils)
# and lib (where the OAuth and Google API Python Client modules reside).
import setup_path  # pylint: disable=unused-import,g-bad-import-order

import admin_api_tool_errors
from admin_sdk_directory_api import users_api
import file_manager
import log_utils
from utils import validators


# Emit progress message after processing this many users.
_USER_PROGRESS_CHECKPOINT_BATCH = 10
_BASE_USER_PROGRESS_FILE_NAME = '%s_progress'  # Name of progress file.


FILE_MANAGER = file_manager.FILE_MANAGER


def _ReadLastUserProgress(prefix):
  """Helper for collection process to possibly resume if interrupted.

  Retrieves previous user and user to make a guess of the sort order.

  Args:
    prefix: custom prefix to identify progress file e.g. 'collect' or 'revoke'.

  Returns:
    Tuple of:
      -prev_user: user_email of the user previous to the next arg.
      -user_email: user_email after which the process was interrupted.
      -count_done: another indicator of progress.
  """
  prev_user = ''
  user_email = ''
  count_done = 0
  file_name = _BASE_USER_PROGRESS_FILE_NAME % prefix
  if FILE_MANAGER.FileExists(file_name):
    prev_user, user_email, count_done = FILE_MANAGER.ReadJsonFile(file_name)
  return prev_user, user_email, count_done


def _WriteLastUserProgress(prefix, prev_user, user_email, count_done):
  """Helper for revocation process to possibly resume if interrupted.

  Track previous user and user to make a guess of the sort order.

  Args:
    prefix: custom prefix to identify progress file e.g. 'collect' or 'revoke'.
    prev_user: user_email of the user previous to the next arg.
    user_email: user_email after which the process was interrupted.
    count_done: another indicator of progress.
  """
  FILE_MANAGER.WriteJsonFile(_BASE_USER_PROGRESS_FILE_NAME % prefix,
                             (prev_user, user_email, count_done),
                             overwrite_ok=True)


def _RemoveLastUserProgress(prefix):
  """Helper to remove progress file when completed.

  If the file is removed, --resume will not function.

  Args:
    prefix: custom prefix to identify progress file e.g. 'collect' or 'revoke'.
  """
  FILE_MANAGER.RemoveFile(_BASE_USER_PROGRESS_FILE_NAME % prefix)


def CheckResumable(user_list, user_count, prefix, flags):
  """Helper to verify a few conditions for resume from file cookies.

  Resuming is tricky.  Try to check as many things as possible and give
  the runner as much detail as possible about the problem if one arises.

  Args:
    user_list: List of tuples of users available in the domain to check.
               Expected to match up with names in collection progress file.
    user_count: Count of users available for resume process.
    prefix: custom prefix to identify progress file e.g. 'collect' or 'revoke'.
    flags: Argparse flags object with apps_domain, resume and first_n.

  Returns:
    Count of users successfully processed so far.

  Raises:
    AdminAPIToolResumeError if resume check failed.
  """
  if flags.first_n > 0:
    raise admin_api_tool_errors.AdminAPIToolResumeError(
        'Cannot supply --resume and --first_n at the same time.')

  prev_user, user_email, users_checked = _ReadLastUserProgress(prefix)
  if not prev_user or not user_email:
    raise admin_api_tool_errors.AdminAPIToolResumeError(
        'Did not find 2 previous users collected. Either progress was not '
        'saved or the last gather task completed successfully.')
  if users_checked < _USER_PROGRESS_CHECKPOINT_BATCH:
    raise admin_api_tool_errors.AdminAPIToolResumeError(
        'Did not make enough progress last %s run to resume.' % prefix)
  if users_checked > user_count:
    raise admin_api_tool_errors.AdminAPIToolResumeError(
        'Seems like you already finished or the users.json file changed.')

  active_user_email = user_list[users_checked - 1][0]
  if user_email != active_user_email:
    raise admin_api_tool_errors.AdminAPIToolResumeError(
        'User mismatch: %s != %s.' % (user_email, active_user_email))
  active_prev_user = user_list[users_checked - 2][0]
  if prev_user != user_list[users_checked - 2][0]:
    raise admin_api_tool_errors.AdminAPIToolResumeError(
        'Prev user mismatch: %s != %s.' % (prev_user, active_prev_user))

  # Skip back to the user after the last-checkpointed user.
  not_saved_users = users_checked % _USER_PROGRESS_CHECKPOINT_BATCH
  return users_checked - not_saved_users


def _GetUserList(http, flags):
  """Helper to retrieve the user list from local file or request.

  The list may be 10's of thousands of users so we prefer to keep a
  cached copy local for user_id lookups.

  Args:
    http: An authorized http interface object.
    flags: Argparse flags object with apps_domain, resume and first_n.

  Returns:
    A list of user tuples. For example:
      [["george@altostrat.com", "000000000298938768732", "George Lasta"],
      ["usertest@altostrat.com", "000000000406809560189", "usertest0
      userlast"], ["usertest100@altostrat.com", "000000000766612723480",
      "usertest100 userlast"]]
  """
  # Need a list of users in the domain.
  if FILE_MANAGER.FileExists(FILE_MANAGER.USERS_FILE_NAME):
    log_utils.LogInfo('Using existing users list last modified on %s.' %
                      FILE_MANAGER.FileTime(FILE_MANAGER.USERS_FILE_NAME))
    users_list = FILE_MANAGER.ReadJsonFile(FILE_MANAGER.USERS_FILE_NAME)
    # Verify that the domain has not changed
    if users_list:
      domain = validators.GetEmailParts(users_list[0][0])[1]
      if domain != flags.apps_domain:
        log_utils.LogError(
            'You have requested to use domain %s, but your existing users '
            'file \n(%s) was generated using\n%s. Please remove the file or '
            'specify %s as your apps_domain.' % (
                flags.apps_domain,
                FILE_MANAGER.BuildFullPathToFileName(
                    FILE_MANAGER.USERS_FILE_NAME),
                domain, domain))
        sys.exit(1)
  else:
    log_utils.LogInfo('Retrieving list of users...')
    api_wrapper = users_api.UsersApiWrapper(http)
    users_list = api_wrapper.GetDomainUsers(flags.apps_domain)
    FILE_MANAGER.WriteJsonFile(FILE_MANAGER.USERS_FILE_NAME, users_list)
  user_count = len(users_list)
  log_utils.LogInfo('Found %d users to check.' % user_count)
  return users_list, user_count


def _GetDomainUsersData(http, flags):
  """Helper to get the user data for a domain that will be used in the queries.

  Args:
    http: Authorized http interface.
    flags: Argparse flags object with apps_domain, resume and first_n.

  Returns:
    Tuple of:
      user_list: list of user tuples.
      user_count: count of users so others can avoid len(user_list).
  """
  try:
    user_list, user_count = _GetUserList(http, flags)
  except admin_api_tool_errors.AdminAPIToolUserError as e:
    log_utils.LogError('Unable to retrieve required users data.', e)
    sys.exit(1)
  return user_list, user_count


def StartUserIterator(http, prefix, flags):
  """Domain user iterator for resumably looping through all domain users.

  Handles the acquisition of the users list and checking of resume which
  makes the code to collect and revoke domain users much easier to read.

  Args:
    http: authorized http interface.
    prefix: custom prefix to identify progress file e.g. 'collect' or 'revoke'.
    flags: Argparse flags object with apps_domain, resume and first_n.

  Yields:
    A 3-Tuple of user data:
    -user email: String e.g. 'larry@domain.com'
    -user id: String of ints e.g. '112351558298938768732'
    -checkpoint: True if batch full or on the last user.
  """
  user_list, user_count = _GetDomainUsersData(http, flags)

  if flags.resume:
    # Resume: check that current users.json file still matches where we
    #         left off and adjust the users list to skip previously checked.
    try:
      users_checked = CheckResumable(user_list, user_count, prefix, flags)
    except admin_api_tool_errors.AdminAPIToolResumeError as e:
      log_utils.LogError(
          'Cannot --resume %s. You must retry without --resume.' % prefix, e)
      sys.exit(1)

    prev_user = user_list[users_checked - 1][0]
    print 'Resuming at user #%d/%d (%s)...' % (users_checked, user_count,
                                               user_list[users_checked][0])
  else:
    users_checked = 0
    prev_user = None
    # Allow users to test revoke with shorter lists.
    if flags.first_n:
      user_count = flags.first_n

  for user_email, user_id, _ in user_list[users_checked:user_count]:
    users_checked += 1
    checkpoint = (users_checked % _USER_PROGRESS_CHECKPOINT_BATCH == 0 or
                  users_checked == user_count)
    # Show some screen output during a longish, tedious process.
    # Each iteration seems to take ~0.6s
    sys.stdout.write('%80s\r' % '')  # Clear the previous entry.
    sys.stdout.write('%s\r' % user_email)
    sys.stdout.flush()

    yield user_email, user_id, checkpoint

    # In the interest of possibly resuming very long runs, save progress
    # cookie. Track last 2 users checked because we may alternate cycling
    # through the list in asc or desc order to to create some entropy and
    # this leaves a hint of the direction that was used that run.
    _WriteLastUserProgress(prefix, prev_user, user_email, users_checked)
    prev_user = user_email

    if checkpoint:
      sys.stdout.write('%80s\r' % '')  # Clear the previous entry.
      sys.stdout.write('Checked %d of %d users.\n' % (users_checked,
                                                      user_count))

  # Cleanup progress file to inhibit resuming completed tasks.
  _RemoveLastUserProgress(prefix)
