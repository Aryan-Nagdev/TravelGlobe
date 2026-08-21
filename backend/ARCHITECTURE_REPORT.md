# TravelGuard AI — Architecture Report

## Platform overview

TravelGuard AI is a FastAPI backend that resolves **place names only** (no user coordinates), gathers multi-source travel intelligence, persists results in Supabase, and powers a **hybrid RAG travel assistant**.

```
User (place name or question)
        │
        ├─► Destination Engine ──► Weather / Crowd / Traffic / Tourism / Disaster
        │         │
        │         └─► Supabase (destination_searches)
        │
        └─► Travel Assistant (RAG)
                  │
                  ├─► Retriever (ChromaDB + FastEmbed)
                  ├─► Live tools (Destination + SAR engines)
                  ├─► Context Builder
                  └─► Groq LLM ──► Answer + recommendations + WHY
```

## Architecture decision: Hybrid RAG + LLM (not SLM-only)

| Approach | Verdict |
|----------|---------|
| **SLM only** (small local LLM) | Insufficient for multi-step reasoning across weather, crowd, SAR, and comparisons |
| **RAG only** | Cannot answer “tomorrow” or live flood risk without fresh API data |
| **LLM only** | Hallucinates numbers; needs grounded context |
| **Hybrid RAG + tools + Groq LLM** | **Selected** — retrieves history/KB, calls live APIs, explains reasoning |

**Embeddings:** FastEmbed `BAAI/bge-small-en-v1.5` (local, no API key)  
**Vector DB:** ChromaDB persistent store (`backend/data/chroma`)  
**LLM:** Groq `llama-3.3-70b-versatile` (configured in `.env`)

## Module map

| Path | Role |
|------|------|
| `app/location/` | Nominatim geocoding |
| `app/weather/` | OpenWeather forecasts |
| `app/crowd/` | Crowd prediction model |
| `app/travel/` | OSRM routing & traffic heuristics |
| `app/safety/` | POI search, disaster heuristics |
| `app/sar/` | SAR flood/landslide, Copernicus STAC |
| `app/rag/` | Embeddings, vector store, indexer, retriever |
| `app/assistant/` | Chat, recommendations, context builder |
| `app/services/destination_engine.py` | Unified destination analysis |
| `app/database/` | Supabase repositories + `schema.sql` |

## API surface (`/api/v1`)

### Destination intelligence
- `POST /destination-analysis`
- `POST /weather`, `/crowd`, `/traffic`, `/safety-score`, `/hotels`, `/attractions`

### Travel assistant (RAG)
- `POST /chat`
- `POST /recommendations`
- `POST /travel-report`
- `POST /disaster-alerts`
- `POST /flood-risk`
- `POST /landslide-risk`
- `POST /index-knowledge` — re-index Supabase history into Chroma

### Ops
- `GET /health`, `GET /health/ready`
- `GET /integrations-status`

## Knowledge sources indexed in RAG

1. Static travel safety KB (`data/knowledge/travel_safety.json`)
2. `destination_searches` unified responses (on analysis + re-index)
3. Chat Q/A turns (after each `/chat`)
4. Live context injected at query time (not embedded): current weather, crowd, SAR

## SAR intelligence

| Capability | Implementation |
|------------|----------------|
| Flood risk | Rain + coastal/monsoon heuristics; optional Sentinel-1 catalogue |
| Landslide risk | Terrain keywords + rainfall |
| Terrain change | Flagged for hills; full delta needs CDSE processing |
| Historical satellite | Copernicus STAC search when OAuth configured |
| Disaster alerts | Structured alerts with `why` field |

## Supabase tables

Run `app/database/schema.sql`:

- `place_analyses` — legacy
- `destination_searches` — all destination/module payloads
- `assistant_conversations` — chat sessions

## Configured credentials (from `.env`)

- Supabase, Groq, OpenWeather, Copernicus password
- Nominatim User-Agent, OSRM, Photon (no keys)

## Additional requirements for full functionality

| Item | Env / action | Purpose |
|------|----------------|---------|
| **Supabase schema** | Run `schema.sql` | Persistence + chat log |
| **Copernicus OAuth** | `COPERNICUS_CLIENT_ID`, `COPERNICUS_CLIENT_SECRET` or `COPERNICUS_USERNAME` | Sentinel STAC catalogue & future SAR processing |
| **Complete Supabase anon key** | `SUPABASE_ANON_KEY` | Frontend clients |
| **Mapbox / Google Maps** | `MAPBOX_ACCESS_TOKEN` / `GOOGLE_MAPS_API_KEY` | Real-time traffic (OSRM heuristic today) |
| **Google Popular Times / Foursquare** | API keys | Observed crowd counts (model today) |
| **OpenWeather One Call 3.0** | Paid tier | Official alert feed |
| **Python 3.11** | `py -3.11 -m venv` | Chroma/FastEmbed wheels |
| **First run** | Downloads embedding model ~100MB | FastEmbed cache |

## Run

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\uvicorn main:app --reload --port 8000
```

Example chat:

```json
POST /api/v1/chat
{ "message": "Is Juhu Beach safe tomorrow?" }
```
