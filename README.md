# AI-First CRM — HCP Module: Log Interaction Screen

An AI-first "Log HCP Interaction" screen for pharma/life-science field
representatives. Reps can log an interaction with a Healthcare Professional
(HCP) either through a **structured form** or a **conversational chat
interface** backed by a **LangGraph agent** running on **Groq**
(`openai/gpt-oss-20b`, with `openai/gpt-oss-120b` as a fallback for heavier
reasoning like follow-up suggestions).

> **Note on model choice:** the task suggested `gemma2-9b-it` and
> `llama-3.3-70b-versatile`. Both have since been deprecated by Groq —
> `gemma2-9b-it` in August 2025 and `llama-3.3-70b-versatile` in June 2026 —
> and are no longer callable via the Groq API. We use Groq's official
> recommended successors instead: `openai/gpt-oss-20b` (replacement for the
> fast/cheap tier) and `openai/gpt-oss-120b` (replacement for the
> heavier-reasoning tier), preserving the same two-tier fast/versatile
> intent the task described.

## Architecture

```
frontend/   React 18 + Redux Toolkit (Vite) — structured form + AI chat panel
backend/    FastAPI + LangGraph + Groq + SQLAlchemy (Postgres/MySQL)
```

- **Frontend → Backend**: REST (`/api/interactions`, `/api/hcps`) for the
  structured form; `/api/chat` for the conversational panel.
- **Backend agent**: a LangGraph `create_react_agent` graph. The LLM node
  reads the rep's message, decides which tool(s) to call, and loops until it
  has a final answer — a standard ReAct-style agent loop implemented via
  LangGraph's prebuilt graph + `ToolNode` + conditional edges + a
  `MemorySaver` checkpointer (so it remembers context within a chat session).

## The LangGraph Agent

**Role:** The agent acts as the "AI Assistant" shown in the mockup's chat
panel — it turns a rep's free-text note ("Met Dr. Smith, discussed Product X
efficacy, positive sentiment, shared brochure") into a fully-populated,
structured interaction record, without the rep touching the form.

### Tools (`backend/app/agent/tools.py`)

| # | Tool | Purpose |
|---|------|---------|
| 1 | `search_hcp` | Looks up (or creates) an HCP by name so the interaction can be linked correctly. |
| 2 | **`log_interaction`** *(required)* | Uses the LLM to extract structured fields (type, topics, materials, samples, sentiment, outcomes, follow-ups) from free text, then persists a new `Interaction` row. |
| 3 | **`edit_interaction`** *(required)* | Applies a JSON patch of field updates to an already-logged interaction. |
| 4 | `summarize_topics` | Condenses a raw voice-note transcript into clean bullet-point "Topics Discussed" text (this is what powers the "Summarize from Voice Note" button in the mockup). |
| 5 | `analyze_sentiment` | Classifies HCP sentiment (positive/neutral/negative) from free text when it isn't explicit. |
| 6 | `suggest_followups` | Generates 2–3 AI-suggested next steps for a logged interaction (the "AI Suggested Follow-ups" list in the mockup). |

Five tools were required; a sixth (`search_hcp`) was added because linking
every interaction to a resolvable HCP record is a prerequisite for reliable
logging and editing.

## Data Model

- `HCP` — id, name, specialty, hospital
- `Interaction` — linked to an HCP; all structured fields from the mockup
  plus `ai_suggested_followups` (JSON) and `source` (`form` or `chat`)
- `ChatLog` — optional raw transcript store for the chat panel

## Setup

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # then fill in GROQ_API_KEY and DATABASE_URL
uvicorn app.main:app --reload --port 8000
```

Create a Postgres database matching `DATABASE_URL` (e.g. `hcp_crm`) before
starting — tables are auto-created on first run via SQLAlchemy.

Get a Groq API key at https://console.groq.com/keys.

#### Environment variables

```dotenv
GROQ_API_KEY=your_key_here
GROQ_MODEL=openai/gpt-oss-20b
GROQ_MODEL_FALLBACK=openai/gpt-oss-120b
DATABASE_URL=postgresql://user:password@localhost:5432/hcp_crm
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. The frontend calls the backend at
`http://localhost:8000` by default (override with `VITE_API_URL`).

## Demoing the 5 Tools

In the chat panel, try:

1. `"Met Dr. Sharma, discussed OncoBoost Phase III data, she seemed positive, shared the brochure"` → triggers `search_hcp` + `log_interaction`.
2. `"Change the sentiment on that last interaction to neutral"` → triggers `edit_interaction`.
3. Paste a rough voice-note transcript and ask *"summarize this for the topics field"* → triggers `summarize_topics`.
4. `"How did Dr. Sharma seem about the trial data?"` → triggers `analyze_sentiment`.
5. `"What should I follow up on?"` → triggers `suggest_followups`.

## Notes / Assumptions

- Voice-note capture itself (audio → text) is out of scope per the task;
  `summarize_topics` assumes a transcript is already available (e.g. from
  browser speech-to-text or a separate ASR service) and focuses on the LLM
  summarization step.
- Auth, multi-tenant orgs, and full HCP CRUD are intentionally minimal —
  the task scope is the Log Interaction screen, not the whole CRM.
- `openai/gpt-oss-20b` is used for fast/cheap structured extraction; the
  larger `openai/gpt-oss-120b` is used for the conversational agent loop and
  follow-up reasoning. These are Groq's current recommended replacements for
  `gemma2-9b-it` and `llama-3.3-70b-versatile` respectively, both of which
  are deprecated and unavailable on Groq's API as of this submission — see
  the model choice note above for details.