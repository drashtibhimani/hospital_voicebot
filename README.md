# Hospital Voicebot

## Project Overview

Hospital Voicebot is a multilingual hospital assistant built with FastAPI and Streamlit.
It accepts text or voice input, detects the user language, searches a hospital knowledge base, and replies in the same language.
The app supports English, Hindi, and Gujarati, and also includes a dashboard for conversation analytics.

## Features

- Text and voice-based hospital question answering
- Automatic language detection for English, Hindi, and Gujarati
- RAG-based responses using a hospital knowledge base
- Knowledge base upload API for PDF, DOCX, and TXT documents
- Reply text in the same language as the user
- Text-to-speech audio response
- Conversation logging for analytics
- Dashboard with charts and recent logs

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Uvicorn |
| Frontend | Streamlit |
| RAG | LangChain, ChromaDB, sentence-transformers |
| LLM | Groq API with `llama-3.3-70b-versatile` |
| STT | SpeechRecognition with Google STT |
| TTS | gTTS |
| Database | PostgreSQL via SQLModel |
| Language Detection | langdetect |

## Setup Instructions

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd hospital-voicebot
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Copy environment file

```bash
cp .env.example .env
```

Add your `GROQ_API_KEY` to the `.env` file.
By default the app uses a local SQLite database at `voicebot.db`. If you want PostgreSQL instead, set `DATABASE_URL` explicitly in `.env`.

### 5. Run the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### Knowledge Base Upload API

Use `POST /knowledgebase/upload` with a multipart form field named `file`.
The API accepts `.pdf`, `.docx`, and `.txt` files, saves them into `backend/knowledge/uploads`, and indexes the extracted text into ChromaDB immediately.

### 6. Run the frontend

```bash
streamlit run frontend/app.py
```

## Project Structure

```text
hospital-voicebot/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── stt.py
│   │   └── analytics.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── rag_service.py
│   │   ├── lang_service.py
│   │   └── tts_service.py
│   └── knowledge/
│       ├── departments.txt
│       ├── doctors.txt
│       ├── faq_en.txt
│       ├── faq_hi.txt
│       └── faq_gu.txt
├── frontend/
│   ├── app.py
│   └── pages/
│       └── dashboard.py
├── .env.example
├── requirements.txt
└── README.md
```

## How to Get a Free Groq API Key

Go to [https://console.groq.com](https://console.groq.com), create an account, and generate an API key from the dashboard.

## Known Limitations

- Voice upload works better in Chrome and Edge than in some other browsers
- iOS Safari can have issues with voice workflows, so the Text Input tab is the safer option
- If speech recognition fails, users may need to use text input as a fallback
- The current app uses simple retrieval and does not store full conversation memory in RAG

## How RAG Works

The knowledge files are split into smaller chunks and stored in ChromaDB with multilingual embeddings.
When a user asks a question, the app finds the most relevant chunks and sends that context to the LLM.
The model then creates an answer based on the hospital knowledge base and responds in the same language.
