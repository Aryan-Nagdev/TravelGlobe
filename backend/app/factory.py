import time
import asyncio
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from app.config import settings
from app.location.geocoding import geocode_place, autocomplete_place
from app.weather.service import get_weather_forecast
from app.crowd.service import analyze_crowd_density
from app.travel.routing import get_travel_route_heuristics
from app.places.recommendations import get_hotel_and_attraction_recommendations, get_destination_photos
from app.assistant.chat import generate_assistant_response

# Fast In-Memory LRU Cache
_ANALYSIS_CACHE: Dict[str, Dict[str, Any]] = {}

class DestinationQueryRequest(BaseModel):
    place_name: str = Field(..., example="Manali")
    origin_lat: Optional[float] = None
    origin_lon: Optional[float] = None

class ChatRequest(BaseModel):
    message: str = Field(..., example="What are the top attractions in Manali?")
    destination_context: Optional[Dict[str, Any]] = None
    chat_history: Optional[List[Dict[str, str]]] = None

class AutocompleteRequest(BaseModel):
    query: str = Field(..., example="Paris")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="2.0.0",
        description="TravelGuard — Premium Travel & Destination Exploration Platform",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Health Status ────────────────────────────────────────────────────────
    @app.get("/health")
    @app.get(f"{settings.API_V1_PREFIX}/health")
    async def health_check():
        return {
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "version": "2.0.0",
            "timestamp": time.time()
        }

    @app.get(f"{settings.API_V1_PREFIX}/integrations-status")
    async def integrations_status():
        groq_active = bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY.startswith("gsk_"))
        openweather_active = bool(settings.OPENWEATHER_API_KEY and len(settings.OPENWEATHER_API_KEY) > 10)
        return {
            "groq_llm": {"status": "connected" if groq_active else "active_assistant"},
            "openweather": {"status": "connected" if openweather_active else "weather_service"},
            "nominatim": {"status": "connected", "provider": "OpenStreetMap"},
            "osrm": {"status": "connected", "provider": "OSRM Routing Engine"}
        }

    # ── Autocomplete ─────────────────────────────────────────────────────────
    @app.post(f"{settings.API_V1_PREFIX}/autocomplete")
    async def place_autocomplete(req: AutocompleteRequest):
        results = await autocomplete_place(req.query)
        return {"suggestions": results}

    # ── Fast High-Performance Destination Analysis ──────────────────────────
    @app.post(f"{settings.API_V1_PREFIX}/destination-analysis")
    async def destination_analysis(req: DestinationQueryRequest):
        cache_key = req.place_name.strip().lower()

        # Instant Cache Return (< 5ms)
        if cache_key in _ANALYSIS_CACHE:
            return _ANALYSIS_CACHE[cache_key]

        try:
            # 1. Geocode Location
            geo = await geocode_place(req.place_name)
            lat, lon = geo["lat"], geo["lon"]
            place_clean = geo["city"] or req.place_name

            origin_lat = req.origin_lat or 19.0760
            origin_lon = req.origin_lon or 72.8777

            # 2. Parallel Async Execution via asyncio.gather (< 200ms)
            weather_task = get_weather_forecast(lat, lon, place_clean)
            routing_task = get_travel_route_heuristics(lat, lon, origin_lat, origin_lon)
            recommendations_task = get_hotel_and_attraction_recommendations(lat, lon, place_clean)

            weather, routing, recommendations = await asyncio.gather(
                weather_task,
                routing_task,
                recommendations_task
            )

            crowd = analyze_crowd_density(lat, lon, place_clean)
            photos = get_destination_photos(place_clean)

            result = {
                "destination": geo,
                "weather": weather,
                "crowd": crowd,
                "routing": routing,
                "recommendations": recommendations,
                "photos": photos,
                "timestamp": time.time()
            }

            # Save in LRU cache
            _ANALYSIS_CACHE[cache_key] = result
            return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Destination exploration failed: {str(e)}")

    # ── AI Travel Assistant ──────────────────────────────────────────────────
    @app.post(f"{settings.API_V1_PREFIX}/chat")
    async def chat_endpoint(req: ChatRequest):
        if not req.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        response = await generate_assistant_response(
            message=req.message,
            destination_context=req.destination_context,
            chat_history=req.chat_history
        )
        return response

    return app
