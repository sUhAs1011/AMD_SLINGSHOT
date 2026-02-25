import random

def get_mock_response(chat_history: list) -> str:
    """
    Simulates the LangGraph agent response (Phase 2 output pipeline).
    Reads the user's latest message and returns a gentle follow-up string.
    """
    if not chat_history:
        return "I'm here for you. How are you feeling today?"
        
    last_message = chat_history[-1].get("content", "").lower()
    
    # Simple keyword detection for context (just for the demo)
    if "tired" in last_message or "burnout" in last_message or "exhausted" in last_message:
        return "It sounds like you've been pushing yourself incredibly hard. It's completely normal to feel exhausted. Can you tell me what’s been draining your energy the most?"
        
    elif "alone" in last_message or "lonely" in last_message:
        return "That sounds incredibly difficult. I want you to know I’m here to listen, and you aren't alone. How long have you been feeling this way?"
        
    else:
        # Generic gentle follow-up options
        responses = [
            "I hear you. It's okay to feel overwhelmed sometimes. What is the hardest part for you right now?",
            "Thank you for sharing that with me. It takes courage to speak up. How does talking about it make you feel?",
            "I’m really sorry you’re going through that. It sounds exhausting. Can you tell me a bit more about it?"
        ]
        return random.choice(responses)

if __name__ == "__main__":
    # Test block
    print("--- Mock Agent Test ---")
    mock_history = [{"role": "user", "content": "I am feeling very tired.", "timestamp": "2026-02-22"}]
    print(f"User said: {mock_history[0]['content']}")
    print(f"Agent replied: {get_mock_response(mock_history)}")
