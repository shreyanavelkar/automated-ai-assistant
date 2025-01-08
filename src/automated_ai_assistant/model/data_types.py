from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, EmailStr


class EndUserMessage(BaseModel):
    content: str


class Intent(BaseModel):
    intent: str


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


class AgentEnum(str, Enum):
    SCHEDULE_MEETING = "schedule_meeting"
    SET_REMINDER = "set_reminder"
    SEND_EMAIL = "send_email"
