import os
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from utils.sarvam_api import transcribe_audio
from utils.privacy import scrub_text
from utils.logger import log_session

# Ensure temp directory exists for Audio files
TEMP_DIR = "temp_audio"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    
    # Add a welcome message if the session is brand new
    welcome_msg = {
        "role": "assistant", 
        "content": "Hi there. I'm here to listen. You can record a voice note below."
    }
    st.session_state.chat_history.append(welcome_msg)

def render_chat_ui():
    """Renders the top-down WhatsApp style chat bubbles."""
    for msg in st.session_state.chat_history:
        role = msg.get("role")
        content = msg.get("content")
        
        with st.chat_message(role):
            # If the content is flagged as an audio file path, render an audio player
            if content.startswith("AUDIO_FILE:"):
                file_path = content.split("AUDIO_FILE:")[1]
                if os.path.exists(file_path):
                    st.audio(file_path, format="audio/wav")
                else:
                    st.error("Audio file missing.")
            else:
                st.markdown(content)

def main():
    st.set_page_config(page_title="Peer Support MVP", layout="centered")
    st.title("AI Peer Support Network")
    
    # 1. Render all previous messages
    render_chat_ui()

    # 2. Add some vertical space to push the recorder to the bottom
    st.write("")
    st.write("")

    # 3. The Audio Recorder (User Input)
    audio_bytes = audio_recorder(
        text="Click to Record (Max 30s)",
        recording_color="#e8b62c",
        neutral_color="#6aa36f",
        icon_name="microphone",
        icon_size="2x",
        pause_threshold=7.0, # CRITICAL: Wait for 10 seconds of pure silence before cutting off
    )

    # 4. Process the recorded audio
    if audio_bytes:
        import hashlib
        from datetime import datetime
        
        # The audio_recorder component can hold stale bytes across reruns.
        # We hash the audio buffer to ensure we only process new recordings.
        current_audio_hash = hashlib.md5(audio_bytes).hexdigest()
        
        if st.session_state.get("last_processed_audio_hash") != current_audio_hash:
            # CRITICAL FIX: Lock the state IMMEDIATELY before doing any slow API calls.
            st.session_state["last_processed_audio_hash"] = current_audio_hash
            
            # Create a unique temporary file path so historic voice notes don't get overwritten
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_audio_path = os.path.join(TEMP_DIR, f"user_input_{timestamp_str}.wav")
            
            # Save the bytes to the file
            with open(temp_audio_path, "wb") as f:
                f.write(audio_bytes)
                
            # 1. Instantly show the user's audio file in the chat (WhatsApp Style)
            audio_log_entry = log_session("user", f"AUDIO_FILE:{temp_audio_path}")
            st.session_state.chat_history.append(audio_log_entry)

            # 2. Show the engagement loader in the UI as a new system/translation message bubble
            with st.chat_message("assistant"):
                with st.spinner("Translating and scrubbing your voice note..."):
                    
                    # A. Send to Sarvam API for Translation (Hindi/Kannada -> English)
                    raw_english_text, detected_lang = transcribe_audio(temp_audio_path)
                    
                    # B. Edge Case Handling: If STT fails
                    if "Error" in raw_english_text:
                        st.error(raw_english_text)
                        # Reset the hash so the user can try recording again
                        st.session_state["last_processed_audio_hash"] = None
                        return
                    
                    # C. Scrub PII (Names, Emails, Phones)
                    scrubbed_text = scrub_text(raw_english_text)
                    
                    # Store the detected language in session state for Phase 2 TTS
                    if detected_lang and detected_lang != "unknown":
                        st.session_state["target_language_code"] = detected_lang
                    
                    # D. Log the translated text as the literal text response, including the language code
                    text_log_entry = log_session(
                        role="assistant", 
                        content=f"**(Detected Language: {detected_lang})**\n\n**Translation:** {scrubbed_text}",
                        language_code=detected_lang
                    )
                    
                    # E. Append to Session State to update UI
                    st.session_state.chat_history.append(text_log_entry)
                    
            # F. Force Streamlit to rerun so the spinner vanishes and the real messages appear
            st.rerun()

if __name__ == "__main__":
    main()
