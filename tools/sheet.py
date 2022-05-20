from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

import os.path
import pickle
import pandas as pd
import json
import logging
import time

from errors.sheets_errors import *

try:
    from passwords import CREDS
except: # pragma: no cover
    CREDS = dict()
    CREDS["type"] = os.environ.get('GOOGLE_TYPE')
    CREDS["project_id"] = os.environ.get('GOOGLE_PROJECT_ID')
    CREDS["private_key_id"] = os.environ.get('GOOGLE_PRIVATE_KEY_ID')
    CREDS["private_key"] = os.environ.get('GOOGLE_PRIVATE_KEY').replace("\\n", "\n")
    CREDS["client_email"] = os.environ.get('GOOGLE_CLIENT_EMAIL')
    CREDS["client_id"] = os.environ.get('GOOGLE_CLIENT_ID')
    CREDS["auth_uri"] = os.environ.get('GOOGLE_AUTH_URI')
    CREDS["token_uri"] = os.environ.get('GOOGLE_TOKEN_URI')
    CREDS["auth_provider_x509_cert_url"] = os.environ.get('GOOGLE_AUTH_PROVIDER')
    CREDS["client_x509_cert_url"] = os.environ.get('GOOGLE_CLIENT_URL')
    

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
TOKEN_PATH = '\\'.join(os.getcwd().split('\\')[:-1]) + "\\token.pickle"

logger = logging.getLogger(__name__)


def get_creds():
    creds = service_account.Credentials.from_service_account_info(CREDS)
    return build("sheets", "v4", credentials = creds)

    # creds = None

    # creds_json = json.loads(CREDS, strict=False)

    # with open("creds.json", "w") as fp:
    #     json.dump(creds_json, fp)

    # creds = ServiceAccountCredentials.from_json(creds_json)

    # # creds = ServiceAccountCredentials.from_json_keyfile_name()
    
    # # creds = service_account.Credentials.from_service_account_file(
    # #     "creds.json", scopes=SCOPES)

    # os.remove(os.path.abspath("creds.json"))
    
    # return build("sheets", "v4", credentials=creds)

    # # if os.path.exists(TOKEN_PATH):
    # #     with open(TOKEN_PATH, 'rb') as token:
    # #         creds = pickle.load(token)

    # # if not creds or not creds.valid:
    # #     logger.warning("Sheet creds invalid or missing")
    # #     if creds and creds.expired and creds.refresh_token:
    # #         creds.refresh(Request())
    # #     else:
    # #         flow = InstalledAppFlow.from_client_config(json.loads(CREDS), SCOPES)
    # #         creds = flow.run_local_server()

    # #     with open(TOKEN_PATH, 'wb') as token:
    # #         pickle.dump(creds, token)

    # # return build("sheets", "v4", credentials=creds)


