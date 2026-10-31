# Darwinistic Cybersecurity — Agentic Workflow Simulator

A safe, six-agent proof of concept that reproduces how an AI-driven phishing
attacker reasons and adapts, running entirely on synthetic (made-up) personas.
It never scrapes real people and never generates real scam text. For every
attack step it also shows the detection cues a person could use to spot it.

Built for NSF EAGER feasibility work (IU Kelley).

## Run locally
```
pip install -r requirements.txt
uvicorn app.api:app --reload --port 8000
# open http://localhost:8000
```

## Deploy
Render reads `render.yaml` and provisions the web service automatically.

## Scope
Synthetic personas only. No scraping. Message structure and defensive cues
only, never deployable attack content.
