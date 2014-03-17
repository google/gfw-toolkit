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

"""Utility functions used by command-line-interface scripts to store local data.

Intended to provide a single class that manages the constants and locations
of files read/written.  Files are used to both cache credentials and to store
intermediate data to aid reports/actions against very large (>20k users)
domains.

For simplicity this class is designed to allow reading/writing of local files
only.  This will not work with AppEngine as AppEngine apps may not write files.

Two common exmples of local files include:

  1. It is convenient for a user working with a single apps domain to stash
     a hint to use that domain for all commands executed.  That default domain
     hint is stored as local data.

  2. Utilities that make round trips cache data that is subsequently used by
     reports to aggregate results.  Retrieving the user list from a large
     domain happens in pages and those results are cached locally during
     the process.  The user list is then used for a few reporting tasks.

There are two types of files read/written by this code: 'base files' and
'working files'.

Base files include the application version file and the defaults
(default domain) file.  Base files reside in the base application directory.
The version file is never written (only read) while the defaults file
(not required) is written infrequently by the set_default_domain.py command.

Working files are generated (automatically) and updated during run-time
operations.  When running on AppEngine, working files will need a backing store
other than files.
"""

import csv
import json
import os
import sys
import time

# setup_path required to allow imports from component dirs (e.g. utils)
# and lib (where the OAuth and Google API Python Client modules reside).
import setup_path  # pylint: disable=unused-import,g-bad-import-order

import admin_api_tool_errors
import log_utils


