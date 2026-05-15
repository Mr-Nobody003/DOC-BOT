# Medical Evidence Retrieval Platform

A production-grade, multi-agent medical evidence retrieval and clinical research assistant built with LangGraph, FastAPI, Qdrant, and Next.js.

## Architecture Overview

This system utilizes a highly modular LangGraph workflow to enforce **strict medical evidence grounding**. It never hallucinates, never invents citations, and relies entirely on a deterministic multi-pass validation architecture.

### The Pipeline

1. **Query Understanding**: Classifies user intent and determines if the query is too vague (triggering a clarification interrupt).
2. **MeSH Translation**: Expands clinical queries using NIH E-utilities for robust retrieval.
3. **Retrieval**: Leverages a multi-pronged approach concurrently fetching from:
   - Local Qdrant (Hybrid Search)
   - Live Wikipedia API
   - Live PubMed Elite Journals (Lancet, BMJ, Nature, JAMA)
4. **Reranking**: Uses local `fastembed` ONNX models or lightweight sorting to instantly prioritize elite evidence while dropping irrelevant web chunks.
5. **Validation**: Deterministically evaluates semantic similarity and chunk count before generating a response.
6. **Grounded Generation**: Restricts the LLM exclusively to the injected evidence context, preventing hallucination.
7. **Citation Formatting**: Generates inline clickable citations pointing back to Wikipedia or PubMed URLs.

### User Interface

- A fluid, ChatGPT/Gemini-style Next.js application with dark mode support.
- Features a live **Vertical Timeline** that visually traces the LangGraph execution steps as they happen.

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

## Deployment (Vercel)

This project is configured for a **Dual-Project Vercel Deployment**. The Next.js frontend and the FastAPI backend must be deployed as two separate projects on Vercel.

### Do I need Docker on Vercel?
**No. Vercel is a serverless environment and does not run Docker containers.** 
The `docker-compose.yml` file is strictly for **local development**. When deploying to Vercel, you cannot use local Docker containers for Redis, Postgres, Qdrant, or MinIO. Instead, you must provision managed cloud alternatives for these services and provide their connection strings as Environment Variables to your Vercel backend deployment.
Examples:
- **Redis**: Upstash
- **Postgres**: Neon, Supabase
- **Qdrant**: Qdrant Cloud
- **MinIO/S3**: AWS S3, Cloudflare R2

### Deployment Steps

#### 1. Backend Deployment
1. Import your repository into Vercel.
2. Name the project `doc-bot-backend`.
3. Set the **Framework Preset** to `Other`.
4. Set the **Root Directory** to `backend`.
5. Vercel will automatically detect the Python project files inside the `backend` folder and build the Python serverless functions.
6. Add all necessary environment variables (Cloud Redis, Cloud Qdrant, etc.) in the Vercel dashboard.
7. **Note on Size Limits:** Vercel limits serverless functions to 250MB (500MB for Pro). Keep heavyweight ML libraries like `sentence-transformers` and `torch` out of the serverless dependency set; this backend uses lighter `fastembed`/ONNX-based retrieval dependencies instead.

#### 2. Frontend Deployment
1. Import the same repository into Vercel again as a new project.
2. Name the project `doc-bot-frontend`.
3. Set the **Framework Preset** to `Next.js`.
4. Set the **Root Directory** to `frontend`.
5. In the Environment Variables section, add:
   - `NEXT_PUBLIC_API_URL`: Set this to the URL of your deployed Vercel backend (e.g., `https://doc-bot-backend.vercel.app`).
6. Deploy.
