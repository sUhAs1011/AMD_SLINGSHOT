import os
import psycopg2
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# Constants
EMBEDDING_MODEL = "bert-base-nli-mean-tokens"
# You'll need to set these in your .env file
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres123@localhost:5432/peerdb")

class PeerMatchmakerPGVector:
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        
        try:
            self.conn = psycopg2.connect(POSTGRES_URL)
            # Ensure pgvector is enabled
            with self.conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            self.conn.commit()
        except Exception as e:
             raise ConnectionError(f"Could not connect to PostgreSQL: {e}")

    def __del__(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

    def find_match(self, root_cause: str, top_k: int = 1):
        """
        Takes a detected root cause, embeds it, and searches pgvector using cosine distance.
        """
        if not root_cause or root_cause == "-":
            return None

        # Embed the query
        query_vector = self.model.encode(root_cause).tolist()

        try:
            with self.conn.cursor() as cur:
                # <=>(cosine distance) operator in pgvector. 
                # Cosine similarity = 1 - cosine distance
                # We want matches with similarity >= 0.70, which means distance <= 0.30
                
                query = """
                SELECT 
                    peer_id, primary_emotion, risk_score, root_cause, clinical_notes,
                    1 - (embedding <=> %s::vector) AS similarity_score
                FROM peers
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
                """
                
                cur.execute(query, (query_vector, query_vector, top_k))
                row = cur.fetchone()

                if row:
                    peer_id, primary_emotion, risk_score, cause, clinical_notes, score = row
                    
                    # Cap the score at 1.0
                    score = min(float(score), 1.0)
                    
                    SIMILARITY_THRESHOLD = 0.70
                    
                    if score < SIMILARITY_THRESHOLD:
                         print(f"[DEBUG]: Match found but score ({score:.4f}) is below threshold ({SIMILARITY_THRESHOLD}).")
                         return None
                        
                    return {
                        "peer_id": peer_id,
                        "primary_emotion": primary_emotion,
                        "risk_score": risk_score,
                        "root_cause_of_the_distress": cause,
                        "clinical_notes": clinical_notes,
                        "score": score
                    }
                
                return None
                
        except Exception as e:
            print(f"[ERROR] Database query failed: {e}")
            self.conn.rollback()
            return None

if __name__ == "__main__":
    # Quick test
    try:
        matchmaker = PeerMatchmakerPGVector()
        test_cause = "Academic pressure and fear of failure"
        match = matchmaker.find_match(test_cause)
        print(f"Test Cause: {test_cause}")
        print(f"Match: {match}")
    except Exception as e:
        print(f"PGVector Matchmaker Test Error: {e}")
