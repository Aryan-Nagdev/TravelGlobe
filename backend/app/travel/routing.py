import httpx
import math
from typing import Dict, Any, List, Optional
from app.config import settings

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate direct distance in kilometers between two lat/lon coordinates."""
    R = 6371.0  # Earth radius km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def downsample_coordinates(coords: List[List[float]], max_points: int = 150) -> List[List[float]]:
    """Downsamples GeoJSON coordinates [lon, lat] to Leaflet [lat, lon] array."""
    if not coords:
        return []
    
    total = len(coords)
    if total <= max_points:
        return [[c[1], c[0]] for c in coords]
    
    step = max(1, total // max_points)
    sampled = [[coords[i][1], coords[i][0]] for i in range(0, total, step)]
    # Ensure exact destination endpoint is included
    if [coords[-1][1], coords[-1][0]] != sampled[-1]:
        sampled.append([coords[-1][1], coords[-1][0]])
    return sampled

async def get_travel_route_heuristics(
    dest_lat: float,
    dest_lon: float,
    origin_lat: Optional[float] = None,
    origin_lon: Optional[float] = None,
    origin_name: Optional[str] = None,
    dest_name: str = "Destination"
) -> Dict[str, Any]:
    """
    Computes real OSRM driving routing data including:
    - distance_km
    - duration_minutes & formatted_time
    - route_points (array of [lat, lon] for Leaflet polyline)
    - origin & destination metadata
    - alternative route choices if available
    - traffic flow estimate based on transit speed
    """
    if origin_lat is None or origin_lon is None or not origin_name:
        return {
            "distance_km": None,
            "duration_minutes": None,
            "formatted_time": "Specify starting location for route",
            "accessibility": "Direct Destination Access",
            "traffic_level": "Normal Local Flow",
            "primary_mode": "Road / Transit",
            "provider": "awaiting_origin",
            "route_points": [],
            "origin": None,
            "destination": {
                "name": dest_name,
                "lat": dest_lat,
                "lon": dest_lon
            },
            "alternatives": []
        }

    # If distance is intercontinental / cross-oceanic (> 2500 km), road driving routing is impossible
    direct_dist = haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon)
    if direct_dist < 0.5:
        return {
            "distance_km": 0.0,
            "duration_minutes": 0,
            "formatted_time": "Local destination",
            "accessibility": "Local City Center",
            "traffic_level": "Local City Traffic",
            "primary_mode": "Local Transit / Walking",
            "provider": "local_destination",
            "route_points": [[dest_lat, dest_lon]],
            "origin": {
                "name": origin_name,
                "lat": origin_lat,
                "lon": origin_lon
            },
            "destination": {
                "name": dest_name,
                "lat": dest_lat,
                "lon": dest_lon
            },
            "alternatives": []
        }

    if direct_dist > 2500.0:
        flight_hours = round((direct_dist / 820.0) + 3.0, 1)
        dur_min = int(flight_hours * 60)
        h = int(flight_hours)
        m = int((flight_hours - h) * 60)
        time_str = f"{h}h {m}m (Flight transit)"
        interpolated = [
            [origin_lat, origin_lon],
            [dest_lat, dest_lon]
        ]
        return {
            "distance_km": round(direct_dist, 1),
            "duration_minutes": dur_min,
            "formatted_time": time_str,
            "accessibility": "International Air Transit",
            "traffic_level": "Air Corridor (Oceanic crossing)",
            "primary_mode": "Flight",
            "provider": "flight_geodesic",
            "route_points": interpolated,
            "origin": {
                "name": origin_name,
                "lat": origin_lat,
                "lon": origin_lon
            },
            "destination": {
                "name": dest_name,
                "lat": dest_lat,
                "lon": dest_lon
            },
            "alternatives": []
        }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            url = f"{settings.OSRM_BASE_URL}/route/v1/driving/{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
            params = {
                "overview": "full",
                "geometries": "geojson",
                "alternatives": "true",
                "steps": "true"
            }
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                routes = data.get("routes", [])
                if routes:
                    primary_route = routes[0]
                    dist_km = round(primary_route.get("distance", 0) / 1000.0, 1)
                    dur_min = round(primary_route.get("duration", 0) / 60.0)
                    
                    hours = dur_min // 60
                    mins = dur_min % 60
                    time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins} mins"

                    # Calculate average road travel speed
                    avg_speed_kmh = (dist_km / (dur_min / 60.0)) if dur_min > 0 else 45.0
                    if avg_speed_kmh < 28.0:
                        traffic_status = "Dense Traffic / Winding Ghat Ascent"
                    elif avg_speed_kmh < 50.0:
                        traffic_status = "Normal Highway Traffic"
                    else:
                        traffic_status = "Free Flowing Expressway"

                    # Extract polyline geometry
                    raw_coords = primary_route.get("geometry", {}).get("coordinates", [])
                    route_points = downsample_coordinates(raw_coords, max_points=160)

                    # Extract alternative routes if available
                    alternatives = []
                    for alt in routes[1:3]:
                        alt_dist = round(alt.get("distance", 0) / 1000.0, 1)
                        alt_dur = round(alt.get("duration", 0) / 60.0)
                        alt_h, alt_m = alt_dur // 60, alt_dur % 60
                        alt_time = f"{alt_h}h {alt_m}m" if alt_h > 0 else f"{alt_m} mins"
                        
                        summary_name = "Alternate Route"
                        legs = alt.get("legs", [])
                        if legs and legs[0].get("summary"):
                            summary_name = legs[0].get("summary")

                        alternatives.append({
                            "distance_km": alt_dist,
                            "duration_minutes": alt_dur,
                            "formatted_time": alt_time,
                            "summary": summary_name
                        })

                    return {
                        "distance_km": dist_km,
                        "duration_minutes": dur_min,
                        "formatted_time": time_str,
                        "accessibility": "Direct Road Access" if dur_min < 120 else ("Moderate Transit" if dur_min < 360 else "Long Distance Transit"),
                        "traffic_level": f"{traffic_status} (Routing model)",
                        "primary_mode": "Road Transit / Cab / Bus",
                        "provider": "osrm",
                        "route_points": route_points,
                        "origin": {
                            "name": origin_name,
                            "lat": origin_lat,
                            "lon": origin_lon
                        },
                        "destination": {
                            "name": dest_name,
                            "lat": dest_lat,
                            "lon": dest_lon
                        },
                        "alternatives": alternatives
                    }
    except Exception as e:
        print(f"[Routing] OSRM call notice: {e}")

    # Fallback Haversine geodesic heuristic
    dist_km = round(haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon), 1)
    if dist_km < 1.0:
        dist_km = 10.0
    
    avg_speed_kmh = 45.0
    dur_min = round((dist_km / avg_speed_kmh) * 60)
    hours = dur_min // 60
    mins = dur_min % 60
    time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins} mins"

    # Create straight line interpolated points
    interpolated_points = [
        [origin_lat, origin_lon],
        [(origin_lat * 0.67 + dest_lat * 0.33), (origin_lon * 0.67 + dest_lon * 0.33)],
        [(origin_lat * 0.33 + dest_lat * 0.67), (origin_lon * 0.33 + dest_lon * 0.67)],
        [dest_lat, dest_lon]
    ]

    return {
        "distance_km": dist_km,
        "duration_minutes": dur_min,
        "formatted_time": time_str,
        "accessibility": "Direct Connection",
        "traffic_level": "Standard Flow (Estimated)",
        "primary_mode": "Highway / Transit",
        "provider": "haversine_geodesic",
        "route_points": interpolated_points,
        "origin": {
            "name": origin_name,
            "lat": origin_lat,
            "lon": origin_lon
        },
        "destination": {
            "name": dest_name,
            "lat": dest_lat,
            "lon": dest_lon
        },
        "alternatives": []
    }
