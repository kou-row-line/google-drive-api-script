# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START drive_quickstart]
from __future__ import print_function
import re
import csv
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

def main():
    global service
    service = build('drive', 'v3', credentials=read_credentials())

    global writer
    f = open('external_shared_files.csv', 'w', encoding="utf_8_sig")
    writer = csv.writer(f, lineterminator='\n')

    root_file_id = 'root_file_id'
    search_for_external_shared_files(root_file_id)

def read_credentials():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

def search_for_external_shared_files(file_id, directory = '', next_page_token = None):
    results = fetch_files(file_id, next_page_token)
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        for item in items:
            if is_external_sharing(item):
                writer.writerow([item['id'], directory, item['name'], item['mimeType']])

            if is_folder(item):
                print('is folder.')
                subdirectory = directory + item['name'] + '/'
                search_for_external_shared_files(item['id'], subdirectory)

    if results.get('nextPageToken', None):
        print('Next Page.')
        search_for_external_shared_files(file_id, directory, results['nextPageToken'])

def fetch_files(file_id, next_page_token = None):
    return service.files().list(
        q="'{0}' in parents and trashed = false".format(file_id),
        fields="nextPageToken, files(id, name, mimeType, permissions(type, emailAddress, domain))",
        pageSize=10,
        pageToken=next_page_token).execute()

def is_folder(item):
    return item['mimeType'] == 'application/vnd.google-apps.folder'

def is_external_sharing(item):
    for _permission in item['permissions']:
        if _permission['type'] == 'anyone':
            return True
        elif _permission['type'] == 'domain':
            if not _permission['domain'] == 'gmail.com':
                return True
            else:
                continue
        elif _permission['type'] in ['user', 'group'] :
            if not re.match('.*{0}$'.format('@gmail.com'), _permission['emailAddress']):
                return True
            else:
                continue

    return False

if __name__ == '__main__':
    main()
# [END drive_quickstart]
