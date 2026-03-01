import requests
import json

MODELS = {
    "ministral-3:3b": {"num_gpu":0, "num_ctx": 8192},   # Use CPU for the conversational friend
    "gemma3:4b": {"num_gpu": -1, "num_ctx": 8192}       # Use GPU for the clinical mapper
}

def warm_up():  
    print("="*40)
    print("KALPANA MODEL WARM-UP UTILITY (Partitioned)")
    print("="*40)
    
    for model, options in MODELS.items():
        print(f"\n[WARMING UP]: {model} (GPU: {'YES' if options['num_gpu'] == -1 else 'NO'})...")
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "keep_alive": -1,
                    "options": options
                },
                stream=True
            )
            
            for line in response.iter_lines():
                if line:
                    status = json.loads(line.decode('utf-8'))
                    if status.get("done"):
                        print(f"[SUCCESS]: {model} is loaded and ready!")
                        break
        except Exception as e:
            print(f"[ERROR]: Could not load {model}. Error: {e}")

    print("\n" + "="*40)
    print("All models are primed and ready in memory!")
    print("You can now run the CLI for instant responses.")
    print("="*40)

if __name__ == "__main__":
    warm_up()
