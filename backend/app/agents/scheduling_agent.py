from typing import Dict, Any
from datetime import datetime
from app.db.session import SessionLocal
from app.db.models import Interview, Candidate, Interviewer
from app.tools.calendar_create_tool import calendar_create_tool
from app.tools.notification_tool import notification_tool
from app.tools.trace import tool_trace
from app.tools.memory_tool import save_state


class SchedulingAgent:

    name = "SchedulingAgent"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:

        data = state.get("conversation_state", {})
        conversation_id = state.get("conversation_id")

        candidate_id = data.get("candidate_id")
        interviewer_id = data.get("interviewer_id")

        scheduled_time = state.get("selected_time_utc") or data.get(
            "preferred_datetime_utc"
        )

        if not candidate_id or not interviewer_id:
            db = SessionLocal()
            try:
                if not candidate_id and data.get("candidate_email"):
                    candidate = (
                        db.query(Candidate)
                        .filter(Candidate.email == data["candidate_email"])
                        .first()
                    )
                    if candidate:
                        data["candidate_id"] = candidate.id

                if not interviewer_id:
                    interviewer = (
                        db.query(Interviewer)
                        .order_by(Interviewer.id.asc())
                        .first()
                    )
                    if interviewer:
                        data["interviewer_id"] = interviewer.id
            finally:
                db.close()

            candidate_id = data.get("candidate_id")
            interviewer_id = data.get("interviewer_id")

        if not candidate_id or not interviewer_id or not scheduled_time:
            return {
                "agent": self.name,
                "reply": "Sorry, I could not schedule the interview because some information is missing.",
                "success": False,
                "reason": "Missing required scheduling data",
                "conversation_state": data,
                "is_complete": True
            }

        db = SessionLocal()

        try:
            interview = Interview(
                candidate_id=candidate_id,
                interviewer_id=interviewer_id,
                scheduled_time=datetime.fromisoformat(scheduled_time),
                status="created"
            )

            db.add(interview)
            db.commit()
            db.refresh(interview)

            interview_id = interview.id

        except Exception:
            db.rollback()
            db.close()
            return {
                "agent": self.name,
                "reply": "A database error occurred while creating your interview.",
                "success": False,
                "reason": "Database error while creating interview",
                "conversation_state": data,
                "is_complete": True
            }

        create_input = {
            "interview_id": interview_id,
            "interviewer_id": interviewer_id,
            "scheduled_time_utc": scheduled_time
        }

        create_result = calendar_create_tool(create_input)

        tool_trace(state, "calendar_create_tool", create_input, create_result)

        if not create_result.get("success"):
            try:
                interview.status = "calendar_failed"
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()

            return {
                "agent": self.name,
                "reply": "I could not create the calendar event. Please try again.",
                "success": False,
                "reason": "Failed to create calendar event",
                "conversation_state": data,
                "is_complete": True
            }

        notify_input = {
            "candidate_id": candidate_id,
            "interviewer_id": interviewer_id,
            "scheduled_time_utc": scheduled_time
        }

        notify_result = notification_tool(notify_input)

        tool_trace(state, "notification_tool", notify_input, notify_result)

        if not notify_result.get("success"):
            try:
                interview.status = "notification_failed"
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()

            return {
                "agent": self.name,
                "reply": "The interview was created, but I could not send notifications.",
                "success": False,
                "reason": "Notification failed",
                "conversation_state": data,
                "is_complete": True
            }

        try:
            interview.status = "scheduled"
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

        
        data.pop("preferred_datetime", None)
        data.pop("preferred_datetime_utc", None)
        data.pop("selected_time_utc", None)
        data.pop("timezone", None)
        data.pop("awaiting_field", None)
        data.pop("reason", None)
        data.pop("intent", None)

        if conversation_id:
            save_state(conversation_id, data)

        return {
            "agent": self.name,
            "reply": "Your interview has been successfully scheduled.",
            "success": True,
            "interview_id": interview_id,
            "scheduled_time_utc": scheduled_time,
            "conversation_state": data,
            "is_complete": True,
            "reason": None
        }
