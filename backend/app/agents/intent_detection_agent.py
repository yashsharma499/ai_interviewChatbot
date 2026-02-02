from typing import Dict

from openai import OpenAI

from app.config import OPENAI_API_KEY

ALLOWED_INTENTS = {"schedule", "reschedule", "cancel", "inquiry"}


class IntentDetectionAgent:

    name = "IntentDetectionAgent"

    def __init__(self):
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is missing")

        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def run(self, state: Dict) -> Dict[str, str]:

        user_message = (state.get("user_message") or "").strip()

        if not user_message:
            return {
                "agent": self.name,
                "intent": "inquiry"
            }

        prompt = (
            "You are an interview scheduling assistant.\n\n"
            "Classify the user's intent into ONE of the following words only:\n"
            "schedule\n"
            "reschedule\n"
            "cancel\n"
            "inquiry\n\n"
            "Important rules:\n"
            "- 'book', 'create', 'set up', 'arrange', 'schedule' all mean schedule\n"
            "- 'change', 'move', 'shift' mean reschedule\n"
            "- 'delete', 'remove' mean cancel\n"
            "- questions or general chat mean inquiry\n\n"
            "Return ONLY one word.\n\n"
            f"User message:\n{user_message}"
        )

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        raw = response.choices[0].message.content.strip().lower()

        raw = raw.replace("intent:", "").strip()
        raw = raw.split()[0].strip(".,\"'")

        if raw not in ALLOWED_INTENTS:
            raw = "inquiry"

        return {
            "agent": self.name,
            "intent": raw
        }
