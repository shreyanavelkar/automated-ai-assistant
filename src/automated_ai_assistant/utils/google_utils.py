import logging
import os
import os.path
import pickle
from datetime import timedelta

from google.auth.transport import Request
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from automated_ai_assistant.model.data_types import MeetingDetails, ReminderDetails, EmailDetails

logging.basicConfig(level=logging.INFO)


class GoogleAPIInterface:
    """Interface for handling Google Calendar and Gmail operations."""

    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/calendar.readonly'
    ]
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    credentials_path = os.path.join(project_root, 'credentials.json')

    def __init__(self, credentials_path=credentials_path, token_path='token.pickle'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = None
        self.calendar_service = None
        self.gmail_service = None
        self._authenticate()

    def _authenticate(self):
        """Handle Google API authentication."""
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                # Explicitly specify local server parameters
                self.creds = flow.run_local_server(
                    port=8080,
                    prompt='consent',
                    access_type='offline',
                    include_granted_scopes='true'
                )

            with open(self.token_path, 'wb') as token:
                pickle.dump(self.creds, token)

        self.calendar_service = build('calendar', 'v3', credentials=self.creds)
        self.gmail_service = build('gmail', 'v1', credentials=self.creds)

    def schedule_meeting(self, meeting_details: MeetingDetails):
        """
        Schedule a meeting on Google Calendar.

        Args:
            meeting_details (MeetingDetails): Details of the meeting to schedule

        Returns:
            dict: Created event details
        """
        event = {
            'summary': meeting_details.summary,
            'description': meeting_details.description,
            'start': {
                'dateTime': meeting_details.start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': meeting_details.end_time.isoformat(),
                'timeZone': 'UTC',
            },
        }

        if meeting_details.attendees:
            event['attendees'] = [{'email': email} for email in meeting_details.attendees]

        try:
            event = self.calendar_service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all'
            ).execute()
            return event
        except Exception as e:
            raise Exception(f"Failed to schedule meeting: {str(e)}")

    def set_reminder(self, reminder_details: ReminderDetails):
        """
        Set a reminder on Google Calendar.

        Args:
            reminder_details: Details of the reminder to set
                title (str): Reminder title
                description (str): Reminder description
                reminder_time (datetime): When to send the reminder

        Returns:
            dict: Created reminder event
        """
        event = {
            'summary': reminder_details.title,
            'description': reminder_details.description,
            'start': {
                'dateTime': reminder_details.reminder_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': (reminder_details.reminder_time + timedelta(minutes=30)).isoformat(),
                'timeZone': 'UTC',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10},
                ]
            }
        }

        try:
            reminder = self.calendar_service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            return reminder
        except Exception as e:
            raise Exception(f"Failed to set reminder: {str(e)}")

    def send_email(self, email_details: EmailDetails):
        """
        Send an email using Gmail API.

        Args:
            email_details: Details of the email to send
                to (str): Recipient email address
                subject (str): Email subject
                body (str): Email body
        """
        from email.mime.text import MIMEText
        import base64

        message = MIMEText(email_details.body)
        message['to'] = email_details.recipients[0]
        message['subject'] = email_details.subject

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        try:
            email = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            return email
        except Exception as e:
            raise Exception(f"Failed to send email: {str(e)}")


def google_api_interface():
    return GoogleAPIInterface()


if __name__ == '__main__':
    print("Running Google API Interface")
