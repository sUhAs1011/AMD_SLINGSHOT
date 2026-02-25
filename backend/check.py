import os
import subprocess

subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["taskkill", "/F", "/IM", "ollama app.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

os.environ["OLLAMA_MAX_LOADED_MODELS"] = "2"
os.environ["OLLAMA_NUM_PARALLEL"] = "2"

subprocess.run(["ollama", "serve"])