class FileManager(object):
  """Manage local files and provide methods for reading/writing."""
  # Data store tag names:
  DEFAULT_DOMAIN_FILE_NAME = 'default_domain.json'  # Auto-fills common cmd arg.
  USERS_FILE_NAME = 'users.json'  # List of users in a domain.
  VERSION_FILE_NAME = 'VERSION'  # Contains application/tool version string.
  WORK_ROOT_DIR = 'working'  # Parent directory of the working files.

  def __init__(self):
    """Initialize variables to locate files properly."""
    self._base_directory = setup_path.APP_BASE_PATH
    self._work_directory = os.path.join(self._base_directory,
                                        FileManager.WORK_ROOT_DIR)

  def BuildFullPathToFileName(self, file_name, work_dir=True, create_dir=False):
    """Build a full path to a 'base' file or 'work' file.

    Also creates directories if needed to properly locate the file.

    Args:
      file_name: String name of a file (e.g. users.json).
      work_dir: Boolean, if True indicates to locate the file under a 'working'
                folder else locates the file in the base application directory.
      create_dir: Boolean, if True ok to create needed directories to write
                  files.  Expected to be False if reading files.

    Returns:
      String of the full path to the file to use for read/write.
    """
    local_path = self._work_directory if work_dir else self._base_directory
    if create_dir and not os.path.isdir(local_path):
      os.makedirs(local_path)
    return os.path.join(local_path, file_name)

  def FileExists(self, file_name, work_dir=True):
    """Helper method to check if a file exists.

    Args:
      file_name: String name of a file (e.g. users.json).
      work_dir: Boolean, if True indicates to locate the file under a 'working'
                folder else locates the file in the base application directory.

    Returns:
      True if the file exists else False.
    """
    return os.path.isfile(self.BuildFullPathToFileName(file_name,
                                                       work_dir=work_dir))

  def FileTime(self, file_name, work_dir=True):
    """Helper method to retrieve the last modified time of a file.

    Args:
      file_name: String name of a file (e.g. users.json).
      work_dir: Boolean, if True indicates to locate the file under a 'working'
                folder else locates the file in the base application directory.

    Returns:
      The last modified time of the file converted to a readable String.
    """
    return time.ctime(os.path.getmtime(
        self.BuildFullPathToFileName(file_name, work_dir=work_dir)))

  def ExitIfCannotOverwriteFile(self, file_name, work_dir=True,
                                overwrite_ok=False):
    """Helper to consistently handle attempts to overwrite existing files.

    Args:
      file_name: String name of a file (e.g. users.json).
      work_dir: Boolean, if True indicates to locate the file under a 'working'
                folder else locates the file in the base application directory.
      overwrite_ok: Boolean that is True if the user has explicitly
                    approved that an existing file may be overwritten.
    """
    if self.FileExists(file_name, work_dir=work_dir):
      not_writable_msg = None
      filename_path = self.BuildFullPathToFileName(file_name, work_dir=work_dir)
      exists_msg = 'Output file (%s) already exists.' % filename_path
      if not os.access(filename_path, os.W_OK):
        not_writable_msg = '%s %s' % (
            exists_msg, 'The file permissions do not allow writing.')
      elif not overwrite_ok:
        not_writable_msg = '%s %s' % (
            exists_msg, 'Use --force to overwrite.')
      if not_writable_msg:
        log_utils.LogError(not_writable_msg)
        sys.exit(1)

  def AddWorkDirectory(self, new_leaf_dir):
    """Add a leaf to our work file tree.

    This is used to split work files between multiple apps domains.  For
    example, work_dir will be set to an apps domain name to allow segregation
    of work files and credential tokens between multiple domains.

    Args:
      new_leaf_dir: String leaf path to locate work files (e.g. mybiz.com).
    """
    self._work_directory = os.path.join(self._work_directory, new_leaf_dir)
    if not os.path.isdir(self._work_directory):
      os.makedirs(self._work_directory)

  def ReadTextFile(self, file_name, work_dir=True):
    """Reads from a text file into a String.

    Expected to be used for small files.

    Args:
      file_name: String name of a file (e.g. mydata.txt).
      work_dir: Boolean, if True indicates to locate the file under a 'working'
                folder else locates the file in the base application directory.

    Returns:
      A String with the entire contents of the file.

    Raises:
      AdminAPIToolFileError: if unable to open the file for reading.
    """
    filename_path = self.BuildFullPathToFileName(file_name, work_dir=work_dir)
    if not self.FileExists(file_name, work_dir=work_dir):
      raise admin_api_tool_errors.AdminAPIToolFileError(
          'Cannot read file %s.' % filename_path)
    with open(filename_path, 'r') as f:
      return f.read()

  def ReadTextFileToSet(self, file_name):
    """Reads text file lines into a set; each line is an entry.

    Args:
      file_name: file name - expected located in the working directory.

    Returns:
      Set object reflecting the file contents.
    """
    if not self.FileExists(file_name):
      log_utils.LogError('Unable to locate file: %s' %
                         self.BuildFullPathToFileName(file_name))
      sys.exit(1)
    line_set = set()
    for line in self.ReadTextFile(file_name).splitlines():
      line_set.add(line)
    return line_set

  def ReadJsonFile(self, file_name, work_dir=True):
    """Reads from a json file into a Python object.

    Args:
      file_name: String name of a file (e.g. users.json).
      work_dir: Boolean, if True indicates to locate the file under a 'working'
                folder else locates the file in the base application directory.

    Returns:
      A valid Python object de-serialized from the json file.

    Raises:
      AdminAPIToolFileError: if unable to open the file for reading.
    """
    filename_path = self.BuildFullPathToFileName(file_name, work_dir=work_dir)
    if not self.FileExists(file_name, work_dir=work_dir):
      raise admin_api_tool_errors.AdminAPIToolFileError(
          'Cannot locate file: %s.' % filename_path)
    with open(filename_path, 'r') as f:
      try:
        new_object = json.load(f)
      except ValueError as e:
        raise admin_api_tool_errors.AdminAPIToolJsonError(
            'File (%s) is not valid json (%s).' % (filename_path, e))
      return new_object

  def WriteJsonFile(self, file_name, content_object, work_dir=True,
                    overwrite_ok=False):
    """Writes an object to a json file as a serial string.

    Args:
      file_name: String name of a file (e.g. users.json).
      content_object: Valid object (usually a dict) to be serialized.
      work_dir: Boolean, if True indicates to locate the file under a 'working'
                folder else locates the file in the base application directory.
      overwrite_ok: Boolean that must be True to allow over write of data.

    Returns:
      String with the fully path'ed file name.

    Raises:
      AdminAPIToolFileError: if unable to open the file for writing.
      AdminAPIToolJsonError: if the object has un-serializable members.
    """
    self.ExitIfCannotOverwriteFile(file_name, work_dir=work_dir,
                                   overwrite_ok=overwrite_ok)
    filename_path = self.BuildFullPathToFileName(file_name, work_dir=work_dir,
                                                 create_dir=True)
    try:
      f = open(filename_path, 'w')
    except IOError as e:
      raise admin_api_tool_errors.AdminAPIToolFileError(
          'Cannot open file %s (%s).' % (filename_path, e))

    try:
      json.dump(content_object, f)
    except TypeError as e:
      raise admin_api_tool_errors.AdminAPIToolJsonError(
          'Cannot create json file %s (%s).' % (filename_path, e))
    finally:
      f.close()

    log_utils.LogDebug('Wrote file %s' % filename_path)
    return filename_path

  def ReadCsvFile(self, file_name, work_dir=True, dictreader=False):
    """Read an existing csv file into a list.

    Args:
      file_name: String name of a file (e.g. report.csv).
      work_dir: Boolean, if True indicates to locate the file under a 'working'
                folder else locates the file in the base application directory.
      dictreader: If True use a csv DictReader instead of a regular reader.
                  The DictReader expects the first row to be a header row.

    Returns:
      List of tuples (1 for each row) or a list of dictionaries (depending on
      the value of the dictreader arg).

    Raises:
      AdminAPIToolFileError: Unable to locate the expected file.
    """
    filename_path = self.BuildFullPathToFileName(file_name, work_dir=work_dir)
    if not self.FileExists(file_name, work_dir=work_dir):
      raise admin_api_tool_errors.AdminAPIToolFileError(
          'Cannot locate file: %s.' % filename_path)
    csv_rows = []
    with open(filename_path, 'rb') as f:
      if dictreader:
        csv_reader = csv.DictReader(f)
      else:
        csv_reader = csv.reader(f)
      csv_rows = [csv_row for csv_row in csv_reader]
    return csv_rows

  def WriteCSVFile(self, file_name, data_rows, header=None, work_dir=True,
                   overwrite_ok=False):
    """Needs to use csv library to serialize object to a file.

    Args:
      file_name: String name of a file (e.g. report.csv).
      data_rows: A list of lists to be converted to csv lines (rows).
                 Each list constitutes one row of csv output.
      header: A list of fields to be used IN-ORDER to produce the output.
              This may be None.
      work_dir: Boolean, if True indicates to locate the file under a 'working'
                folder else locates the file in the base application directory.
      overwrite_ok: Boolean that must be True to allow over write of data.

    Returns:
      If successful, returns a String with the fully path'ed file name,
      otherwise, returns None.
    """
    self.ExitIfCannotOverwriteFile(file_name, work_dir=work_dir,
                                   overwrite_ok=overwrite_ok)
    filename_path = self.BuildFullPathToFileName(file_name, work_dir=work_dir,
                                                 create_dir=True)
    if not data_rows:
      log_utils.LogWarning('Improperly formed csv rows. File not written: %s' %
                           filename_path)
      return None
    with open(filename_path, 'wb') as f:
      writer = csv.writer(f)
      if header:
        writer.writerows([header])
      writer.writerows(data_rows)
    log_utils.LogDebug('Wrote %s' % filename_path)
    return filename_path

  def RemoveFile(self, file_name, work_dir=True):
    """Removes a file if it exists.

    Args:
      file_name: String name of a file (e.g. users.json).
      work_dir: Boolean, if True indicates to locate the file under a 'working'
                folder else locates the file in the base application directory.
    """
    if self.FileExists(file_name, work_dir=work_dir):
      filename_path = self.BuildFullPathToFileName(file_name, work_dir=work_dir)
      os.remove(filename_path)

      log_utils.LogDebug('Removed file %s' % filename_path)

  def ReadAppVersion(self):
    """Read the application/tool version # from a file.

    Given a version string of the format: v1.20130517 Beta, throws away the
    initial 'v' and any trailing tokens. This is appropriate to include
    in an http header e.g. 'my-tool/1.20130517'.

    Returns:
      A single String token with no spaces.

    Raises:
      AdminAPIToolError: if VERSION file is not found.
    """
    if not self.FileExists(self.VERSION_FILE_NAME, work_dir=False):
      raise admin_api_tool_errors.AdminAPIToolError(
          'Not found: %s' % self.BuildFullPathToFileName(self.VERSION_FILE_NAME,
                                                         work_dir=False))
    version = self.ReadTextFile(self.VERSION_FILE_NAME, work_dir=False).strip()
    return version.split(None, 1)[0][1:]

  def ReadDefaultDomain(self):
    """Read apps_domain from a local defaults data file.

    Returns:
      apps_domain: String reflecting the default Apps Domain (e.g. mybiz.com).
    """
    apps_domain = ''
    if self.FileExists(self.DEFAULT_DOMAIN_FILE_NAME, work_dir=False):
      defaults_object = self.ReadJsonFile(self.DEFAULT_DOMAIN_FILE_NAME,
                                          work_dir=False)
      if not defaults_object or 'apps_domain' not in defaults_object:
        raise admin_api_tool_errors.AdminAPIToolJsonError(
            'Unexpected defaults read!')
      apps_domain = defaults_object.get('apps_domain')
    return apps_domain

  def WriteDefaults(self, apps_domain, customer_id, overwrite_ok):
    """Write apps_domain and customer_id to a file for later use.

    Writes data as strings in a dictionary.

    Args:
      apps_domain: String reflecting an apps domain: altostrat.com
      customer_id: Unique id for an owner of apps domain(s).
                   Can map to multiple domains.
      overwrite_ok: Boolean that is True if the user has explicitly
                    approved that an existing file may be overwritten.

    Returns:
      String with the fully path'ed file name.

    Raises:
      AdminAPIToolError: if blank supplied for domain or customer_id.
    """
    if not apps_domain or not customer_id:
      raise admin_api_tool_errors.AdminAPIToolError(
          'Unexpectedly empty defaults to write!')

    try:
      filename_path = self.WriteJsonFile(
          self.DEFAULT_DOMAIN_FILE_NAME,
          {'apps_domain': apps_domain, 'customer_id': customer_id},
          work_dir=False, overwrite_ok=overwrite_ok)
    except admin_api_tool_errors.AdminAPIToolError as e:
      log_utils.LogError('Unable to write defaults file (%s).' % e)
      sys.exit(1)
    return filename_path

# Singleton global for access throughout all modules.
FILE_MANAGER = FileManager()
