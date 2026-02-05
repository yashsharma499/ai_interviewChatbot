from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import os
import smtplib
from email.mime.text import MIMEText
import time

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.db.session import SessionLocal
from app.db.models import Candidate, Interviewer


TOOL_NAME = "notification_tool"


class NotificationInput(BaseModel):
    candidate_id: int = Field(..., gt=0)
    interviewer_id: int = Field(..., gt=0)
    scheduled_time_utc: str = Field(..., min_length=1)

    @field_validator("scheduled_time_utc")
    @classmethod
    def validate_datetime(cls, v: str) -> str:
        datetime.fromisoformat(v)
        return v


class ToolTrace(BaseModel):
    tool_name: str
    trace_id: str
    started_at: str
    finished_at: str
    status: str
    input: Dict[str, Any]


class NotificationOutput(BaseModel):
    success: bool
    candidate_email: Optional[str] = None
    interviewer_email: Optional[str] = None
    error: Optional[str] = None
    trace: ToolTrace


def _send_email(to_email: str, subject: str, body: str):
    host = os.getenv("MAILTRAP_HOST", "sandbox.smtp.mailtrap.io")
    port = int(os.getenv("MAILTRAP_PORT", "2525"))
    username = os.getenv("MAILTRAP_USERNAME")
    password = os.getenv("MAILTRAP_PASSWORD")
    from_email = os.getenv("MAILTRAP_FROM", "no-reply@test.local")

    if not username or not password:
        raise RuntimeError("Mailtrap credentials not configured")

    msg = MIMEText(body)
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    with smtplib.SMTP(host, port, timeout=10) as server:
        server.starttls()
        server.login(username, password)
        server.send_message(msg)


def notification_tool(payload: Dict[str, Any]) -> Dict[str, Any]:

    trace_id = str(uuid.uuid4())
    started_at = datetime.utcnow().isoformat()

    safe_input = dict(payload or {})

    try:
        data = NotificationInput.model_validate(safe_input)
    except ValidationError:
        finished_at = datetime.utcnow().isoformat()

        return NotificationOutput(
            success=False,
            error="Invalid input payload",
            trace=ToolTrace(
                tool_name=TOOL_NAME,
                trace_id=trace_id,
                started_at=started_at,
                finished_at=finished_at,
                status="validation_error",
                input=safe_input
            )
        ).model_dump()

    db = SessionLocal()

    try:
        candidate = (
            db.query(Candidate)
            .filter(Candidate.id == data.candidate_id)
            .first()
        )

        interviewer = (
            db.query(Interviewer)
            .filter(Interviewer.id == data.interviewer_id)
            .first()
        )

        if not candidate or not interviewer:
            finished_at = datetime.utcnow().isoformat()

            return NotificationOutput(
                success=False,
                error="User not found",
                trace=ToolTrace(
                    tool_name=TOOL_NAME,
                    trace_id=trace_id,
                    started_at=started_at,
                    finished_at=finished_at,
                    status="not_found",
                    input=safe_input
                )
            ).model_dump()

        subject = "Interview Scheduled"
        body = (
            f"Interview scheduled at {data.scheduled_time_utc} UTC\n\n"
            f"Candidate: {candidate.email}\n"
            f"Interviewer: {interviewer.email}\n"
        )

        
        _send_email(candidate.email, subject, body)
        
        finished_at = datetime.utcnow().isoformat()

        return NotificationOutput(
            success=True,
            candidate_email=candidate.email,
            interviewer_email=interviewer.email,
            trace=ToolTrace(
                tool_name=TOOL_NAME,
                trace_id=trace_id,
                started_at=started_at,
                finished_at=finished_at,
                status="success",
                input=safe_input
            )
        ).model_dump()

    except Exception as e:
        print("NOTIFICATION ERROR:", repr(e))
        finished_at = datetime.utcnow().isoformat()

        return NotificationOutput(
            success=False,
            error=str(e),
            trace=ToolTrace(
                tool_name=TOOL_NAME,
                trace_id=trace_id,
                started_at=started_at,
                finished_at=finished_at,
                status="runtime_error",
                input=safe_input
            )
        ).model_dump()

    finally:
        db.close()
