from typing import Dict, Any, List

def compute_safety_score(
    weather: Dict[str, Any],
    crowd: Dict[str, Any],
    disaster: Dict[str, Any],
    place_name: str
) -> Dict[str, Any]:
    """
    Computes a composite Travel Safety Score (0-100 scale) by fusing weather severity,
    crowd density index, and SAR flood/landslide risk metrics.
    """
    # Start from baseline 92
    score = 92.0
    deductions = []

    # Weather deduction
    cond = weather.get("condition", "").lower()
    temp = weather.get("temperature", 22)
    if "rain" in cond or "thunder" in cond:
        score -= 15
        deductions.append("Active rain (-15 pts)")
    if temp > 38 or temp < 2:
        score -= 10
        deductions.append("Extreme temperature (-10 pts)")

    # Crowd deduction
    crowd_score = crowd.get("score", 50)
    if crowd_score > 80:
        score -= 12
        deductions.append("High crowd congestion (-12 pts)")

    # Disaster / SAR deduction
    flood_score = disaster.get("flood_risk", {}).get("score", 0)
    landslide_score = disaster.get("landslide_risk", {}).get("score", 0)

    if flood_score > 60:
        score -= 22
        deductions.append("Elevated flood risk (-22 pts)")
    elif flood_score > 40:
        score -= 10
        deductions.append("Moderate flood caution (-10 pts)")

    if landslide_score > 60:
        score -= 25
        deductions.append("High terrain slope risk (-25 pts)")

    # Clamp score to range [15, 99]
    final_score = int(min(99, max(15, round(score))))

    if final_score >= 82:
        badge = "Optimal Safety"
        level_color = "emerald"
        summary = "Destination conditions are highly safe for travel. Regular precautions apply."
    elif final_score >= 60:
        badge = "Moderate Caution"
        level_color = "amber"
        summary = "Destination conditions are generally safe but require weather/crowd awareness."
    else:
        badge = "High Travel Risk"
        level_color = "red"
        summary = "Active weather or safety alerts detected. Re-check weather advisories before traveling."

    return {
        "overall_score": final_score,
        "badge": badge,
        "badge_color": level_color,
        "summary": summary,
        "risk_factors": deductions if deductions else ["No major risk factors detected"],
        "safety_breakdown": {
            "environmental_safety": min(100, max(20, final_score + 5)),
            "crowd_safety": min(100, max(20, 100 - crowd_score)),
            "infrastructure_accessibility": 88,
            "disaster_resilience": min(100, max(20, 100 - max(flood_score, landslide_score)))
        }
    }
