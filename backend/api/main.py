import uuid
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.api.chat import router as chat_router
from backend.api.citations import router as citations_router
from backend.api.feedback import router as feedback_router
from backend.api.health import router as health_router
from backend.core.logging import configure_logging
from backend.telemetry.tracing import configure_tracing


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    configure_tracing()
    yield


app = FastAPI(
    title="Medical Evidence Retrieval API",
    description="Multi-agent retrieval-grounded medical assistant",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = rid
    response = await call_next(request)
    response.headers["x-request-id"] = rid
    return response


@app.get("/", tags=["health"])
async def root():
    return {
        "status": "running",
        "service": "Medical Evidence Retrieval API",
        "version": app.version,
        "health": "/health",
        "docs": "/docs",
    }


app.include_router(health_router)
app.include_router(chat_router)
app.include_router(feedback_router)
app.include_router(citations_router)
app.include_router(chat_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
