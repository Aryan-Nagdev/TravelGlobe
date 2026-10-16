"""
Google Gemini & Multi-LLM Client for TravelGuard AI.

Provides resilient inference across Google Gemini (Primary) and Groq (Secondary),
securely utilizing backend environment variables without exposing keys to frontend.
"""

import httpx
from typing import List, Dict, Any, Optional
from groq import Groq
from app.config import settings

def get_groq_client() -> Optional[Groq]:
    """Returns Groq client if key is configured."""
    key = (settings.GROQ_API_KEY or "").strip()
    if key and key.startswith("gsk_") and len(key) > 20:
        try:
            return Groq(api_key=key)
        except Exception as e:
            print(f"[Groq AI] Init notice: {e}")
    return None

async def call_gemini_generate(
    system_instruction: str,
    prompt: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    timeout_secs: float = 25.0
) -> Optional[str]:
    """Calls Google Gemini generateContent REST API."""
    api_key = (settings.GEMINI_API_KEY or "").strip()
    if not api_key:
        return None

    # Prioritize fast, reliable models
    preferred_model = settings.GEMINI_MODEL or "gemini-3.5-flash-lite"
    models_to_try = [preferred_model, "gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.5-flash"]
    models_to_try = list(dict.fromkeys(models_to_try))

    contents = []
    
    # Format chat history
    if chat_history:
        for turn in chat_history[-4:]:
            role = turn.get("role", "user")
            gemini_role = "model" if role in ["assistant", "model"] else "user"
            contents.append({
                "role": gemini_role,
                "parts": [{"text": turn.get("content", "")}]
            })

    # Append current user prompt
    contents.append({
        "role": "user",
        "parts": [{"text": prompt}]
    })

    payload: Dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 1200
        }
    }
    
    if system_instruction:
        payload["system_instruction"] = {
            "parts": [{"text": system_instruction}]
        }

    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        text = "".join(p.get("text", "") for p in parts if "text" in p)
                        if text:
                            return text
                else:
                    print(f"[Gemini AI] {model_name} status {resp.status_code}: {resp.text[:120]}")
        except Exception as e:
            print(f"[Gemini AI] {model_name} notice: {e}")

    return None

async def call_groq_generate(
    system_instruction: str,
    prompt: str,
    chat_history: Optional[List[Dict[str, str]]] = None
) -> Optional[str]:
    """Calls Groq API as secondary LLM fallback."""
    client = get_groq_client()
    if not client:
        return None

    messages: List[Dict[str, str]] = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})

    if chat_history:
        for turn in chat_history[-4:]:
            role = "assistant" if turn.get("role") in ["assistant", "model"] else "user"
            messages.append({"role": role, "content": turn.get("content", "")})

    messages.append({"role": "user", "content": prompt})

    try:
        completion = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            temperature=0.6,
            max_tokens=1200
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"[Groq AI] Completion fallback notice: {e}")
        return None

async def generate_llm_response(
    system_instruction: str,
    prompt: str,
    chat_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Main entry point for LLM inference.
    Executes Gemini -> Groq -> Heuristic fallback with full reliability.
    """
    # 1. Try Gemini
    gemini_resp = await call_gemini_generate(system_instruction, prompt, chat_history)
    if gemini_resp:
        return {
            "answer": gemini_resp,
            "model": settings.GEMINI_MODEL,
            "provider": "Google Gemini",
            "is_llm": True
        }

    # 2. Try Groq
    groq_resp = await call_groq_generate(system_instruction, prompt, chat_history)
    if groq_resp:
        return {
            "answer": groq_resp,
            "model": settings.GROQ_MODEL,
            "provider": "Groq",
            "is_llm": True
        }

    return {
        "answer": None,
        "model": "Fallback",
        "provider": "Local",
        "is_llm": False
    }
