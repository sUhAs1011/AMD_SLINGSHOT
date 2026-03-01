# backend/agents/listener.py
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import SystemMessage

class ListenerAgent:
    def __init__(self):
        self.llm = ChatOllama(
            model="ministral-3:3b", 
            temperature=0.3, # Lower temperature for more consistent, grounded output
            num_gpu=0,  
            keep_alive=-1,
            num_ctx=2048,
            num_thread=8,
            num_predict=300,
            repeat_penalty=1.2,
            stop=["\n\n", "User:", "You:", "Name: Response"]
        )
        self.system_prompt = SystemMessage(
            content=(
                    "You are a supportive pyschotherapist/counsellor. Your job is to listen and acknowledge the user's feelings in a simple, direct way. "
                    "CRITICAL RULES: "
                    "1. MAXIMUM 3 or 4 SENTENCES. No poetic or metaphorical language. "
                    "2. Use simple, everyday words that are easy to understand and translate. "
                    "3. NO LISTS. NO BULLET POINTS. NO NUMBERING. Write only one short, continuous paragraph. "
                    "4. NEVER give advice, solutions, or helpline numbers. "
                    "5. End with a single, simple question to understand more (e.g., 'When did this start?' or 'How are you handling it?')."
                )
        )

    def generate_stream(self, history: list):
        prompt = [self.system_prompt] + history[-10:]
        for chunk in self.llm.stream(prompt):
            yield chunk.content