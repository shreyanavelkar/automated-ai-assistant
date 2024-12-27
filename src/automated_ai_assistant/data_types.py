from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr


class MeetingDetails(BaseModel):
    start_time: datetime
    end_time: datetime
    summary: str
    description: str
    attendees: List[EmailStr]


class ReminderDetails(BaseModel):
    title: str
    description: str
    reminder_time: datetime


class EmailDetails(BaseModel):
    subject: str
    body: str
    recipients: List[EmailStr]
