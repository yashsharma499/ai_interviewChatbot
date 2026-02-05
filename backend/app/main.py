from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import os
from dotenv import load_dotenv
from app.db.database import engine
from app.db import models
from app.graph.interview_graph import build_graph
from app.api.interviews import router as interview_router

load_dotenv()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Interview Scheduler")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interview_router)

graph = build_graph()

class ChatRequest(BaseModel):
    user_message: str
    conversation_id: Optional[str] = None

@app.get("/")
def health_check():
    return {"status": "running"}


@app.post("/chat")
def chat(req: ChatRequest) -> Dict[str, Any]:

    conversation_id = req.conversation_id or str(uuid.uuid4())

    initial_state = {
        "conversation_id": conversation_id,
        "user_message": req.user_message
    }

    result = graph.invoke(initial_state) or {}

    response: Dict[str, Any] = {
        "conversation_id": conversation_id
    }

    for key in [
        "agent",
        "reply",
        "is_complete",
        "conversation_state",
        "interview_id",
        "reason",
        "trace",
        "success"
    ]:
        if key in result:
            response[key] = result[key]

    return response
