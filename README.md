# DOC-BOT: Medical Evidence Retrieval Platform

A production-grade, multi-agent medical evidence retrieval and clinical research assistant built with LangGraph, FastAPI, Qdrant, and Next.js.

---

## 🧠 The AI Pipeline & Working

This system utilizes a highly modular LangGraph workflow to enforce **strict medical evidence grounding**. It never hallucinates, never invents citations, and relies entirely on a deterministic multi-pass validation architecture.

1. **Query Understanding**: Classifies user intent and determines if the query is too vague.
2. **MeSH Translation**: Expands clinical queries using NIH E-utilities for robust retrieval.
3. **Multi-Source Retrieval**: Concurrently fetches data from:
   - **Qdrant Vector Database:** Fast, dense retrieval of pre-ingested medical abstracts.
   - **Live Wikipedia API:** Real-time medical definitions.
   - **Live PubMed API:** Real-time search against elite journals (Lancet, BMJ, Nature, JAMA).
4. **Validation**: Evaluates semantic similarity and chunk count before generating a response.
5. **Grounded Generation**: Restricts the LLM exclusively to the injected evidence context, preventing hallucination.

---

## ❓ The Feedback Mechanism (Thumbs Up/Down)

### Why does the project ask for feedback?
In production AI systems, user feedback (thumbs up / thumbs down) is critical for **RLHF (Reinforcement Learning from Human Feedback)** and quality monitoring. If an AI gives a bad medical response, doctors or users can rate it negatively. The backend stores this rating, the `session_id`, and the exact `trace_id` of the LLM execution in the Postgres database so developers can debug exactly *why* the AI failed.

### Why is there no feedback on the frontend?
The backend developers built the `/feedback` API endpoint and the Postgres database logic in anticipation of this feature. However, **the frontend UI developers have not yet built the thumbs up/down buttons** in the React/Next.js application. 

Because the frontend never calls this API, the `medical_feedback` database table is never created (the backend is designed to create the table dynamically the very first time a rating is submitted). This is why your Supabase database currently shows 0 tables!

---

## 🌿 Branch Strategy: Local vs. Deployed

This project uses a dual-environment strategy, separated by Git branches.

### 1. `origin/main` (The Local Workflow)
The `main` branch is designed for **Local Development**. It relies heavily on Docker to spin up the infrastructure on your personal computer. 
*   **Infrastructure:** Uses `docker-compose.yml` to spin up local instances of Postgres, Redis, Qdrant, and MinIO.
*   **Workflow:** You run the backend and frontend locally on `localhost:8000` and `localhost:3000`.
*   **Timeouts:** No strict timeouts. The local server will process complex AI graphs for as long as it takes.

### 2. `deploy` (The Cloud Workflow)
The `deploy` branch contains the exact same AI logic as `main`, but is heavily optimized for **Serverless Cloud Deployment (Vercel)**.
*   **Infrastructure:** Docker is completely ignored. Instead, the app connects to managed cloud services (Supabase, Upstash Redis, Qdrant Cloud).
*   **Workflow:** Deployed as two separate projects on Vercel (one for the FastAPI backend, one for the Next.js frontend).
*   **Timeouts:** Because Vercel's Free Hobby Plan forcibly terminates functions after **60 seconds**, the `deploy` branch includes highly specific logic (in `vercel.json` and `retrieval.py`) to aggressively time-out the Qdrant (50s) and PubMed (45s) retrieval steps so the app doesn't crash with a `504 Gateway Timeout`.

---

## 💻 Local Setup Instructions (For `main` branch)

1. **Start Local Infrastructure:**
   ```bash
   docker compose up -d
   ```
2. **Configure `.env`:** Copy `.env.example` to `backend/.env` and add your `OPENROUTER_API_KEY`.
3. **Start Backend:**
   ```powershell
   pip install -e ".\backend[dev]"
   $env:PYTHONPATH="."
   python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
   ```
4. **Start Frontend:**
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

---

## ☁️ Cloud Deployment Instructions (For `deploy` branch)

### 1. Cloud Dependencies Setup
Before deploying to Vercel, you must set up the following free cloud services and place their connection strings in your `backend/.env` file:
*   **Postgres (Supabase):** Provides the `POSTGRES_DSN` for the feedback database.
*   **Redis (Upstash):** Provides `UPSTASH_REDIS_REST_URL` and `REDIS_URL` for caching and LangGraph state.
*   **Vector DB (Qdrant Cloud):** Provides `QDRANT_CLIENT_API_ENDPOINT` and `QDRANT_CLIENT_API_KEY` for vector storage.

### 2. Vercel Backend Deployment
1. Import your repository into Vercel. Name it `doc-bot-backend`.
2. Set **Framework Preset** to `Other` and **Root Directory** to `backend`.
3. Add all your Cloud Environment Variables in the Vercel dashboard.
4. Deploy. (Vercel will read `vercel.json` and deploy it as Python Serverless Functions).

### 3. Vercel Frontend Deployment
1. Import the repository into Vercel again. Name it `doc-bot-frontend`.
2. Set **Framework Preset** to `Next.js` and **Root Directory** to `frontend`.
3. Add the `NEXT_PUBLIC_API_URL` environment variable, pointing to your deployed Vercel backend URL.
4. Deploy.

### 4. Cloud Data Ingestion
To populate your Qdrant Cloud vector database with the most commonly searched medical queries (so inference is fast), run the cloud ingestion script locally on your computer:
```powershell
$env:PYTHONPATH="."
python scripts/ingest_qdrant_cloud.py core
```
*(This consumes roughly ~50MB of your 1GB free Qdrant tier).*
