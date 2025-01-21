from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import datetime
import os
import pickle
from typing import List, Dict

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


class GoogleCalendarService:
    def __init__(self):
        self.service = self._get_calendar_service()

    def _get_calendar_service(self):
        """Initialize and return the Google Calendar service."""
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        return build('calendar', 'v3', credentials=creds)

    def get_events(self, date: datetime.date) -> List[Dict]:
        """Get calendar events for a specific date."""
        start_of_day = datetime.datetime.combine(date, datetime.time.min).isoformat() + 'Z'
        end_of_day = datetime.datetime.combine(date, datetime.time.max).isoformat() + 'Z'

        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        return self._format_events(events_result.get('items', []))

    def _format_events(self, events: List[Dict]) -> List[Dict]:
        """Format calendar events into a consistent structure."""
        formatted_events = []

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))

            start_time = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_time = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))

            formatted_events.append({
                'summary': event['summary'],
                'start': start_time.strftime('%I:%M%p').lstrip('0').lower(),
                'end': end_time.strftime('%I:%M%p').lstrip('0').lower(),
                'start_time': start_time,
                'end_time': end_time
            })

        return formatted_events