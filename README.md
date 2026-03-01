# 🌿 Kalpana: Intelligent Peer Support MVP

Kalpana is an empathetic, AI-driven mental health peer-support protocol. This repository contains the Minimum Viable Product (MVP) of a specialized dual-agent architecture designed to provide an immediate, safe listening space for users while asynchronously routing them to peers who have experienced similar life challenges.

While the frontend UI is intentionally minimal and calming, the backend utilizes two specialized local Large Language Models (LLMs) working concurrently, a strict deterministic routing protocol, and a vector database for semantic peer matching.

---

## 🏗️ Architecture Overview

The system relies on a **Decoupled Dual-Agent Architecture** to separate the act of empathetic listening from the act of clinical analysis. 

### 1. The Listener Agent (Frontend/CPU)
* **Model:** `ministral-3:3b`
* **Role:** The user-facing persona. It provides immediate, warm, and non-judgmental validation.
* **Mechanism:** It streams responses instantly to the user. It operates under a **Dynamic Phase Prompting** system. Depending on the user's state, it shifts its system prompt between 5 phases:
  * `Greeting` - Simple welcome without assuming distress.
  * `Explore` - Validating feelings and asking broad contextual questions.
  * `Probe` - Gently asking if a specific event triggered the feelings.
  * `Process` - Acknowledging the identified root cause and providing deeper validation.
  * `Crisis` - Grounding the user if self-harm indicators are detected (overriding all probing).

### 2. The Clinical Mapper Agent (Background/GPU)
* **Model:** `gemma3:4b`
* **Role:** The analytical engine. It runs invisibly in the background.
* **Mechanism:** While the Listener is streaming its response, the Mapper asynchronously analyzes the recent conversation transcript. It is heavily constrained to output a strict JSON `Clinical Profile` containing:
  * `clinical_summary`: A synthesized context anchor for the Listener's next turn.
  * `primary_emotion`: The core feeling detected.
  * `root_cause_of_the_distress`: Extracted specific life event (e.g., "Job loss", "Breakup").
  * `risk_score`: A 1-10 severity rating based on distress markers.
  * `self_harm_indicators`: Boolean flag for immediate escalation.

### 3. The Matchmaker (Vector Database)
* **Technology:** Pinecone & HuggingFace `SentenceTransformer` (`bert-base-nli-mean-tokens`)
* **Role:** Semantic peer routing. 
* **Mechanism:** Once the Mapper locks onto a stable `root_cause`, the Matchmaker embeds that root cause and queries the Pinecone vector database to find the closest historical peer who has survived a highly similar experience (threshold > 0.50 similarity).

---

## ⚙️ Core Logic Flow

The MVP enforces a strict, deterministic routing protocol over the LLMs' outputs to ensure user safety and prevent premature matching:

1. **Initial Disclosure (Turns 1-3):** The user enters and shares their feelings. The Listener stays in the `Explore` phase. The Mapper runs in the background, logging risk scores but taking no external action.
2. **Root Cause Extraction:** The Mapper identifies the specific event driving the distress (e.g., "Job loss/Layoffs") and locks it into the session state.
3. **Threshold Evaluation (Turn 4+):** If the conversation has lasted at least 4 turns, the risk score is moderate-to-high (>= 5), and a root cause has been established, the system triggers the Matchmaker.
4. **Peer Connection:** The UI surfaces an empathetic message offering a connection to the matched peer, alongside their anonymous ID.
5. **Safety Override:** If `self_harm_indicators` is ever flagged as `true` by the Mapper, the system instantly switches the Listener into `Crisis` mode, halts all peer matchmaking, and prepares for human escalation.

---

## 🚀 Getting Started

### Prerequisites
* **Ollama:** Installed and running locally. We rely on local models to ensure absolute data privacy for the user's mental health disclosures.
* **Models:** Pull the required models via Ollama:
  ```bash
  ollama pull ministral-3:3b
  ollama pull gemma3:4b
  ```
* **Pinecone:** A Pinecone index named `mental-health-peers` dimensioned for `bert-base-nli-mean-tokens` (768 dims).

### Setup
1. Clone the repository and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `.env` file in the root directory and add your Pinecone API key:
   ```
   PINECONE_API_KEY="your-api-key-here"
   ```
3. Run the model warm-up script (Optional, but highly recommended to prevent initial load delays):
   ```bash
   python backend/scripts/warm_up_models.py
   ```
4. Launch the Streamlit Frontend:
   ```bash
   streamlit run app0.py
   ```

---

## 🔮 Future Scope & Roadmap

This repository represents the MVP of the matchmaking intelligence layer. The architecture is designed to scale into a full platform with the following upcoming features:

1. **Real-Time Peer Chatrooms:**
   * Implementing WebSockets (e.g., via FastAPI) to allow the matched user and peer to enter an anonymous, end-to-end encrypted live text chat when both parties accept the connection.
   * "Availability Status" pinging to ensure peers are only matched if they are currently online and willing to chat.

2. **Passive Moderation Agent:**
   * Deploying a lightweight safety LLM that passively monitors the live peer-to-peer chatroom transcript. It will ensure conversations remain supportive and don't escalate into shared harmful ideation, triggering graceful interventions or closing the room if community guidelines are breached.

3. **Opt-In Voice Integration:**
   * Reintegrating seamless Speech-to-Text (STT) and Text-to-Speech (TTS) models (e.g., Sarvam AI) so users can choose between text-based chat or realistic voice conversations depending on their accessibility needs and what feels safest for them in the moment.

4. **PII Scrubbing Pipeline:**
   * Running all user input through Microsoft Presidio to scrub Personally Identifiable Information (names, locations, phone numbers) *before* it hits the LLMs or gets logged to the session state.