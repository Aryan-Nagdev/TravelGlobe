from datetime import datetime
from typing import Dict, Any, List, Optional

def analyze_crowd_density(lat: float, lon: float, place_name: str, weather_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Computes category-specific footfall density levels, peak hours, and recommended quiet windows.
    Takes into account day of week, time of day, local category, and live meteorological weather.
    Clearly distinguishes ESTIMATED status and never claims physical sensor ground-truth.
    """
    name_lower = place_name.lower()
    now = datetime.now()
    current_hour = now.hour
    is_weekend = now.weekday() >= 5

    # Live meteorological weather impact on crowd
    weather_cond = str(weather_data.get("condition", "") if weather_data else "").lower()
    has_heavy_rain = any(k in weather_cond for k in ["heavy rain", "storm", "thunderstorm", "downpour"])
    has_rain = has_heavy_rain or "rain" in weather_cond or "drizzle" in weather_cond


    # 1. Determine attraction category and temporal profile
    if any(k in name_lower for k in ["temple", "mandir", "shrine", "church", "mosque", "cathedral", "gurdwara"]):
        category = "religious"
        base_crowd = 74 if is_weekend else 62
        peak_hours = "6:30 AM - 9:30 AM & 6:00 PM - 8:30 PM (Morning & Evening Puja)"
        best_visiting_window = "1:00 PM - 3:30 PM (Mid-day quiet window)"
        advice = "Footfall surges during morning darshan and evening aarti. Visiting between 1:00 PM and 3:30 PM offers significantly shorter queues."
    
    elif any(k in name_lower for k in ["beach", "sea", "promenade", "marine drive", "waterfront"]):
        category = "beach"
        base_crowd = 82 if is_weekend else 68
        peak_hours = "4:30 PM - 7:30 PM (Golden hour & sunset)"
        best_visiting_window = "6:00 AM - 8:30 AM (Morning breeze & sunrise)"
        advice = "High visitor influx around sunset. Early morning is ideal for quiet jogging, photography, and peaceful strolls."

    elif any(k in name_lower for k in ["point", "viewpoint", "lake", "waterfall", "valley", "trek", "cliff", "hill", "peak"]):
        category = "nature"
        base_crowd = 65 if is_weekend else 48
        peak_hours = "5:00 PM - 6:45 PM (Sunset rush)"
        best_visiting_window = "7:00 AM - 10:00 AM (Crisp morning visibility)"
        advice = "Cliff-edge viewpoints get crowded towards sunset. Morning treks offer crisp Sahyadri panoramic visibility without crowd congestion."

    elif any(k in name_lower for k in ["market", "bazar", "bazaar", "mall", "street", "shopping", "square"]):
        category = "market"
        base_crowd = 78 if is_weekend else 64
        peak_hours = "5:30 PM - 9:30 PM (Evening shopping)"
        best_visiting_window = "10:30 AM - 1:00 PM (Opening hours)"
        advice = "Evening brings heavy local and tourist footfall. Morning visits ensure relaxed shopping with attentive store staff."

    elif any(k in name_lower for k in ["museum", "fort", "palace", "monument", "caves", "heritage"]):
        category = "monument"
        base_crowd = 58 if is_weekend else 44
        peak_hours = "11:30 AM - 3:30 PM"
        best_visiting_window = "9:00 AM - 10:30 AM (Opening slot)"
        advice = "Arrive right at ticket counter opening to explore halls and viewpoints before tour buses arrive."

    else:
        category = "general"
        base_crowd = 54 if is_weekend else 42
        peak_hours = "12:00 PM - 3:00 PM & 6:00 PM - 8:00 PM"
        best_visiting_window = "8:30 AM - 10:30 AM"
        advice = "Moderate overall flow. Morning hours typically offer calm access to primary sights."

    # 2. Compute dynamic 24-hour curve based on category
    hourly_levels: List[Dict[str, Any]] = []
    for hour in range(24):
        if 0 <= hour < 5:
            multiplier = 0.08
        elif 5 <= hour < 8:
            multiplier = 0.55 if category in ["nature", "religious", "beach"] else 0.25
        elif 8 <= hour < 11:
            multiplier = 0.65
        elif 11 <= hour < 14:
            multiplier = 0.85 if category in ["monument", "general"] else 0.45
        elif 14 <= hour < 17:
            multiplier = 0.50 if category == "religious" else 0.70
        elif 17 <= hour < 21:
            multiplier = 1.18 if category in ["beach", "nature", "market", "religious"] else 0.90
        else:
            multiplier = 0.28
        
        level = min(99, max(5, int(base_crowd * multiplier)))
        hourly_levels.append({
            "hour": f"{hour:02d}:00",
            "level": level,
            "status": "Low" if level < 35 else ("Moderate" if level < 70 else "High")
        })

    # Current level with meteorological weather adjustment
    current_density = hourly_levels[current_hour]["level"]
    if has_heavy_rain:
        current_density = max(1, int(current_density * 0.40))
        advice = f"🌧️ Torrential rain sharply reduces visitor footfall. {advice}"
    elif has_rain:
        current_density = max(2, int(current_density * 0.75))
        advice = f"🌦️ Rainy conditions reduce outdoor congregation. {advice}"

    if current_density >= 75:
        density_status = "High Footfall / Peak"
        badge_color = "red"
    elif current_density >= 45:
        density_status = "Moderate Flow"
        badge_color = "amber"
    else:
        density_status = "Quiet / Low Footfall"
        badge_color = "emerald"

    return {
        "score": current_density,
        "status": density_status,
        "badge_color": badge_color,
        "peak_hours": peak_hours,
        "best_visiting_window": best_visiting_window,
        "hourly_density": hourly_levels,
        "recommendation": advice,
        "category": category,
        "source_type": "ESTIMATED",
        "is_live_sensor": False,
        "data_label": f"ESTIMATED: {category.title()} diurnal curve combined with day-of-week and weather conditions"
    }

