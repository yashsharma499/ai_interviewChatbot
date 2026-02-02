from typing import List, Dict, Any, Optional
from datetime import timedelta, datetime
import uuid

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.db.session import SessionLocal
from app.db.models import Interview


INTERVIEW_DURATION_MINUTES = 60
TOOL_NAME = "calendar_read_tool"


class CalendarReadInput(BaseModel):
    interviewer_id: int = Field(..., gt=0)


class BusySlot(BaseModel):
    start: str
    end: str

    @field_validator("start", "end")
    @classmethod
    def validate_iso_datetime(cls, v: str) -> str:
        datetime.fromisoformat(v)
        return v


class ToolTrace(BaseModel):
    tool_name: str
    trace_id: str
    started_at: str
    finished_at: str
    status: str
    input: Dict[str, Any]


class CalendarReadOutput(BaseModel):
    success: bool
    slots: Optional[List[BusySlot]] = None
    error: Optional[str] = None
    trace: ToolTrace


def calendar_read_tool(payload: Dict[str, Any]) -> Dict[str, Any]:

    trace_id = str(uuid.uuid4())
    started_at = datetime.utcnow().isoformat()

    safe_input = dict(payload or {})

    try:
        data = CalendarReadInput.model_validate(safe_input)
    except ValidationError:
        finished_at = datetime.utcnow().isoformat()

        return CalendarReadOutput(
            success=False,
            error="Invalid input payload",
            slots=None,
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
        interviews = (
            db.query(Interview)
            .filter(
                Interview.interviewer_id == data.interviewer_id,
                Interview.status != "cancelled"
            )
            .all()
        )

        slots: List[BusySlot] = []

        for interview in interviews:

            if not interview.scheduled_time:
                continue

            start_dt = interview.scheduled_time
            end_dt = start_dt + timedelta(minutes=INTERVIEW_DURATION_MINUTES)

            slots.append(
                BusySlot(
                    start=start_dt.isoformat(),
                    end=end_dt.isoformat()
                )
            )

        finished_at = datetime.utcnow().isoformat()

        return CalendarReadOutput(
            success=True,
            slots=slots,
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

        return CalendarReadOutput(
            success=False,
            slots=None,
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
