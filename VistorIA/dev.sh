#!/usr/bin/env bash
source .venv/bin/activate
export PYTHONPATH=VistorIA
uvicorn app.main:app --reload --port 8000