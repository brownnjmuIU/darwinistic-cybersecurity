"""
FastAPI service.

  GET /                -> the dashboard page
  GET /api/health      -> liveness check for Render + which reasoning backend
  GET /api/run?n=5&seed=42 -> run the simulation, return the full traces as JSON

This is what Render runs. Start command:
    uvicorn app.api:app --host 0.0.0.0 --port $PORT
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from .llm import active_backend
from .orchestrator import run_batch

app = FastAPI(title="Darwinistic Cybersecurity — Workflow Simulator")

_STATIC = Path(__file__).parent / "static"


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "backend": active_backend()}


@app.get("/api/run")
def api_run(n: int = 5, seed: int = 42) -> JSONResponse:
    n = max(1, min(n, 25))  # keep the free tier happy
    cases = run_batch(n, seed=seed)
    return JSONResponse([c.model_dump(mode="json") for c in cases])


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(_STATIC / "dashboard.html")
