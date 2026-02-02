from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.db.session import SessionLocal
from app.db.models import Interview


TOOL_NAME = "calendar_update_tool"


class CalendarUpdateInput(BaseModel):
    interview_id: int = Field(..., gt=0)
    new_time_utc: str = Field(..., min_length=1)

    @field_validator("new_time_utc")
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


class CalendarUpdateOutput(BaseModel):
    success: bool
    interview_id: Optional[int] = None
    new_time_utc: Optional[str] = None
    error: Optional[str] = None
    trace: ToolTrace


def calendar_update_tool(payload: Dict[str, Any]) -> Dict[str, Any]:

    trace_id = str(uuid.uuid4())
    started_at = datetime.utcnow().isoformat()

    safe_input = dict(payload or {})

    try:
        data = CalendarUpdateInput.model_validate(safe_input)
    except ValidationError:
        finished_at = datetime.utcnow().isoformat()

        return CalendarUpdateOutput(
            success=False,
            interview_id=None,
            new_time_utc=None,
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
        interview = (
            db.query(Interview)
            .filter(Interview.id == data.interview_id)
            .first()
        )

        if not interview:
            finished_at = datetime.utcnow().isoformat()

            return CalendarUpdateOutput(
                success=False,
                interview_id=None,
                new_time_utc=None,
                error="Interview not found",
                trace=ToolTrace(
                    tool_name=TOOL_NAME,
                    trace_id=trace_id,
                    started_at=started_at,
                    finished_at=finished_at,
                    status="not_found",
                    input=safe_input
                )
            ).model_dump()

        new_time = datetime.fromisoformat(data.new_time_utc)

        interview.scheduled_time = new_time
        interview.status = "rescheduled"

        db.commit()
        db.refresh(interview)

        finished_at = datetime.utcnow().isoformat()

        return CalendarUpdateOutput(
            success=True,
            interview_id=interview.id,
            new_time_utc=interview.scheduled_time.isoformat(),
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
        db.rollback()
        finished_at = datetime.utcnow().isoformat()

        return CalendarUpdateOutput(
            success=False,
            interview_id=None,
            new_time_utc=None,
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
