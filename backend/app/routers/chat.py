import json
import time

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage
from groq import RateLimitError

from app.agent.graph import get_agent
from app import schemas

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatRequest):
    agent = get_agent()
    config = {"configurable": {"thread_id": payload.session_id}}

    # MemorySaver checkpoints the FULL message history per thread_id, so
    # result["messages"] below is cumulative across every turn in this
    # session, not just this turn. Capture how many messages existed before
    # this call so we can slice out only what THIS turn added.
    prior_state = agent.get_state(config)
    prior_count = (
        len(prior_state.values.get("messages", [])) if prior_state.values else 0
    )

    # Groq's free tier has a tokens-per-minute cap. A single agent turn can
    # involve several LLM calls (planning + one per tool round-trip), so
    # bursts of messages can trip it. Retry with backoff instead of letting
    # it surface as a raw 500 to the frontend.
    result = None
    last_error = None
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            result = agent.invoke(
                {"messages": [HumanMessage(content=payload.message)]}, config=config
            )
            break
        except RateLimitError as e:
            last_error = e
            if attempt == max_attempts - 1:
                break
            time.sleep(5 * (attempt + 1))  # 5s, then 10s

    if result is None:
        raise HTTPException(
            status_code=429,
            detail="The AI assistant is temporarily rate-limited. Please wait a few seconds and try again.",
        ) from last_error

    messages = result["messages"]
    new_messages = messages[prior_count:]  # only this turn's messages
    final_message = messages[-1]

    tool_calls_used = [
        m.name for m in new_messages if getattr(m, "type", None) == "tool"
    ]

    interaction_data = None
    followups = None

    for m in new_messages:
        if getattr(m, "type", None) != "tool":
            continue
        if m.name in ("log_interaction", "edit_interaction"):
            try:
                parsed = json.loads(m.content)
                if isinstance(parsed, dict) and "error" not in parsed:
                    interaction_data = parsed
            except (json.JSONDecodeError, TypeError):
                pass
        elif m.name == "suggest_followups":
            try:
                parsed = json.loads(m.content)
                if isinstance(parsed, list):
                    followups = parsed
            except (json.JSONDecodeError, TypeError):
                pass

    if interaction_data is not None and followups is not None:
        interaction_data["ai_suggested_followups"] = followups

    return schemas.ChatResponse(
        reply=final_message.content,
        tool_calls=tool_calls_used,
        interaction=interaction_data,
        ai_suggested_followups=followups,
    )