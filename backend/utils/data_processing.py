# backend/utils/data_processing.py
from typing import Dict, Any
from database.connection import get_db_connection

def load_dataset_context() -> str:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT text, self_harm, harming_others FROM training_data.few_shot_examples LIMIT 15;")
        records = cursor.fetchall()
        context_str = "Example Patterns:\n"
        for row in records:
            context_str += f"- Text: '{row[0]}' | Self Harm: {row[1]} | Harm Others: {row[2]}\n"
        cursor.close()
        conn.close()
        return context_str
    except Exception:
        return ""

def evaluate_threshold(profile: Dict[str, Any], session_id: str) -> str:
    risk_level = profile.get("detected_risk", "low").lower()
    self_harm = profile.get("self_harm_indicators", False)
    risk_score = profile.get("risk_score", 1)
    
    if self_harm is True or risk_score >= 9:
        action = "escalate_to_tele_manas"
    elif risk_level == "high" or risk_score >= 7:
        action = "route_to_peer_group"
    else:
        action = "continue_listening"
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO triage.assessments (profile_id, risk_score, routing_decision)
            VALUES (
                (SELECT profile_id FROM clinical.profiles WHERE session_id = %s ORDER BY evaluated_at DESC LIMIT 1),
                %s, 
                %s
            )
            """,
            (session_id, risk_score, action)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        pass
        
    return action