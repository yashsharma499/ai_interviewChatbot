from typing import Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo

from app.db.session import SessionLocal
from app.db.models import Interview, Candidate

from app.tools.calendar_update_tool import calendar_update_tool
from app.tools.notification_tool import notification_tool
from app.tools.trace import tool_trace
from app.tools.timezone_tool import timezone_normalize_tool
from app.tools.memory_tool import save_state


class RescheduleAgent:

    name = "RescheduleAgent"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:

        data = state.get("conversation_state") or {}
        data.setdefault("tool_traces", [])

        conversation_id = state.get("conversation_id")

        interview_id = state.get("interview_id") or data.get("interview_id")

        data["active_subflow"] = "reschedule"

        
        if not interview_id:

            candidate_email = data.get("candidate_email")

            if not candidate_email:
                return {
                    "agent": self.name,
                    "reply": "Please share your email address so I can find your interview.",
                    "is_complete": False,
                    "conversation_state": data
                }

            db = SessionLocal()
            try:
                interviews = (
                    db.query(Interview)
                    .join(Candidate, Candidate.id == Interview.candidate_id)
                    .filter(
                        Candidate.email == candidate_email,
                        Interview.status == "scheduled"
                    )
                    .order_by(Interview.scheduled_time)
                    .all()
                )
            finally:
                db.close()

            if not interviews:
                return {
                    "agent": self.name,
                    "reply": "No interview found for your account.",
                    "is_complete": True,
                    "conversation_state": data
                }

            lines = []
            ids = []

            for i, it in enumerate(interviews, 1):

                if not it.scheduled_time:
                    continue

                ist_time = it.scheduled_time.astimezone(
                    ZoneInfo("Asia/Kolkata")
                ).strftime("%d/%m/%Y, %I:%M %p")

                lines.append(f"{i}. {ist_time} with Default Interviewer")
                ids.append(it.id)

            data["reschedule_candidates"] = ids

            if conversation_id:
                save_state(conversation_id, data)

            return {
                "agent": self.name,
                "reply": "Please select the interview:\n" + "\n".join(lines),
                "is_complete": False,
                "conversation_state": data
            }

        

        new_time_utc = state.get("new_time_utc")

        if not new_time_utc:

            if not data.get("new_preferred_datetime"):
                data["awaiting_field"] = "new_preferred_datetime"

                if conversation_id:
                    save_state(conversation_id, data)

                return {
                    "agent": self.name,
                    "reply": "Please tell me the new date and time for your interview. (Example: 2026-02-10 11:00)",
                    "is_complete": False,
                    "conversation_state": data
                }

            if not data.get("new_timezone"):
                data["awaiting_field"] = "new_timezone"

                if conversation_id:
                    save_state(conversation_id, data)

                return {
                    "agent": self.name,
                    "reply": "Please tell me your timezone for the new time. (Example: Asia/Kolkata)",
                    "is_complete": False,
                    "conversation_state": data
                }

            tool_input = {
                "datetime_str": data["new_preferred_datetime"],
                "timezone_str": data["new_timezone"]
            }

            tz_result = timezone_normalize_tool(tool_input)
            tool_trace(state, "timezone_tool", tool_input, tz_result)

            if not tz_result.get("success"):

                data.pop("new_timezone", None)
                data["awaiting_field"] = "new_timezone"

                if conversation_id:
                    save_state(conversation_id, data)

                return {
                    "agent": self.name,
                    "reply": "I could not understand the timezone. Please enter it again (for example: Asia/Kolkata).",
                    "is_complete": False,
                    "conversation_state": data
                }

            new_time_utc = tz_result["utc_datetime"]

        data["preferred_datetime_utc"] = new_time_utc

        db = SessionLocal()
        try:
            interview = (
                db.query(Interview)
                .filter(Interview.id == interview_id)
                .first()
            )

            if not interview:
                return {
                    "agent": self.name,
                    "reply": "Interview not found.",
                    "is_complete": True,
                    "conversation_state": data
                }

            candidate_id = interview.candidate_id
            interviewer_id = interview.interviewer_id

        finally:
            db.close()

        update_input = {
            "interview_id": interview_id,
            "new_time_utc": new_time_utc
        }

        update_result = calendar_update_tool(update_input)

        tool_trace(state, "calendar_update_tool", update_input, update_result)

        if update_result.get("trace"):
            data["tool_traces"].append(update_result["trace"])

        if not update_result.get("success"):
            return {
                "agent": self.name,
                "reply": update_result.get("error", "Failed to update calendar."),
                "is_complete": True,
                "conversation_state": data,
                "new_time_utc": new_time_utc
            }

        notify_input = {
            "candidate_id": candidate_id,
            "interviewer_id": interviewer_id,
            "scheduled_time_utc": new_time_utc
        }

        notify_result = notification_tool(notify_input)

        tool_trace(state, "notification_tool", notify_input, notify_result)

        if notify_result.get("trace"):
            data["tool_traces"].append(notify_result["trace"])

        if not notify_result.get("success"):
            return {
                "agent": self.name,
                "reply": "Interview updated, but notification failed.",
                "is_complete": True,
                "conversation_state": data,
                "new_time_utc": new_time_utc
            }

        db = SessionLocal()
        try:
            interview = (
                db.query(Interview)
                .filter(Interview.id == interview_id)
                .first()
            )

            if interview:
                interview.scheduled_time = datetime.fromisoformat(new_time_utc)
                interview.status = "scheduled"
                db.commit()

        finally:
            db.close()

        data.pop("new_preferred_datetime", None)
        data.pop("new_timezone", None)
        data.pop("awaiting_field", None)
        data.pop("active_subflow", None)
        data.pop("reschedule_candidates", None)
        data.pop("interview_id", None)

        if conversation_id:
            save_state(conversation_id, data)

        return {
            "agent": self.name,
            "reply": "Your interview has been successfully rescheduled.",
            "is_complete": True,
            "conversation_state": data,
            "new_time_utc": new_time_utc
        }
