# PDF Summarizer

A full-stack application built with FastAPI and React (Vite + Tailwind CSS) for extracting, analyzing, and summarizing PDF documents.

## Project Structure

```text
pdf summarizer/
├── backend/            # FastAPI Application
│   ├── app/
│   │   ├── api/        # Endpoint routes
│   │   ├── core/       # Configurations & Settings
│   │   ├── services/   # Business logic & PDF processing
│   │   └── main.py     # FastAPI entry point
│   └── requirements.txt
├── frontend/           # React + Vite + Tailwind UI
│   ├── src/
│   │   ├── components/ # Reusable React UI components
│   │   ├── pages/      # Application views/pages
│   │   ├── services/   # Axios API client setup
│   │   └── App.jsx
│   └── package.json
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm

### Backend Setup
1. `cd backend`
2. `python3 -m venv venv && source venv/bin/activate`
3. `pip install -r requirements.txt`
4. `uvicorn app.main:app --reload --port 8000`

### Frontend Setup
1. `cd frontend`
2. `npm install`
3. `npm run dev`
