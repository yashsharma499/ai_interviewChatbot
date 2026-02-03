from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class InterviewCreate(BaseModel):
    candidate_name: str
    candidate_email: EmailStr
    preferred_datetime: str
    timezone: str

class InterviewResponse(BaseModel):
    interview_id: int
    scheduled_time_utc: datetime
    status: str

class ChatResponse(BaseModel):
    conversation_id: str
    reply: Optional[str] = None
    success: Optional[bool] = None
    interview_id: Optional[int] = None
    reason: Optional[str] = None
