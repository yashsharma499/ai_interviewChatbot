from typing import Dict, Any, List
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.tools.calendar_read_tool import calendar_read_tool
from app.tools.trace import tool_trace


WORK_START = time(4, 30)
WORK_END = time(12, 30)
BUFFER_MINUTES = 30

IST = ZoneInfo("Asia/Kolkata")


class AvailabilityAgent:

    name = "AvailabilityAgent"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:

        data = state.get("conversation_state", {})

        interviewer_id = data.get("interviewer_id")
        preferred_time = state.get("selected_time_utc") or data.get("preferred_datetime_utc")

        if not interviewer_id or not preferred_time:
            data["available"] = False
            data.pop("preferred_datetime_utc", None)
            data.pop("selected_time_utc", None)

            return {
                "agent": self.name,
                "reply": "I could not find a valid interview time. Please suggest another date and time.",
                "available": False,
                "reason": "no_available_slot",
                "conversation_state": data,
                "selected_time_utc": None
            }

        try:
            preferred_dt = datetime.fromisoformat(preferred_time)
        except Exception:
            data["available"] = False
            data.pop("preferred_datetime_utc", None)
            data.pop("selected_time_utc", None)

            return {
                "agent": self.name,
                "reply": "The provided date and time is invalid. Please suggest another date and time.",
                "available": False,
                "reason": "no_available_slot",
                "conversation_state": data,
                "selected_time_utc": None
            }

        if preferred_dt.tzinfo is None:
            preferred_dt = preferred_dt.replace(tzinfo=timezone.utc)

        now_utc = datetime.now(timezone.utc)

        if preferred_dt <= now_utc:
            data["available"] = False
            data.pop("preferred_datetime_utc", None)
            data.pop("selected_time_utc", None)

            return {
                "agent": self.name,
                "reply": "The selected time is in the past. Please choose a future date and time.",
                "available": False,
                "reason": "past_time",
                "conversation_state": data,
                "selected_time_utc": None
            }

        if not self._is_within_working_hours_ist(preferred_dt):
            data["available"] = False
            data.pop("preferred_datetime_utc", None)
            data.pop("selected_time_utc", None)

            return {
                "agent": self.name,
                "reply": "The selected time is outside working hours. Please choose another time.",
                "available": False,
                "reason": "no_available_slot",
                "conversation_state": data,
                "selected_time_utc": None
            }

        tool_input = {"interviewer_id": interviewer_id}

        tool_result = calendar_read_tool(tool_input)
        tool_trace(state, "calendar_read_tool", tool_input, tool_result)

        if not tool_result.get("success"):
            data["available"] = False

            return {
                "agent": self.name,
                "reply": "Sorry, I could not access the calendar right now. Please try again.",
                "available": False,
                "reason": "calendar_read_failed",
                "conversation_state": data
            }

        busy_slots = tool_result.get("slots", [])

        if self._has_conflict(preferred_dt, busy_slots):
            data["available"] = False
            data.pop("preferred_datetime_utc", None)
            data.pop("selected_time_utc", None)

            return {
                "agent": self.name,
                "reply": "That time slot is not available. Please suggest another date and time.",
                "available": False,
                "reason": "no_available_slot",
                "conversation_state": data,
                "selected_time_utc": None
            }

        data["available"] = True
        data["selected_time_utc"] = preferred_time

        return {
            "agent": self.name,
            "reply": "The selected slot is available.",
            "available": True,
            "selected_time_utc": preferred_time,
            "conversation_state": data
        }

    def _is_within_working_hours_ist(self, dt_utc: datetime) -> bool:
        ist_dt = dt_utc.astimezone(IST)
        t = ist_dt.time()
        return WORK_START <= t <= WORK_END

    def _has_conflict(
        self,
        requested_time: datetime,
        busy_slots: List[Dict[str, str]]
    ) -> bool:

        buffer_delta = timedelta(minutes=BUFFER_MINUTES)

        requested_start = requested_time - buffer_delta
        requested_end = requested_time + buffer_delta

        for slot in busy_slots:
            try:
                start = datetime.fromisoformat(slot["start"])
                end = datetime.fromisoformat(slot["end"])

                if start.tzinfo is None:
                    start = start.replace(tzinfo=timezone.utc)

                if end.tzinfo is None:
                    end = end.replace(tzinfo=timezone.utc)

            except Exception:
                continue

            if requested_start < end and requested_end > start:
                return True

        return False
