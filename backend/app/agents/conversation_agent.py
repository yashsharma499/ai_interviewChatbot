from typing import Dict, Any, List
import re
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import joinedload
from groq import Groq

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

_groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class ConversationAgent:

    name = "ConversationAgent"

    def _is_valid_email(self, email: str) -> bool:
        return bool(
            re.fullmatch(
                r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                email
            )
        )

    def _llm_reply(self, user_message: str) -> str:
        system_prompt = (
            "You are a helpful and concise interview scheduling assistant. "
            "When the user greets for the first time, greet back, clearly say that you can help to schedule, reschedule or cancel interviews, and then ask for their full name. "
            "If the user asks what you can do, explain you can schedule, reschedule or cancel interviews. "
            "If the message is not related to interview scheduling, answer briefly and guide the user back to interview scheduling. "
            "Keep responses short and professional."
        )

        try:
            resp = _groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.2,
                max_tokens=300,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            
            print("Groq Error:", str(e))
            return "I can help you schedule, reschedule or cancel interviews."

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

        current_intent = state.get("intent") or stored_state.get("intent")

        if current_intent == "unknown":
            save_state(conversation_id, stored_state)
            return {
                "agent": self.name,
                "reply": "I can help you schedule, reschedule, or cancel an interview. What would you like to do?",
                "is_complete": False,
                "conversation_state": stored_state
            }

        if re.fullmatch(r"(ok|okay|no|yes|hmm|thanks|thank you)", user_message, re.I):
            return {
                "agent": self.name,
                "reply": "Please tell me whether you want to schedule, reschedule, or cancel an interview.",
                "is_complete": False,
                "conversation_state": stored_state
            }

        awaiting = stored_state.get("awaiting_field")

        if awaiting and user_message:

            if awaiting == "candidate_email":
                if not self._is_valid_email(user_message.strip()):
                    return {
                        "agent": self.name,
                        "reply": "Please enter a valid email address.",
                        "is_complete": False,
                        "conversation_state": stored_state
                    }

            if awaiting == "candidate_name":
                m = re.search(r"([A-Za-z]+(?:\s+[A-Za-z]+)*)", user_message)
                if not m:
                    return {
                        "agent": self.name,
                        "reply": "Please enter only your full name.",
                        "is_complete": False,
                        "conversation_state": stored_state
                    }
                stored_state["candidate_name"] = m.group(1).strip()
            else:
                stored_state[awaiting] = user_message.strip()

            stored_state.pop("awaiting_field", None)
            save_state(conversation_id, stored_state)

        if current_intent == "schedule" and not stored_state.get("preferred_datetime_utc"):
            state["reason"] = None

        if current_intent:
            stored_state["intent"] = current_intent

        if user_message and current_intent == "inquiry" and not stored_state.get("awaiting_field"):

            if re.search(
                r"\b(no|nah|nope|not now|not really|don't want|do not want|dont want|stop|leave it|later|cancel it|forget it|never mind|nevermind|nothing|nothing else|no thanks|not interested)\b",
                user_message,
                re.I
            ):
                save_state(conversation_id, stored_state)
                return {
                    "agent": self.name,
                    "reply": "Okay. Let me know if you want to schedule, reschedule, or cancel an interview.",
                    "is_complete": False,
                    "conversation_state": stored_state
                }

            if not stored_state.get("candidate_email") and not re.search(r"\b(interview|interviews|my interviews|list)\b", user_message, re.I):
                save_state(conversation_id, stored_state)
                return {
                    "agent": self.name,
                    "reply": "I can help you schedule, reschedule, or cancel an interview. What would you like to do?",
                    "is_complete": False,
                    "conversation_state": stored_state
                }

            if not stored_state.get("candidate_email"):
                stored_state["awaiting_field"] = "candidate_email"
                save_state(conversation_id, stored_state)
                return {
                    "agent": self.name,
                    "reply": "Please share your email address so I can list your interviews.",
                    "is_complete": False,
                    "conversation_state": stored_state
                }

            interviews = self._get_upcoming_interviews(stored_state["candidate_email"])

            if not interviews:
                save_state(conversation_id, stored_state)
                return {
                    "agent": self.name,
                    "reply": "You do not have any upcoming interviews.",
                    "is_complete": True,
                    "conversation_state": stored_state
                }

            lines = []
            for i, item in enumerate(interviews, 1):
                ts = (
                    item.scheduled_time.astimezone(
                        ZoneInfo("Asia/Kolkata")
                    ).strftime("%d/%m/%Y, %I:%M %p")
                    if item.scheduled_time else ""
                )
                name = item.interviewer.name if item.interviewer else "Interviewer"
                lines.append(f"{i}. {ts} with {name}")

            save_state(conversation_id, stored_state)

            return {
                "agent": self.name,
                "reply": "Here are your upcoming interviews:\n" + "\n".join(lines),
                "is_complete": True,
                "conversation_state": stored_state
            }

        if user_message:

            if not stored_state.get("candidate_email"):
                m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_message)
                if m and self._is_valid_email(m.group().strip()):
                    stored_state["candidate_email"] = m.group().strip()

            if not stored_state.get("candidate_name"):
                m = re.search(
                    r"(?:\bmy name is\b|\bi am\b|\bi'm\b|\bthis is\b|\bmyself\b|\bname is\b|\bcall me\b|\bit is\b|\bim\b)\s+([A-Za-z]+(?:\s+[A-Za-z]+){0,3})",
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

                interviews = self._get_upcoming_interviews(stored_state["candidate_email"])

                if not interviews:
                    save_state(conversation_id, stored_state)
                    return {
                        "agent": self.name,
                        "reply": "I could not find any upcoming interviews for this email.",
                        "is_complete": False,
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
                    ts = (
                        datetime.fromisoformat(item["scheduled_time"])
                        .replace(tzinfo=ZoneInfo("UTC"))
                        .astimezone(ZoneInfo("Asia/Kolkata"))
                        .strftime("%d/%m/%Y, %I:%M %p")
                        if item["scheduled_time"] else ""
                    )
                    lines.append(f"{idx}. {ts} with {item['interviewer']}")

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

                if current_intent == "reschedule":
                    stored_state["awaiting_field"] = "new_preferred_datetime"
                    save_state(conversation_id, stored_state)
                    return {
                        "agent": self.name,
                        "reply": "Please tell me the new date and time for your interview. (Example: 2026-02-10 11:00)",
                        "is_complete": False,
                        "conversation_state": stored_state
                    }

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

                if datetime.utcnow() >= datetime.fromisoformat(stored_state["preferred_datetime_utc"]):
                    stored_state.pop("preferred_datetime_utc", None)
                    stored_state.pop("new_preferred_datetime", None)
                    stored_state["awaiting_field"] = "new_preferred_datetime"
                    save_state(conversation_id, stored_state)
                    return {
                        "agent": self.name,
                        "reply": "The selected new date and time is in the past. Please provide a future date and time.",
                        "is_complete": False,
                        "conversation_state": stored_state
                    }

                save_state(conversation_id, stored_state)

                return {
                    "agent": self.name,
                    "reply": "Thanks. Processing your reschedule request...",
                    "is_complete": True,
                    "conversation_state": stored_state,
                    "new_time_utc": stored_state["preferred_datetime_utc"]
                }

            return {
                "agent": self.name,
                "reply": "Processing your cancellation request...",
                "is_complete": True,
                "conversation_state": stored_state
            }

        if (
            current_intent == "schedule"
            and state.get("reason") == "past_time"
            and stored_state.get("preferred_datetime_utc")
        ):
            stored_state.pop("preferred_datetime_utc", None)
            stored_state["awaiting_field"] = "preferred_datetime"
            save_state(conversation_id, stored_state)
            return {
                "agent": self.name,
                "reply": "The selected date and time is in the past. Please provide a future date and time.",
                "is_complete": False,
                "conversation_state": stored_state
            }

        if (
            current_intent == "schedule"
            and state.get("reason") == "no_available_slot"
            and stored_state.get("preferred_datetime_utc")
        ):
            stored_state.pop("preferred_datetime_utc", None)
            stored_state["awaiting_field"] = "preferred_datetime"
            save_state(conversation_id, stored_state)
            return {
                "agent": self.name,
                "reply": "No interview slots are available at the selected time. Please suggest another date and time.",
                "is_complete": False,
                "conversation_state": stored_state
            }

        if current_intent != "schedule":
            save_state(conversation_id, stored_state)
            return {
                "agent": self.name,
                "reply": "How can I help you with interview scheduling?",
                "is_complete": False,
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
            stored_state.pop("preferred_datetime", None)
            stored_state["awaiting_field"] = "preferred_datetime"
            save_state(conversation_id, stored_state)
            return {
                "agent": self.name,
                "reply": "I could not understand the date and time. Please enter it like: 2026-02-13 11:00",
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
            "conversation_state": stored_state,
            "selected_time_utc": stored_state["preferred_datetime_utc"]
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

        return "Please provide the required information."
