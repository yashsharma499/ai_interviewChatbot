from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from pydantic import BaseModel, Field, ValidationError

from app.db.session import SessionLocal
from app.db.models import Interview


TOOL_NAME = "calendar_delete_tool"


class CalendarDeleteInput(BaseModel):
    interview_id: int = Field(..., gt=0)


class ToolTrace(BaseModel):
    tool_name: str
    trace_id: str
    started_at: str
    finished_at: str
    status: str
    input: Dict[str, Any]


class CalendarDeleteOutput(BaseModel):
    success: bool
    interview_id: Optional[int] = None
    error: Optional[str] = None
    trace: ToolTrace


def calendar_delete_tool(payload: Dict[str, Any]) -> Dict[str, Any]:

    trace_id = str(uuid.uuid4())
    started_at = datetime.utcnow().isoformat()

    safe_input = dict(payload or {})

    try:
        data = CalendarDeleteInput.model_validate(safe_input)
    except ValidationError:
        finished_at = datetime.utcnow().isoformat()

        return CalendarDeleteOutput(
            success=False,
            interview_id=None,
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

            return CalendarDeleteOutput(
                success=False,
                interview_id=None,
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

        interview.status = "cancelled"
        db.commit()

        finished_at = datetime.utcnow().isoformat()

        return CalendarDeleteOutput(
            success=True,
            interview_id=interview.id,
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

        return CalendarDeleteOutput(
            success=False,
            interview_id=None,
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
