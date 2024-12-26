from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr


class MeetingDetails(BaseModel):
    start_time: datetime
    end_time: datetime
    summary: str
    description: str
    attendees: List[EmailStr]
