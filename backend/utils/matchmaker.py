import os
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# Constants
EMBEDDING_MODEL = "bert-base-nli-mean-tokens"
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "mental-health-peers")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

class PeerMatchmaker:
    def __init__(self):
        if not PINECONE_API_KEY:
             raise ValueError("PINECONE_API_KEY not found in environment.")
        
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.index = self.pc.Index(INDEX_NAME)
        self.model = SentenceTransformer(EMBEDDING_MODEL)

    def find_match(self, root_cause: str, top_k: int = 1):
        """
        Takes a detected root cause, embeds it, and searches Pinecone for the closest peer.
        """
        if not root_cause or root_cause == "-":
            return None

        # Embed the query
        query_vector = self.model.encode(root_cause).tolist()

        # Query Pinecone
        results = self.index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True
        )

        if results and results["matches"]:
            # Return the top match with ID included in metadata, but ONLY if it exceeds the threshold
            match = results["matches"][0]
            score = match.get("score", 0.0)
            
            # Cap the score at 1.0 to handle potential floating point precision drift
            score = min(score, 1.0)
            
            # Use a default threshold of 0.70 (cosine similarity)
            SIMILARITY_THRESHOLD = 0.70
            
            if score < SIMILARITY_THRESHOLD:
                print(f"[DEBUG]: Match found but score ({score:.4f}) is below threshold ({SIMILARITY_THRESHOLD}).")
                return None

            metadata = match["metadata"]
            metadata["peer_id"] = match["id"]
            metadata["score"] = score # Also include score for reference
            return metadata
        
        return None

if __name__ == "__main__":
    # Quick test
    try:
        matchmaker = PeerMatchmaker()
        test_cause = "Academic pressure and fear of failure"
        match = matchmaker.find_match(test_cause)
        print(f"Test Cause: {test_cause}")
        print(f"Match: {match}")
    except Exception as e:
        print(f"Matchmaker Test Error: {e}")
