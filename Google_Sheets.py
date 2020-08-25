from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
import pickle
import pandas as pd

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1rmJVnfWvVe3tSnFrXpExv4XGbIN3syZO12dGBeoAf-w"

def update_cell(spreadsheet_id, cell, value):
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server()
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    service = build("sheets", "v4", credentials=creds)
    
    body = {"values": [[value]]}
    
    return service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=cell, body=body, valueInputOption="USER_ENTERED").execute()

def get_google_sheet(spreadsheet_id, range_name):
    """ Retrieve sheet data using OAuth credentials and Google Python API. """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    service = build("sheets", "v4", credentials=creds)

    return (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_name)
        .execute()
    )
    
def append_data(spreadsheet_id, range_name, values, insertDataOption = "INSERT_ROWS"):
    creds = None
    
    if insertDataOption != "INSERT_ROWS":
        insertDataOption = "OVERWRITE"
    
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server()
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    service = build("sheets", "v4", credentials=creds)

    request = (
        service.spreadsheets()
        .values()
        .append(spreadsheetId=spreadsheet_id, range=range_name, valueInputOption="USER_ENTERED", insertDataOption=insertDataOption, body=values)
    )
    
    response = request.execute()

def gsheet2df(gsheet):
    """ Converts Google sheet data to a Pandas DataFrame.
    Note: This script assumes that your data contains a header file on the first row!
    Also note that the Google API returns 'none' from empty cells - in order for the code
    below to work, you'll need to make sure your sheet doesn't contain empty cells,
    or update the code to account for such instances.
    """
    header = gsheet.get('values', [])[0]   # Assumes first line is header!
    values = gsheet.get('values', [])[1:]  # Everything else is data.
    if not values:
        print('No data found.')
    else:
        all_data = []
        for col_id, col_name in enumerate(header):
            column_data = []
            for row in values:
                try: datapoint = row[col_id]
                except: datapoint = ""
                column_data.append(datapoint)
            ds = pd.Series(data=column_data, name=col_name)
            all_data.append(ds)
        df = pd.concat(all_data, axis=1)
        return df
    
def df_to_sheet(sheet_id, range_name, df, dimension="COLUMNS"):
    values = []
    for column in df.columns:
        col_values = df[column].to_list()
        values.append(col_values)
    body = {'majorDimension': f'{dimension}', 'values': values}
    append_data(sheet_id, range_name, body)