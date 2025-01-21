from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import datetime
import os
import pickle
from typing import List, Dict
import logging

logger = logging.getLogger('dayplanner')

SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendarService:
    def __init__(self):
        self.service = self._get_calendar_service()

        # Verify permissions
        try:
            calendar_list = self.service.calendarList().list().execute()
            logger.info("✅ Successfully connected to Google Calendar")
            logger.info(f"📅 Primary Calendar ID: {calendar_list['items'][0]['id']}")
        except Exception as e:
            logger.error("❌ Error accessing Google Calendar:")
            logger.error(str(e))
            raise

    def _get_calendar_service(self):
        """Initialize and return the Google Calendar service."""
        creds = None
        # Look for existing token.pickle file
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        # If credentials are invalid or don't exist, try to refresh or create new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None
            
            if not creds:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                except FileNotFoundError:
                    raise FileNotFoundError(
                        "credentials.json not found in day_planner directory. "
                        "Please ensure you have downloaded your OAuth credentials file from Google Cloud Console."
                    )

            # Save the credentials for future use
            with open('day_planner/token.pickle', 'wb') as token:
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

    def create_event(self, summary, start_time, end_time, description=None):
        """Create a new calendar event."""
        logger.info(f"\n🔍 Attempting to create event: {summary}")
        logger.info(f"Start: {start_time}")
        logger.info(f"End: {end_time}")
        
        event = {
            'summary': f"🎯 {summary} ⚡️",
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/Los_Angeles',
            },
            'reminders': {
                'useDefault': True
            },
        }

        try:
            response = self.service.events().insert(calendarId='primary', body=event).execute()
            logger.info(f"✅ Successfully created event:")
            logger.info(f"  ID: {response.get('id')}")
            logger.info(f"  Link: {response.get('htmlLink')}")
            return response
        except Exception as e:
            logger.error(f"❌ Error creating calendar event: {str(e)}")
            logger.error(f"Full error details: {type(e).__name__}")
            raise