import sqlite3
import json
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field


DB_PATH = "interview_scheduler.db"


class MemoryLoadInput(BaseModel):
    conversation_id: str = Field(...)


class MemorySaveInput(BaseModel):
    conversation_id: str = Field(...)
    state: Dict[str, Any] = Field(...)


class MemoryLoadOutput(BaseModel):
    found: bool
    state: Optional[Dict[str, Any]] = None


class MemorySaveOutput(BaseModel):
    success: bool


def _get_connection():
    return sqlite3.connect(DB_PATH)


def _init_table():
    conn = _get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_memory (
                conversation_id TEXT PRIMARY KEY,
                state_json TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


_init_table()


def load_state(conversation_id: str) -> Optional[Dict[str, Any]]:

    MemoryLoadInput(conversation_id=conversation_id)

    conn = None
    try:
        conn = _get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT state_json FROM conversation_memory WHERE conversation_id = ?",
            (conversation_id,)
        )

        row = cur.fetchone()

        if not row:
            return None

        try:
            return json.loads(row[0])
        except Exception:
            return None

    except Exception:
        return None

    finally:
        if conn:
            conn.close()


def save_state(conversation_id: str, state: Dict[str, Any]) -> bool:

    MemorySaveInput(conversation_id=conversation_id, state=state)

    conn = None
    try:
        conn = _get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO conversation_memory (conversation_id, state_json)
            VALUES (?, ?)
            ON CONFLICT(conversation_id)
            DO UPDATE SET state_json = excluded.state_json
            """,
            (conversation_id, json.dumps(state))
        )

        conn.commit()
        return True

    except Exception:
        if conn:
            conn.rollback()
        return False

    finally:
        if conn:
            conn.close()
