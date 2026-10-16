import httpx
from typing import Dict, Any, List, Optional
from app.config import settings

# In-memory query caches for speed
_GEO_CACHE: Dict[str, Dict[str, Any]] = {}
_AUTOCOMPLETE_CACHE: Dict[str, List[Dict[str, Any]]] = {}

# Rich curated database of top global & Indian travel hubs
KNOWN_DESTINATIONS: Dict[str, Dict[str, Any]] = {
    # India
    "manali": {"lat": 32.2432, "lon": 77.1892, "city": "Manali", "country": "India", "country_code": "IN"},
    "shimla": {"lat": 31.1048, "lon": 77.1734, "city": "Shimla", "country": "India", "country_code": "IN"},
    "dharamshala": {"lat": 32.2190, "lon": 76.3234, "city": "Dharamshala", "country": "India", "country_code": "IN"},
    "mumbai": {"lat": 19.0760, "lon": 72.8777, "city": "Mumbai", "country": "India", "country_code": "IN"},
    "juhu": {"lat": 19.0988, "lon": 72.8264, "city": "Juhu", "parent_city": "Mumbai", "country": "India", "country_code": "IN"},
    "juhu beach": {"lat": 19.0988, "lon": 72.8264, "city": "Juhu Beach", "parent_city": "Mumbai", "country": "India", "country_code": "IN"},
    "goa": {"lat": 15.2993, "lon": 74.1240, "city": "Goa", "country": "India", "country_code": "IN"},
    "delhi": {"lat": 28.6139, "lon": 77.2090, "city": "Delhi", "country": "India", "country_code": "IN"},
    "new delhi": {"lat": 28.6139, "lon": 77.2090, "city": "New Delhi", "country": "India", "country_code": "IN"},
    "jaipur": {"lat": 26.9124, "lon": 75.7873, "city": "Jaipur", "country": "India", "country_code": "IN"},
    "udaipur": {"lat": 24.5854, "lon": 73.7125, "city": "Udaipur", "country": "India", "country_code": "IN"},
    "agra": {"lat": 27.1767, "lon": 78.0081, "city": "Agra", "country": "India", "country_code": "IN"},
    "varanasi": {"lat": 25.3176, "lon": 82.9739, "city": "Varanasi", "country": "India", "country_code": "IN"},
    "rishikesh": {"lat": 30.0869, "lon": 78.2676, "city": "Rishikesh", "country": "India", "country_code": "IN"},
    "kerala": {"lat": 9.9312, "lon": 76.2673, "city": "Kochi", "country": "India", "country_code": "IN"},
    "munnar": {"lat": 10.0889, "lon": 77.0595, "city": "Munnar", "country": "India", "country_code": "IN"},
    "ooty": {"lat": 11.4102, "lon": 76.6950, "city": "Ooty", "country": "India", "country_code": "IN"},
    "bengaluru": {"lat": 12.9716, "lon": 77.5946, "city": "Bengaluru", "country": "India", "country_code": "IN"},
    "bangalore": {"lat": 12.9716, "lon": 77.5946, "city": "Bengaluru", "country": "India", "country_code": "IN"},
    "kolkata": {"lat": 22.5726, "lon": 88.3639, "city": "Kolkata", "country": "India", "country_code": "IN"},
    "chennai": {"lat": 13.0827, "lon": 80.2707, "city": "Chennai", "country": "India", "country_code": "IN"},
    "hyderabad": {"lat": 17.3850, "lon": 78.4867, "city": "Hyderabad", "country": "India", "country_code": "IN"},
    "amritsar": {"lat": 31.6340, "lon": 74.8723, "city": "Amritsar", "country": "India", "country_code": "IN"},
    "srinagar": {"lat": 34.0837, "lon": 74.7973, "city": "Srinagar", "country": "India", "country_code": "IN"},
    "leh": {"lat": 34.1526, "lon": 77.5771, "city": "Leh", "country": "India", "country_code": "IN"},
    "ladakh": {"lat": 34.1526, "lon": 77.5771, "city": "Leh", "country": "India", "country_code": "IN"},
    "darjeeling": {"lat": 27.0410, "lon": 88.2663, "city": "Darjeeling", "country": "India", "country_code": "IN"},
    "nashik": {"lat": 19.9975, "lon": 73.7898, "city": "Nashik", "country": "India", "country_code": "IN"},
    "nasik": {"lat": 19.9975, "lon": 73.7898, "city": "Nashik", "country": "India", "country_code": "IN"},
    "matheran": {"lat": 18.9868, "lon": 73.2682, "city": "Matheran", "country": "India", "country_code": "IN"},
    "pune": {"lat": 18.5204, "lon": 73.8567, "city": "Pune", "country": "India", "country_code": "IN"},
    "lonavala": {"lat": 18.7557, "lon": 73.4091, "city": "Lonavala", "country": "India", "country_code": "IN"},
    "khandala": {"lat": 18.7610, "lon": 73.3762, "city": "Khandala", "country": "India", "country_code": "IN"},
    "neral": {"lat": 19.0274, "lon": 73.3188, "city": "Neral", "country": "India", "country_code": "IN"},
    "statue of liberty": {"lat": 40.6892, "lon": -74.0445, "city": "New York", "country": "United States", "country_code": "US"},

    # International
    "paris": {"lat": 48.8566, "lon": 2.3522, "city": "Paris", "country": "France", "country_code": "FR"},
    "tokyo": {"lat": 35.6762, "lon": 139.6503, "city": "Tokyo", "country": "Japan", "country_code": "JP"},
    "kyoto": {"lat": 35.0116, "lon": 135.7681, "city": "Kyoto", "country": "Japan", "country_code": "JP"},
    "bali": {"lat": -8.4095, "lon": 115.1889, "city": "Bali", "country": "Indonesia", "country_code": "ID"},
    "swiss alps": {"lat": 46.5601, "lon": 8.5612, "city": "Alps", "country": "Switzerland", "country_code": "CH"},
    "alps": {"lat": 46.5601, "lon": 8.5612, "city": "Alps", "country": "Switzerland", "country_code": "CH"},
    "new york": {"lat": 40.7128, "lon": -74.0060, "city": "New York", "country": "United States", "country_code": "US"},
    "london": {"lat": 51.5074, "lon": -0.1278, "city": "London", "country": "United Kingdom", "country_code": "GB"},
    "dubai": {"lat": 25.2048, "lon": 55.2708, "city": "Dubai", "country": "United Arab Emirates", "country_code": "AE"},
    "rome": {"lat": 41.9028, "lon": 12.4964, "city": "Rome", "country": "Italy", "country_code": "IT"},
    "barcelona": {"lat": 41.3879, "lon": 2.1699, "city": "Barcelona", "country": "Spain", "country_code": "ES"},
    "amsterdam": {"lat": 52.3676, "lon": 4.9041, "city": "Amsterdam", "country": "Netherlands", "country_code": "NL"},
    "singapore": {"lat": 1.3521, "lon": 103.8198, "city": "Singapore", "country": "Singapore", "country_code": "SG"},
    "bangkok": {"lat": 13.7563, "lon": 100.5018, "city": "Bangkok", "country": "Thailand", "country_code": "TH"},
    "phuket": {"lat": 7.8804, "lon": 98.3923, "city": "Phuket", "country": "Thailand", "country_code": "TH"},
    "maldives": {"lat": 3.2028, "lon": 73.2207, "city": "Malé", "country": "Maldives", "country_code": "MV"},
    "sydney": {"lat": -33.8688, "lon": 151.2093, "city": "Sydney", "country": "Australia", "country_code": "AU"},
    "cairo": {"lat": 30.0444, "lon": 31.2357, "city": "Cairo", "country": "Egypt", "country_code": "EG"},
    "istanbul": {"lat": 41.0082, "lon": 28.9784, "city": "Istanbul", "country": "Turkey", "country_code": "TR"},
    "venice": {"lat": 45.4408, "lon": 12.3155, "city": "Venice", "country": "Italy", "country_code": "IT"},
    "vienna": {"lat": 48.2082, "lon": 16.3738, "city": "Vienna", "country": "Austria", "country_code": "AT"},
    "prague": {"lat": 50.0755, "lon": 14.4378, "city": "Prague", "country": "Czech Republic", "country_code": "CZ"},
    "santorini": {"lat": 36.3932, "lon": 25.4615, "city": "Santorini", "country": "Greece", "country_code": "GR"},
    "thailand": {"lat": 13.7563, "lon": 100.5018, "city": "Bangkok", "country": "Thailand", "country_code": "TH"}
}

