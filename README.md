# Medical Evidence Retrieval Platform

A production-grade, multi-agent medical evidence retrieval and clinical research assistant built with LangGraph, FastAPI, Qdrant, and Next.js.

## Architecture Overview

This system utilizes a highly modular LangGraph workflow to enforce **strict medical evidence grounding**. It never hallucinates, never invents citations, and relies entirely on a deterministic multi-pass validation architecture.

### The Pipeline

1. **Query Understanding**: Classifies user intent and determines if the query is too vague (triggering a clarification interrupt).
2. **MeSH Translation**: Expands clinical queries using NIH E-utilities for robust retrieval.
3. **Retrieval**: Leverages Qdrant (Hybrid Search) and BAAI/bge-large embeddings to fetch medical chunks.
4. **Reranking**: Uses cross-encoder reranking (`BAAI/bge-reranker-large` or fallback) to ensure top precision.
5. **Validation**: Deterministically evaluates semantic similarity and chunk count before generating a response.
6. **Grounded Generation**: Restricts the LLM exclusively to the injected evidence context.
7. **Citation Formatting & Audit Logging**: Maps all claims back to their exact PMIDs and logs the transaction.

## Infrastructure Stack

- **Backend**: Python 3.12, FastAPI, LangGraph, ARQ (Async Redis Workers)
- **Frontend**: Next.js 14, Tailwind CSS, TypeScript
- **Database Layer**:
  - **Qdrant**: Vector storage and hybrid search
  - **Postgres**: Audit logging and relational storage
  - **Redis**: Caching and LangGraph Checkpointing
  - **MinIO**: Object storage for unstructured medical PDFs

## Getting Started

### 1. Start Infrastructure

```bash
docker compose up -d
```

### 2. Configure Environment

Copy the `.env.example` file to `.env` in the `backend/` directory:

```bash
cp backend/.env.example backend/.env
```

Ensure you set an `OPENROUTER_API_KEY` (or `OPENAI_API_KEY`). The system currently defaults to `google/gemma-2-9b-it:free`.

### 3. Start Backend

```powershell
pip install -e ".\backend[dev]"
$env:PYTHONPATH="."
python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Testing

The project includes an integrated direct-graph test suite to bypass FastAPI networking for quick debugging:

```powershell
$env:PYTHONPATH="."
python scripts/debug_graph.py
```
