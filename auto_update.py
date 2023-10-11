# Functions for automatic updates

import requests
import re
import time
import os
import hashlib
import zipfile

# Check two version strings and determine if the left argument represents a "greater" version than the right
def leftVersionGreater(left_version, right_version):
    left_nums = [int(a) for a in left_version.split('.')]
    right_nums = [int(a) for a in right_version.split('.')]
    
    # Pad the smalles list with 0s case lists are not of equal length.
    diff = len(left_nums) - len(right_nums)
    if len(left_nums) > len(right_nums):
        right_nums = right_nums + [0]*diff
    
    diff = len(right_nums) - len(left_nums)
    if len(right_nums) > len(left_nums):
        left_nums = left_nums + [0]*diff
    
    for i in range(0, len(right_nums)):
        if left_nums[i] > right_nums[i]:
            return True
        elif left_nums[i] < right_nums[i]:
            return False
    
    # At this point they have to represent the same version, hence the left version is not greater.
    return False

# Reads a string containing a line of the format
# `# v. 00.00.0.00`. Where the 0s can be any numbers. It filters the string
# for only these numbers and outputs the first occurrance as a string.
def getVersionString(file_string):
    m = re.search(r"\n?#\s+[vV]\.\s+([0-9\.]+)\n?", file_string)
    if m:
        return m.group(1)
    else:
        return ""

# Uses the request module to get the text content from a URL.
def getUrlContent(url):
    res = requests.get(url)
    if res.status_code != 200:
        raise Exception("ERROR in getUrlContent:\nReceived code '" + res.status_code + "'\nwhen attempting to get content at URL:\n\"" + url + "\"")
    return res.text

# Reads the file with the input file in the current folder and returns the number of
# days between now and the timestamp given in the file.
def daysSinceUpdate(fn):
    with open(fn, 'r') as f:
        fn_time_str = f.read()
    fn_time = float(fn_time_str)
    return int((round(time.time()) - fn_time)//(24*60*60))

# This functions takes in settings_dict and reads the time of
# the last update from the file specified in the last-check-fn key. Then it compares
# the amount of days elapsed to the number of days specified by the check-interval
# key. If the days are above the interval, then it queries the current file version
# of the repository, and if the repository file version is greater than the existing
# file, it returns true, if not it returns false.
def checkForUpdate(settings_dict):

    # Check if the sufficient time has passed for an update.
    days_since_check = daysSinceUpdate(settings_dict['last-check-fn'])
    if days_since_check <= settings_dict['check-interval']:
        return False
    
    # Get the current repo version
    repo_text = getUrlContent(settings_dict['remote-url'])
    repo_version = getVersionString(repo_text)
    
    print("Days since last check: " + str(days_since_check))
    print("Most up-to-day version: " + repo_version)
    
    # Get the existing file version
    with open("sentinel_alerts.py", 'r') as f:
        file_text = f.read()
    existing_version = getVersionString(file_text)
    
    print("Existing version: " + existing_version)
    
    # Set current timestamp
    with open(settings_dict['last-check-fn'], 'w') as f:
        print(round(time.time()), file=f, end='')
    
    return leftVersionGreater(repo_version, existing_version)

# Downloads a file from a URL and saves it is as a file specified by the path. If the
# path already exists it appends ' (n)' where 'n' is the next available digit to the
# filename before the last .
def downloadBytes(url, file_path, overwrite=False):

    # Make sure file paths use backward slashes
    file_path = os.path.normpath(file_path)

    # Download file from URL
    res = requests.get(url)
    if res.status_code != 200:
        raise Exception("ERROR in downloadBytes\nFailed to download content from\n" + url)
    
    # Check if file already exists
    orig_file_path = file_path
    if os.path.isfile(file_path) and not overwrite:
        n = 1
        m = re.search(r'(.*\\)?([^\\]+)$', file_path)
        if m.group(1) == None:
            folder = ""
        else:
            folder = m.group(1)
        file_name = m.group(2)
        # Assuming there is a . in the file name
        m = re.search(r'(.*)(\.[^\.]*)$', file_name)
        if m:
            pre_part = m.group(1)
            post_part = m.group(2)
        else:
            pre_part = file_name
            post_part = ""
        file_path = folder + pre_part + f" ({n})" + post_part
        while os.path.isfile(file_path):
            n += 1
            file_path = folder + pre_part + f" ({n})" + post_part
        print("Warning: file '" + orig_file_path + "' exists. Creating '" + file_path + "'.")
    
    # Now we can be sure that either file_path points to a new file, or we are allowed
    # to overwrite whatever exists there.
    with open(file_path, 'wb') as f:
        f.write(res.content)
    
    return file_path

# Downloads a .zip file from the supplied url and then extracts that zip file to the
# destination path.
def downloadAndExpandArchive(url, path, tmp_fn = "downloaded_archive.zip"):

    tmp_fn = downloadBytes(url, tmp_fn)
    
    with zipfile.ZipFile(tmp_fn, 'r') as zip_f:
        zip_f.extractall(path)
    
    os.remove(tmp_fn)
    
# Downloads a .zip file containing the repository and then extracts all files in the
# repository to the destination file.
def downloadRepoTo(url, dest_path, tmp_fn = "downloaded_archive.zip"):
    
    tmp_fn = downloadBytes(url, tmp_fn)
    
    with zipfile.ZipFile(tmp_fn, 'r') as zip_f:
    
        # Go through all files in the archive
        file_paths = zip_f.namelist()
        # Since this is an archive, everything is contained in a folder given by the first
        # entry.
        folder_name = file_paths[0]
        for file_path in file_paths[1:]:
            
            # Creating path to archive file relative to the first folder
            relative_path = file_path[len(folder_name):]
            dest_file_path = os.path.normpath(dest_path + "/" + relative_path)
            
            # Create necessary directories
            os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)
            
            # Extract file to destination
            with zip_f.open(file_path) as source, open(dest_file_path, 'wb') as target:
                target.write(source.read())
            
            print("Extracted: " + dest_file_path)
            
    
    os.remove(tmp_fn)

def update(settings_dict):
    
    # First we check if an update is needed.
    need_update = checkForUpdate(settings_dict)
    
    if need_update:
        # Get current directory
        script_directory = os.path.abspath('')
        print("Update needed. Downloading archive from '" + settings_dict['repo-url'] + "'")
        print("and extracting to '" + script_directory + "'")
        downloadRepoTo(settings_dict['repo-url'], script_directory)
        print("Successfully updated sentinel_alerts!")