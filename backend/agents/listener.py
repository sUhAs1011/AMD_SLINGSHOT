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
        # Base persona is constant; phase instructions are selected at call time
        self.base_persona = (
            "You are a calm, grounded psychotherapist. Use plain, simple language, strictly no overly poetic or metaphorical language. "
            "Maximum 4 sentences. No lists, no bullet points. Never give advice or helpline numbers."
        )
        self.phase_instructions = {
            "explore": "Validate their feelings warmly. Ask one soft question about what has been happening in their life — not about feelings.",
            "probe":   "Gently ask if a specific event might have brought these feelings on. One soft question only. Do not push.",
            "process": "The root cause has been identified. Acknowledge their situation with care. Help them feel understood.",
            "crisis":  "The user may be in crisis. Do NOT probe. Be gentle and grounding. Let them know they are heard and safe.",
        }

    def generate_stream(self, history: list, phase: str = "explore", context_summary: str = ""):
        # Build the system prompt dynamically based on the current phase
        instruction = self.phase_instructions.get(phase, self.phase_instructions["explore"])

        # Inject clinical_summary as a compact memory anchor (if available)
        memory_note = f" [Session context: {context_summary}]" if context_summary else ""

        system_prompt = SystemMessage(content=self.base_persona + " " + instruction + memory_note)
        prompt = [system_prompt] + history[-6:]
        for chunk in self.llm.stream(prompt):
            yield chunk.content