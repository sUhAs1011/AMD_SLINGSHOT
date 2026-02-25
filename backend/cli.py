import uuid
import json
import os
import concurrent.futures
from langchain_core.messages import HumanMessage, AIMessage


from agents.listener import ListenerAgent
from agents.mapper import ClinicalMapperAgent
from utils.matchmaker import PeerMatchmaker

def run_cli():
    listener_agent = ListenerAgent()
    mapper_agent = ClinicalMapperAgent()
    matchmaker = PeerMatchmaker()
    
    session_id = str(uuid.uuid4())
    raw_history = []
    
    os.makedirs("session_logs", exist_ok=True)
    log_file = f"session_logs/{session_id}.json"
    
    with open(log_file, "w") as f:
        json.dump([], f)
        
    print("Initializing Kalpana 6.0 CLI with GPU Acceleration & Vector Search...")
    print(f"\nSession started [ID: {session_id}]")
    print("Type 'quit' or 'exit' to end the session.\n")
    print("=" * 60)
    
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

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_mapper = executor.submit(mapper_agent.analyze, user_input)
                
                print(f"\nKalpana: ", end="", flush=True)
                full_listener_response = ""
                
                for chunk in listener_agent.generate_stream(langchain_history):
                    print(chunk, end="", flush=True)
                    full_listener_response += chunk
                print("\n")

                profile = future_mapper.result()

            risk_level = profile.get("detected_risk", "low").lower()
            self_harm = profile.get("self_harm_indicators", False)
            risk_score = profile.get("risk_score", 1)
            
            if self_harm is True or risk_score >= 9:
                action = "escalate_to_tele_manas"
            elif risk_level == "high" or risk_score >= 7:
                action = "route_to_peer_group"
            else:
                action = "continue_listening"
            
            # Print insight for debugging/demo
            root_cause = profile.get("root_cause_of_the_distress", "-")
            if root_cause != "-":
                print(f"[INSIGHT]: Detected potential cause: {root_cause}")
            
            peer_group = None

            log_entry = {
                "user_input": user_input,
                "assistant_response": full_listener_response,
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

            # Check for peer match based on root cause and dynamic readiness
            if root_cause != "-" and profile.get("ready_for_matchmaking", False):
                match = matchmaker.find_match(root_cause)
                if match:
                    print(f"\n[PEER MATCH]: I've found someone who has gone through something similar. They are available to talk.")
                    print(f"Type 'connect' if you'd like to reach out to them.")
                    # Store match in a temporary place for the 'connect' command
                    current_match = match
                else:
                    current_match = None
            else:
                current_match = None

            # Inner loop for 'connect' or next user input
            while current_match:
                next_action = input("\n(Type 'connect' or press Enter to continue): ").lower().strip()
                if next_action == 'connect':
                    print("\n" + "="*40)
                    print(f"CONNECTING YOU TO PEER: {current_match.get('primary_emotion', 'Friend')}")
                    print(f"Context: {current_match.get('clinical_notes', 'N/A')}")
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