# CLAUDE.md

## Project Overview

**weave-bot-orb** - Event discovery system for Oakland Review of Books (ORB).

Two components:

1. **agent/** - Event scraping API (Playwright + Gemini LLM)
2. **discord/** - Discord bot for event display and submission

## Quick Start

```bash
# Terminal 1: Start the agent API
cd ~/Symbols/Codes/weave-bot-orb
./agent/run.sh

# Terminal 2: Start the Discord bot
cd ~/Symbols/Codes/weave-bot-orb/discord
uv run python src/main.py

# Test agent health
curl http://localhost:8000/health

# Test sync scrape (returns full result)
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://lu.ma/example-event"}'

# Test async parse (returns request_id, sends callback when done)
curl -X POST "http://localhost:8000/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://lu.ma/example-event",
    "callback_url": "http://localhost:3000/callback"
  }'
```

## Project Structure

```
weave-bot-orb/
├── agent/                      # Event scraping API
│   ├── main.py                 # FastAPI entry point
│   ├── run.sh                  # Start script
│   ├── .env                    # GEMINI_API_KEY config
│   ├── api/routes.py           # Endpoints: /scrape, /parse, /health
│   ├── core/
│   │   ├── config.py           # Settings from .env
│   │   ├── schemas.py          # Pydantic models (Event, ParseRequest, etc.)
│   │   ├── callback.py         # Sends results to Discord webhook
│   │   └── tasks.py            # Background task runner
│   ├── scraper/
│   │   ├── browser.py          # Playwright (fault-tolerant)
│   │   ├── processor.py        # JSON-LD + trafilatura extraction
│   │   └── orchestrator.py     # Pipeline + date override
│   └── llm/
│       ├── base.py             # Abstract interface
│       └── gemini.py           # Gemini 2.5 Flash Lite
├── discord/                    # Discord bot
│   ├── src/
│   │   ├── main.py             # Entry point (bot + webhook server)
│   │   ├── bot.py              # WeaveBotClient - message handling
│   │   ├── config.py           # Environment config loader
│   │   ├── database.py         # SQLite request tracking
│   │   ├── webhook.py          # aiohttp callback server (port 3000)
│   │   └── utils.py            # URL extraction utilities
│   ├── tests/
│   │   ├── mock_agent.py       # Mock agent for testing
│   │   └── test_callback.sh    # Callback test script
│   ├── .env                    # Discord token, channel IDs
│   ├── pyproject.toml          # UV dependencies
│   └── railway.toml            # Railway deployment config
└── CLAUDE.md                   # This file
```

---

## Integration Architecture

```
┌─────────────────┐                    ┌─────────────────┐
│  Discord Bot    │                    │  Agent API      │
│  (webhook:3000) │                    │  (api:8000)     │
└────────┬────────┘                    └────────┬────────┘
         │                                      │
    1. User posts link in Discord               │
         │                                      │
    2. POST /parse ────────────────────────────►│
       {url, callback_url, discord_message_id}  │
         │                                      │
    3. Returns immediately ◄────────────────────│
       {"request_id": "uuid", "status": "accepted"}
         │                                      │
         │         4. Background processing     │
         │            - Playwright fetch        │
         │            - LLM extraction          │
         │            - JSON-LD override        │
         │                                      │
    5. POST /callback ◄─────────────────────────│
       {request_id, status, event, result_url}  │
         │                                      │
    6. Update Discord with formatted event      │
         │                                      │
```

---

## Agent Component

### API Endpoints

| Endpoint  | Method | Description                                      |
| --------- | ------ | ------------------------------------------------ |
| `/scrape` | POST   | Sync scrape - returns full result                |
| `/parse`  | POST   | Async parse - returns request_id, sends callback |
| `/health` | GET    | Health check with active task count              |
| `/docs`   | GET    | Swagger UI                                       |

### Async Parse Request

```json
{
  "url": "https://lu.ma/event",
  "callback_url": "http://discord-bot:3000/callback",
  "discord_message_id": 123456789,
  "include_screenshot": true,
  "wait_time": 3000
}
```

### Callback Payload (sent to Discord)

```json
{
  "request_id": "uuid",
  "discord_message_id": 123456789,
  "status": "completed",
  "event": {
    "title": "Event Name",
    "start_datetime": "2025-11-20T18:30:00",
    "location": { "venue": "...", "address": "..." },
    "confidence_score": 0.85
  },
  "result_url": null
}
```

### Configuration

**agent/.env:**

```
GEMINI_API_KEY=your_key_here
HEADLESS=true
BROWSER_TIMEOUT=30000
```

### Key Files

| File                      | Purpose                                         |
| ------------------------- | ----------------------------------------------- |
| `api/routes.py`           | `/scrape` (sync) and `/parse` (async) endpoints |
| `core/tasks.py`           | Background task runner using asyncio            |
| `core/callback.py`        | Sends results to Discord webhook                |
| `core/schemas.py`         | ParseRequest, ParseResponse, CallbackPayload    |
| `scraper/orchestrator.py` | Main scraping pipeline                          |

---

## Discord Component

### Architecture

1. Bot monitors configured channels for links
2. On link detected: replies "Parsing...", sends to Agent
3. Agent returns `request_id` immediately
4. Bot stores request in SQLite (status: IN_PROGRESS)
5. Agent processes in background (2-20 seconds)
6. Agent POSTs callback to Bot's webhook server
7. Bot updates Discord with formatted event details

### Configuration

**discord/.env:**

```
DISCORD_TOKEN=your_bot_token
DISCORD_CHANNELS=channel_id_1,channel_id_2
AGENT_API_URL=http://localhost:8000/parse
WEBHOOK_PORT=3000
WEBHOOK_HOST=0.0.0.0
DB_PATH=weave_bot.db
```

### Key Files

| File              | Purpose                                           |
| ----------------- | ------------------------------------------------- |
| `src/bot.py`      | Message handling, sends to agent, formats replies |
| `src/webhook.py`  | Receives callbacks from agent on port 3000        |
| `src/database.py` | SQLite tracking of parse requests                 |

---

## Tested Platforms

| Platform   | Score | Notes                      |
| ---------- | ----- | -------------------------- |
| Eventbrite | 0.95  | Excellent                  |
| Luma       | 0.90  | JSON-LD override critical  |
| BAMPFA     | 0.90  | Works                      |
| UCB Events | 0.95  | Works                      |
| Instagram  | 0.85  | Needs screenshot           |
| Meetup     | N/A   | Auth wall - requires login |

---

## Common Issues

### Agent Issues

**429 quota error**: Wait 1-2 min or disable screenshots

**Wrong dates**: Check JSON-LD override in `orchestrator.py`

**Import errors**: Run from weave-bot-orb root with `PYTHONPATH=$(pwd)`

**Browser timeout**: Increase `BROWSER_TIMEOUT` in .env

### Discord Issues

**Bot not responding**: Check DISCORD_CHANNELS includes the channel ID

**Database locked**: Ensure only one bot instance running

**Callback not received**: Verify WEBHOOK_PORT is accessible from agent

### Integration Issues

**Callback URL unreachable**: When running locally, both services need to reach each other. Use `localhost` for same machine.

**Request not found**: Check that `discord_message_id` is being passed through correctly.

---

## Future Enhancements

### Grist Integration (Next)

The callback system is designed for Grist integration:

1. Agent successfully parses event
2. Agent saves event to Grist database
3. Agent includes `result_url` (Grist link) in callback
4. Discord shows "Added to database: {result_url}"

Changes needed:

- Add `agent/integrations/grist.py`
- Modify `core/tasks.py` to save to Grist after successful parse
- Discord bot already handles `result_url` in callback

### Other Future Work

- **Batch scraping**: Multiple URLs in one request
- **Event editing**: Allow users to correct parsed data
- **Duplicate detection**: Check if event already exists in Grist