class Sheet:
    def __init__(self, sheet_id, refresh_cooldown=30):
        self.service = get_creds()
        self.sheet_id = sheet_id
        self.ranges = {}
        self.last_refreshed = time.time()
        self.cooldown = refresh_cooldown

    def get(self, data_range: str) -> dict:
        """
        Gets cell values over the given range

        Parameters
        ----------
        data_range : str
            Sheet range to get data from, such as 'Sheet1!A1:B2'.

        Returns
        -------
        gsheet : dict
            Contains majorDimension, range, and cell values.

        """
        self.ensure_recent(self.cooldown)
        gsheet = self.ranges.get(data_range)

        if not gsheet:
            try:
                gsheet = self.service.spreadsheets().values().get(
                    spreadsheetId=self.sheet_id, range=data_range).execute()
                self.ranges[data_range] = gsheet
                return gsheet
            except HttpError as error:
                if "permission" in error.error_details:
                    raise NoPermissionError("You do not have permission to access this sheet", self.sheet_id)
                else:
                    raise GetSheetError("Couldn't get values from sheet", self.sheet_id, data_range)
        else:
            return gsheet

    def to_df(self, data_range: str) -> pd.DataFrame:
        """
        Converts sheet values to dataframe

        Parameters
        ----------
        data_range : str
            Sheet range to get data from, such as 'Sheet1!A1:B2'.

        Returns
        -------
        df : pd.DataFrame
            Dataframe of specified range.

        """
        self.ensure_recent(self.cooldown)
        gsheet = self.ranges.get(data_range)

        if not gsheet:
            gsheet = self.get(data_range)

        try:
            # Assumes first line is header!
            header = gsheet.get('values', [])[0]
            values = gsheet.get('values', [])[1:]  # Everything else is data.
        except AttributeError as error:
            raise SheetToDfError("Error converting range to df", self.sheet_id, data_range)
        if not values:
            raise SheetToDfError("Error converting range to df", self.sheet_id, data_range)
        else:
            all_data = []
            for col_id, col_name in enumerate(header):
                column_data = []
                for row in values:
                    if col_id >= len(row):
                        datapoint = ""
                        column_data.append(datapoint)
                        continue
                    try:
                        datapoint = row[col_id]
                    except:
                        datapoint = ""
                    column_data.append(datapoint)
                ds = pd.Series(data=column_data, name=col_name)
                all_data.append(ds)
            df = pd.concat(all_data, axis=1)
            return df

    def update_cell(self, cell: str, value) -> dict:
        """
        Changes the value of a single cell

        Parameters
        ----------
        cell : str
            1-cell sheet range, such as 'Sheet1!A1'.
        value
            Value to put in the cell.

        Returns
        -------
        response : dict.
            Google API response.

        """
        body = {"values": [[value]]}
        try:
            return self.service.spreadsheets().values().update(spreadsheetId=self.sheet_id, range=cell, body=body, valueInputOption="USER_ENTERED").execute()
        except Exception as error:
            raise UpdateCellError("Couldn't update cell", self.sheet_id, cell)

    def append(self, data_range: str, values: list, insertDataOption: str = "INSERT_ROWS", majorDimension: str = "ROWS") -> dict:
        """
        Appends list(s) of values to the sheet

        Parameters
        ----------
        data_range : str
            Sheet range to append data to, such as 'Sheet1!A1:B2'.
        values : list
            1- or 2-dimensional array of values to append.
        insertDataOption : str, optional
            Google API insertDataOption. The default is "INSERT_ROWS".
        majorDimension : str, optional
            Google API majorDimension. The default is "COLUMNS".

        Returns
        -------
        response : dict
            Google API response.

        """
        try:
            body = {'majorDimension': majorDimension, 'values': values}
            return self.service.spreadsheets().values().append(spreadsheetId=self.sheet_id, range=data_range, valueInputOption="USER_ENTERED", insertDataOption=insertDataOption, body=body).execute()
        except HttpError as error:
                if "permission" in error.error_details:
                    raise NoPermissionError("You do not have permission to access this sheet", self.sheet_id)
                else:
                    raise AppendError("Couldn't append values", self.sheet_id, data_range) 

    def clear(self, data_range: str) -> dict:
        """
        Clears range in spreadsheet of all values

        Parameters
        ----------
        data_range : str
            Sheet range to clear, such as 'Sheet1!A1:B2'.

        Returns
        -------
        response : dict
            Google API response.

        """
        try:
            return self.service.spreadsheets().values().clear(spreadsheetId=self.sheet_id, range=data_range, body={}).execute()
        except HttpError as error:
            raise ClearValuesError("Couldn't clear values", self.sheet_id, data_range)

    def refresh(self):
        self.ranges = {}
        self.last_refreshed = time.time()

    def ensure_recent(self, minutes=10):
        if (time.time() - self.last_refreshed) > (60*minutes):
            self.refresh()

    def push_df(self, range: str, df: pd.DataFrame, dimension: str = "COLUMNS") -> dict:
        """
        Appends values in a dataframe to the specified range

        Parameters
        ----------
        sheet_id : str
            Spreadsheet ID.
        range_name : str
            Sheet range to append to, such as 'Sheet1!A1:B2'.
        df : pd.DataFrame
            Dataframe to append.
        dimension : str, optional
            Major Dimension of the dataframe. The default is "COLUMNS".

        Returns
        -------
        response : dict
            Google API response.

        """
        values = []
        for column in df.columns:
            col_values = df[column].to_list()
            values.append(col_values)
        try:
            response = self.append(range, values, majorDimension=dimension)
            return response
        except Exception as error:
            raise PushDfError("Couldn't push dataframe to sheet", self.sheet_id, range, df)
        # except AppendError:
        #     raise PushDfError("Couldn't push df to sheet, most likely because of an invalid range")
        # except NoPermissionError:
        #     raise PushDfError("You don't have access to this sheet")
