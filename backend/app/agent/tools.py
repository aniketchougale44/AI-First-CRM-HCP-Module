"""
LangGraph Agent Tools for the HCP Interaction module.

5 required tools:
1. log_interaction        - creates a new interaction record (uses LLM for entity
                             extraction/summarization from free-text)
2. edit_interaction        - modifies an existing logged interaction
3. summarize_topics        - condenses a raw voice-note transcript into structured
                             "Topics Discussed" bullet points (LLM summarization)
4. analyze_sentiment       - infers HCP sentiment (positive/neutral/negative) from
                             free-text description of the interaction
5. suggest_followups       - LLM-generated recommended next-step actions based on
                             the logged interaction content

Bonus 6th tool:
6. search_hcp              - looks up / creates an HCP record by name so interactions
                             can be linked to the right doctor
"""
import json
from typing import List, Optional
from datetime import date
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.database import SessionLocal
from app.models import HCP, Interaction
from app.agent.llm import get_llm, get_llm_reasoning


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_or_create_hcp(db, name: str) -> HCP:
    hcp = db.query(HCP).filter(HCP.name.ilike(name.strip())).first()
    if not hcp:
        hcp = HCP(name=name.strip())
        db.add(hcp)
        db.commit()
        db.refresh(hcp)
    return hcp


def _most_recent_interaction(db, hcp_name: Optional[str] = None) -> Optional[Interaction]:
    """Fallback lookup used when the LLM can't recall an exact interaction_id.
    If hcp_name is given, scopes to that HCP's most recent interaction instead
    of the globally most recent one (prevents cross-HCP bleed in multi-doctor
    chat sessions)."""
    query = db.query(Interaction)
    if hcp_name:
        hcp = db.query(HCP).filter(HCP.name.ilike(hcp_name.strip())).first()
        if hcp:
            query = query.filter(Interaction.hcp_id == hcp.id)
    return query.order_by(Interaction.created_at.desc()).first()


def _interaction_to_dict(i: Interaction, db) -> dict:
    hcp = db.query(HCP).filter(HCP.id == i.hcp_id).first()
    return {
        "id": i.id,
        "hcp_id": i.hcp_id,
        "hcp_name": hcp.name if hcp else "",
        "interaction_type": i.interaction_type,
        "date": i.date,
        "time": i.time,
        "attendees": i.attendees or [],
        "topics_discussed": i.topics_discussed,
        "materials_shared": i.materials_shared or [],
        "samples_distributed": i.samples_distributed or [],
        "sentiment": i.sentiment.value if hasattr(i.sentiment, "value") else i.sentiment,
        "outcomes": i.outcomes,
        "follow_up_actions": i.follow_up_actions,
        "ai_suggested_followups": i.ai_suggested_followups or [],
        "source": i.source,
    }


# ---------------------------------------------------------------------------
# Tool 1: search_hcp
# ---------------------------------------------------------------------------

@tool
def search_hcp(name: str) -> str:
    """Search for a Healthcare Professional (HCP) by name. Creates the HCP record
    if one doesn't already exist. Returns the HCP id, name, and specialty as JSON.
    Use this before logging an interaction so it can be linked to the right HCP."""
    db = SessionLocal()
    try:
        hcp = _get_or_create_hcp(db, name)
        return json.dumps({"id": hcp.id, "name": hcp.name, "specialty": hcp.specialty})
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 2: log_interaction
# ---------------------------------------------------------------------------

class LogInteractionInput(BaseModel):
    hcp_name: str = Field(description="Name of the HCP the interaction was with")
    raw_text: str = Field(
        description="Free-text / conversational description of the interaction, "
        "e.g. 'Met Dr. Smith, discussed Product X efficacy, positive sentiment, shared brochure'"
    )


@tool(args_schema=LogInteractionInput)
def log_interaction(hcp_name: str, raw_text: str) -> str:
    """Log a new HCP interaction. Uses the LLM to extract structured entities
    (interaction type, date, time, attendees, topics discussed, materials/samples
    shared, sentiment, outcomes, follow-up actions) from a raw free-text/voice-note
    description, then persists a new Interaction row. Returns the created
    interaction as JSON."""
    db = SessionLocal()
    try:
        hcp = _get_or_create_hcp(db, hcp_name)

        llm = get_llm(temperature=0)
        extraction_prompt = f"""Extract structured CRM fields from this field rep's note
about an interaction with a healthcare professional. Respond with STRICT JSON only,
no markdown, matching this schema:
{{
  "interaction_type": "Meeting" | "Call" | "Email" | "Conference",
  "date": "YYYY-MM-DD - use today's date {date.today().isoformat()} if the note doesn't mention a specific date",
  "time": "HH:MM in 24-hour format, empty string if not mentioned",
  "attendees": ["list of any OTHER people present besides the HCP being visited (e.g. colleagues, nurses) - do NOT include the HCP's own name here, empty list if none"],
  "topics_discussed": "short paragraph summary",
  "materials_shared": ["list", "of", "materials"],
  "samples_distributed": ["list", "of", "samples"],
  "sentiment": "positive" | "neutral" | "negative",
  "outcomes": "short summary of outcomes/agreements",
  "follow_up_actions": "short summary of next steps mentioned, if any"
}}

Note: \"\"\"{raw_text}\"\"\""""

        result = llm.invoke(extraction_prompt)
        try:
            extracted = json.loads(result.content.strip().strip("`").replace("json\n", ""))
        except Exception:
            extracted = {
                "interaction_type": "Meeting",
                "date": date.today().isoformat(),
                "time": "",
                "attendees": [],
                "topics_discussed": raw_text,
                "materials_shared": [],
                "samples_distributed": [],
                "sentiment": "neutral",
                "outcomes": "",
                "follow_up_actions": "",
            }

        interaction = Interaction(
            hcp_id=hcp.id,
            interaction_type=extracted.get("interaction_type", "Meeting"),
            date=extracted.get("date", date.today().isoformat()),
            time=extracted.get("time", ""),
            attendees=extracted.get("attendees", []),
            topics_discussed=extracted.get("topics_discussed", raw_text),
            materials_shared=extracted.get("materials_shared", []),
            samples_distributed=extracted.get("samples_distributed", []),
            sentiment=extracted.get("sentiment", "neutral"),
            outcomes=extracted.get("outcomes", ""),
            follow_up_actions=extracted.get("follow_up_actions", ""),
            source="chat",
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)
        return json.dumps(_interaction_to_dict(interaction, db))
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 3: edit_interaction
# ---------------------------------------------------------------------------

