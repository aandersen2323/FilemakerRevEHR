"""Google Sheets Integration for Monthly Report"""

import logging
from pathlib import Path
from typing import Optional, Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

class GoogleSheetsClient:
    def __init__(self, credentials_file: str, spreadsheet_id: str, sheet_name: str = 'Data'):
        self.credentials_file = Path(credentials_file)
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self._service = None

    @property
    def service(self):
        if self._service is None:
            if not self.credentials_file.exists():
                raise FileNotFoundError(f"Credentials not found: {self.credentials_file}")
            creds = Credentials.from_service_account_file(str(self.credentials_file), scopes=SCOPES)
            self._service = build('sheets', 'v4', credentials=creds)
        return self._service

    def get_all_data(self):
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id, range=f"'{self.sheet_name}'!A:Z").execute()
        return result.get('values', [])

    def find_row_by_period(self, year: int, month: str) -> Optional[int]:
        data = self.get_all_data()
        for i, row in enumerate(data, start=1):
            if len(row) >= 2:
                try:
                    if int(row[0]) == year and str(row[1]).strip() == month:
                        return i
                except: pass
        return None

    def append_row(self, row_data: list):
        body = {'values': [row_data]}
        return self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id, range=f"'{self.sheet_name}'!A:Z",
            valueInputOption='USER_ENTERED', insertDataOption='INSERT_ROWS', body=body).execute()

    def update_row(self, row_number: int, row_data: list):
        body = {'values': [row_data]}
        return self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id, range=f"'{self.sheet_name}'!A{row_number}:Z{row_number}",
            valueInputOption='USER_ENTERED', body=body).execute()

    def upsert_monthly_data(self, year: int, month: str, row_data: list):
        existing = self.find_row_by_period(year, month)
        if existing:
            return self.update_row(existing, row_data)
        return self.append_row(row_data)

    def verify_connection(self) -> bool:
        try:
            result = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            logger.info(f"Connected to: {result.get('properties', {}).get('title')}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
