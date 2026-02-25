import os
import psycopg2
from langchain_postgres.vectorstores import PGVector
from langchain_community.embeddings import OllamaEmbeddings

def get_vector_store():
    connection_string = f"postgresql+psycopg://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'kalpana_db')}"
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    store = PGVector(
        embeddings=embeddings,
        collection_name="peer_groups",
        connection=connection_string,
        use_jsonb=True,
    )
    return store

def find_matching_peer_group(clinical_notes: str, threshold_distance: float = 0.35):
    try:
        store = get_vector_store()
        results = store.similarity_search_with_score(clinical_notes, k=1)
        if results:
            best_match, distance = results[0]
            if distance <= threshold_distance: 
                return best_match.metadata.get("trauma_type", "General Support")
    except Exception:
        pass
    return None

def search_trauma_patterns(user_message: str) -> str:
    try:
        embeddings_model = OllamaEmbeddings(model="nomic-embed-text")
        query_vector = embeddings_model.embed_query(user_message)
        
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "kalpana_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "password"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT text_content, self_harm, harming_others, reference_to_harm 
            FROM matchmaking.dataset_vectors 
            ORDER BY embedding <=> %s::vector LIMIT 6;
            """,
            (query_vector,)
        )
        results = cursor.fetchall()
        
        context_str = "Matched Clinical Trauma Datasets Context:\n"
        for row in results:
            context_str += f"- Pattern: '{row[0]}' | Self Harm: {row[1]} | Harm Others: {row[2]} | Harm Reference: {row[3]}\n"
            
        cursor.close()
        conn.close()
        return context_str
    except Exception:
        return "No matched patterns."