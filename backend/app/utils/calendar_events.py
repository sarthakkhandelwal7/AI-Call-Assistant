from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import datetime
import pytz
import os
from typing import Optional, Union
from app.models.user import User


async def get_calendar_events(user: User) -> Union[str, list]:
    """
    Get today's calendar events using user's stored credentials and timezone
    
    Args:
        user: User object containing refresh_token and timezone
        
    Returns:
        str: Formatted string of today's events or "No events found" message
        list: Empty list in case of error
    """
    if not user.refresh_token or not user.calendar_connected:
        return "Calendar is not connected"
        
    try:
        # Create credentials from stored user data
        credentials = Credentials.from_authorized_user_info({
            'refresh_token': user.refresh_token,
            'client_id': os.getenv("GOOGLE_CLIENT_ID"),
            'client_secret': os.getenv("GOOGLE_CLIENT_SECRET"),
            'scopes': ["https://www.googleapis.com/auth/calendar.events"]
        })

        # Build service
        service = build('calendar', 'v3', credentials=credentials)
        
        # Use stored timezone from user model
        timezone = pytz.timezone(user.timezone)
        now = datetime.datetime.now(timezone)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + datetime.timedelta(days=1)

        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        events_resp = f"The current date and time is {now.strftime('%Y-%m-%d %H:%M:%S')} and the timezone is {user.timezone}. Here are the events for today: "
        
        events_str = ""
        for event in events:
            event_start = event.get('start', {}).get('dateTime', 'No start time')
            event_end = event.get('end', {}).get('dateTime', 'No end time')
            if event_start and event_end:
                # Convert to timezone-aware datetime objects
                start_dt = datetime.datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                end_dt = datetime.datetime.fromisoformat(event_end.replace('Z', '+00:00'))
                
                if start_dt <= now <= end_dt:
                    # Format event times in user's timezone
                    start_local = start_dt.astimezone(timezone)
                    end_local = end_dt.astimezone(timezone)
                    events_str += f"\n{start_local.strftime('%H:%M')} - {end_local.strftime('%H:%M')}: {event.get('summary', 'No title')}"
        
        return events_resp + events_str if events_str else "No events found for today."
                
    except Exception as e:
        print(f"Error fetching calendar events: {str(e)}")
        return []