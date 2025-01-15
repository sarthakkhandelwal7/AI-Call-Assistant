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
        self.credentials = self._get_credentials()
        self.service = build('calendar', 'v3', credentials=self.credentials) if self.credentials else None
        self.user_timezone = self._get_user_timezone() if self.service else 'UTC'

    def _get_credentials(self) -> Credentials:
        """Get and refresh Google credentials"""
        try:
            with open('backend/credentials/credentials.json', 'r') as f:
                credentials_dict = json.load(f)
                return Credentials.from_authorized_user_info(credentials_dict, self.SCOPES)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def _get_user_timezone(self) -> str:
        """Get user's timezone from their primary calendar"""
        try:
            calendar = self.service.calendars().get(calendarId='primary').execute()
            return calendar.get('timeZone', 'UTC')
        except HttpError as error:
            print(f'Error fetching timezone: {error}')
            return 'UTC'

    def get_todays_events(self) -> List[dict]:
        """Get today's calendar events"""
        if not self.service:
            return []
            
        # Get the timezone-aware datetime objects for start and end of today
        timezone = pytz.timezone(self.user_timezone)
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
            
            events = events_result.get('items', [])
            events_resp = f"The current date and time is {now.strftime('%Y-%m-%d %H:%M:%S')} and the timezone is {self.user_timezone}. Here are the events for today: "
            events_str = ""
            for event in events:
                event_start = event.get('start', {}).get('dateTime', 'No start time')
                event_end = event.get('end', {}).get('dateTime', 'No end time')
                if event_start and event_end:  # Make sure we have valid datetime strings
                    # Convert ISO format strings to datetime objects
                    start_dt = datetime.datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                    end_dt = datetime.datetime.fromisoformat(event_end.replace('Z', '+00:00'))
                    
                    # Now compare with datetime objects
                    if start_dt <= now <= end_dt:
                        events_str += f"\n{event_start} - {event_end}"
            
            if events_str == "":
                return "No events found for today."
            else:
                return events_resp + events_str
                
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []