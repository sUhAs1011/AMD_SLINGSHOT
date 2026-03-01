import streamlit as st
import uuid
import datetime
import json
import os
import concurrent.futures
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# Import backend modules
from backend.agents.listener import ListenerAgent
from backend.agents.mapper import ClinicalMapperAgent
from backend.utils.matchmaker import PeerMatchmaker

# --- UI Customization ---
st.set_page_config(page_title="Kalpana - Peer Support", page_icon="🌿", layout="centered")

def inject_custom_css():
    st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #F8F9FA;
        color: #2D3748;
    }
    
    /* Header */
    header {
        background-color: transparent !important;
    }
    
    /* Chat inputs */
    .stChatInputContainer {
        border-radius: 20px !important;
        border: 1px solid #E2E8F0 !important;
        background-color: white !important;
    }
    
    /* Chat message styling */
    .stChatMessage {
        background-color: transparent !important;
    }
    
    /* Title Styling */
    .title-wrapper {
        text-align: center;
        padding-bottom: 2rem;
    }
    .title-wrapper h1 {
        color: #2F855A;
        font-weight: 700;
        margin-bottom: 0px;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialization ---
@st.cache_resource
def load_agents():
    return ListenerAgent(), ClinicalMapperAgent(), PeerMatchmaker()

def init_session():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.raw_history = []
        st.session_state.messages = []
        
        # Backend states
        st.session_state.current_phase = "explore"
        st.session_state.context_summary = ""
        st.session_state.session_root_cause = "-"
        st.session_state.session_risk_score = 1
        
        # Logging setup
        os.makedirs("session_logs", exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.log_file = f"session_logs/session_{st.session_state.session_id}_{timestamp}.json"
        
        with open(st.session_state.log_file, "w") as f:
            json.dump([], f)
            
        # Greeting
        greeting = "Hi there. I'm Kalpana. I'm here to listen and support you. What's on your mind today?"
        st.session_state.messages.append({"role": "assistant", "content": greeting})
        st.session_state.raw_history.append({"role": "assistant", "content": greeting})

def main():
    inject_custom_css()
    
    st.markdown("<div class='title-wrapper'><h1>🌿 Kalpana</h1><p style='color: #718096;'>A safe space to share what's on your mind.</p></div>", unsafe_allow_html=True)
    
    listener_agent, mapper_agent, matchmaker = load_agents()
    init_session()

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if user_input := st.chat_input("Type your message here..."):
        # Display user message
        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # --- Reconstruct Langchain history for Listener ---
        langchain_history = []
        for msg in st.session_state.raw_history:
            if msg["role"] == "user":
                langchain_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_history.append(AIMessage(content=msg["content"]))
        langchain_history.append(HumanMessage(content=user_input))

        # --- Reconstruct context transcript for Mapper ---
        transcript_lines = []
        for msg in st.session_state.raw_history[-4:]:
            speaker = "User" if msg["role"] == "user" else "Kalpana"
            transcript_lines.append(f"{speaker}: {msg['content']}")
        transcript_lines.append(f"User: {user_input}")
        full_context_str = "\n".join(transcript_lines)

        # Process Listener and Mapper concurrently
        with st.chat_message("assistant"):
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Submit mapper task first
                future_mapper = executor.submit(mapper_agent.analyze, full_context_str)
                
                # Stream the listener response
                stream = listener_agent.generate_stream(
                    langchain_history, 
                    st.session_state.current_phase, 
                    st.session_state.context_summary
                )
                full_listener_response = st.write_stream(stream)
                
                # Wait for mapper profile (if it's not done yet, this will block slightly)
                profile = future_mapper.result()

        st.session_state.messages.append({"role": "assistant", "content": full_listener_response})

        # --- Process Mapper Results (State Management) ---
        current_risk_score = profile.get("risk_score", 1)
        risk_level = profile.get("detected_risk", "low").lower()
        self_harm = profile.get("self_harm_indicators", False)
        
        # Evaluate Root Cause
        extracted_root_cause = profile.get("root_cause_of_the_distress", "-")
        if extracted_root_cause != "-" and st.session_state.session_root_cause == "-":
            st.session_state.session_root_cause = extracted_root_cause
            profile["root_cause_of_the_distress"] = st.session_state.session_root_cause
        elif st.session_state.session_root_cause != "-":
            # Restore locked state in profile for logging
            profile["root_cause_of_the_distress"] = st.session_state.session_root_cause
            
        st.session_state.session_risk_score = max(st.session_state.session_risk_score, current_risk_score)

        # Log action determination
        if self_harm:
            action = "escalate_to_human"
        elif st.session_state.session_root_cause != "-" and st.session_state.session_risk_score >= 5:
            action = "route_to_peer_group"
        else:
            action = "continue_listening"

        # Capture the phase and context that were actually used to generate this turn's response
        used_phase = st.session_state.current_phase
        used_context = st.session_state.context_summary

        # Update next turn's context
        st.session_state.context_summary = profile.get("clinical_summary", "")

        # Target next phase
        candidates = []
        if self_harm:
            candidates.append((0, "crisis"))
        if st.session_state.session_root_cause != "-":
            candidates.append((1, "process"))
        if current_risk_score >= 5:
            candidates.append((2, "probe"))
        
        # Greeting phase detection (very short input + low risk)
        if len(user_input.split()) < 5 and current_risk_score == 1:
            candidates.append((3, "greeting"))
            
        candidates.append((4, "explore"))
        st.session_state.current_phase = min(candidates, key=lambda x: x[0])[1]

        # --- Peer Matchmaker ---
        peer_group = None
        # We require at least 4 items in raw_history (including the 2 being added this turn)
        if st.session_state.session_root_cause != "-" and current_risk_score >= 5 and (len(st.session_state.raw_history) + 2) >= 4:
            match = matchmaker.find_match(st.session_state.session_root_cause)
            if match:
                peer_id = match.get("peer_id", "Unknown Peer")
                st.success(f"**Peer Match Found:** I've found someone who has gone through something similar. Talking to them might help you feel better. ([{peer_id}])")
                st.button("Connect", key=f"connect_btn_{len(st.session_state.raw_history)}")
                peer_group = match

        # --- Logging ---
        log_entry = {
            "user_input": user_input,
            "assistant_response": full_listener_response,
            "listener_phase": used_phase,
            "listener_context": used_context,
            "action": action,
            "peer_group_match": peer_group,
            "clinical_profile": profile
        }
        
        with open(st.session_state.log_file, "r") as f:
            logs = json.load(f)
            
        logs.append(log_entry)
        
        with open(st.session_state.log_file, "w") as f:
            json.dump(logs, f, indent=4)

        # Append to raw_history
        st.session_state.raw_history.append({"role": "user", "content": user_input})
        st.session_state.raw_history.append({"role": "assistant", "content": full_listener_response})

if __name__ == "__main__":
    main()
