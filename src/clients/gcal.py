"""Google Calendar client (fallback if TickTick sync doesn't work)."""

from datetime import datetime
from typing import Optional
import pickle
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.config import settings


class GoogleCalendarClient:
    """
    Google Calendar API client.

    Note: This is a fallback. TickTick natively syncs to Google Calendar,
    so we prefer creating events in TickTick and letting them sync automatically.
    Only use this if TickTick sync is disabled or broken.
    """

    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self):
        self.credentials_path = settings.gmail_credentials_path  # Reuse Gmail credentials
        self.token_path = "gcal_token.pickle"
        self.service = None

    def authenticate(self) -> None:
        """Authenticate with Google Calendar API."""
        creds = None

        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path,
                    self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('calendar', 'v3', credentials=creds)

    async def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: str = "",
        location: str = "",
    ) -> dict:
        """Create a calendar event."""
        if not self.service:
            self.authenticate()

        event = {
            'summary': title,
            'description': description,
            'location': location,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 60},
                    {'method': 'popup', 'minutes': 1440},  # 1 day
                ],
            },
        }

        result = self.service.events().insert(
            calendarId='primary',
            body=event
        ).execute()

        return result
