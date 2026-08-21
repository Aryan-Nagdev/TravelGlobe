import httpx
import math
from typing import Dict, Any
from app.config import settings

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate direct distance in kilometers between two lat/lon coordinates."""
    R = 6371.0 # Earth radius km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

async def get_travel_route_heuristics(
    dest_lat: float,
    dest_lon: float,
    origin_lat: float = 19.0760, # Default Mumbai hub baseline if not specified
    origin_lon: float = 72.8777
) -> Dict[str, Any]:
    """
    Computes OSRM routing data or fallback distance/travel time heuristics.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = f"{settings.OSRM_BASE_URL}/route/v1/driving/{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
            resp = await client.get(url, params={"overview": "false"})
            if resp.status_code == 200:
                routes = resp.json().get("routes", [])
                if routes:
                    r = routes[0]
                    dist_km = round(r.get("distance", 0) / 1000.0, 1)
                    dur_min = round(r.get("duration", 0) / 60.0)
                    
                    hours = dur_min // 60
                    mins = dur_min % 60
                    time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins} mins"

                    return {
                        "distance_km": dist_km,
                        "duration_minutes": dur_min,
                        "formatted_time": time_str,
                        "accessibility": "Very Good" if dur_min < 90 else ("Moderate" if dur_min < 360 else "Long Transit"),
                        "traffic_level": "Normal Traffic",
                        "primary_mode": "Driving / Cab",
                        "provider": "osrm"
                    }
    except Exception as e:
        print(f"[Routing] OSRM call fallback: {e}")

    # Fallback Haversine heuristic
    dist_km = round(haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon), 1)
    if dist_km < 1.0: dist_km = 12.5 # Local destination estimate
    
    avg_speed_kmh = 42.0 # urban/suburban average
    dur_min = round((dist_km / avg_speed_kmh) * 60)
    hours = dur_min // 60
    mins = dur_min % 60
    time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins} mins"

    return {
        "distance_km": dist_km,
        "duration_minutes": dur_min,
        "formatted_time": time_str,
        "accessibility": "Good",
        "traffic_level": "Moderate Traffic",
        "primary_mode": "Highway / Flight / Train depending on distance",
        "provider": "haversine_heuristic"
    }
