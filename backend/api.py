import os
import sys
import uuid
import json
import concurrent.futures

# --- PATH FIX ---
# Add the 'backend' directory to the python path so it can find its own modules
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from agents.listener import ListenerAgent
from agents.mapper import ClinicalMapperAgent
from utils.matchmaker import PeerMatchmaker
from langchain_core.messages import HumanMessage, AIMessage

app = FastAPI(title="Kalpana Web API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components on startup
print("Initializing AI components...")
listener_agent = ListenerAgent()
mapper_agent = ClinicalMapperAgent()
matchmaker = PeerMatchmaker()
print("AI components ready.")

# In-memory store for sessions (for demo purposes)
sessions = {}

class ChatMessage(BaseModel):
    session_id: str
    message: str

@app.post("/api/chat")
async def chat_endpoint(payload: ChatMessage):
    session_id = payload.session_id
    user_input = payload.message

    if session_id not in sessions:
        sessions[session_id] = {
            "history": [],
            "langchain_history": [],
            "session_root_cause": "-",
            "session_risk_score": 1
        }
    
    state = sessions[session_id]
    
    # 1. Start Mapping asynchronously
    map_future = None
    with concurrent.futures.ThreadPoolExecutor() as executor:
        map_future = executor.submit(mapper_agent.analyze, user_input)

    # 2. Add user message to langchain history
    state["langchain_history"].append(HumanMessage(content=user_input))

    # 3. Wait for mapper to process
    profile = map_future.result()

    current_risk_score = profile.get("risk_score", 1)
    risk_level = profile.get("detected_risk", "low").lower()
    self_harm = profile.get("self_harm_indicators", False)

    # State-Locking Logic
    detected_cause = profile.get("root_cause_of_the_distress", "-")
    if state["session_root_cause"] == "-" and detected_cause != "-":
        state["session_root_cause"] = detected_cause
        state["session_risk_score"] = current_risk_score
    elif state["session_root_cause"] != "-":
        profile["root_cause_of_the_distress"] = state["session_root_cause"]
        if current_risk_score == 1:
            current_risk_score = state["session_risk_score"]

    # --- Phase Derivation ---
    context_summary = profile.get("clinical_summary", "")
    candidates = []
    if self_harm:
        candidates.append((0, "crisis"))
    if state["session_root_cause"] != "-":
        candidates.append((1, "process"))
    if current_risk_score >= 5:
        candidates.append((2, "probe"))
    candidates.append((3, "explore"))
    current_phase = min(candidates, key=lambda x: x[0])[1]

    # Generate response from Listener
    full_listener_response = ""
    for chunk in listener_agent.generate_stream(state["langchain_history"], current_phase, context_summary):
        full_listener_response += chunk

    state["langchain_history"].append(AIMessage(content=full_listener_response))
    
    # Check for match
    state["history"].extend([{"role": "user", "content": user_input}, {"role": "assistant", "content": full_listener_response}])
    
    match_data = None
    if state["session_root_cause"] != "-" and current_risk_score >= 5 and len(state["history"]) >= 4:
        match = matchmaker.find_match(state["session_root_cause"])
        if match:
            match_data = {
                "root_cause": state["session_root_cause"],
                "peer": match
            }

    return {
        "response": full_listener_response,
        "match": match_data
    }

# Mount the frontend folder to serve index.html
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
