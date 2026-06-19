# Ednex AI Presenter

Upload a deck, point it at your knowledge base; get a tireless presenter that pitches and handles Q&A — on screen now, on a robot later.

## Prerequisites

- Python 3.10+
- Node.js 20+

## Setup

### 1. Environment variables

```bash
cp .env.example .env
# Fill in OPENAI_API_KEY and ELEVENLABS_API_KEY
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend

```bash
cd frontend
npm install
```

## Run

### Backend (API server)

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

API available at `http://localhost:8000` — health check: `GET /health`

### Frontend (dev server)

```bash
cd frontend
npm run dev
```

UI available at `http://localhost:5173`

## Test

### Backend

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

### Frontend

```bash
cd frontend
npm test
```
