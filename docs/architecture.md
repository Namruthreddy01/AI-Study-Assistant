# Architecture for Viva

## Why this design?

This project separates the user interface, API, and study logic. It keeps the mini-project understandable while making each part independently testable.

1. React dashboard gives students one place to upload a PDF and study it.
2. FastAPI validates requests and exposes documented endpoints automatically.
3. PDF service uses PyMuPDF because it can extract text page-by-page, which lets the application cite a page.
4. Chunking service makes long notes small enough to search and send to an AI model.
5. Embedding and vector services convert chunks to numbers and find the most relevant chunks. FAISS is fast and local, so no cloud database is required for a demo.
6. RAG service supplies retrieved chunks as context to the model. This makes the answer depend on the uploaded PDF rather than the model's general knowledge.

## Request flow

~~~
PDF upload
  -> validate PDF
  -> extract text per page
  -> split into overlapping chunks
  -> create embeddings
  -> save chunks in vector index

Student question
  -> embed question
  -> retrieve top matching chunks
  -> reject weak matches
  -> build grounded context
  -> generate answer with citations
~~~

## Local-first choice

For a college demonstration, the default is lightweight local storage. It has a clear upgrade path:

| Current boundary | Production replacement |
| --- | --- |
| SQLite document/history repository | PostgreSQL tables |
| FAISS files | pgvector index |
| Optional OpenAI-compatible client | institution-approved model provider |

This avoids infrastructure setup during a viva but does not lock the code to a temporary design.
