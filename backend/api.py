# backend/api.py
import json
import os
import datetime
import base64
import concurrent.futures
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from agents.listener import ListenerAgent
from agents.mapper import ClinicalMapperAgent
from utils.matchmaker import PeerMatchmaker
from utils.sarvam_api import transcribe_audio, translate_text, synthesize_speech

# ---------------------------------------------------------------------------
# Global State
# ---------------------------------------------------------------------------
ACTIVE_SESSIONS: dict = {}
listener_agent = None
mapper_agent = None
matchmaker = None
CRISIS_RISK_THRESHOLD = 8
VOICE_LANGUAGE_CONFIDENCE_THRESHOLD = 0.70
DEFAULT_VOICE_LANGUAGE = "en-IN"

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

class ScheduleRequest(BaseModel):
    session_id: str
    peer_id: str
    selected_slot: str


class TTSRequest(BaseModel):
    text: str
    session_id: str | None = None
    target_language_code: str | None = None

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
            "preferred_voice_language": DEFAULT_VOICE_LANGUAGE,
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

    # Build transcript for the Mapper (user messages only, last 3 turns)
    # NOTE: We intentionally exclude long Kalpana responses — they eat the 4B model's
    # input budget and are not clinically relevant for profiling the USER's state.
    recent = req.chat_history[-6:]  # pull last 6, then filter
    transcript_lines = []
    for msg in recent:
        if msg.role == "user":
            transcript_lines.append(f"User: {msg.content}")
    full_context_str = "\n".join(transcript_lines[-3:])  # cap at last 3 user turns

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
        crisis_intercept = bool(self_harm or current_risk_score >= CRISIS_RISK_THRESHOLD)

        # Root cause state-locking
        extracted_root_cause = profile.get("root_cause_of_the_distress", "-")
        if extracted_root_cause != "-" and session["session_root_cause"] == "-":
            session["session_root_cause"] = extracted_root_cause
        elif session["session_root_cause"] != "-":
            profile["root_cause_of_the_distress"] = session["session_root_cause"]

        session["session_risk_score"] = max(session["session_risk_score"], current_risk_score)

        # Action determination
        if crisis_intercept:
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
        if crisis_intercept:
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
        if (not crisis_intercept) and session["session_root_cause"] != "-" and current_risk_score >= 5 and history_len >= 4:
            match = matchmaker.find_match(session["session_root_cause"])
            if match:
                peer_match = match
                # Always pre-seed availability so frontend never gets undefined
                peer_match["availability"] = []
                # Intercept match and attach dynamic availability from peers.json
                try:
                    peers_path = os.path.join(PROJECT_ROOT, "data", "peers.json")
                    with open(peers_path, "r", encoding="utf-8") as f:
                        peers_db = json.load(f)
                    matched_pid = peer_match.get("peer_id", "")
                    print(f"[DEBUG] Looking up availability for peer_id='{matched_pid}'")
                    found = False
                    for p in peers_db:
                        if p.get("peer_id") == matched_pid:
                            peer_match["availability"] = p.get("availability", [])
                            print(f"[DEBUG] Found availability: {peer_match['availability']}")
                            found = True
                            break
                    if not found:
                        print(f"[DEBUG] peer_id='{matched_pid}' not found in peers.json!")
                except Exception as e:
                    print(f"[API ERROR] Failed to load availability array: {e}")
                    peer_match["availability"] = []

        # Log the turn
        log_entry = {
            "user_input": user_input,
            "assistant_response": full_response,
            "listener_phase": used_phase,
            "listener_context": used_context,
            "action": action,
            "crisis_intercept": crisis_intercept,
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

        # Send the final metadata event (peer match info + crisis routing flag)
        yield f"data: {json.dumps({'type': 'metadata', 'peer_group_match': peer_match, 'crisis_intercept': crisis_intercept})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Voice STT Endpoint
# ---------------------------------------------------------------------------
@app.post("/api/transcribe")
async def transcribe_voice(audio: UploadFile = File(...), session_id: str | None = Form(None)):
    try:
        audio_bytes = await audio.read()
        if not audio_bytes:
            return {"status": "error", "message": "Uploaded audio file is empty."}

        stt_result = transcribe_audio(
            audio_bytes=audio_bytes,
            filename=audio.filename or "voice_note.webm",
            content_type=audio.content_type or "audio/webm",
        )

        detected_language = stt_result.get("detected_language_code") or DEFAULT_VOICE_LANGUAGE
        language_probability = float(stt_result.get("language_probability", 0.0))
        effective_voice_language = detected_language

        if session_id:
            session = get_or_create_session(session_id)
            effective_voice_language = session.get("preferred_voice_language", DEFAULT_VOICE_LANGUAGE)
            if language_probability >= VOICE_LANGUAGE_CONFIDENCE_THRESHOLD:
                session["preferred_voice_language"] = detected_language
                effective_voice_language = detected_language

        return {
            "status": "success",
            "transcript_en": stt_result.get("transcript_en", ""),
            "detected_language_code": detected_language,
            "language_probability": language_probability,
            "effective_voice_language": effective_voice_language,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# Voice TTS Endpoint
# ---------------------------------------------------------------------------
@app.post("/api/tts")
async def tts_response(req: TTSRequest):
    try:
        clean_text = (req.text or "").strip()
        if not clean_text:
            return {"status": "error", "message": "Text cannot be empty."}

        target_language = req.target_language_code
        if not target_language and req.session_id:
            session = get_or_create_session(req.session_id)
            target_language = session.get("preferred_voice_language", DEFAULT_VOICE_LANGUAGE)
        if not target_language:
            target_language = DEFAULT_VOICE_LANGUAGE

        spoken_text = clean_text
        try:
            spoken_text = translate_text(clean_text, target_language)
        except Exception as translation_error:
            print(f"[VOICE WARN] Translation failed, falling back to original text: {translation_error}")
            spoken_text = clean_text

        tts_result = synthesize_speech(spoken_text, target_language)
        audio_base64 = base64.b64encode(tts_result["audio_bytes"]).decode("utf-8")

        return {
            "status": "success",
            "audio_base64": audio_base64,
            "mime_type": tts_result.get("mime_type", "audio/mpeg"),
            "spoken_text": spoken_text,
            "spoken_language_code": target_language,
            "tts_model": tts_result.get("tts_model"),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------------
# Peer Scheduling Endpoint
# ---------------------------------------------------------------------------
@app.post("/api/schedule")
async def schedule_connection(req: ScheduleRequest):
    try:
        appointments_file = os.path.join(PROJECT_ROOT, "data", "appointments.json")
        if not os.path.exists(appointments_file):
            with open(appointments_file, "w", encoding="utf-8") as f:
                json.dump([], f)
                
        with open(appointments_file, "r", encoding="utf-8") as f:
            appts = json.load(f)
            
        appt_record = {
            "session_id": req.session_id,
            "peer_id": req.peer_id,
            "selected_slot": req.selected_slot,
            "created_at": datetime.datetime.now().isoformat()
        }
        appts.append(appt_record)
        
        with open(appointments_file, "w", encoding="utf-8") as f:
            json.dump(appts, f, indent=4)
            
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