@tool
def edit_interaction(interaction_id: str, updates_json: str, hcp_name: str = "") -> str:
    """Edit/modify an already-logged interaction. `updates_json` must be a JSON
    string of the fields to change, e.g. '{"sentiment": "positive"}'.
    To correct the HCP's name, include "hcp_name" as a key inside updates_json.
    Other valid keys: interaction_type, date, time, attendees, topics_discussed,
    materials_shared, samples_distributed, sentiment, outcomes, follow_up_actions.

    If unsure of the exact interaction_id, pass your best guess AND ALWAYS pass
    the hcp_name argument (the doctor currently being discussed in the
    conversation) - this tool will then fall back to that specific HCP's most
    recently logged interaction if the id doesn't match, instead of guessing at
    the globally most recent interaction which may belong to a different HCP.

    Returns the updated interaction as JSON."""
    db = SessionLocal()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()

        if not interaction:
            interaction = _most_recent_interaction(db, hcp_name or None)

        if not interaction:
            return json.dumps({"error": "No interactions have been logged yet."})

        updates = json.loads(updates_json)

        if "hcp_name" in updates:
            new_name = updates.pop("hcp_name")
            if new_name:
                new_hcp = _get_or_create_hcp(db, new_name)
                interaction.hcp_id = new_hcp.id

        for field, value in updates.items():
            if hasattr(interaction, field) and value is not None:
                setattr(interaction, field, value)

        db.commit()
        db.refresh(interaction)
        return json.dumps(_interaction_to_dict(interaction, db))
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 4: summarize_topics (voice-note -> structured summary)
# ---------------------------------------------------------------------------

@tool
def summarize_topics(transcript: str) -> str:
    """Summarize a raw voice-note transcript of an HCP interaction into concise
    bullet-point 'Topics Discussed' text suitable for the CRM form. Returns plain text."""
    llm = get_llm(temperature=0.1)
    prompt = f"""Summarize the following field rep voice-note transcript into 2-4
concise bullet points capturing the key topics discussed with the HCP. Return
plain text bullet points only, no preamble.

Transcript: \"\"\"{transcript}\"\"\""""
    result = llm.invoke(prompt)
    return result.content.strip()


# ---------------------------------------------------------------------------
# Tool 5: analyze_sentiment
# ---------------------------------------------------------------------------

@tool
def analyze_sentiment(text: str) -> str:
    """Infer the HCP's sentiment (positive, neutral, or negative) from a free-text
    description of the interaction. Returns a single word: positive, neutral, or negative."""
    llm = get_llm(temperature=0)
    prompt = f"""Classify the HCP's sentiment expressed or implied in this interaction
note as exactly one word: positive, neutral, or negative. Respond with only that word.

Note: \"\"\"{text}\"\"\""""
    result = llm.invoke(prompt)
    sentiment = result.content.strip().lower()
    if sentiment not in ("positive", "neutral", "negative"):
        sentiment = "neutral"
    return sentiment


# ---------------------------------------------------------------------------
# Tool 6: suggest_followups
# ---------------------------------------------------------------------------

@tool
def suggest_followups(interaction_id: str, hcp_name: str = "") -> str:
    """Generate 2-3 AI-suggested follow-up actions for a logged interaction
    (e.g. 'Schedule follow-up meeting in 2 weeks', 'Send Phase III PDF').

    Always pass hcp_name (the doctor currently being discussed) alongside
    interaction_id - if interaction_id doesn't match a real record, this tool
    falls back to that HCP's most recent interaction instead of a possibly
    unrelated other HCP's most recent interaction.

    Persists the suggestions onto the interaction and returns them as a JSON
    list of strings."""
    db = SessionLocal()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            interaction = _most_recent_interaction(db, hcp_name or None)
        if not interaction:
            return json.dumps({"error": "No interaction found."})

        llm = get_llm_reasoning(temperature=0.4)
        prompt = f"""Based on this HCP interaction, suggest 2-3 short, actionable
follow-up tasks for the field rep. Return a JSON array of strings only, no markdown.

Topics discussed: {interaction.topics_discussed}
Outcomes: {interaction.outcomes}
Sentiment: {interaction.sentiment}"""

        result = llm.invoke(prompt)
        try:
            suggestions = json.loads(result.content.strip().strip("`").replace("json\n", ""))
        except Exception:
            suggestions = [
                line.strip("-• ").strip()
                for line in result.content.strip().splitlines()
                if line.strip()
            ][:3]

        interaction.ai_suggested_followups = suggestions
        db.commit()
        return json.dumps(suggestions)
    finally:
        db.close()


ALL_TOOLS = [
    search_hcp,
    log_interaction,
    edit_interaction,
    summarize_topics,
    analyze_sentiment,
    suggest_followups,
]