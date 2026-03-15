# Kalpana AI Assistant Guide (AGENTS.md)

This file contains comprehensive and crucial context for any AI coding assistant or agent working on the **Kalpana** repository. Read this entirely before proposing architectural changes or writing new features.

---

## 1. Project Overview & Philosophy

**Kalpana** is a privacy-first, AI-driven mental health peer-support platform. It acts as an empathetic conversational agent (a "Listener") that provides immediate psychological first-aid while silently analyzing the transcript in the background (a "Mapper") to extract a root cause. Once a safe threshold is met, the system anonymously matches the user with a real human peer who has survived the exact same life experience, and allows them to **schedule a connection time**.

**Core Principles:**
- **Privacy By Design:** All conversational AI executes completely locally. We never send sensitive mental health transcripts to OpenAI, Anthropic, or any third-party APIs.
- **Safety First:** We utilize deterministic Python routing logic (not LLM decisions) to evaluate self-harm vectors and trigger crisis modes.
- **Decoupled Architecture:** Empathy Generation (UX) and Psychological Profiling (Data Extraction) are strictly separated into two concurrent AI agents.

---

## 2. System Architecture (The Dual-Agent Setup)

The backend handles two parallel tasks for every single user input using Python's `concurrent.futures.ThreadPoolExecutor`.

### A. The Listener Agent (`backend/agents/listener.py`)
- **Model:** `ministral-3:3b` executing locally via Ollama.
- **Role:** Providing real-time empathetic psychological support.
- **Mechanism:** Streams text tokens via **Server-Sent Events (SSE)** to the React frontend through FastAPI's `StreamingResponse`. Each token is sent as `data: {"type": "chunk", "content": "..."}`.
- **Dynamic Prompting:** The controller injects changing "Phases" (`Greeting`, `Explore`, `Probe`, `Process`, `Crisis`) into the system prompt based on session state.

### B. The Clinical Mapper Agent (`backend/agents/mapper.py`)
- **Model:** `gemma3:4b` executing locally via Ollama.
- **Role:** Silent psychological and safety screening.
- **Mechanism:** Runs transparently in the background, reading the most recent transcript turns (capped to last 5 messages). It is strictly constrained to output a formatted **JSON Clinical Profile** containing:
  - `clinical_summary`
  - `primary_emotion`
  - `detected_risk`
  - `risk_score` (Int: 1-10)
  - `self_harm_indicators` (Bool)
  - `root_cause_of_the_distress` (String or `-`)
- **Known Fragility:** `gemma3:4b` can hallucinate broken JSON if given a confusing or duplicate prompt. The `except Exception as e` block in `mapper.py` logs `[MAPPER ERROR]` and returns a safe fallback profile so the system never crashes.

### C. The Controller / Routing Logic (`backend/api.py`)
The FastAPI `POST /api/chat` endpoint manages all state transitions using the Mapper's JSON output:
1. **Crisis Override:** If `self_harm_indicators == True`, instantly force the `Crisis` phase and stop matchmaking.
2. **Data Lock:** If `root_cause` is identified (not `-`), lock it into the session state.
3. **Peer Match Threshold:** If conversation `history_len >= 4` AND `risk_score >= 5` AND `root_cause` is locked → Execute Matchmaker.
4. **Availability Lookup:** After a Pinecone match is found, the `peer_id` is used to look up the peer's `availability` array from `data/peers.json` and attach it to the match metadata.
5. **Crisis Intercept:** If `self_harm_indicators == True` OR `risk_score >= CRISIS_RISK_THRESHOLD (8)`, set `crisis_intercept = True`, skip Pinecone entirely, and send it in the final SSE metadata event. This bypasses peer scheduling and triggers the `CrisisModal` in the frontend.
6. **SSE Metadata Event:** Every turn ends with `data: {"type": "metadata", "peer_group_match": ..., "crisis_intercept": bool}\n\n`.

### D. The Matchmaker (`backend/utils/matchmaker.py`)
- Takes the locked `root_cause` and embeds it using a local HuggingFace `SentenceTransformer` (`bert-base-nli-mean-tokens`).
- Queries a Pinecone Serverless Vector Database.
- Cosine Similarity threshold is **0.70** (raised from 0.50). Matches below this threshold return `None`.
- Returns a `metadata` dict with `peer_id` injected as `metadata["peer_id"] = match["id"]`.

