# AI Study Assistant

A B.Tech mini-project that turns PDF study material into a grounded study workspace. Upload a PDF, ask questions based on its content, create summaries, generate MCQs and revision questions, and take a quiz.

## Features

- Secure PDF upload with size/type validation and page-aware text extraction
- Chunking, local embeddings, and a FAISS-backed semantic search layer
- RAG answers with page citations; an explicit not-found response for weak matches
- Short summaries, key points, exam focus, MCQs, and revision questions
- Browser-based quiz flow, scoring, answer review, and local study history
- OpenAI-compatible LLM adapter with an offline deterministic fallback for demos

## Architecture

~~~
React dashboard -> FastAPI routes -> study services
                                      |-- PyMuPDF extraction + chunking
                                      |-- embedding provider -> FAISS vector search
                                      |-- RAG / LLM provider
                                      |-- SQL database document and history repository
~~~

The initial repository uses SQLite metadata locally plus FAISS-compatible files so it is easy to run in a viva. Set DATABASE_URL to a PostgreSQL connection string for deployment; the database repository and vector store are separate boundaries.

## Tech stack

- Frontend: React, TypeScript, Vite
- Backend: Python, FastAPI
- PDF processing: PyMuPDF
- Retrieval: FAISS (with a NumPy fallback if FAISS is unavailable)
- AI: OpenAI-compatible API, or offline grounded fallback

## Run locally

1. Create and activate a Python 3.11+ virtual environment.
2. Install backend dependencies:

   ~~~bash
   cd backend
   pip install -r requirements.txt
   ~~~

3. Copy the configuration file and optionally add an API key:

   ~~~bash
   cp .env.example .env
   ~~~

   The default DATABASE_URL uses SQLite. For PostgreSQL, set it to a connection
   string such as postgresql+psycopg://student:password@localhost:5432/study_assistant.

4. Start the API:

   ~~~bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ~~~

5. In a second terminal, start the UI:

   ~~~bash
   cd frontend
   npm install
   npm run dev
   ~~~

Open http://localhost:5173. The API documentation is at http://localhost:8000/docs.

## Testing

Run the backend tests from the project root:

~~~bash
python3 -m pytest -q
~~~

Build-check the frontend:

~~~bash
cd frontend
npm run build
~~~

## API overview

| Endpoint | Purpose |
| --- | --- |
| POST /api/documents/upload | Upload, extract, chunk, and index a PDF |
| GET /api/documents | List uploaded material |
| POST /api/study/chat | Answer a question using a selected document |
| POST /api/study/summary | Generate a structured summary |
| POST /api/study/mcqs | Generate MCQs |
| POST /api/study/revision | Generate revision questions |
| POST /api/study/quiz/score | Score a submitted quiz |
| GET /api/study/history | Retrieve basic study history |

## Project structure

~~~
backend/app/
  api/             # HTTP routes
  core/            # configuration and errors
  models/          # API request/response shapes
  services/        # PDF, embeddings, vectors, RAG, study generation
  storage/         # local persistence boundary
frontend/src/      # React UI
docs/architecture.md
~~~

## RAG behaviour

The backend embeds the question, retrieves the nearest chunks for the selected PDF, and gives only those chunks to the LLM. A relevance threshold prevents unsupported generic answers. The UI displays each source filename and page number returned by retrieval.

## Screenshots

Add screenshots here after running the dashboard locally.

## Future improvements

- pgvector and user authentication
- OCR for scanned PDFs
- Background jobs for large documents
- Streaming answers and token usage controls
- Rich study-progress analytics
