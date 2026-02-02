from typing import Dict, Any, Optional
from datetime import datetime
import uuid

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
            candidate_email=None,
            interviewer_email=None,
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
                candidate_email=None,
                interviewer_email=None,
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

        message = (
            f"Interview scheduled at {data.scheduled_time_utc} UTC "
            f"between {candidate.email} and {interviewer.email}"
        )

        print("[NOTIFICATION]", message)

        finished_at = datetime.utcnow().isoformat()

        return NotificationOutput(
            success=True,
            candidate_email=candidate.email,
            interviewer_email=interviewer.email,
            error=None,
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
        finished_at = datetime.utcnow().isoformat()

        return NotificationOutput(
            success=False,
            candidate_email=None,
            interviewer_email=None,
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