---

## 3. Technology Stack

- **Frontend:** React 18, Vite, Tailwind CSS v4 (`/kalpana-frontend`). **This is the ACTIVE, LIVE UI** — not Streamlit. Uses the WEAL color palette (Magenta `#D81B60` / Deep Purple `#1a0a2e`).
- **Backend API:** FastAPI (`backend/api.py`) with `uvicorn`. **This has replaced Streamlit as the active backend.** Run with `uvicorn backend.api:app --reload` from the project root.
- **Streaming:** Server-Sent Events (SSE) via FastAPI `StreamingResponse`. The frontend uses `response.body.getReader()` to consume the stream.
- **Concurrency:** `concurrent.futures.ThreadPoolExecutor` (Listener streams while Mapper runs in a thread).
- **Orchestration:** LangChain (`langchain_community.chat_models.ChatOllama`)
- **Local LLM Engine:** Ollama API
- **LLMs:** `ministral-3:3b` (Listener), `gemma3:4b` (Mapper)
- **Embedding Model:** `bert-base-nli-mean-tokens` (Local execution via `sentence-transformers`)
- **Vector Database:** Pinecone Serverless (Cloud)
- **Data Persistence:**
  - `session_logs/session_logN.json` — sequential integer-named session logs (e.g., `session_log1.json`, `session_log2.json`). Created instantly at session start.
  - `data/peers.json` — peer profile database including `availability` arrays.
  - `data/appointments.json` — saved peer scheduling appointments (auto-created by the `/api/schedule` endpoint).

---

## 4. Repository Structure Highlights

- `kalpana-frontend/` — **Primary active UI.** React 18 + Vite + Tailwind v4.
  - `src/App.jsx` — Main app orchestrator. Manages SSE stream consumption, message state, `peerMatch` state, `isCrisisMode` state, and session ID generation. When `payload.crisis_intercept === true` is received, it sets `isCrisisMode = true`, clears any peer match, and locks the chat input.
  - `src/components/PeerMatchModal.jsx` — The Peer Scheduling Modal. Displays a **custom div-based dropdown** (not a native `<select>`) of the matched peer's availability slots from `data/peers.json`. Shows the matched peer's `root_cause` and `clinical_notes` for context. Calls `POST /api/schedule` to lock in an appointment. Has `idle → connecting → connected` connection state lifecycle.
  - `src/components/CrisisModal.jsx` — High-priority crisis intervention overlay. Rendered when `isCrisisMode = true`. **Supercedes the PeerMatchModal** — both cannot show simultaneously. Provides professional help resources.
  - `src/components/ChatInput.jsx` — Mocked WhatsApp-style audio input UI. Accepts an `isInputLocked` prop that disables sending when in crisis mode.
  - `src/components/MessageBubble.jsx` — Individual chat message display.
- `backend/api.py` — **PRIMARY BACKEND CONTROLLER.** FastAPI app. Contains all session management, SSE streaming, concurrent agent execution, availability lookup, and the `/api/schedule` endpoint. **Start here for all backend routing.**
- `backend/agents/listener.py` — `ministral-3:3b` prompt + Phase definitions. I/O pipeline only.
- `backend/agents/mapper.py` — `gemma3:4b` JSON profiler. I/O pipeline only. Has `[DEBUG RAW MAPPER OUTPUT]` print for debugging.
- `backend/utils/matchmaker.py` — Pinecone embedding + ANN query logic.
- `backend/scripts/warm_up_models.py` — Preloads Ollama model weights to prevent cold-start hangs.
- `backend/cli.py` — CLI testbed for routing logic without UI overhead. Use this for isolated backend testing.
- `data/peers.json` — Peer database. Each peer has: `peer_id`, `primary_emotion`, `detected_risk`, `risk_score`, `clinical_notes`, `root_cause_of_the_distress`, and an **`availability` array** of `[{"start_time": "ISO-8601"}]` objects.
- `app0.py` — Legacy Streamlit MVP. No longer the active server, kept for reference only.
- `app1.py` — Legacy Streamlit voice/STT variant. Includes Sarvam Voice API integrations.
- `session_logs/` — Sequential JSON logs (`session_log1.json`, `session_log2.json`, ...).

---

## 5. Coding Standards & Agent Instructions

When writing code for Kalpana, you **must** adhere to the following rules:

