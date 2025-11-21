#!/bin/bash
# Test script for sending callbacks to the Discord bot webhook

set -e

BOT_URL="${BOT_URL:-http://localhost:3000}"
REQUEST_ID="${1:-test-request-$(date +%s)}"

echo "==================================="
echo "Testing Discord Bot Callbacks"
echo "==================================="
echo "Bot URL: $BOT_URL"
echo "Request ID: $REQUEST_ID"
echo ""

# Test 1: Successful callback
echo "Test 1: Sending SUCCESSFUL callback..."
curl -X POST "$BOT_URL/callback" \
  -H "Content-Type: application/json" \
  -d "{
    \"request_id\": \"$REQUEST_ID\",
    \"status\": \"completed\",
    \"result_url\": \"https://grist.example.com/test-event-123\"
  }" \
  -v
echo -e "\n"

echo "Waiting 3 seconds..."
sleep 3

# Test 2: Failed callback
REQUEST_ID_FAIL="${REQUEST_ID}-fail"
echo "Test 2: Sending FAILED callback..."
curl -X POST "$BOT_URL/callback" \
  -H "Content-Type: application/json" \
  -d "{
    \"request_id\": \"$REQUEST_ID_FAIL\",
    \"status\": \"failed\"
  }" \
  -v
echo -e "\n"

echo "Waiting 3 seconds..."
sleep 3

# Test 3: Invalid callback (missing fields)
echo "Test 3: Sending INVALID callback (should return 400)..."
curl -X POST "$BOT_URL/callback" \
  -H "Content-Type: application/json" \
  -d "{
    \"status\": \"completed\"
  }" \
  -v
echo -e "\n"

echo "==================================="
echo "Testing complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Check your Discord channel for bot responses"
echo "2. Check bot logs for callback processing"
echo "3. Verify SQLite database has been updated"
echo ""
echo "To check the database:"
echo "  sqlite3 weave_bot.db 'SELECT * FROM parse_requests;'"
