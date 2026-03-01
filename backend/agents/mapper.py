# backend/agents/mapper.py
import json
import re
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage


class ClinicalMapperAgent:
    def __init__(self):
        self.llm = ChatOllama(
            model="gemma3:4b", 
            temperature=0.0,
            num_gpu=-1,  
            keep_alive=-1,
            num_ctx=8192,
            num_thread=8,
            num_predict=200,
            format="json"
        )

    def analyze(self, user_message: str) -> dict:
        system_prompt_template = """You are an expert Clinical Psychologist AI mapping a user's trauma.
        Read the provided conversation transcript and analyze the user's current psychological state.
        
        CRITICAL RULES:
        1. clinical_summary: Summarize the user's situation in 2-3 sentences. Justify the chosen emotion, risk level, and root cause.
        2. primary_emotion: e.g., severe anxiety, suicidal ideation, depression, fear.
        3. detected_risk: "low" (1-4), "moderate" (5-7), or "high" (8-10).
        4. self_harm_indicators: boolean (true/false).
        5. risk_score: Integer 1-10.
        6. root_cause_of_the_distress: Identify the specific, external life-event that caused this distress (e.g. 'Job loss', 'Bereavement', 'Breakup'). If the user only describes feelings without naming a specific event, return '-'.
        
        Output ONLY valid JSON matching this exact structure:
        {{
            "clinical_summary": "string",
            "primary_emotion": "string",
            "detected_risk": "low/moderate/high",
            "self_harm_indicators": false,
            "risk_score": 1,
            "root_cause_of_the_distress": "string"
        }}"""

        messages = [
            SystemMessage(content=system_prompt_template), 
            HumanMessage(content=user_message)
        ]
        try:
            analysis = self.llm.invoke(messages)
            raw_text = analysis.content.strip()
            print(f"[DEBUG RAW MAPPER OUTPUT]: '{raw_text}'")  # Temporary debug print
            
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                # Defend against empty {} or missing critical fields
                if not parsed.get("clinical_summary"):
                    raise ValueError("Empty or incomplete JSON received")
                return parsed
                
            parsed_raw = json.loads(raw_text)
            if not parsed_raw.get("clinical_summary"):
                raise ValueError("Empty or incomplete JSON received")
            return parsed_raw
        except Exception:
            return {
                "clinical_summary": "Parsing failed or format error.",
                "primary_emotion": "unknown",
                "detected_risk": "low", 
                "self_harm_indicators": False, 
                "risk_score": 1,
                "root_cause_of_the_distress": "-"
            }
