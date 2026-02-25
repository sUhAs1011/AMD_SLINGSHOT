# backend/agents/listener.py
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import SystemMessage

class ListenerAgent:
    def __init__(self):
        self.llm = ChatOllama(
            model="hf.co/QuantFactory/Mental-Health-FineTuned-Mistral-7B-Instruct-v0.2-GGUF:Q4_K_M", 
            temperature=0.6,
            num_gpu=-1,  
            keep_alive=-1,
            num_ctx=2048,
            num_thread=8,
            num_predict=300,
            repeat_penalty=1.2,
            stop=["\n\n", "User:", "You:", "Name: Response"]
        )
        self.system_prompt = SystemMessage(
            content=(
                    "You are an empathetic, listening friend. Your only job is to validate feelings and make the user feel heard. "
                    "CRITICAL RULES: "
                    "1. MAXIMUM 3 SENTENCES. "
                    "2. NO LISTS. NO BULLET POINTS. NO NUMBERING. Write only one short, continuous paragraph. "
                    "3. NEVER give advice, solutions, or helpline numbers. "
                    "4. End with a single, gentle follow-up question."
                )
        )

    def generate_stream(self, history: list):
        prompt = [self.system_prompt] + history[-5:]
        for chunk in self.llm.stream(prompt):
            yield chunk.content