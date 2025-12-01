"""
Gmail API client for reading emails from inbox and sent folder.
"""

import base64
import pickle
import os
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.config import settings
from src.db.models import EmailModel


class GmailClient:
    """Gmail API client for email retrieval."""

    def __init__(self):
        self.credentials_path = settings.gmail_credentials_path
        self.token_path = settings.gmail_token_path
        self.scopes = settings.gmail_scopes
        self.service = None

    def authenticate(self) -> None:
        """Authenticate with Gmail API using OAuth2."""
        creds = None

        # Load existing token
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        # Refresh or obtain new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path,
                    self.scopes
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for future use
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        # Build service
        self.service = build('gmail', 'v1', credentials=creds)

    def _decode_message_part(self, part: dict) -> str:
        """Decode message part data."""
        if 'data' in part.get('body', {}):
            data = part['body']['data']
            return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        return ""

    def _extract_body(self, payload: dict) -> tuple[str, str]:
        """
        Extract text and HTML body from message payload.

        Returns:
            (text_body, html_body)
        """
        text_body = ""
        html_body = ""

        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')

                if mime_type == 'text/plain':
                    text_body += self._decode_message_part(part)
                elif mime_type == 'text/html':
                    html_body += self._decode_message_part(part)
                elif 'parts' in part:
                    # Recursive for nested parts (multipart/alternative)
                    sub_text, sub_html = self._extract_body(part)
                    text_body += sub_text
                    html_body += sub_html
        else:
            # Single part message
            mime_type = payload.get('mimeType', '')
            if mime_type == 'text/plain':
                text_body = self._decode_message_part(payload)
            elif mime_type == 'text/html':
                html_body = self._decode_message_part(payload)

        return text_body, html_body

    def _extract_header(self, headers: List[dict], name: str) -> Optional[str]:
        """Extract header value by name."""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return None

    def _parse_email(self, message: dict) -> EmailModel:
        """Parse Gmail message into EmailModel."""
        headers = message['payload']['headers']

        # Extract headers
        subject = self._extract_header(headers, 'Subject')
        from_header = self._extract_header(headers, 'From') or ""
        to_header = self._extract_header(headers, 'To') or ""
        date_header = self._extract_header(headers, 'Date')

        # Parse sender
        sender_email = from_header
        sender_name = None
        if '<' in from_header and '>' in from_header:
            sender_name = from_header.split('<')[0].strip().strip('"')
            sender_email = from_header.split('<')[1].split('>')[0].strip()

        # Parse recipient
        recipient_email = to_header
        if '<' in to_header and '>' in to_header:
            recipient_email = to_header.split('<')[1].split('>')[0].strip()

        # Parse date
        received_at = datetime.now()
        if date_header:
            try:
                from email.utils import parsedate_to_datetime
                received_at = parsedate_to_datetime(date_header)
            except Exception:
                pass

        # Extract body
        text_body, html_body = self._extract_body(message['payload'])

        return EmailModel(
            gmail_id=message['id'],
            thread_id=message['threadId'],
            subject=subject,
            sender_email=sender_email,
            sender_name=sender_name,
            recipient_email=recipient_email,
            received_at=received_at,
            body_text=text_body or None,
            body_html=html_body or None,
        )

    async def get_messages(
        self,
        query: str = "",
        max_results: int = 50,
        label_ids: List[str] = None,
    ) -> List[EmailModel]:
        """
        Get messages from Gmail.

        Args:
            query: Gmail search query (e.g., "is:unread", "after:2025/01/01")
            max_results: Maximum number of messages to retrieve
            label_ids: Filter by label IDs (e.g., ['INBOX'], ['SENT'])

        Returns:
            List of EmailModel objects
        """
        if not self.service:
            self.authenticate()

        try:
            # List messages
            list_params = {
                'userId': 'me',
                'maxResults': max_results,
            }

            if query:
                list_params['q'] = query

            if label_ids:
                list_params['labelIds'] = label_ids

            results = self.service.users().messages().list(**list_params).execute()
            messages = results.get('messages', [])

            # Fetch full message details
            emails = []
            for msg in messages:
                try:
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()

                    email = self._parse_email(message)
                    emails.append(email)

                except HttpError as e:
                    print(f"Error fetching message {msg['id']}: {e}")
                    continue

            return emails

        except HttpError as e:
            print(f"Gmail API error: {e}")
            return []

    async def get_inbox_messages(
        self,
        max_results: int = 50,
        only_unread: bool = False,
    ) -> List[EmailModel]:
        """Get messages from inbox."""
        query = "is:unread" if only_unread else ""
        return await self.get_messages(
            query=query,
            max_results=max_results,
            label_ids=['INBOX']
        )

    async def get_sent_messages(
        self,
        max_results: int = 50,
    ) -> List[EmailModel]:
        """Get sent messages."""
        return await self.get_messages(
            max_results=max_results,
            label_ids=['SENT']
        )

    async def get_messages_after_date(
        self,
        after_date: datetime,
        label_ids: List[str] = None,
        max_results: int = 100,
    ) -> List[EmailModel]:
        """Get messages received after a specific date."""
        # Format: after:YYYY/MM/DD
        date_str = after_date.strftime('%Y/%m/%d')
        query = f"after:{date_str}"

        return await self.get_messages(
            query=query,
            max_results=max_results,
            label_ids=label_ids
        )

    async def mark_as_read(self, gmail_id: str) -> bool:
        """Mark message as read."""
        if not self.service:
            self.authenticate()

        try:
            self.service.users().messages().modify(
                userId='me',
                id=gmail_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except HttpError as e:
            print(f"Error marking message as read: {e}")
            return False

    async def create_draft(self, to: str, subject: str, body: str, thread_id: Optional[str] = None) -> Optional[str]:
        """Create a draft email."""
        from email.mime.text import MIMEText
        import base64

        if not self.service:
            self.authenticate()

        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            body = {'message': {'raw': raw}}

            if thread_id:
                body['message']['threadId'] = thread_id

            draft = self.service.users().drafts().create(
                userId='me',
                body=body
            ).execute()

            return draft['id']
        except Exception as e:
            print(f"Error creating draft: {e}")
            return None
