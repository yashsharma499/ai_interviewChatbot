from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, END

from app.agents.intent_detection_agent import IntentDetectionAgent
from app.agents.conversation_agent import ConversationAgent
from app.agents.availability_agent import AvailabilityAgent
from app.agents.scheduling_agent import SchedulingAgent
from app.agents.reschedule_agent import RescheduleAgent
from app.agents.cancellation_agent import CancellationAgent

from app.tools.trace import agent_trace
from app.tools.memory_tool import load_state


class InterviewState(TypedDict, total=False):
    conversation_id: str
    user_message: str
    intent: str
    confidence: float
    reply: str
    is_complete: bool
    conversation_state: Dict[str, Any]
    available: bool
    reason: str
    selected_time_utc: str
    interview_id: int
    new_time_utc: str
    success: bool
    trace: list


intent_agent = IntentDetectionAgent()
conversation_agent = ConversationAgent()
availability_agent = AvailabilityAgent()
scheduling_agent = SchedulingAgent()
reschedule_agent = RescheduleAgent()
cancellation_agent = CancellationAgent()


def intent_node(state: InterviewState) -> InterviewState:

    state.pop("reason", None)

    conversation_id = state.get("conversation_id")

    stored = {}
    if conversation_id:
        stored = load_state(conversation_id) or {}

    if stored.get("awaiting_field"):
        return state

    result = intent_agent.run(state)
    agent_trace(state, "IntentDetectionAgent", result)
    state.update(result)

    return state


def conversation_node(state: InterviewState) -> InterviewState:
    result = conversation_agent.run(state)
    agent_trace(state, "ConversationAgent", result)
    state.update(result)
    return state


def availability_node(state: InterviewState) -> InterviewState:
    result = availability_agent.run(state)
    agent_trace(state, "AvailabilityAgent", result)
    state.update(result)
    return state


def scheduling_node(state: InterviewState) -> InterviewState:
    result = scheduling_agent.run(state)
    agent_trace(state, "SchedulingAgent", result)
    state.update(result)
    return state


def reschedule_node(state: InterviewState) -> InterviewState:
    result = reschedule_agent.run(state)
    agent_trace(state, "RescheduleAgent", result)
    state.update(result)
    return state


def cancellation_node(state: InterviewState) -> InterviewState:
    result = cancellation_agent.run(state)
    agent_trace(state, "CancellationAgent", result)
    state.update(result)
    return state


def route_after_intent(state: InterviewState) -> str:
    return "conversation"


def route_after_conversation(state: InterviewState) -> str:

    if not state.get("is_complete"):
        return END

    stored_state = state.get("conversation_state") or {}

    intent = state.get("intent") or stored_state.get("intent")

    if intent == "unknown":
        return END

    if intent == "inquiry":
        return END

    if intent == "schedule":
        return "availability"

    if intent == "reschedule":

        if stored_state.get("awaiting_field"):
            return END

        if stored_state.get("interview_id") and not stored_state.get("preferred_datetime_utc"):
            return END

        if stored_state.get("preferred_datetime_utc"):
            return "reschedule"

        return END

    if intent == "cancel":
        return "cancel"

    return END


def route_after_availability(state: InterviewState) -> str:
    if state.get("available") is True:
        return "scheduling"
    return "conversation"


def build_graph():
    graph = StateGraph(InterviewState)

    graph.add_node("intent", intent_node)
    graph.add_node("conversation", conversation_node)
    graph.add_node("availability", availability_node)
    graph.add_node("scheduling", scheduling_node)
    graph.add_node("reschedule", reschedule_node)
    graph.add_node("cancel", cancellation_node)

    graph.set_entry_point("intent")

    graph.add_conditional_edges(
        "intent",
        route_after_intent,
        {
            "conversation": "conversation",
        },
    )

    graph.add_conditional_edges(
        "conversation",
        route_after_conversation,
        {
            "availability": "availability",
            "reschedule": "reschedule",
            "cancel": "cancel",
            "conversation": "conversation",
            END: END,
        },
    )

    graph.add_conditional_edges(
        "availability",
        route_after_availability,
        {
            "scheduling": "scheduling",
            "conversation": "conversation",
        },
    )

    graph.add_edge("scheduling", END)
    graph.add_edge("reschedule", END)
    graph.add_edge("cancel", END)

    return graph.compile()
