# backend/api.py
import json
import os
import datetime
import concurrent.futures
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from agents.listener import ListenerAgent
from agents.mapper import ClinicalMapperAgent
from utils.matchmaker import PeerMatchmaker

# ---------------------------------------------------------------------------
# Global State
# ---------------------------------------------------------------------------
ACTIVE_SESSIONS: dict = {}
listener_agent = None
mapper_agent = None
matchmaker = None

# ---------------------------------------------------------------------------
# Lifespan – Load heavy models once at startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global listener_agent, mapper_agent, matchmaker
    print("[STARTUP] Loading Listener Agent...", flush=True)
    listener_agent = ListenerAgent()
    print("[STARTUP] Loading Mapper Agent...", flush=True)
    mapper_agent = ClinicalMapperAgent()
    print("[STARTUP] Connecting to Pinecone...", flush=True)
    matchmaker = PeerMatchmaker()
    print("[STARTUP] All systems ready.", flush=True)
    yield
    # Shutdown – nothing to clean up

app = FastAPI(lifespan=lifespan)

# Allow the Vite dev server origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session_id: str
    chat_history: list[ChatMessage]

# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_or_create_session(session_id: str) -> dict:
    if session_id not in ACTIVE_SESSIONS:
        log_dir = os.path.join(PROJECT_ROOT, "session_logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # Generate sequential log filename like cli.py
        existing_logs = [f for f in os.listdir(log_dir) if f.startswith("session_log") and f.endswith(".json")]
        next_index = len(existing_logs) + 1
        log_file = os.path.join(log_dir, f"session_log{next_index}.json")
        
        with open(log_file, "w") as f:
            json.dump([], f)

        ACTIVE_SESSIONS[session_id] = {
            "current_phase": "explore",
            "context_summary": "",
            "session_root_cause": "-",
            "session_risk_score": 1,
            "log_file": log_file,
        }
    return ACTIVE_SESSIONS[session_id]

# ---------------------------------------------------------------------------
# SSE Streaming Endpoint
# ---------------------------------------------------------------------------
@app.post("/api/chat")
async def chat(req: ChatRequest):
    session = get_or_create_session(req.session_id)
    user_input = req.chat_history[-1].content if req.chat_history else ""

    # Build LangChain history for the Listener
    langchain_history = []
    for msg in req.chat_history:
        if msg.role == "user":
            langchain_history.append(HumanMessage(content=msg.content))
        else:
            langchain_history.append(AIMessage(content=msg.content))

    # Build transcript for the Mapper (last 4 messages + current)
    recent = req.chat_history[-5:]  # last 4 + current
    transcript_lines = []
    for msg in recent:
        speaker = "User" if msg.role == "user" else "Kalpana"
        transcript_lines.append(f"{speaker}: {msg.content}")
    full_context_str = "\n".join(transcript_lines)

    def generate():
        # Fire the Mapper in a background thread
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_mapper = executor.submit(mapper_agent.analyze, full_context_str)

            # Stream listener response word-by-word
            full_response = ""
            for chunk in listener_agent.generate_stream(
                langchain_history,
                session["current_phase"],
                session["context_summary"],
            ):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            # Wait for the Mapper to finish
            profile = future_mapper.result()

        # --- State Management (mirrors app0.py / cli.py logic) ---
        current_risk_score = profile.get("risk_score", 1)
        self_harm = profile.get("self_harm_indicators", False)

        # Root cause state-locking
        extracted_root_cause = profile.get("root_cause_of_the_distress", "-")
        if extracted_root_cause != "-" and session["session_root_cause"] == "-":
            session["session_root_cause"] = extracted_root_cause
        elif session["session_root_cause"] != "-":
            profile["root_cause_of_the_distress"] = session["session_root_cause"]

        session["session_risk_score"] = max(session["session_risk_score"], current_risk_score)

        # Action determination
        if self_harm:
            action = "escalate_to_human"
        elif session["session_root_cause"] != "-" and session["session_risk_score"] >= 5:
            action = "route_to_peer_group"
        else:
            action = "continue_listening"

        # Capture used phase/context before updating for next turn
        used_phase = session["current_phase"]
        used_context = session["context_summary"]

        # Update context for next turn
        session["context_summary"] = profile.get("clinical_summary", "")

        # Phase derivation (priority candidates pattern)
        candidates = []
        if self_harm:
            candidates.append((0, "crisis"))
        if session["session_root_cause"] != "-":
            candidates.append((1, "process"))
        if current_risk_score >= 5:
            candidates.append((2, "probe"))
        if len(user_input.split()) < 5 and current_risk_score == 1:
            candidates.append((3, "greeting"))
        candidates.append((4, "explore"))
        session["current_phase"] = min(candidates, key=lambda x: x[0])[1]

        # Peer Matchmaker
        peer_match = None
        history_len = len(req.chat_history)
        if session["session_root_cause"] != "-" and current_risk_score >= 5 and history_len >= 4:
            match = matchmaker.find_match(session["session_root_cause"])
            if match:
                peer_match = match

        # Log the turn
        log_entry = {
            "user_input": user_input,
            "assistant_response": full_response,
            "listener_phase": used_phase,
            "listener_context": used_context,
            "action": action,
            "peer_group_match": peer_match,
            "clinical_profile": profile,
        }
        try:
            with open(session["log_file"], "r") as f:
                logs = json.load(f)
            logs.append(log_entry)
            with open(session["log_file"], "w") as f:
                json.dump(logs, f, indent=4)
        except Exception as e:
            print(f"[LOG ERROR]: {e}")

        # Send the final metadata event (peer match info)
        yield f"data: {json.dumps({'type': 'metadata', 'peer_group_match': peer_match})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
