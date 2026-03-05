# Kalpana AI Assistant Guide (AGENTS.md)

This file contains comprehensive and crucial context for any AI coding assistant or agent working on the **Kalpana** repository. Read this entirely before proposing architectural changes or writing new features.

---

## 1. Project Overview & Philosophy

**Kalpana** is a privacy-first, AI-driven mental health peer-support platform. It acts as an empathetic conversational agent (a "Listener") that provides immediate psychological first-aid while silently analyzing the transcript in the background (a "Mapper") to extract a root cause. Once a safe threshold is met, the system anonymously matches the user with a real human peer who has survived the exact same life experience.

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
- **Mechanism:** Streams text tokens immediately to the UI (Streamlit). 
- **Dynamic Prompting:** The controller injects changing "Phases" (`Greeting`, `Explore`, `Probe`, `Process`, `Crisis`) into the system prompt based on session state to steer the conversation safely without hardcoded decision trees.

### B. The Clinical Mapper Agent (`backend/agents/mapper.py`)
- **Model:** `gemma3:4b` executing locally via Ollama.
- **Role:** Silent psychological and safety screening.
- **Mechanism:** Runs transparently in the background, reading the most recent transcript turns. It is strictly constrained to output a formatted **JSON Clinical Profile** containing:
  - `clinical_summary`
  - `primary_emotion`
  - `detected_risk`
  - `risk_score` (Int: 1-10)
  - `self_harm_indicators` (Bool)
  - `root_cause_of_the_distress` (String or `-`)

### C. The Controller / Routing Logic
The central application state determines what happens next using the Mapper's JSON output:
1. **Crisis Override:** If `self_harm_indicators == True`, instantly force the `Crisis` phase and stop matchmaking.
2. **Data Lock:** If `root_cause` is identified, lock it into the session state.
3. **Peer Match Threshold:** If conversation `turns >= 4` AND `risk_score >= 5` AND `root_cause` is locked -> Execute Matchmaker.

### D. The Matchmaker (`backend/utils/matchmaker.py`)
- Takes the locked `root_cause` and embeds it using a local HuggingFace `SentenceTransformer` (`bert-base-nli-mean-tokens`).
- Queries a Pinecone Serverless Vector Database.
- Expects an Approximate Nearest Neighbor (Cosine Similarity > 0.50) to return a `peer_id`.

---

## 3. Technology Stack

- **Frontend / State Management:** React 18, Vite, Tailwind CSS v4 (`/kalpana-frontend`). UI redesign is currently replacing the Streamlit MVP.
- **Backend API:** Currently relying on Python Streamlit (`app0.py`) controllers. A dedicated FastAPI backend server is planned to replace it.
- **Concurrency:** `concurrent.futures.ThreadPoolExecutor`
- **Orchestration:** LangChain (`langchain_community.chat_models.ChatOllama`)
- **Local LLM Engine:** Ollama API 
- **LLMs:** `ministral-3:3b` (Listener), `gemma3:4b` (Mapper)
- **Embedding Model:** `bert-base-nli-mean-tokens` (Local execution)
- **Vector Database:** Pinecone (Cloud)
- **Data Persistence:** Local flat JSON files (`/session_logs`)

---

## 4. Repository Structure Highlights

*   `kalpana-frontend`: The primary UI codebase built on React, Vite, and Tailwind v4. Features a strict "WEAL" color palette (Magenta/Deep Purple), a fully mocked WhatsApp-style Audio Recording component (`ChatInput.jsx`), Custom HTML5 Audio Players. (Note: Currently relies on mock requests until the FastAPI backend is ready).
*   `app0.py`: The Main MVP Text-based Streamlit UI and routing controller. Manages streaming chat, concurrent threading, complex state mapping, and log dumping. **Start Here for backend routing.**
*   `app1.py`: Voice/STT variant of the app (Legacy/Alt version). Includes Sarvam Voice API integrations.
*   `backend/cli.py`: The core business logic testbed. Everything in `app0.py` was modeled directly off this CLI runner. Use this for testing deterministic routing without UI overhead.
*   `backend/agents/listener.py`: Contains the `ministral-3:3b` prompt configurations and the Phase Definitions.
*   `backend/agents/mapper.py`: Contains the `gemma3:4b` JSON schema enforcements and parsing safety nets.
*   `backend/utils/matchmaker.py`: SentenceTransformer embedding and Pinecone DB integration.
*   `backend/scripts/warm_up_models.py`: Essential script to preload Ollama weights into RAM/VRAM to prevent Streamlit UI hangs on cold startups.

---

## 5. Coding Standards & Agent Instructions

When writing code for Kalpana, you **must** adhere to the following rules:

1.  **Do Not Mutate State Directly in Agents:** The LLM agents `listener.py` and `mapper.py` are strictly I/O pipelines. All session state updates, risk threshold evaluation, and data locking must occur in the central controller (`app0.py` or `cli.py`).
2.  **Defensive JSON Parsing:** The Mapper agent uses small local models (`gemma3:4b`) that occasionally hallucinate or return empty `{}` objects if starved of context. Always assume the Mapper output pipeline can fail and build bulletproof `try/except` fallback objects.
3.  **Local Context Bounds:** If modifying the Mapper prompt, never pass the entire chat history. Keep transcript injection to `raw_history[-4:]` or smaller context windows. Massive contexts crash the JSON grammar parser of 4B models. 
4.  **No Cloud LLMs:** Do not add dependencies for `openai`, `anthropic`, etc., unless it's strictly for local debugging. Production code must use Ollama.
5.  **Logging synchronization:** The JSON logs appended in `app0.py` must record the exact `phase` and `context` used at the moment of generation, not the predicted phase for the next turn.

---

## 6. Future Roadmap & Development Priorities

If tasked with adding features, these are the prioritized roadmap items:

-   **Real-Time Chatrooms:** Implement WebSockets (e.g., FastAPI) to seamlessly transition users from the AI interface into an encrypted, live peer-to-peer room once a match is found and accepted.
-   **AI Chat Moderation:** Deploy a lightweight safety agent to passively monitor live peer chats for community guideline breaches or shared harmful ideation.
-   **PII Scrubbing Pipeline:** Integrate Microsoft Presidio (`utils/privacy.py`) forcefully into `app0.py` to scrub names/locations from the chat before they hit the LLMs or the session logs.
-   **Voice Interface:** Stabilize and port the Sarvam STT/TTS models from `app1.py` into the `app0.py` architecture for users who prefer voice-based peer support.
