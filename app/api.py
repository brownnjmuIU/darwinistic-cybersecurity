"""
FastAPI service.

  GET /                     -> the dashboard page
  GET /api/health           -> liveness + reasoning backend + whether a trained policy is loaded
  GET /api/run?n=5&seed=42&policy=baseline  -> run the simulation, return full traces as JSON
                               policy=learned uses the trained RL policy (if present)
  GET /learning_curve.png   -> the training chart, for the dashboard

Start command (unchanged):
    uvicorn app.api:app --host 0.0.0.0 --port $PORT
"""

from __future__ import annotations

import copy
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from .llm import active_backend
from .orchestrator import run_batch
from .rl import StrategyLearner

app = FastAPI(title="Darwinistic Cybersecurity — Workflow Simulator")

_STATIC = Path(__file__).parent / "static"
_ROOT = Path(__file__).parent.parent

# Load the trained policy once at startup, if training has been run.
_LEARNER = StrategyLearner()
_POLICY_PATH = _ROOT / "learned_policy.json"
_HAS_POLICY = _POLICY_PATH.exists()
if _HAS_POLICY:
    _LEARNER.load(str(_POLICY_PATH))


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "backend": active_backend(), "has_policy": _HAS_POLICY}


@app.get("/api/run")
def api_run(n: int = 5, seed: int = 42, policy: str = "baseline") -> JSONResponse:
    n = max(1, min(n, 25))  # keep the free tier happy
    if policy == "learned" and _HAS_POLICY:
        # deep-copy so serving never mutates the shared trained policy
        learner = copy.deepcopy(_LEARNER)
        cases = run_batch(n, seed=seed, learner=learner, epsilon=0.0)
    else:
        cases = run_batch(n, seed=seed)
    return JSONResponse([c.model_dump(mode="json") for c in cases])


@app.get("/learning_curve.png")
def curve() -> FileResponse:
    return FileResponse(_ROOT / "learning_curve.png")


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(_STATIC / "dashboard.html")
