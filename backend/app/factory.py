import time
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
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
from app.sar.disaster import assess_sar_disaster_risk
from app.safety.engine import compute_safety_score
from app import hdfs_store, kafka_bus, pipeline
from app import bigdata_analytics

class DestinationQueryRequest(BaseModel):
    place_name: str = Field(..., example="Manali")
    origin_lat: Optional[float] = None
    origin_lon: Optional[float] = None
    origin_city: Optional[str] = None

class ChatRequest(BaseModel):
    message: str = Field(..., example="What are the top attractions in Manali?")
    destination_context: Optional[Dict[str, Any]] = None
    chat_history: Optional[List[Dict[str, str]]] = None

class AutocompleteRequest(BaseModel):
    query: str = Field(..., example="Paris")


@asynccontextmanager
async def lifespan(app: FastAPI):
    for path in (
        "/travelglobe/events",
        "/travelglobe/analyses",
        "/travelglobe/sar",
        "/travelglobe/chat",
        "/travelglobe/graph",
        "/travelglobe/analytics",
    ):
        hdfs_store.mkdir(path)
    hdfs_store.ensure_seed_data()
    kafka_bus.start_background()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="3.0.0",
        description="TravelGlobe — Big Data travel platform (HDFS, MapReduce, Kafka, Spark, PageRank)",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    @app.get(f"{settings.API_V1_PREFIX}/health")
    async def health_check():
        return {
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "version": "3.0.0",
            "timestamp": time.time(),
        }

    @app.get(f"{settings.API_V1_PREFIX}/integrations-status")
    async def integrations_status():
        groq_active = bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY.startswith("gsk_"))
        openweather_active = bool(settings.OPENWEATHER_API_KEY and len(settings.OPENWEATHER_API_KEY) > 10)
        cluster = pipeline.cluster_status()
        return {
            "groq_llm": {"status": "connected" if groq_active else "active_assistant"},
            "openweather": {"status": "connected" if openweather_active else "weather_service"},
            "nominatim": {"status": "connected", "provider": "OpenStreetMap"},
            "osrm": {"status": "connected", "provider": "OSRM Routing Engine"},
            "hadoop_hdfs": cluster["hdfs"],
            "apache_kafka": cluster["kafka"],
            "hadoop_mapreduce": cluster["mapreduce"],
            "apache_spark": cluster["spark"],
            "pagerank": cluster["pagerank"],
        }

    @app.post(f"{settings.API_V1_PREFIX}/autocomplete")
    async def place_autocomplete(req: AutocompleteRequest):
        results = await autocomplete_place(req.query)
        return {"suggestions": results}

    @app.post(f"{settings.API_V1_PREFIX}/destination-analysis")
    async def destination_analysis(req: DestinationQueryRequest):
        try:
            geo = await geocode_place(req.place_name)
            lat, lon = geo["lat"], geo["lon"]
            place_clean = req.place_name.strip()

            origin_city = req.origin_city.strip() if (req.origin_city and req.origin_city.strip()) else None
            origin_lat = req.origin_lat
            origin_lon = req.origin_lon

            if origin_city:
                if origin_lat is None or origin_lon is None:
                    try:
                        orig_geo = await geocode_place(origin_city)
                        origin_lat = orig_geo["lat"]
                        origin_lon = orig_geo["lon"]
                        origin_city = orig_geo.get("city") or origin_city
                    except Exception:
                        origin_lat = None
                        origin_lon = None

            weather_task = get_weather_forecast(lat, lon, place_clean)
            routing_task = get_travel_route_heuristics(
                dest_lat=lat,
                dest_lon=lon,
                origin_lat=origin_lat,
                origin_lon=origin_lon,
                origin_name=origin_city,
                dest_name=place_clean
            )
            recommendations_task = get_hotel_and_attraction_recommendations(lat, lon, place_clean)

            weather, routing, recommendations = await asyncio.gather(
                weather_task,
                routing_task,
                recommendations_task,
            )

            crowd = analyze_crowd_density(lat, lon, place_clean, weather_data=weather)
            photos = recommendations.get("photos") or (await get_destination_photos(place_clean))
            sar_disaster = await assess_sar_disaster_risk(
                lat, lon, place_clean, weather.get("condition", "")
            )
            safety = compute_safety_score(weather, crowd, sar_disaster, place_clean)

            result = {
                "destination": geo,
                "weather": weather,
                "crowd": crowd,
                "routing": routing,
                "recommendations": recommendations,
                "photos": photos,
                "sar_disaster": sar_disaster,
                "safety": safety,
                "timestamp": time.time(),
            }
            return pipeline.persist_destination_analysis(req.place_name.strip(), origin_city, result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Destination exploration failed: {str(e)}")

    @app.post(f"{settings.API_V1_PREFIX}/chat")
    async def chat_endpoint(req: ChatRequest):
        if not req.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        response = await generate_assistant_response(
            message=req.message,
            destination_context=req.destination_context,
            chat_history=req.chat_history,
        )
        place = ""
        if req.destination_context:
            place = (req.destination_context.get("destination") or {}).get("city") or ""
        
        # Persist event asynchronously without blocking chat response
        asyncio.create_task(asyncio.to_thread(pipeline.persist_chat, req.message, response, place))
        return response

    @app.get(f"{settings.API_V1_PREFIX}/bigdata/status")
    async def bigdata_status():
        return pipeline.cluster_status()

    @app.get(f"{settings.API_V1_PREFIX}/bigdata/popularity")
    async def bigdata_popularity():
        return bigdata_analytics.popularity()

    @app.get(f"{settings.API_V1_PREFIX}/bigdata/pagerank")
    async def bigdata_pagerank():
        return bigdata_analytics.pagerank()

    @app.get(f"{settings.API_V1_PREFIX}/bigdata/spark")
    async def bigdata_spark():
        return bigdata_analytics.spark_stats()

    @app.get(f"{settings.API_V1_PREFIX}/bigdata/hdfs")
    async def bigdata_hdfs(path: str = "/travelglobe"):
        return {"path": path, "files": hdfs_store.list_status(path)}

    @app.get(f"{settings.API_V1_PREFIX}/bigdata/proof")
    async def bigdata_proof():
        events = hdfs_store.get_text("/travelglobe/events/stream.jsonl") or hdfs_store.get_text(
            "/travelglobe/events/sample_events.jsonl"
        ) or ""
        return {
            "hdfs": {
                "webhdfs": settings.HDFS_WEBHDFS,
                "root": hdfs_store.list_status("/travelglobe"),
                "event_log_sample": "\n".join(events.splitlines()[-8:]),
            },
            "kafka": kafka_bus.STATS,
            "mapreduce": bigdata_analytics.popularity(),
            "spark": bigdata_analytics.spark_stats(),
            "pagerank": bigdata_analytics.pagerank(),
        }

    return app
