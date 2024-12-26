import base64
import os
from email.message import EmailMessage

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/calendar',
          'https://www.googleapis.com/auth/gmail.send']

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
credentials_path = os.path.join(project_root, 'credentials.json')
creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=SCOPES)

service_calendar = build('calendar', 'v3', credentials=creds)
service_gmail = build('gmail', 'v1', credentials=creds)


def schedule_meeting(start_time, end_time, summary, description, attendees):
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time,
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'America/New_York',
        },
        'attendees': [{'email': attendee} for attendee in attendees],
    }
    event = service_calendar.events().insert(calendarId='primary', body=event).execute()
    print(f'Meeting created: {event.get("htmlLink")}')
    return event


def create_message(sender, to, subject, message_text):
    message = EmailMessage()
    message.set_content(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}


def send_message(user_id, message):
    try:
        sent_message = service_gmail \
            .users().messages() \
            .send(userId=user_id, body=message) \
            .execute()
        print('Message Id: %s' % sent_message['id'])
        return sent_message
    except HttpError as error:
        print('An error occurred: %s' % error)
        sent_message = None
        return sent_message


def send_email(to, subject, message_text):
    message = create_message('me', to, subject, message_text)
    send_message('me', message)


if __name__ == '__main__':
    print('This is a utility module. Import this module to use the functions defined in it.')