1. **Do Not Mutate State in Agents:** `listener.py` and `mapper.py` are strictly I/O pipelines. All session state updates, risk threshold evaluation, and data locking must occur in `backend/api.py` (the controller).
2. **Defensive JSON Parsing:** The Mapper agent uses `gemma3:4b` which can hallucinate broken JSON. Always wrap the Mapper call in `try/except` and return a safe fallback profile. Log the error with `[MAPPER ERROR]`.
3. **Local Context Bounds:** Never pass the full chat history to the Mapper. The transcript injected must be **user messages only** from the last 3 turns (`req.chat_history[-6:]` filtered to `msg.role == "user"`, then capped to 3). **Do NOT include Kalpana's assistant responses** — they are clinically irrelevant for profiling and their verbosity exhausts the 4B model's input token budget, causing empty `{}` JSON output on longer conversations.
4. **No Cloud LLMs:** Do not add `openai`, `anthropic`, etc. Production code must use Ollama.
5. **Logging Synchronization:** Session logs in `session_logs/` must record the `phase` and `context` used at the moment of generation, NOT the predicted phase for the next turn.
6. **SSE Packet Format:** The final SSE metadata event MUST be `data: {"type": "metadata", "peer_group_match": ..., "crisis_intercept": bool}\n\n`. In `App.jsx`, `payload.crisis_intercept === true` takes priority and triggers `CrisisModal`. `payload.type === 'metadata'` (without crisis) triggers `PeerMatchModal`. Any deviation will silently break the UI.
7. **Custom Dropdowns Only:** Do not use native HTML `<select>/<option>` for dropdowns in the React frontend. The WEAL dark theme makes options invisible on most OS/browsers. Use fully custom div-based dropdowns as established in `PeerMatchModal.jsx`.
8. **Availability Pre-Seeding:** When building the `peer_match` dict in `api.py`, always set `peer_match["availability"] = []` before attempting the `peers.json` lookup. This ensures the frontend never receives `undefined` for this key.

---

## 6. API Endpoints (FastAPI — `backend/api.py`)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/chat` | Main SSE streaming endpoint. Accepts `{session_id, chat_history}`. Streams listener tokens, then fires final `metadata` event with peer match + availability. |
| `POST` | `/api/schedule` | Saves a scheduled appointment. Accepts `{session_id, peer_id, selected_slot}`. Appends to `data/appointments.json`. |

---

## 7. Current Development Status (as of 2026-03-15)

| Feature | Status |
|---------|--------|
| FastAPI SSE Backend | ✅ Live & Active |
| React Frontend | ✅ Live & Active |
| Session Logging (`session_logN.json`) | ✅ Working |
| Dual-Agent Concurrency | ✅ Working |
| Pinecone Peer Matching (threshold: 0.70) | ✅ Working |
| Peer Scheduling Modal with Custom Dropdown | ✅ Implemented |
| `/api/schedule` Endpoint → `appointments.json` | ✅ Implemented |
| Availability Lookup from `peers.json` | ✅ Implemented |
| Crisis Routing (`crisis_intercept` flag + `CrisisModal.jsx`) | ✅ Implemented (partial — CrisisModal UI content TBD) |
| PII Scrubbing (Microsoft Presidio) | 🔲 Planned |
| Real-Time WebSocket Chatrooms | 🔲 Planned |
| Voice Interface (Sarvam STT/TTS) | 🔲 Future |

---

## 8. Future Roadmap & Development Priorities

-   **Crisis Routing Protocol:** When the Mapper detects `self_harm_indicators = True` OR `risk_score >= 8`, bypass Pinecone entirely and send `"crisis_intercept": true` in the SSE metadata. The frontend should render a distinct `CrisisModal.jsx` with professional help resources. Full plan in `crisis_routing_plan.md`.
-   **Real-Time Chatrooms:** FastAPI WebSocket room to transition user from AI interface to live peer chat once connection is scheduled/accepted.
-   **AI Chat Moderation:** Lightweight safety agent to passively monitor peer chatrooms for harmful ideation.
-   **PII Scrubbing Pipeline:** Integrate Microsoft Presidio into `api.py` to scrub names/locations before they reach the LLMs or session logs.
-   **Voice Interface:** Stabilize and port Sarvam STT/TTS from `app1.py` into the FastAPI + React architecture.
