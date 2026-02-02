from typing import Dict, Any, List
from datetime import datetime, time, timedelta

from app.tools.calendar_read_tool import calendar_read_tool
from app.tools.trace import tool_trace


WORK_START = time(4, 30)
WORK_END = time(12, 30)
BUFFER_MINUTES = 30


class AvailabilityAgent:

    name = "AvailabilityAgent"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:

        data = state["conversation_state"]

        interviewer_id = data.get("interviewer_id")
        preferred_time = data.get("preferred_datetime_utc")

        if not interviewer_id or not preferred_time:
            return {
                "agent": self.name,
                "reply": "I could not find a valid interview time. Please suggest another date and time.",
                "available": False,
                "reason": "no_available_slot",
                "conversation_state": data
            }

        try:
            preferred_dt = datetime.fromisoformat(preferred_time)
        except Exception:
            return {
                "agent": self.name,
                "reply": "The provided date and time is invalid. Please suggest another date and time.",
                "available": False,
                "reason": "no_available_slot",
                "conversation_state": data
            }

        if not self._is_within_working_hours(preferred_dt):
            return {
                "agent": self.name,
                "reply": "The selected time is outside working hours. Please choose another time.",
                "available": False,
                "reason": "no_available_slot",
                "conversation_state": data
            }

        tool_input = {
            "interviewer_id": interviewer_id
        }

        tool_result = calendar_read_tool(tool_input)

        tool_trace(state, "calendar_read_tool", tool_input, tool_result)

        data.setdefault("tool_traces", [])

        if "trace" in tool_result:
            data["tool_traces"].append(tool_result["trace"])

        if not tool_result.get("success"):
            return {
                "agent": self.name,
                "reply": "Sorry, I could not access the calendar right now. Please try again.",
                "available": False,
                "reason": "calendar_read_failed",
                "conversation_state": data
            }

        busy_slots = tool_result.get("slots", [])

        if self._has_conflict(preferred_dt, busy_slots):
            return {
                "agent": self.name,
                "reply": "That time slot is not available. Please suggest another date and time.",
                "available": False,
                "reason": "no_available_slot",
                "conversation_state": data
            }

        return {
            "agent": self.name,
            "reply": "The selected slot is available.",
            "available": True,
            "selected_time_utc": preferred_time,
            "conversation_state": data
        }

    def _is_within_working_hours(self, dt: datetime) -> bool:
        t = dt.time()
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
            except Exception:
                continue

            if requested_start < end and requested_end > start:
                return True

        return False
