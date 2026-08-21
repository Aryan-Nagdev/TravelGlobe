import os
import json
import httpx
from typing import Dict, Any, List, Optional
from groq import Groq
from app.config import settings

def get_groq_client() -> Optional[Groq]:
    """Returns Groq client instance if GROQ_API_KEY is configured."""
    key = settings.GROQ_API_KEY.strip()
    if key and key.startswith("gsk_"):
        try:
            return Groq(api_key=key)
        except Exception as e:
            print(f"[Groq AI] Client init error: {e}")
    return None

async def generate_assistant_response(
    message: str,
    destination_context: Optional[Dict[str, Any]] = None,
    chat_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Generates intelligent travel assistant response using Groq LLM (llama-3.3-70b-versatile).
    Injects real-time weather, safety, crowd, and SAR disaster intelligence into LLM context.
    """
    clean_msg = message.strip()
    client = get_groq_client()

    # System prompt definition
    system_prompt = (
        "You are TravelGuard AI, an elite professional travel intelligence assistant. "
        "Your task is to provide concise, structured, highly helpful, and accurate travel advice, "
        "safety assessments, weather warnings, crowd advice, and customized itineraries.\n\n"
        "Guidance:\n"
        "- Format responses cleanly with Markdown (bullet points, bold key terms, clear sections).\n"
        "- Emphasize traveler safety, peak crowd windows, weather precautions, and local recommendations.\n"
        "- Keep responses professional, warm, encouraging, and actionable."
    )

    context_str = ""
    if destination_context:
        place = destination_context.get("destination", {})
        weather = destination_context.get("weather", {})
        safety = destination_context.get("safety", {})
        crowd = destination_context.get("crowd", {})
        disaster = destination_context.get("sar_disaster", {})

        context_str = f"""
LIVE DESTINATION CONTEXT:
- Destination: {place.get('display_name', 'Requested Location')}
- Safety Score: {safety.get('overall_score', 85)}/100 ({safety.get('badge', 'Safe')})
- Weather: {weather.get('temperature', 22)}°C, {weather.get('condition', 'Clear')} ({weather.get('description', '')}), Humidity: {weather.get('humidity', 50)}%
- Weather Advisory: {weather.get('advisory', 'Normal conditions')}
- Crowd Status: {crowd.get('status', 'Moderate')}, Peak Hours: {crowd.get('peak_hours', 'Evening')}
- Flood Risk: {disaster.get('flood_risk', {}).get('level', 'Low')} (Score: {disaster.get('flood_risk', {}).get('score', 10)})
- Landslide Risk: {disaster.get('landslide_risk', {}).get('level', 'Low')}
        """

    messages_payload = [{"role": "system", "content": system_prompt}]
    if context_str:
        messages_payload.append({"role": "system", "content": context_str})

    if chat_history:
        for turn in chat_history[-4:]: # include recent history
            messages_payload.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})

    messages_payload.append({"role": "user", "content": clean_msg})

    if client:
        try:
            completion = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages_payload,
                temperature=0.7,
                max_tokens=1024
            )
            answer = completion.choices[0].message.content
            return {
                "answer": answer,
                "model": settings.GROQ_MODEL,
                "is_groq_llm": True,
                "context_used": bool(destination_context)
            }
        except Exception as e:
            print(f"[Groq AI] LLM error: {e}")

    # Intelligent Fallback response generator if Groq key is missing or encounters network error
    fallback_text = generate_rule_based_response(clean_msg, destination_context)
    return {
        "answer": fallback_text,
        "model": "TravelGuard Heuristic Engine",
        "is_groq_llm": False,
        "context_used": bool(destination_context)
    }

def generate_rule_based_response(user_msg: str, context: Optional[Dict[str, Any]] = None) -> str:
    msg_lower = user_msg.lower()
    
    dest_name = "your destination"
    weather_desc = "pleasant"
    safety_score = 88
    
    if context:
        dest_name = context.get("destination", {}).get("city", "your destination")
        weather_desc = context.get("weather", {}).get("description", "pleasant weather")
        safety_score = context.get("safety", {}).get("overall_score", 88)

    if "safe" in msg_lower or "safety" in msg_lower:
        return (
            f"### 🛡️ Safety Assessment for {dest_name.title()}\n\n"
            f"- **Travel Safety Index:** **{safety_score}/100**\n"
            f"- **Environmental Status:** Currently experiencing **{weather_desc}**.\n"
            f"- **Advisory:** Overall conditions are safe for tourists. Stay mindful of personal belongings in crowded areas and stay hydrated!"
        )
    elif "itinerary" in msg_lower or "plan" in msg_lower or "days" in msg_lower:
        return (
            f"### 🗺️ Recommended 3-Day Travel Plan for {dest_name.title()}\n\n"
            f"- **Day 1: Arrival & Landmark Exploration**\n"
            f"  - Morning: Check-in to accommodation and visit the central city square.\n"
            f"  - Evening: Scenic promenade sunset stroll and local dining.\n\n"
            f"- **Day 2: Heritage & Outdoor Adventure**\n"
            f"  - Morning: Guided tour of cultural museums and historical monuments.\n"
            f"  - Afternoon: Visit nearby nature parks & botanical gardens.\n\n"
            f"- **Day 3: Local Shopping & Culinary Discovery**\n"
            f"  - Morning: Artisanal markets & souvenir shopping.\n"
            f"  - Afternoon: Relaxing cafe crawl and traditional cuisine tasting."
        )
    elif "weather" in msg_lower or "rain" in msg_lower:
        return (
            f"### 🌤️ Weather Forecast Overview for {dest_name.title()}\n\n"
            f"- **Current Condition:** {weather_desc.title()}\n"
            f"- **Recommendation:** Wear comfortable breathable clothing. Keep lightweight rain gear handy if traveling during monsoon seasons."
        )
    else:
        return (
            f"### 🌐 TravelGuard AI Insights for {dest_name.title()}\n\n"
            f"Welcome to **{dest_name.title()}**! Here are three quick travel tips:\n"
            f"1. **Best Visiting Time:** Early morning hours (8:00 AM - 10:30 AM) offer the lowest crowd levels.\n"
            f"2. **Local Transport:** Ride-hailing cabs and public transit are convenient and widely accessible.\n"
            f"3. **Emergency Support:** Access local emergency contacts in our Alert Portal at any time."
        )
