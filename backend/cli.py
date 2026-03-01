import uuid
import json
import os
import concurrent.futures
from langchain_core.messages import HumanMessage, AIMessage


from agents.listener import ListenerAgent
from agents.mapper import ClinicalMapperAgent
from utils.matchmaker import PeerMatchmaker

def run_cli():
    session_id = str(uuid.uuid4())
    raw_history = []
    log_dir = "session_logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate sequential log filename
    existing_logs = [f for f in os.listdir(log_dir) if f.startswith("session_log") and f.endswith(".json")]
    next_index = len(existing_logs) + 1
    log_file = os.path.join(log_dir, f"session_log{next_index}.json")
    
    with open(log_file, "w") as f:
        json.dump([], f)
        
    print("=" * 60)
    print("KALPANA 6.0 - EMOTIONAL SUPPORT CLI")
    print("=" * 60)
    print(f"\n[SYSTEM]: Initializing components... (this may take a moment)")
    
    print(" - Loading Listener Agent...", end="", flush=True)
    listener_agent = ListenerAgent()
    print(" Ready.")
    
    print(" - Loading Mapper Agent...", end="", flush=True)
    mapper_agent = ClinicalMapperAgent()
    print(" Ready.")
    
    print(" - Connecting to Vector Database...", end="", flush=True)
    matchmaker = PeerMatchmaker()
    print(" Ready.")
    
    print(f"\n[SUCCESS]: Session started [ID: {session_id}]")
    print("Type 'quit' or 'exit' to end the session.\n")
    print("-" * 60)
    session_root_cause = "-" # State-locking variable
    current_phase = "explore"   # Safe default for Turn 1
    context_summary = ""        # No clinical context yet
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ['quit', 'exit']:
                print("\nEnding session. Goodbye!")
                break
            if not user_input.strip():
                continue

            langchain_history = []
            for msg in raw_history:
                if msg["role"] == "user":
                    langchain_history.append(HumanMessage(content=msg["content"]))
                else:
                    langchain_history.append(AIMessage(content=msg["content"]))
            
            langchain_history.append(HumanMessage(content=user_input))

            # Compile last 4 messages + current input into a transcript for the Mapper
            transcript_lines = []
            for msg in raw_history[-4:]:
                speaker = "User" if msg["role"] == "user" else "Kalpana"
                transcript_lines.append(f"{speaker}: {msg['content']}")
            transcript_lines.append(f"User: {user_input}")
            full_context_str = "\n".join(transcript_lines)

            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Give Mapper full context string instead of just the latest sentence
                future_mapper = executor.submit(mapper_agent.analyze, full_context_str)
                
                print(f"\nKalpana: ", end="", flush=True)
                full_listener_response = ""
                
                for chunk in listener_agent.generate_stream(langchain_history, current_phase, context_summary):
                    print(chunk, end="", flush=True)
                    full_listener_response += chunk
                print("\n")

                profile = future_mapper.result()
                print(f"[DEBUG MAPPER]: {profile}")
            # If the mapper fails completely, don't overwrite previous critical decisions
            current_risk_score = profile.get("risk_score", 1)
            risk_level = profile.get("detected_risk", "low").lower()
            self_harm = profile.get("self_harm_indicators", False)
            
            # Action logic
            if self_harm is True or current_risk_score >= 9:
                action = "escalate_to_tele_manas"
            elif risk_level == "high" or current_risk_score >= 5:
                action = "route_to_peer_group"
            else:
                action = "continue_listening"
            
            # State-Locking Logic
            detected_cause = profile.get("root_cause_of_the_distress", "-")
            if session_root_cause == "-" and detected_cause != "-":
                session_root_cause = detected_cause
                print(f"[INSIGHT]: Discovered root cause: {session_root_cause}")
                # We store the risk_score that triggered this lock so it persists even if mapper fails later
                session_risk_score = current_risk_score
            elif session_root_cause != "-":
                # Restore locked state in profile for logging
                profile["root_cause_of_the_distress"] = session_root_cause
                # If the mapper failed to produce a score this turn, fall back to the score that locked the cause
                if current_risk_score == 1 and 'session_risk_score' in locals():
                    current_risk_score = session_risk_score
            
            # --- Phase Derivation (Priority Candidates Pattern) ---
            context_summary = profile.get("clinical_summary", "")
            candidates = []
            if profile.get("self_harm_indicators", False):
                candidates.append((0, "crisis"))
            if session_root_cause != "-":
                candidates.append((1, "process"))
            if profile.get("risk_score", 1) >= 5:
                candidates.append((2, "probe"))
            candidates.append((3, "explore"))
            current_phase = min(candidates, key=lambda x: x[0])[1]
            
            peer_group = None
            # Check for peer match based on locked root cause and risk score
            # We require at least 4 items in raw_history (including the 2 being added this turn)
            if session_root_cause != "-" and current_risk_score >= 5 and (len(raw_history) + 2) >= 4:
                match = matchmaker.find_match(session_root_cause)
                if match:
                    print(f"\n[PEER MATCH]: I've found someone who has gone through something similar. They are available to talk.")
                    print(f"Type 'connect' if you'd like to reach out to them.")
                    current_match = match
                    peer_group = current_match  # Pass to logger
                else:
                    current_match = None
            else:
                current_match = None

            log_entry = {
                "user_input": user_input,
                "assistant_response": full_listener_response,
                "listener_phase": current_phase,
                "listener_context": context_summary,
                "action": action,
                "peer_group_match": peer_group,
                "clinical_profile": profile
            }
            
            with open(log_file, "r") as f:
                logs = json.load(f)
                
            logs.append(log_entry)
            
            with open(log_file, "w") as f:
                json.dump(logs, f, indent=4)

            raw_history.append({"role": "user", "content": user_input})
            raw_history.append({"role": "assistant", "content": full_listener_response})

            # Inner loop for 'connect' or next user input
            while current_match:
                next_action = input("\n(Type 'connect' or press Enter to continue): ").lower().strip()
                if next_action == 'connect':
                    print("\n" + "="*40)
                    print(f"CONNECTING YOU TO PEER: {current_match.get('primary_emotion', 'Friend')}")
                    print(f"Context: {current_match.get('clinical_notes', 'N/A')}") # Note: peers.json still uses clinical_notes
                    print("="*40)
                    print("\n[SYSTEM]: Connection request sent. They will be notified.")
                    current_match = None # Reset after connecting
                else:
                    break

        except KeyboardInterrupt:
            print("\nEnding session. Goodbye!")
            break
        except Exception as e:
            print(f"\n[ERROR] An issue occurred during processing: {e}")

if __name__ == "__main__":
    run_cli()