"""
Intent Detection and Entity Extraction Router for TravelGuard AI.

Parses normalized travel queries into structured intents, origins,
destinations, timeframes, and maps them to the minimal necessary toolset.
Supports multi-step requests, spatial nearby attraction searches, mode comparisons,
and explicit user location confirmation.
"""

import re
from typing import Dict, Any, List, Optional, Tuple

KNOWN_CITIES = [
    "matheran", "nashik", "nasik", "mumbai", "pune", "lonavala", "khandala",
    "manali", "shimla", "dharamshala", "delhi", "new delhi", "goa",
    "jaipur", "udaipur", "agra", "varanasi", "rishikesh", "kerala",
    "munnar", "ooty", "bengaluru", "bangalore", "kolkata", "chennai",
    "hyderabad", "amritsar", "srinagar", "leh", "ladakh", "darjeeling",
    "paris", "tokyo", "kyoto", "bali", "swiss alps", "alps", "new york",
    "london", "dubai", "rome", "barcelona", "amsterdam", "singapore",
    "bangkok", "phuket", "maldives", "sydney", "cairo", "istanbul",
    "statue of liberty", "juhu beach", "marine drive", "neral"
]

def clean_place_name(text: str) -> str:
    """Cleans up auxiliary words from extracted place strings."""
    t = text.strip()
    # Remove leading/trailing prepositions or punctuation
    t = re.sub(r"^(?:to|from|in|at|near|around|for|by)\s+", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+(?:to|from|by|in|considering|now|today|tomorrow|\?)+$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"[?!.,;]+", "", t)
    return t.strip().title()

def extract_origin_destination(query: str, default_destination: str = "", default_origin: str = "") -> Tuple[str, str]:
    """
    Extracts origin and destination from route and travel queries like:
    - 'nashik to matheran'
    - 'from nashik to matheran'
    - 'how can i go to matheran from nashik'
    - 'route between nashik and matheran'
    - 'how to reach matheran from nashik'
    """
    q_lower = query.lower()
    origin = ""
    destination = ""

    # Pattern 1: from <origin> to <destination>
    m1 = re.search(r"\bfrom\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:\s+(?:by|with|considering|in|on|\?|$)|$)", q_lower)
    if m1:
        origin = clean_place_name(m1.group(1))
        destination = clean_place_name(m1.group(2))
        if origin and destination:
            return origin, destination

    # Pattern 2: <origin> to <destination> (e.g. "Nashik to Matheran")
    m2 = re.search(r"\b([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\s+to\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)(?:\s+(?:by|with|considering|in|on|\?|$)|$)", q_lower)
    if m2:
        cand_orig = clean_place_name(m2.group(1))
        cand_dest = clean_place_name(m2.group(2))
        # Exclude stop words
        if cand_orig.lower() not in ["how", "want", "like", "need", "go", "way", "best", "road", "train", "bus"] and cand_dest.lower() not in ["go", "reach", "visit"]:
            return cand_orig, cand_dest

    # Pattern 3: to <destination> from <origin>
    m3 = re.search(r"\b(?:go\s+to|reach|visit|travel\s+to)\s+([a-zA-Z\s]+?)\s+from\s+([a-zA-Z\s]+?)(?:\s+(?:by|with|considering|\?|$)|$)", q_lower)
    if m3:
        destination = clean_place_name(m3.group(1))
        origin = clean_place_name(m3.group(2))
        if destination and origin:
            return origin, destination

    # Pattern 4: <destination> from <origin>
    m4 = re.search(r"\b([a-zA-Z\s]+?)\s+from\s+([a-zA-Z\s]+?)(?:\s+(?:by|with|\?|$)|$)", q_lower)
    if m4:
        cand_dest = clean_place_name(m4.group(1).replace("how can i go to", "").replace("how to go to", "").replace("how to reach", ""))
        cand_orig = clean_place_name(m4.group(2))
        if cand_dest and cand_orig and cand_dest.lower() not in ["where", "what", "which", "distance"]:
            return cand_orig, cand_dest

    # Pattern 5: match known cities in the query
    found_cities = []
    for city in sorted(KNOWN_CITIES, key=len, reverse=True):
        if re.search(r"\b" + re.escape(city) + r"\b", q_lower):
            found_cities.append(city.title())

    if len(found_cities) >= 2:
        idx0 = q_lower.find(found_cities[0].lower())
        idx1 = q_lower.find(found_cities[1].lower())
        if idx0 < idx1:
            origin, destination = found_cities[0], found_cities[1]
        else:
            origin, destination = found_cities[1], found_cities[0]
        return origin, destination
    elif len(found_cities) == 1:
        destination = found_cities[0]

    if not destination and default_destination:
        destination = default_destination.title()
    if not origin and default_origin:
        origin = default_origin.title()

    return origin, destination