async def geocode_place(place_name: str) -> Dict[str, Any]:
    """
    Geocodes a place name into latitude, longitude, display name, and country details
    using Nominatim with fallback to Photon (with proper headers) and fast cache/known hubs.
    """
    clean_query = place_name.strip()
    if not clean_query:
        raise ValueError("Place name cannot be empty")

    cache_key = clean_query.lower()
    if cache_key in _GEO_CACHE:
        return _GEO_CACHE[cache_key]

    # 1. Check curated known hubs first for instant, accurate matching
    if cache_key in KNOWN_DESTINATIONS:
        info = KNOWN_DESTINATIONS[cache_key]
        result = {
            "query": clean_query,
            "display_name": f"{info['city']}, {info.get('parent_city') or ''} {info['country']}".strip(),
            "lat": info["lat"],
            "lon": info["lon"],
            "type": "destination",
            "city": info["city"],
            "parent_city": info.get("parent_city"),
            "country": info["country"],
            "country_code": info["country_code"],
            "boundingbox": [info["lat"]-0.05, info["lat"]+0.05, info["lon"]-0.05, info["lon"]+0.05],
            "provider": "curated_database"
        }
        _GEO_CACHE[cache_key] = result
        return result

    headers = {"User-Agent": settings.NOMINATIM_USER_AGENT or "TravelGuardAI/1.0 (travel@example.com)"}

    # 2. Try Nominatim (OpenStreetMap)
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
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
                    specific_loc = address.get("suburb") or address.get("neighbourhood") or address.get("town") or address.get("village")
                    parent_city = address.get("city") or address.get("state_district") or address.get("county")

                    # If query matches specific local place (e.g. Juhu within Mumbai), keep destination as Juhu
                    if specific_loc and (clean_query.lower() in specific_loc.lower() or specific_loc.lower() in clean_query.lower()):
                        city = specific_loc
                    else:
                        city = address.get("city") or specific_loc or parent_city or clean_query.title()

                    result = {
                        "query": clean_query,
                        "display_name": item.get("display_name", clean_query),
                        "lat": float(item["lat"]),
                        "lon": float(item["lon"]),
                        "type": item.get("type", "location"),
                        "city": city,
                        "parent_city": parent_city if parent_city != city else None,
                        "country": address.get("country", "Global"),
                        "country_code": address.get("country_code", "").upper(),
                        "boundingbox": [float(b) for b in item.get("boundingbox", [0,0,0,0])],
                        "provider": "nominatim"
                    }
                    _GEO_CACHE[cache_key] = result
                    return result
    except Exception as e:
        print(f"[Geocoding] Nominatim lookup notice: {e}")

    # 2. Fallback to Photon (Komoot) — MUST pass User-Agent header to avoid 403
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(
                settings.PHOTON_API_URL,
                params={"q": clean_query, "limit": 1},
                headers=headers
            )
            if resp.status_code == 200:
                data = resp.json()
                features = data.get("features", [])
                if features:
                    feat = features[0]
                    coords = feat.get("geometry", {}).get("coordinates", [0, 0])
                    props = feat.get("properties", {})
                    city = props.get("city") or props.get("name") or clean_query
                    result = {
                        "query": clean_query,
                        "display_name": f"{props.get('name', clean_query)}, {props.get('country', '')}".strip(", "),
                        "lat": float(coords[1]),
                        "lon": float(coords[0]),
                        "type": props.get("osm_value", "location"),
                        "city": city,
                        "country": props.get("country", "Global"),
                        "country_code": props.get("countrycode", "").upper(),
                        "boundingbox": [coords[1]-0.05, coords[1]+0.05, coords[0]-0.05, coords[0]+0.05],
                        "provider": "photon"
                    }
                    _GEO_CACHE[cache_key] = result
                    return result
    except Exception as e:
        print(f"[Geocoding] Photon lookup notice: {e}")

    # 3. Check known destinations dictionary
    for key, info in KNOWN_DESTINATIONS.items():
        if key == cache_key or key in cache_key or cache_key in key:
            result = {
                "query": clean_query,
                "display_name": f"{info['city']}, {info['country']}",
                "lat": info["lat"],
                "lon": info["lon"],
                "type": "city",
                "city": info["city"],
                "country": info["country"],
                "country_code": info.get("country_code", "GLOBAL"),
                "boundingbox": [info["lat"]-0.05, info["lat"]+0.05, info["lon"]-0.05, info["lon"]+0.05],
                "provider": "known_hub"
            }
            _GEO_CACHE[cache_key] = result
            return result

    # 4. Default fallback
    result = {
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
    _GEO_CACHE[cache_key] = result
    return result

async def autocomplete_place(query: str) -> list[Dict[str, Any]]:
    """Instant location autocomplete with Photon API and known hub fast match."""
    if not query or len(query.strip()) < 2:
        return []

    clean_q = query.strip()
    cache_key = clean_q.lower()
    if cache_key in _AUTOCOMPLETE_CACHE:
        return _AUTOCOMPLETE_CACHE[cache_key]

    results: List[Dict[str, Any]] = []

    # First add matching known hubs for immediate responsiveness
    for key, info in KNOWN_DESTINATIONS.items():
        if cache_key in key or key.startswith(cache_key):
            results.append({
                "name": info["city"],
                "label": f"{info['city']}, {info['country']}",
                "lat": info["lat"],
                "lon": info["lon"],
                "country": info["country"]
            })
            if len(results) >= 4:
                break

    # Try Photon with required User-Agent header
    headers = {"User-Agent": settings.NOMINATIM_USER_AGENT or "TravelGuardAI/1.0 (travel@example.com)"}
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                settings.PHOTON_API_URL,
                params={"q": clean_q, "limit": 6},
                headers=headers
            )
            if resp.status_code == 200:
                features = resp.json().get("features", [])
                for feat in features:
                    props = feat.get("properties", {})
                    coords = feat.get("geometry", {}).get("coordinates", [0, 0])
                    name = props.get("name") or clean_q
                    country = props.get("country", "")
                    city = props.get("city") or props.get("state") or ""
                    item_label = f"{name}{', ' + city if city else ''}{', ' + country if country else ''}"
                    
                    # Avoid duplicate names in suggestion list
                    if not any(r["name"].lower() == name.lower() for r in results):
                        results.append({
                            "name": name,
                            "label": item_label,
                            "lat": coords[1],
                            "lon": coords[0],
                            "country": country
                        })
    except Exception:
        pass

    if not results:
        results = [{
            "name": clean_q.title(),
            "label": f"{clean_q.title()}, Global Destination",
            "lat": 28.6139,
            "lon": 77.2090,
            "country": "World"
        }]

    _AUTOCOMPLETE_CACHE[cache_key] = results[:6]
    return results[:6]
