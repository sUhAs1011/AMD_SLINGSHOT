import os
import json
from datetime import datetime

# Resolve the absolute path to the logs directory, regardless of where this script is run from
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
SESSION_LOG_FILE = os.path.join(LOGS_DIR, "session_logs.json")

def initialize_logs_dir():
    """Ensure the logs folder and the JSON file exist."""
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
        
    if not os.path.exists(SESSION_LOG_FILE):
        with open(SESSION_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

def log_session(role: str, content: str, language_code: str = None) -> dict:
    """
    Appends the message to the session log file with a strict YYYY-MM-DD HH:MM:SS timestamp.
    Optionally includes the detected language_code.
    Returns the exact dictionary that was appended.
    """
    initialize_logs_dir()
    
    # The exact strict timestamp required by your teammates
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = {
        "role": role,
        "content": content,
        "timestamp": timestamp
    }
    
    # Add language code only if it exists (usually only for user voice notes)
    if language_code:
        log_entry["language_code"] = language_code
    
    try:
        # Read the existing logs, append the new one, and write back
        with open(SESSION_LOG_FILE, "r+", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                # If file is empty or corrupt, start fresh
                data = []
            
            data.append(log_entry)
            
            # Reset file pointer and overwrite
            f.seek(0)
            json.dump(data, f, indent=4, ensure_ascii=False)
            f.truncate()
            
    except Exception as e:
        print(f"Error logging session: {e}")
        
    return log_entry

if __name__ == "__main__":
    # Test block for manual verification
    entry = log_session("user", "This is a test message to verify the JSON schema.")
    print("--- Session Logger Test ---")
    print(f"Appended Entry: {json.dumps(entry, indent=2)}")
    print(f"Logs file location: {SESSION_LOG_FILE}")