def detect_intent(
    query: str,
    context_destination: Optional[str] = None,
    context_origin: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes normalized query and determines:
    - intent: 'route' | 'mode_comparison' | 'nearby_places' | 'places' | 'weather' | 'safety_disaster' | 'news_search' | 'itinerary' | 'multi_step' | 'general'
    - entities: origin, destination, category, timeframe, disaster_focus, needs_user_location
    - tools_required: minimal necessary toolset (e.g. ['routing', 'weather', 'sar_disaster'])
    """
    q_lower = query.lower()
    default_dest = context_destination or ""
    default_orig = context_origin or ""
    origin, destination = extract_origin_destination(query, default_dest, default_orig)

    tools_required = set()
    intents_detected = []

    # 1. Check for NEARBY ATTRACTIONS INTENT ("near me", "near Nashik", "near Mumbai")
    nearby_triggers = ["places near", "tourist places near", "attractions near", "spots near", "places to visit near", "sightseeing near", "near me", "around me"]
    if any(k in q_lower for k in nearby_triggers):
        # Check if user specifically asked "near me" or "around me"
        if "near me" in q_lower or "around me" in q_lower:
            # If we don't have user coordinates or city context
            if not default_orig and not default_dest:
                return {
                    "intent": "nearby_places_ask_location",
                    "needs_user_location": True,
                    "tools_required": [],
                    "message": "Please share your current city or location so I can calculate and rank the nearest tourist spots by exact distance."
                }
            starting_loc = default_orig or default_dest
        else:
            # Extract target city after "near"
            m_near = re.search(r"\bnear\s+([a-zA-Z\s]+?)(?:\s+(?:under|within|in|\?|$)|$)", q_lower)
            starting_loc = clean_place_name(m_near.group(1)) if m_near else destination

        return {
            "intent": "nearby_places",
            "starting_location": starting_loc or destination or "Mumbai",
            "destination": starting_loc or destination or "Mumbai",
            "tools_required": ["nearby_attractions"]
        }

    # 2. Check for TRANSPORT MODE COMPARISON INTENT ("bus or train", "train vs bus", "should i take bus or train")
    mode_comparison_triggers = [
        "bus or train", "train or bus", "bus vs train", "train vs bus",
        "which should i choose bus or train", "which thing i choose bus or train",
        "should i take train or bus", "flight or train", "cab or train", "drive or train"
    ]
    if any(k in q_lower for k in mode_comparison_triggers):
        tools_required.add("routing")
        return {
            "intent": "mode_comparison",
            "origin": origin or "Nashik",
            "destination": destination or "Matheran",
            "modes_to_compare": ["train", "bus"],
            "tools_required": ["routing"]
        }

    # 3. ROUTE / DIRECTIONS INTENT
    route_triggers = [
        "how can i go", "how to go", "how to reach", "best route", "driving direction",
        "drive to", "road to", "distance from", "route from", "go from", "distance between"
    ]
    is_route = any(k in q_lower for k in route_triggers) or (origin and destination and (" to " in q_lower or " from " in q_lower))
    if is_route:
        tools_required.add("routing")
        intents_detected.append("route")

    # 4. SAFETY / SAR / DISASTER INTENT
    disaster_triggers = ["flood", "landslide", "safe", "safety", "danger", "risk", "sar", "radar", "satellite", "heavy rain", "disaster"]
    disaster_focus = []
    if any(k in q_lower for k in disaster_triggers):
        tools_required.add("weather")
        tools_required.add("sar_disaster")
        intents_detected.append("safety_disaster")
        if "flood" in q_lower: disaster_focus.append("flood")
        if "landslide" in q_lower: disaster_focus.append("landslide")
        if "rain" in q_lower or "weather" in q_lower: disaster_focus.append("rain_safety")
        if not disaster_focus: disaster_focus.append("general_safety")

    # 5. WEATHER INTENT
    weather_triggers = ["weather", "rain", "temperature", "forecast", "climate", "humid", "sunny", "pack clothes"]
    if any(k in q_lower for k in weather_triggers):
        tools_required.add("weather")
        intents_detected.append("weather")

    # 6. PLACES / HOTELS / RESTAURANTS / ATTRACTIONS INTENT
    restaurant_triggers = ["food", "restaurant", "restaurants", "eat", "dining", "cuisine", "dishes", "lunch", "dinner", "breakfast", "cafe", "cafes"]
    hotel_triggers = ["hotel", "hotels", "stay", "resort", "resorts", "accommodation", "room", "rooms"]
    attraction_triggers = ["tourist spot", "tourist spots", "spot", "spots", "attraction", "attractions", "places to visit", "popular places", "sightseeing", "viewpoint", "viewpoints", "things to do"]
    
    category = "general"
    if any(k in q_lower for k in restaurant_triggers):
        category = "restaurant"
        tools_required.add("places")
        intents_detected.append("places")
    elif any(k in q_lower for k in hotel_triggers):
        category = "hotel"
        tools_required.add("places")
        intents_detected.append("places")
    elif any(k in q_lower for k in attraction_triggers):
        category = "attraction"
        tools_required.add("places")
        intents_detected.append("places")

    # 7. NEWS / CURRENT UPDATES / GOOGLE SEARCH INTENT
    news_triggers = ["what happened recently", "recent news", "what happened in", "latest news", "recent updates", "current status", "news about", "railway update", "ropeway"]
    if any(k in q_lower for k in news_triggers):
        tools_required.add("gemini_search")
        intents_detected.append("news_search")

    # 8. ITINERARY INTENT
    itinerary_triggers = ["itinerary", "travel plan", "plan my trip", "tour plan", "schedule"]
    if any(k in q_lower for k in itinerary_triggers):
        tools_required.add("places")
        tools_required.add("weather")
        intents_detected.append("itinerary")

    # Decide primary intent
    if len(intents_detected) > 1:
        primary_intent = "multi_step"
    elif len(intents_detected) == 1:
        primary_intent = intents_detected[0]
    else:
        primary_intent = "general"
        if destination:
            tools_required.add("places")

    return {
        "intent": primary_intent,
        "sub_intents": intents_detected,
        "origin": origin,
        "destination": destination or default_dest or "Matheran",
        "category": category,
        "disaster_focus": disaster_focus,
        "tools_required": list(tools_required)
    }
