import os
from dotenv import load_dotenv
from sarvamai import SarvamAI

# Load environment variables (API Key)
load_dotenv()

# Initialize the Sarvam AI client using the exact required syntax from docs
try:
    sarvam_key = os.getenv("SARVAM_API_KEY")
    client = SarvamAI(api_subscription_key=sarvam_key)
except Exception as e:
    print(f"Warning: Failed to initialize Sarvam client. Is SARVAM_API_KEY set? Error: {e}")
    client = None

def transcribe_audio(file_path: str) -> tuple[str, str]:
    """
    Sends the audio file to Sarvam 'saaras:v3' for translation.
    Returns a tuple: (English Text, Detected Language Code).
    If it fails, returns (Error Message, None).
    """
    if not client:
        return "Error: Sarvam API client not initialized. Check your API key.", None
        
    if not os.path.exists(file_path):
        return "Error: Audio file not found.", None
        
    try:
        # Exact syntax from the Sarvam SDK documentation
        with open(file_path, "rb") as audio_file:
            response = client.speech_to_text.transcribe(
                file=audio_file,
                model="saaras:v3",
                mode="translate"
            )
            
        # Extract the transcript and language code from the response object
        # According to SDK docs, we can access response attributes directly
        transcript = response.transcript
        language_code = getattr(response, 'language_code', 'unknown')
        
        return transcript, language_code
        
    except Exception as e:
        return f"Error during Sarvam API call: {e}"

if __name__ == "__main__":
    # Note: To manually test this, you need a highly compressed .wav file named 'test_audio.wav'
    # in the same directory as this script.
    print("--- Sarvam API Tester ---")
    print("Ensure SARVAM_API_KEY is in your .env file.")
    test_file = "test_audio.wav"
    if os.path.exists(test_file):
        print(f"Testing with {test_file}...")
        result = transcribe_audio(test_file)
        print(f"Result: {result}")
    else:
        print(f"No '{test_file}' found to test with. This is expected.")
