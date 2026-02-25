import sys
import os

# Ensure the backend directory is in the path so we can import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.matchmaker import PeerMatchmaker

def run_search_tool():
    try:
        matchmaker = PeerMatchmaker()
    except Exception as e:
        print(f"Error initializing matchmaker: {e}")
        return

    print("="*60)
    print("KALPANA SEMANTIC SEARCH TEST TOOL")
    print("="*60)
    print("Type 'exit' or 'quit' to stop.")

    while True:
        query = input("\nEnter a distress description to search for a peer: ").strip()
        
        if query.lower() in ['exit', 'quit']:
            break
        
        if not query:
            continue

        print(f"Searching Pinecone for matches to: '{query}'...")
        
        # We can ask for top 3 matches to see more data
        # Note: I'll update matchmaker.find_match to support top_k if I haven't already
        # Wait, the current matchmaker returns the top 1 by default.
        
        match = matchmaker.find_match(query)
        
        if match:
            print("\n" + "-"*40)
            print(f"BEST MATCH FOUND:")
            print(f"Peer ID:         {match.get('peer_id', 'N/A')}")
            print(f"Confidence Score: {match.get('score', 0.0):.4f}")
            print(f"Primary Emotion: {match.get('primary_emotion', 'N/A')}")
            print(f"Root Cause:      {match.get('root_cause', 'N/A')}")
            print(f"Clinical Notes:  {match.get('clinical_notes', 'N/A')}")
            print("-"*40)
        else:
            print("\nNo close peer matches found for that specific query.")

if __name__ == "__main__":
    run_search_tool()
