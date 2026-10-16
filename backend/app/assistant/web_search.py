"""
Web Search & Live Information Retrieval for TravelGuard AI.

Retrieves up-to-date real-world news, road/railway updates, and attraction status.
Tries Gemini with Google Search tool first; if quota-limited, seamlessly
falls back to Google News RSS and live web headline extraction.
"""

import httpx
import urllib.parse
from xml.etree import ElementTree as ET
from typing import Dict, Any, List
from app.config import settings

async def retrieve_live_web_information(query: str, destination: str = "") -> Dict[str, Any]:
    """
    Retrieves live web information for query.
    Only called when necessary (recent news, updates, live status).
    """
    clean_dest = destination.strip() or "travel"
    search_term = f"{destination} {query}".strip()
    
    # 1. Try Gemini with Google Search grounding tool
    api_key = settings.GEMINI_API_KEY.strip()
    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": f"Search the web and summarize recent news, road/railway updates, and travel events for: {search_term}"}]
                    }
                ],
                "tools": [{"google_search": {}}]
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidate = data.get("candidates", [{}])[0]
                    content_parts = candidate.get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in content_parts if "text" in p)
                    grounding = candidate.get("groundingMetadata", {})
                    sources = []
                    for chunk in grounding.get("groundingChunks", []):
                        web = chunk.get("web", {})
                        if web.get("uri"):
                            sources.append({"title": web.get("title", "Web Source"), "url": web.get("uri")})
                    
                    if text:
                        return {
                            "success": True,
                            "provider": "gemini_google_search",
                            "summary": text,
                            "sources": sources[:5]
                        }
        except Exception as e:
            print(f"[WebSearch] Gemini Search notice (falling back to news RSS): {e}")

    # 2. Fallback to Google News RSS for verified live news headlines
    try:
        encoded_q = urllib.parse.quote_plus(f"{clean_dest} news updates")
        rss_url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-IN&gl=IN&ceid=IN:en"
        
        async with httpx.AsyncClient(timeout=8.0) as client:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            res = await client.get(rss_url, headers=headers)
            if res.status_code == 200:
                root = ET.fromstring(res.text)
                items = root.findall(".//item")[:5]
                articles = []
                for it in items:
                    title_elem = it.find("title")
                    pub_elem = it.find("pubDate")
                    link_elem = it.find("link")
                    title = title_elem.text if title_elem is not None else ""
                    pub = pub_elem.text if pub_elem is not None else ""
                    link = link_elem.text if link_elem is not None else ""
                    if title:
                        articles.append({
                            "title": title,
                            "date": pub[:16] if pub else "Recent",
                            "url": link
                        })
                
                if articles:
                    formatted_summary = f"Recent news headlines for {clean_dest}:\n"
                    for a in articles:
                        formatted_summary += f"- [{a['date']}] {a['title']}\n"
                    return {
                        "success": True,
                        "provider": "google_news_rss",
                        "summary": formatted_summary,
                        "articles": articles
                    }
    except Exception as e:
        print(f"[WebSearch] RSS search fallback notice: {e}")

    # 3. Honest fallback if web search is unreachable
    return {
        "success": False,
        "provider": "none",
        "summary": f"Live web search is currently unreachable for {clean_dest}. Relying on verified system records.",
        "articles": []
    }
