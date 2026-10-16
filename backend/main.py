"""
TravelGuard AI — FastAPI entrypoint.

Run from the backend directory:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from app.factory import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

