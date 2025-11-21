# CLAUDE.md

## Project Overview

**weave-bot-orb** - Event discovery system for Oakland Review of Books (ORB).

Two components:
1. **agent/** - Event scraping API (Playwright + Gemini LLM)
2. **discord/** - Discord bot for event display (planned)

## Quick Start

```bash
# Start the agent API
cd ~/Symbols/Codes/weave-bot-orb
./agent/run.sh

# Or manually:
PYTHONPATH=$(pwd) python3 agent/main.py

# Test
curl http://localhost:8000/api/v1/health
curl -X POST "http://localhost:8000/api/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://lu.ma/example-event"}'
```

## Project Structure

```
weave-bot-orb/
├── agent/                      # Event scraping API
│   ├── main.py                 # FastAPI entry point
│   ├── run.sh                  # Start script
│   ├── api/routes.py           # Endpoints: /scrape, /health
│   ├── core/
│   │   ├── config.py           # Settings from .env
│   │   └── schemas.py          # Pydantic models
│   ├── scraper/
│   │   ├── browser.py          # Playwright (fault-tolerant)
│   │   ├── processor.py        # JSON-LD + trafilatura extraction
│   │   └── orchestrator.py     # Pipeline + date override
│   └── llm/
│       ├── base.py             # Abstract interface
│       └── gemini.py           # Gemini 2.5 Flash Lite
├── discord/                    # Discord bot (planned)
└── CLAUDE.md                   # This file
```

---

## Agent Component

### Architecture

```
URL → Browser (Playwright) → Processor (JSON-LD + Markdown) → LLM (Gemini) → Date Override → Response
```

Key features:
- **JSON-LD date override**: Extracts dates programmatically, overrides LLM output (fixes year hallucination)
- **Screenshot by default**: Vision helps with Instagram/image-heavy pages (~$0.00015/request)
- **Fault-tolerant**: Continues extraction even on page timeout
- **Retry logic**: Exponential backoff on 429 errors

### Configuration

**agent/.env:**
```
GEMINI_API_KEY=your_key_here
HEADLESS=true
BROWSER_TIMEOUT=30000
```

### API Endpoints

- `POST /api/v1/scrape` - Scrape event from URL
- `GET /api/v1/health` - Health check
- `GET /docs` - Swagger UI

### Response Format

```json
{
  "success": true,
  "event": {
    "title": "Event Name",
    "start_datetime": "2025-11-20T18:30:00",
    "location": {"venue": "...", "address": "..."},
    "confidence_score": 0.85
  }
}
```

### Tested Platforms

| Platform | Status | Notes |
|----------|--------|-------|
| Eventbrite | 0.95 | Excellent |
| Luma | 0.90 | JSON-LD override critical |
| BAMPFA | 0.90 | Works |
| UCB Events | 0.95 | Works |
| Instagram | 0.85 | Needs screenshot |
| Meetup | Auth wall | Requires login |

### Key Files for Debugging

1. **`agent/llm/gemini.py`** - LLM prompt, retry logic
2. **`agent/scraper/processor.py`** - JSON-LD extraction
3. **`agent/scraper/orchestrator.py`** - Date override logic
4. **`agent/core/schemas.py`** - Data models

---

## Discord Component (Planned)

Will consume the agent API to:
- Accept event URLs from users
- Display formatted event embeds
- Post to Grist database

---

## Common Issues

### Agent Issues

**429 quota error**: Wait 1-2 min or disable screenshots

**Wrong dates**: Check JSON-LD override in orchestrator.py

**Import errors**: Run from weave-bot-orb root with `PYTHONPATH=$(pwd)`

**Browser timeout**: Increase `BROWSER_TIMEOUT` in .env

---

## Development

### Adding to Agent

The agent uses modular design. To add features:
- New LLM provider: Extend `agent/llm/base.py`
- New scraping logic: Modify `agent/scraper/processor.py`
- New endpoints: Add to `agent/api/routes.py`

### Future Integration

- **Grist**: Auto-insert events to database
- **Discord**: Webhook for bot to call agent API
- **Batch scraping**: Multiple URLs in one request
