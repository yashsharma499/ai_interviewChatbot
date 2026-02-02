from typing import Dict, Any, List
import re
from datetime import datetime
from sqlalchemy.orm import joinedload
from app.tools.memory_tool import load_state, save_state
from app.tools.timezone_tool import timezone_normalize_tool
from app.tools.trace import tool_trace
from app.db.session import SessionLocal
from app.db.models import Candidate, Interviewer, Interview

REQUIRED_FIELDS = [
    "candidate_name",
    "candidate_email",
    "preferred_datetime",
    "timezone"
]

class ConversationAgent:

    name = "ConversationAgent"
    
    def _normalize_tz(self, tz: str) -> str:
        tz = tz.strip()

        if tz.lower() == "ist":
            return "Asia/Kolkata"

        if "/" in tz:
            parts = tz.split("/")
            return "/".join(
                p[:1].upper() + p[1:].lower()
                for p in parts if p
            )

        return tz

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:

        conversation_id = state.get("conversation_id")
        user_message = (state.get("user_message") or "").strip()

        if not conversation_id:
            return {
                "agent": self.name,
                "reply": "Something went wrong. Please start the conversation again.",
                "is_complete": False
            }

        stored_state = load_state(conversation_id) or {}
        tool_trace(state, "load_state", conversation_id, stored_state)

        awaiting = stored_state.get("awaiting_field")
        if awaiting and user_message:
            stored_state[awaiting] = user_message.strip()
            stored_state.pop("awaiting_field", None)
            save_state(conversation_id, stored_state)

        current_intent = stored_state.get("intent") or state.get("intent")
        if current_intent:
            stored_state["intent"] = current_intent

        if user_message:

            if not stored_state.get("candidate_email"):
                m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_message)
                if m:
                    stored_state["candidate_email"] = m.group().strip()

            if not stored_state.get("candidate_name"):
                m = re.search(
                    r'for\s+([A-Za-z ]+?)(?:,|$)',
                    user_message,
                    re.IGNORECASE
                )
                if m:
                    stored_state["candidate_name"] = m.group(1).strip()

            if not stored_state.get("timezone"):
                tz = re.search(r'\b[A-Za-z]+\/[A-Za-z_]+|\bIST\b', user_message)
                if tz:
                    val = tz.group().strip()
                    if val.upper() == "IST":
                        val = "Asia/Kolkata"
                    stored_state["timezone"] = val

            if not stored_state.get("preferred_datetime"):
                parts = [p.strip() for p in user_message.split(",")]
                if len(parts) >= 2:
                    dt = parts[-1]
                    dt = re.sub(r'\bIST\b', '', dt, flags=re.IGNORECASE)
                    dt = re.sub(r'\b[A-Za-z]+\/[A-Za-z_]+\b', '', dt)
                    dt = re.sub(r'^\s*(on|at)\s+', '', dt, flags=re.IGNORECASE)
                    dt = dt.strip()
                    if dt:
                        stored_state["preferred_datetime"] = dt

        if current_intent in ("reschedule", "cancel"):

            if not stored_state.get("candidate_email"):
                stored_state["awaiting_field"] = "candidate_email"
                save_state(conversation_id, stored_state)

                return {
                    "agent": self.name,
                    "reply": "Please share your email address so I can find your interview.",
                    "is_complete": False,
                    "conversation_state": stored_state
                }

            if not stored_state.get("interview_id") and not stored_state.get("pending_interviews"):

                interviews = self._get_upcoming_interviews(
                    stored_state["candidate_email"]
                )

                if not interviews:
                    save_state(conversation_id, stored_state)
                    return {
                        "agent": self.name,
                        "reply": "I could not find any upcoming interviews for this email.",
                        "is_complete": True,
                        "conversation_state": stored_state
                    }

                stored_state["pending_interviews"] = [
                    {
                        "id": i.id,
                        "scheduled_time": i.scheduled_time.isoformat() if i.scheduled_time else "",
                        "interviewer": i.interviewer.name if i.interviewer else "Interviewer"
                    }
                    for i in interviews
                ]

                stored_state["awaiting_field"] = "interview_choice"

                lines = []
                for idx, item in enumerate(stored_state["pending_interviews"], 1):
                    lines.append(
                        f"{idx}. {item['scheduled_time'].replace('T', ' ')} with {item['interviewer']}"
                    )

                save_state(conversation_id, stored_state)

                return {
                    "agent": self.name,
                    "reply": "Please select the interview:\n" + "\n".join(lines),
                    "is_complete": False,
                    "conversation_state": stored_state
                }

            if not stored_state.get("interview_id"):

                choice = user_message or stored_state.get("interview_choice", "")

                if not str(choice).isdigit():
                    save_state(conversation_id, stored_state)
                    return {
                        "agent": self.name,
                        "reply": "Please reply with the number of the interview you want to select.",
                        "is_complete": False,
                        "conversation_state": stored_state
                    }

                idx = int(choice) - 1

                if idx < 0 or idx >= len(stored_state["pending_interviews"]):
                    save_state(conversation_id, stored_state)
                    return {
                        "agent": self.name,
                        "reply": "Invalid selection. Please choose a valid number from the list.",
                        "is_complete": False,
                        "conversation_state": stored_state
                    }

                stored_state["interview_id"] = stored_state["pending_interviews"][idx]["id"]
                stored_state.pop("pending_interviews", None)
                stored_state.pop("interview_choice", None)

                save_state(conversation_id, stored_state)

                return {
                    "agent": self.name,
                    "reply": "Thanks. Processing your request...",
                    "is_complete": True,
                    "conversation_state": stored_state
                }

            if current_intent == "reschedule":

                if not stored_state.get("new_preferred_datetime"):
                    stored_state["awaiting_field"] = "new_preferred_datetime"
                    save_state(conversation_id, stored_state)

                    return {
                        "agent": self.name,
                        "reply": "Please tell me the new date and time for your interview. (Example: 2026-02-10 11:00)",
                        "is_complete": False,
                        "conversation_state": stored_state
                    }

                if not stored_state.get("new_timezone"):
                    stored_state["awaiting_field"] = "new_timezone"
                    save_state(conversation_id, stored_state)

                    return {
                        "agent": self.name,
                        "reply": "Please tell me your timezone for the new time. (Example: Asia/Kolkata)",
                        "is_complete": False,
                        "conversation_state": stored_state
                    }

                clean_new_dt = stored_state["new_preferred_datetime"]
                clean_new_dt = re.sub(r'\bIST\b', '', clean_new_dt, flags=re.IGNORECASE)
                clean_new_dt = re.sub(r'\b[A-Za-z]+\/[A-Za-z_]+\b', '', clean_new_dt)
                clean_new_dt = re.sub(r'^\s*(on|at)\s+', '', clean_new_dt, flags=re.IGNORECASE)
                clean_new_dt = clean_new_dt.strip()

                tool_input = {
                    "datetime_str": clean_new_dt,
                    "timezone_str": self._normalize_tz(stored_state["new_timezone"])
                }

                tz_result = timezone_normalize_tool(tool_input)
                tool_trace(state, "timezone_tool", tool_input, tz_result)

                if not tz_result.get("success"):
                    stored_state.pop("new_timezone", None)
                    stored_state["awaiting_field"] = "new_timezone"
                    save_state(conversation_id, stored_state)

                    return {
                        "agent": self.name,
                        "reply": "I could not understand your timezone. Please re-enter your timezone.",
                        "is_complete": False,
                        "conversation_state": stored_state
                    }

                stored_state["preferred_datetime_utc"] = tz_result["utc_datetime"]
                save_state(conversation_id, stored_state)

                return {
                    "agent": self.name,
                    "reply": "Thanks. Processing your reschedule request...",
                    "is_complete": True,
                    "conversation_state": stored_state
                }

            return {
                "agent": self.name,
                "reply": "Processing your cancellation request...",
                "is_complete": True,
                "conversation_state": stored_state
            }

        if state.get("reason") == "no_available_slot":

            stored_state.pop("preferred_datetime_utc", None)
            stored_state["awaiting_field"] = "preferred_datetime"
            save_state(conversation_id, stored_state)

            return {
                "agent": self.name,
                "reply": "No interview slots are available at the selected time. Please suggest another date and time.",
                "is_complete": False,
                "conversation_state": stored_state
            }

        if current_intent == "inquiry" and not stored_state:
            save_state(conversation_id, stored_state)
            return {
                "agent": self.name,
                "reply": "How can I help you?",
                "is_complete": True,
                "conversation_state": stored_state
            }

        missing = self._missing_fields(stored_state)

        if missing:
            field = missing[0]
            stored_state["awaiting_field"] = field
            save_state(conversation_id, stored_state)

            return {
                "agent": self.name,
                "reply": self._question_for_field(field),
                "is_complete": False,
                "conversation_state": stored_state
            }

        stored_state["timezone"] = stored_state["timezone"].strip()

        clean_dt = stored_state["preferred_datetime"]
        clean_dt = re.sub(r'\bIST\b', '', clean_dt, flags=re.IGNORECASE)
        clean_dt = re.sub(r'\b[A-Za-z]+\/[A-Za-z_]+\b', '', clean_dt)
        clean_dt = re.sub(r'^\s*(on|at)\s+', '', clean_dt, flags=re.IGNORECASE)
        clean_dt = clean_dt.strip()

        tool_input = {
            "datetime_str": clean_dt,
            "timezone_str": self._normalize_tz(stored_state["timezone"])
        }

        tz_result = timezone_normalize_tool(tool_input)
        tool_trace(state, "timezone_tool", tool_input, tz_result)

        if not tz_result.get("success"):
            stored_state.pop("timezone", None)
            stored_state["awaiting_field"] = "timezone"
            save_state(conversation_id, stored_state)

            return {
                "agent": self.name,
                "reply": "I could not understand your timezone. Please re-enter your timezone (for example: Asia/Kolkata).",
                "is_complete": False,
                "conversation_state": stored_state
            }

        stored_state["preferred_datetime_utc"] = tz_result["utc_datetime"]
        stored_state["timezone"] = tz_result["timezone"]

        if not stored_state.get("candidate_id"):
            self._attach_candidate_and_interviewer(stored_state)

        save_state(conversation_id, stored_state)

        return {
            "agent": self.name,
            "reply": "Thanks. Checking available slots for your interview...",
            "is_complete": True,
            "conversation_state": stored_state
        }

    def _get_upcoming_interviews(self, email: str) -> List[Interview]:

        db = SessionLocal()
        try:
            return (
                db.query(Interview)
                .options(joinedload(Interview.interviewer))
                .join(Candidate)
                .filter(
                    Candidate.email == email,
                    Interview.status == "scheduled"
                )
                .order_by(Interview.scheduled_time.asc())
                .all()
            )
        finally:
            db.close()

    def _attach_candidate_and_interviewer(self, state: Dict[str, Any]) -> None:

        db = SessionLocal()
        try:
            candidate = (
                db.query(Candidate)
                .filter(Candidate.email == state["candidate_email"])
                .first()
            )

            if not candidate:
                candidate = Candidate(
                    name=state["candidate_name"],
                    email=state["candidate_email"]
                )
                db.add(candidate)
                db.commit()
                db.refresh(candidate)

            state["candidate_id"] = candidate.id

            interviewer = (
                db.query(Interviewer)
                .order_by(Interviewer.id.asc())
                .first()
            )

            if not interviewer:
                interviewer = Interviewer(
                    name="Default Interviewer",
                    email="interviewer@example.com"
                )
                db.add(interviewer)
                db.commit()
                db.refresh(interviewer)

            state["interviewer_id"] = interviewer.id

        finally:
            db.close()

    def _missing_fields(self, state: Dict[str, Any]) -> List[str]:
        return [f for f in REQUIRED_FIELDS if not state.get(f)]

    def _question_for_field(self, field: str) -> str:

        if field == "candidate_name":
            return "May I know your full name?"

        if field == "candidate_email":
            return "Please share your email address."

        if field == "preferred_datetime":
            return "What date and time would you prefer for the interview? (Example: 2026-02-01 11:00)"

        if field == "timezone":
            return "Please tell me your timezone (for example: Asia/Kolkata)."
