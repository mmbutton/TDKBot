from __future__ import print_function
import csv
from hero.hero import Hero
from pathlib import Path


import os
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def get_all_heros_from_api():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    tokenJsonPath = Path(__file__).parent / '../../token.json'
    if os.path.exists(tokenJsonPath):
        creds = Credentials.from_authorized_user_file(tokenJsonPath, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                Path(__file__).parent / '../../credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(tokenJsonPath, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=os.getenv('GOOGLE_SPREADHSEET_ID'),
                                    range='A:AA').execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return
        
        return list(map(lambda x: Hero(x), values[1:]))
    except HttpError as err:
        print(err)

# Deprecated. I'm keeping this here in case others want to run the bot using CSV files due to not having access to my Google sheet.
def _get_all_heros_from_csv():
    heros = []
    # CSV Import
    with open(Path(__file__).parent / '../../resources/hero_attr_stats.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            heros.append(Hero(row))
    return heros
