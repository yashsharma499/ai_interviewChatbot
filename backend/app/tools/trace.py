from typing import Dict, Any
from datetime import datetime

def _ensure_trace_container(state: Dict[str, Any]) -> None:
    if "trace" not in state or not isinstance(state.get("trace"), list):
        state["trace"] = []


def _clean_output(output: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(output, dict):
        return {}

    cleaned = {}

    for k, v in output.items():
        if k in ("conversation_state", "trace"):
            continue

        cleaned[k] = v

    return cleaned


def add_trace(state: Dict[str, Any], entry: Dict[str, Any]) -> None:
    _ensure_trace_container(state)

    entry = dict(entry)
    entry["timestamp"] = datetime.utcnow().isoformat()

    state["trace"].append(entry)


def agent_trace(state: Dict[str, Any], agent_name: str, output: Dict[str, Any]) -> None:
    add_trace(
        state,
        {
            "type": "agent",
            "name": agent_name,
            "output": _clean_output(output),
        }
    )


def tool_trace(
    state: Dict[str, Any],
    tool_name: str,
    tool_input: Dict[str, Any],
    tool_output: Any,
) -> None:
    add_trace(
        state,
        {
            "type": "tool",
            "name": tool_name,
            "input": tool_input,
            "output": tool_output,
        }
    )
