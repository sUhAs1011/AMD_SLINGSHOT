# 🌿 Kalpana – Intelligent AI Peer Support Platform

Kalpana is an **AI-powered mental health peer-support platform** that combines empathetic conversational AI with intelligent peer matching. The system provides users with an immediate, safe, and non-judgmental space to express their emotions while leveraging AI to connect them with peers who have overcome similar life experiences.

Built using a **dual-agent architecture**, Kalpana separates empathetic conversation from clinical reasoning, enabling safe, explainable, and context-aware support while preserving user privacy through locally hosted Large Language Models (LLMs).

---

# ✨ Features

* 🤖 Dual-agent AI architecture for conversation and clinical reasoning
* 💙 Empathetic conversational assistant with dynamic response strategies
* 🧠 Context-aware emotional and root-cause analysis
* 👥 AI-powered semantic peer matching using vector search
* ⚡ Asynchronous background reasoning for seamless conversations
* 🔒 Privacy-first design using locally hosted LLMs
* 📊 Structured clinical profiling for explainable decision making
* 🛡️ Built-in crisis detection and safety escalation pipeline

---

# 🏗️ System Architecture

Kalpana follows a **Decoupled Dual-Agent Architecture**, where each AI agent performs a specialized task independently.

## 🎧 1. Listener Agent

**Model:** `ministral-3:3b`

The Listener Agent is the user-facing conversational assistant responsible for providing empathetic, supportive, and non-judgmental interactions.

### Responsibilities

* Streams responses in real time
* Provides emotional validation
* Maintains natural conversations
* Adapts responses based on user state

### Dynamic Conversation Phases

* 👋 Greeting
* 💬 Explore
* 🔍 Probe
* 🌱 Process
* 🚨 Crisis

These phases allow the system to gradually understand the user's emotional state without making assumptions or rushing into conclusions.

---

## 🧠 2. Clinical Mapper Agent

**Model:** `gemma3:4b`

The Clinical Mapper runs asynchronously in the background while the Listener interacts with the user.

Instead of generating free-form text, it produces a structured clinical profile containing:

* Clinical summary
* Primary emotion
* Root cause of distress
* Risk score
* Self-harm indicators

This structured output enables deterministic decision-making and minimizes hallucinations.

---

## 👥 3. Matchmaker Engine

**Technology**

* Pinecone Vector Database
* Hugging Face Sentence Transformers
* `bert-base-nli-mean-tokens`

Once a stable root cause has been identified, the Matchmaker performs semantic similarity search to connect users with peers who have successfully navigated similar life experiences.

This creates meaningful peer support based on experience rather than keyword matching.

---

# ⚙️ Workflow

```text
User
   │
   ▼
Listener Agent
   │
   ├──────────────► Streams empathetic responses
   │
   ▼
Clinical Mapper Agent
   │
   ▼
Clinical Profile
   │
   ▼
Risk Evaluation
   │
   ├── Crisis Detected
   │      ▼
   │  Crisis Response
   │
   └── Stable Root Cause
          ▼
   Matchmaker Engine
          ▼
 Semantic Peer Search
          ▼
 Anonymous Peer Recommendation
```

---

# 🛠️ Tech Stack

| Category                   | Technologies                       |
| -------------------------- | ---------------------------------- |
| **Programming Language**   | Python                             |
| **Frontend**               | Streamlit                          |
| **LLMs**                   | Ministral 3B, Gemma 3 4B           |
| **LLM Runtime**            | Ollama                             |
| **Embeddings**             | Hugging Face Sentence Transformers |
| **Vector Database**        | Pinecone                           |
| **Similarity Search**      | Semantic Embeddings                |
| **Environment Management** | Python Dotenv                      |

---

# 🚀 Getting Started

## Prerequisites

Install and configure the following:

* Ollama
* Pinecone Account
* Python 3.10+

Pull the required models:

```bash
ollama pull ministral-3:3b
ollama pull gemma3:4b
```

---

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd <repository-folder>
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
PINECONE_API_KEY=your_api_key
```

(Optional) Warm up the models:

```bash
python backend/scripts/warm_up_models.py
```

Launch the application:

```bash
streamlit run app0.py
```

---

# 🔒 Privacy & Safety

Kalpana is designed with privacy and responsible AI principles at its core.

* Local LLM inference using Ollama
* No external sharing of sensitive conversations
* Deterministic clinical reasoning
* Crisis detection pipeline
* Explainable AI decisions
* Human escalation support for high-risk situations

---

# 🚀 Future Roadmap

* 💬 Anonymous real-time peer chatrooms
* 🔐 End-to-end encrypted messaging
* 🤖 Passive AI moderation agent
* 🎙️ Speech-to-Text and Text-to-Speech integration
* 🧹 Automatic PII detection and removal
* 📈 Long-term emotional trend analysis
* 📱 Mobile application
* 🏥 Integration with professional mental health services

---

# 🏆 Achievement

🏅 **Top 8 Finalist – HealthHack 4.0**

Kalpana was recognized as one of the **Top 8 teams** at **HealthHack 4.0**, where it showcased an AI-driven approach to empathetic peer support, semantic matchmaking, and responsible mental health assistance.

### Certificate

<p align="center">
  <img src="https://github.com/user-attachments/assets/7ef8670f-284f-4eab-a682-a9bd978edefc" alt="HealthHack 4.0 Certificate"/>
</p>
