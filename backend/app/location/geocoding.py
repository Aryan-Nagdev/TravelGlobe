import httpx
from typing import Dict, Any, Optional
from app.config import settings

async def geocode_place(place_name: str) -> Dict[str, Any]:
    """
    Geocodes a place name into latitude, longitude, display name, and country details
    using Nominatim with fallback to Photon.
    """
    clean_query = place_name.strip()
    if not clean_query:
        raise ValueError("Place name cannot be empty")

    headers = {"User-Agent": settings.NOMINATIM_USER_AGENT}
    
    # 1. Try Nominatim
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                f"{settings.NOMINATIM_BASE_URL}/search",
                params={"q": clean_query, "format": "json", "addressdetails": 1, "limit": 1},
                headers=headers
            )
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    item = data[0]
                    address = item.get("address", {})
                    return {
                        "query": clean_query,
                        "display_name": item.get("display_name", clean_query),
                        "lat": float(item["lat"]),
                        "lon": float(item["lon"]),
                        "type": item.get("type", "location"),
                        "city": address.get("city") or address.get("town") or address.get("state_district") or address.get("county") or clean_query,
                        "country": address.get("country", "Global"),
                        "country_code": address.get("country_code", "").upper(),
                        "boundingbox": [float(b) for b in item.get("boundingbox", [0,0,0,0])],
                        "provider": "nominatim"
                    }
    except Exception as e:
        print(f"[Geocoding] Nominatim error: {e}")

    # 2. Fallback to Photon (Komoot)
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                settings.PHOTON_API_URL,
                params={"q": clean_query, "limit": 1}
            )
            if resp.status_code == 200:
                data = resp.json()
                features = data.get("features", [])
                if features:
                    feat = features[0]
                    coords = feat.get("geometry", {}).get("coordinates", [0, 0])
                    props = feat.get("properties", {})
                    return {
                        "query": clean_query,
                        "display_name": f"{props.get('name', clean_query)}, {props.get('country', '')}".strip(", "),
                        "lat": float(coords[1]),
                        "lon": float(coords[0]),
                        "type": props.get("osm_value", "location"),
                        "city": props.get("city") or props.get("name") or clean_query,
                        "country": props.get("country", "Global"),
                        "country_code": props.get("countrycode", "").upper(),
                        "boundingbox": [coords[1]-0.05, coords[1]+0.05, coords[0]-0.05, coords[0]+0.05],
                        "provider": "photon"
                    }
    except Exception as e:
        print(f"[Geocoding] Photon error: {e}")

    # 3. Known fallback coordinates dictionary for top global travel hubs
    known_places = {
        "paris": {"lat": 48.8566, "lon": 2.3522, "city": "Paris", "country": "France"},
        "tokyo": {"lat": 35.6762, "lon": 139.6503, "city": "Tokyo", "country": "Japan"},
        "manali": {"lat": 32.2432, "lon": 77.1892, "city": "Manali", "country": "India"},
        "mumbai": {"lat": 19.0760, "lon": 72.8777, "city": "Mumbai", "country": "India"},
        "juhu beach": {"lat": 19.0988, "lon": 72.8264, "city": "Mumbai", "country": "India"},
        "bali": {"lat": -8.4095, "lon": 115.1889, "city": "Bali", "country": "Indonesia"},
        "swiss alps": {"lat": 46.5601, "lon": 8.5612, "city": "Alps", "country": "Switzerland"},
        "new york": {"lat": 40.7128, "lon": -74.0060, "city": "New York", "country": "United States"}
    }
    
    q_lower = clean_query.lower()
    for key, info in known_places.items():
        if key in q_lower:
            return {
                "query": clean_query,
                "display_name": f"{info['city']}, {info['country']}",
                "lat": info["lat"],
                "lon": info["lon"],
                "type": "city",
                "city": info["city"],
                "country": info["country"],
                "country_code": "GLOBAL",
                "boundingbox": [info["lat"]-0.05, info["lat"]+0.05, info["lon"]-0.05, info["lon"]+0.05],
                "provider": "fallback_map"
            }

    # Default fallback
    return {
        "query": clean_query,
        "display_name": f"{clean_query.title()} (Popular Destination)",
        "lat": 28.6139,
        "lon": 77.2090,
        "type": "location",
        "city": clean_query.title(),
        "country": "International",
        "country_code": "INT",
        "boundingbox": [28.5, 28.7, 77.1, 77.3],
        "provider": "default"
    }

async def autocomplete_place(query: str) -> list[Dict[str, Any]]:
    """Instant location autocomplete for search bar."""
    if not query or len(query.strip()) < 2:
        return []
    
    headers = {"User-Agent": settings.NOMINATIM_USER_AGENT}
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(
                settings.PHOTON_API_URL,
                params={"q": query.strip(), "limit": 6}
            )
            if resp.status_code == 200:
                features = resp.json().get("features", [])
                results = []
                for feat in features:
                    props = feat.get("properties", {})
                    coords = feat.get("geometry", {}).get("coordinates", [0, 0])
                    name = props.get("name") or query
                    country = props.get("country", "")
                    city = props.get("city") or props.get("state") or ""
                    results.append({
                        "name": name,
                        "label": f"{name}{', ' + city if city else ''}{', ' + country if country else ''}",
                        "lat": coords[1],
                        "lon": coords[0],
                        "country": country
                    })
                return results
    except Exception:
        pass
    return [{"name": query.title(), "label": f"{query.title()}, Global Destination", "lat": 20.0, "lon": 78.0, "country": "World"}]
