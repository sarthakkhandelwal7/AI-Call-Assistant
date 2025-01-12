import datetime
import json
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz
from typing import List


class CalendarService:
    SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
    
    
    @classmethod
    def get_instance(cls) -> "CalendarService":
        return cls()
    
    def __init__(self, credentials_dict: dict = None):
        self.credentials_dict = credentials_dict
        self.credentials = self._get_credentials()
        self.service = build('calendar', 'v3', credentials=self.credentials) if self.credentials else None

    def _get_credentials(self) -> Credentials:
        """Get and refresh Google credentials"""
        try:
            with open('credentials/credentials.json', 'r') as f:
                credentials_dict = json.load(f)
                return Credentials.from_authorized_user_info(credentials_dict, self.SCOPES)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def get_todays_events(self) -> List[dict]:
        """Get today's calendar events"""
        if not self.service:
            return []
            
        # Get the timezone-aware datetime objects for start and end of today
        timezone = pytz.timezone('UTC')
        now = datetime.datetime.now(timezone)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + datetime.timedelta(days=1)

        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []