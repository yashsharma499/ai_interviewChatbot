from typing import Dict, Any
import json
from openai import OpenAI
from app.config import OPENAI_API_KEY

ALLOWED_INTENTS = {"schedule", "reschedule", "cancel", "inquiry"}

class IntentDetectionAgent:

    name = "IntentDetectionAgent"

    def __init__(self):
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is missing")

        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:

        user_message = (state.get("user_message") or "").strip()

        if not user_message:
            return {
                "agent": self.name,
                "intent": "inquiry",
                "confidence": 1.0
            }

        prompt = (
            "You are an interview scheduling assistant.\n\n"
            "Classify the user's intent and return a JSON object only.\n\n"
            "Allowed intents:\n"
            "schedule, reschedule, cancel, inquiry\n\n"
            "Rules:\n"
            "- booking or creating an interview means schedule\n"
            "- changing an existing interview means reschedule\n"
            "- deleting or cancelling an interview means cancel\n"
            "- general questions or chat mean inquiry\n\n"
            "Return strictly in this format:\n"
            "{ \"intent\": \"<intent>\", \"confidence\": <number between 0 and 1> }\n\n"
            f"User message:\n{user_message}"
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )

            content = response.choices[0].message.content.strip()
            data = json.loads(content)

            intent = str(data.get("intent", "")).lower().strip()
            confidence = float(data.get("confidence", 0.0))

            if intent not in ALLOWED_INTENTS:
                intent = "unknown"

            if confidence < 0.60:
                intent = "unknown"

            return {
                "agent": self.name,
                "intent": intent,
                "confidence": confidence
            }

        except Exception:
            return {
                "agent": self.name,
                "intent": "unknown",
                "confidence": 0.0
            }
