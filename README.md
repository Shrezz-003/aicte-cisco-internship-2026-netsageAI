# NetSage AI

NetSage AI is an intelligent, Human-in-the-Loop (HITL) network diagnostic copilot designed for enterprise environments. It translates natural language network symptoms into structured root cause analyses, maps faults to specific OSI layers, and generates step-by-step CLI remediation runbooks. 

To ensure production safety, NetSage AI prevents automated configuration changes by enforcing a strict engineer verification process. Every AI-generated diagnostic must be manually accepted or rejected, with all interactions logged to a live telemetry dashboard for audit and model retraining purposes.

## Key Features

* **Natural Language Diagnostics:** Ingests plain-English network fault descriptions and translates them into actionable engineering data.
* **Structured Remediation:** Generates precise, non-intrusive `show` commands and sequential CLI runbooks for Cisco and standard networking hardware.
* **Human-in-the-Loop (HITL) Architecture:** Mandates explicit engineer sign-off (Accept/Reject) on all AI recommendations before they can be considered for execution.
* **Responsible AI Dashboard:** Features a live telemetry module that tracks human approval rates, total evaluated cases, and maintains an immutable log of rejected solutions for safety reviews.

## Architecture & Tech Stack

* **Frontend:** Streamlit (Python) with a custom dark-mode UI and persistent state management.
* **Backend LLM:** Google Gemini API for natural language understanding and JSON schema enforcement.
* **Knowledge Retrieval:** Retrieval-Augmented Generation (RAG) pipeline to inject verified networking logic and documentation into the model context.
* **Data Processing:** Pandas for real-time dashboard analytics and log management.

## Setup Instructions

Follow these steps to configure and run the project locally.

**1. Create and activate a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Configure environment variables:**
Create a file named `.env` in the root directory of the project and add your Gemini API key:
```env
GEMINI_API_KEY=your_api_key_here
```

**4. Run the application:**
```bash
streamlit run app.py
```

## Author

Subham
