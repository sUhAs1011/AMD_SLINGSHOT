# backend/agents/mapper.py
import json
import re
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from utils.vector_search import search_trauma_patterns

class ClinicalMapperAgent:
    def __init__(self):
        self.llm = ChatOllama(
            model="hf.co/QuantFactory/Mental-Health-FineTuned-Mistral-7B-Instruct-v0.2-GGUF:Q4_K_M", 
            temperature=0.0,
            num_gpu=0,  
            keep_alive=-1,
            num_ctx=2048,
            num_thread=8,
            num_predict=200,
            format="json"
        )

    def analyze(self, user_message: str) -> dict:
        dataset_context = search_trauma_patterns(user_message)
        
        system_prompt_template = f"""You are an expert Clinical Psychologist AI mapping a user's trauma.
        Analyze the exact keywords and implied distress in the user's message against the retrieved database patterns.
        
        {dataset_context}
        
        1. primary_emotion: e.g., severe anxiety, suicidal ideation, depression, fear.
        2. detected_risk: "low" (1-4), "moderate" (5-7), or "high" (8-10).
        3. self_harm_indicators: true ONLY if explicit/implied intent matches high-risk database patterns.
        4. clinical_notes: Concise mapping of the user's trauma category based on vector similarity.
        5. risk_score: Integer 1-10.
        6. root_cause_of_the_distress: Identify the specific, external life-event or legitimate incident that is the root cause of the distress. Examples include: 'Bereavement/Loss', 'Job loss/Layoffs', 'Academic failure/Exam stress', 'Physical assault', 'War/Conflict', 'Breakup/Divorce'. CRITICAL: Do NOT identify generic emotional states (e.g., 'Loneliness', 'Isolation', 'Sadness', 'Anxiety') as the root cause. If the user only describes their feelings without mentioning a specific triggering event, use "-".
        7. ready_for_matchmaking: Boolean. Set to true ONLY if the user has shared enough specific context about their situation and sounds psychologically ready to connect with a peer. If the conversation is still in early stages or the user seems too overwhelmed/unstable for a peer connection, set to false.
        
        Output ONLY valid JSON.
        {{
            "primary_emotion": "string",
            "detected_risk": "low/moderate/high",
            "self_harm_indicators": false,
            "clinical_notes": "string",
            "risk_score": 1,
            "root_cause_of_the_distress": "string",
            "ready_for_matchmaking": false
        }}"""

        messages = [
            SystemMessage(content=system_prompt_template), 
            HumanMessage(content=user_message)
        ]
        try:
            analysis = self.llm.invoke(messages)
            raw_text = analysis.content.strip()
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return json.loads(raw_text)
        except Exception:
            return {
                "primary_emotion": "unknown",
                "detected_risk": "low", 
                "self_harm_indicators": False, 
                "clinical_notes": "Failed to parse clinical profile.",
                "risk_score": 1,
                "root_cause_of_the_distress": "-",
                "ready_for_matchmaking": False
            }