# Testing the Discord Bot

This directory contains testing tools for the Weave Discord bot.

## Quick Start

### 1. Start the Discord Bot

In one terminal:

```bash
cd discord
cp .env.example .env
# Edit .env with your Discord token and channel IDs
# Set AGENT_API_URL=http://localhost:8000/parse
uv run python -m src.main
```

The bot will:
- Connect to Discord
- Start webhook server on `http://localhost:3000`

### 2. Start the Mock Agent Server

In another terminal:

```bash
cd discord
uv run python tests/mock_agent.py
```

This starts a mock agent server on `http://localhost:8000` that simulates the real agent API.

### 3. Test in Discord

Post a link in your monitored Discord channel:
```
https://example.com/event
```

The bot will:
1. Reply with "⏳ Parsing event..."
2. Send request to mock agent
3. Mock agent responds immediately with request ID
4. After 2 seconds, mock agent sends callback
5. Bot deletes "Parsing..." message and posts final result

### 4. Manual Callback Testing

Test callbacks directly using the bash script:

```bash
cd discord
./tests/test_callback.sh
```

This script sends:
- ✅ Successful callback with result URL
- ❌ Failed callback
- 🚫 Invalid callback (missing fields)

## Mock Agent Modes

The mock agent supports different testing modes via query parameters:

### Success Mode (Default)
```bash
# Posts link in Discord, mock agent returns success after 2s
curl -X POST http://localhost:8000/parse?mode=success&delay=2 \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "discord_message_id": 123}'
```

### Failure Mode
```bash
# Posts link in Discord, mock agent returns failure after 2s
curl -X POST http://localhost:8000/parse?mode=fail&delay=2 \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "discord_message_id": 123}'
```

### Delayed Mode
```bash
# Simulates longer processing (10 seconds)
curl -X POST http://localhost:8000/parse?mode=delayed&delay=10 \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "discord_message_id": 123}'
```

## Testing the Full Flow

### End-to-End Test

1. **Start both servers** (bot and mock agent)
2. **Post a test link** in Discord: `https://lu.ma/test-event`
3. **Watch the logs** in both terminals
4. **Verify in Discord** that messages appear correctly
5. **Check the database**:

```bash
sqlite3 weave_bot.db "SELECT * FROM parse_requests;"
```

Expected output:
```
id|discord_message_id|discord_response_id|agent_request_id|status|result_url|created_at|updated_at
1|1234567890|1234567891|uuid-here|completed|https://grist.example.com/mock-event-123|2024-...|2024-...
```

### Test Scenarios

#### Scenario 1: Immediate Success
1. Post link in Discord
2. Bot responds "⏳ Parsing event..."
3. After 2 seconds, bot deletes message and posts:
   > All set! I've added your event: https://grist.example.com/mock-event-123

#### Scenario 2: Immediate Failure
1. Change mock agent URL to use `mode=fail`
2. Post link in Discord
3. Bot responds "⏳ Parsing event..."
4. After 2 seconds, bot deletes message and posts:
   > I couldn't parse that link. Could you double-check it's an event link and try again?

#### Scenario 3: Agent Connection Failure
1. Stop the mock agent server
2. Post link in Discord
3. Bot immediately updates message to:
   > Hmm, I'm having trouble connecting right now. Mind trying again in a moment?

## Debugging

### Check Bot Logs
```bash
# Look for these log lines:
# - "Bot logged in as ..."
# - "Monitoring channels: ..."
# - "Processing message ... with link: ..."
# - "Message ... sent to agent with ID ..."
# - "Received callback for request ..."
# - "Completed processing for agent request ..."
```

### Check Mock Agent Logs
```bash
# Look for these log lines:
# - "Mock agent server started on ..."
# - "Received parse request for URL: ..."
# - "Sending callback for ... with status ..."
# - "Callback sent successfully"
```

### Check Database State
```bash
# View all requests
sqlite3 weave_bot.db "SELECT * FROM parse_requests;"

# View only completed requests
sqlite3 weave_bot.db "SELECT * FROM parse_requests WHERE status='completed';"

# View requests from last hour
sqlite3 weave_bot.db "SELECT * FROM parse_requests WHERE created_at > datetime('now', '-1 hour');"

# Clear database (for fresh testing)
rm weave_bot.db
# Bot will recreate it on next run
```

### Common Issues

**Bot not responding to messages:**
- Check `DISCORD_CHANNELS` in `.env` has correct channel IDs
- Verify bot has permissions in the channel
- Ensure MESSAGE_CONTENT intent is enabled

**Mock agent callback fails:**
- Verify bot webhook is running on port 3000
- Check `BOT_CALLBACK_URL` in mock agent
- Look for connection errors in mock agent logs

**Database errors:**
- Delete `weave_bot.db` and restart bot to recreate
- Check file permissions in discord directory

## Manual Testing with curl

### Send a callback directly:
```bash
curl -X POST http://localhost:3000/callback \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "test-123",
    "status": "completed",
    "result_url": "https://grist.example.com/test"
  }'
```

### Check health endpoint:
```bash
curl http://localhost:3000/health
# Should return: {"status":"ok"}
```

### Check home page:
```bash
curl http://localhost:3000/
# Should return: "You found Weave Bot!\nSay hi at https://oaklog.org"
```

## CI/CD Testing

For automated testing in CI/CD, you can use the mock agent programmatically:

```python
import asyncio
from tests.mock_agent import MockAgent

async def test():
    agent = MockAgent(bot_callback_url="http://bot:3000/callback")
    # Run your tests

asyncio.run(test())
```
