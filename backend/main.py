"""
TravelGuard AI — FastAPI entrypoint.

Run from the backend directory:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from app.factory import create_app

app = create_app()
