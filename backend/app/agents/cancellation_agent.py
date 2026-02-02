from typing import Dict, Any

from app.db.session import SessionLocal
from app.db.models import Interview

from app.tools.calendar_delete_tool import calendar_delete_tool
from app.tools.notification_tool import notification_tool
from app.tools.trace import tool_trace


class CancellationAgent:

    name = "CancellationAgent"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:

        data = state.get("conversation_state") or {}
        data.setdefault("tool_traces", [])

        interview_id = state.get("interview_id") or data.get("interview_id")

        if not interview_id:
            return {
                "agent": self.name,
                "reply": "Please select the interview you want to cancel first.",
                "is_complete": False,
                "conversation_state": data
            }

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

            scheduled_time_utc = (
                interview.scheduled_time.isoformat()
                if interview.scheduled_time
                else None
            )

        finally:
            db.close()

        delete_input = {
            "interview_id": interview_id
        }

        delete_result = calendar_delete_tool(delete_input)

        tool_trace(state, "calendar_delete_tool", delete_input, delete_result)

        if delete_result.get("trace"):
            data["tool_traces"].append(delete_result["trace"])

        if not delete_result.get("success"):
            return {
                "agent": self.name,
                "reply": delete_result.get("error", "Failed to cancel interview."),
                "is_complete": True,
                "conversation_state": data
            }

        notify_input = {
            "candidate_id": candidate_id,
            "interviewer_id": interviewer_id,
            "scheduled_time_utc": scheduled_time_utc
        }

        notify_result = notification_tool(notify_input)

        tool_trace(state, "notification_tool", notify_input, notify_result)

        if notify_result.get("trace"):
            data["tool_traces"].append(notify_result["trace"])

        db = SessionLocal()
        try:
            interview = (
                db.query(Interview)
                .filter(Interview.id == interview_id)
                .first()
            )

            if interview:
                interview.status = "cancelled"
                db.commit()

        finally:
            db.close()

        return {
            "agent": self.name,
            "reply": "Your interview has been cancelled successfully.",
            "is_complete": True,
            "conversation_state": data
        }
