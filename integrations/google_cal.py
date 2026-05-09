import logging
import os
import pickle
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger('groot.google_cal')

SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendar:
    def __init__(self, config: dict):
        self._creds_file = config['google']['credentials_file']
        self._token_file = config['google'].get('token_file', 'google_token.pkl')
        self.service = self._auth()

    def _auth(self):
        creds = None
        if os.path.exists(self._token_file):
            with open(self._token_file, 'rb') as f:
                creds = pickle.load(f)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self._creds_file, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self._token_file, 'wb') as f:
                pickle.dump(creds, f)
        return build('calendar', 'v3', credentials=creds)

    def get_events(self, start: datetime, end: datetime, max_results: int = 15) -> list:
        result = self.service.events().list(
            calendarId='primary',
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime',
        ).execute()
        events = []
        for e in result.get('items', []):
            events.append({
                'id': e['id'],
                'title': e.get('summary', 'Untitled'),
                'start': e['start'].get('dateTime', e['start'].get('date')),
                'end': e['end'].get('dateTime', e['end'].get('date')),
                'location': e.get('location', ''),
                'source': 'google',
            })
        return events

    def create_event(self, title: str, start: datetime, end: datetime,
                     description: str = '', location: str = '') -> dict:
        body = {
            'summary': title,
            'description': description,
            'location': location,
            'start': {'dateTime': start.isoformat()},
            'end': {'dateTime': end.isoformat()},
        }
        result = self.service.events().insert(calendarId='primary', body=body).execute()
        return {'id': result['id'], 'title': title}
