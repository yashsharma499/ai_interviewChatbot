from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any
import uuid

from pydantic import BaseModel, Field, ValidationError


TOOL_NAME = "timezone_tool"


SUPPORTED_FORMATS = [
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%d %b %Y %I:%M %p",
    "%d %B %Y %I:%M %p",
]


class TimezoneNormalizeInput(BaseModel):
    datetime_str: str = Field(..., min_length=1)
    timezone_str: str = Field(..., min_length=1)


class ToolTrace(BaseModel):
    tool_name: str
    trace_id: str
    started_at: str
    finished_at: str
    status: str
    input: Dict[str, Any]


class TimezoneNormalizeOutput(BaseModel):
    success: bool
    utc_datetime: Optional[str] = None
    timezone: Optional[str] = None
    error: Optional[str] = None
    trace: ToolTrace


def timezone_normalize_tool(payload: Dict[str, Any]) -> Dict[str, Any]:

    trace_id = str(uuid.uuid4())
    started_at = datetime.utcnow().isoformat()

    safe_input = dict(payload or {})

    try:
        data = TimezoneNormalizeInput.model_validate(safe_input)
    except ValidationError:
        finished_at = datetime.utcnow().isoformat()

        return TimezoneNormalizeOutput(
            success=False,
            utc_datetime=None,
            timezone=None,
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

    try:
        try:
            tz = ZoneInfo(data.timezone_str)
        except Exception:
            finished_at = datetime.utcnow().isoformat()

            return TimezoneNormalizeOutput(
                success=False,
                utc_datetime=None,
                timezone=None,
                error="invalid timezone",
                trace=ToolTrace(
                    tool_name=TOOL_NAME,
                    trace_id=trace_id,
                    started_at=started_at,
                    finished_at=finished_at,
                    status="invalid_timezone",
                    input=safe_input
                )
            ).model_dump()

        parsed_dt = None
        clean_dt = data.datetime_str.strip()

        for fmt in SUPPORTED_FORMATS:
            try:
                parsed_dt = datetime.strptime(clean_dt, fmt)
                break
            except ValueError:
                continue

        if not parsed_dt:
            finished_at = datetime.utcnow().isoformat()

            return TimezoneNormalizeOutput(
                success=False,
                utc_datetime=None,
                timezone=None,
                error="unsupported datetime format",
                trace=ToolTrace(
                    tool_name=TOOL_NAME,
                    trace_id=trace_id,
                    started_at=started_at,
                    finished_at=finished_at,
                    status="invalid_datetime_format",
                    input=safe_input
                )
            ).model_dump()

        local_dt = parsed_dt.replace(tzinfo=tz)
        utc_dt = local_dt.astimezone(ZoneInfo("UTC"))

        finished_at = datetime.utcnow().isoformat()

        return TimezoneNormalizeOutput(
            success=True,
            utc_datetime=utc_dt.replace(tzinfo=None).isoformat(),
            timezone=data.timezone_str,
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

        return TimezoneNormalizeOutput(
            success=False,
            utc_datetime=None,
            timezone=None,
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
