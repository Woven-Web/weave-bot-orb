#!/usr/bin/env python3
"""
Mock agent server for testing the Discord bot.

This simulates the agent API that receives event URLs and returns request IDs.
It can respond immediately with success/failure or simulate delayed processing.
"""
import asyncio
import aiohttp
from aiohttp import web
import logging
import uuid
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockAgent:
    def __init__(self, bot_callback_url: str = "http://localhost:3000/callback"):
        self.app = web.Application()
        self.bot_callback_url = bot_callback_url
        self._setup_routes()

    def _setup_routes(self):
        """Set up mock agent routes."""
        self.app.router.add_post('/parse', self.handle_parse)

    async def handle_parse(self, request: web.Request) -> web.Response:
        """
        Handle parse request from Discord bot.

        Query parameters:
        - mode: 'success' (default), 'fail', or 'delayed'
        - delay: seconds to delay callback (default: 2)
        """
        try:
            data = await request.json()
            url = data.get('url')
            discord_message_id = data.get('discord_message_id')

            logger.info(f'Received parse request for URL: {url}')
            logger.info(f'Discord message ID: {discord_message_id}')

            # Generate unique request ID
            request_id = str(uuid.uuid4())

            # Get mode from query params
            mode = request.query.get('mode', 'success')
            delay = int(request.query.get('delay', '2'))

            logger.info(f'Mode: {mode}, Delay: {delay}s, Request ID: {request_id}')

            # Return request ID immediately
            response_data = {'request_id': request_id}

            # Schedule callback based on mode
            if mode == 'success':
                asyncio.create_task(
                    self._send_callback_delayed(request_id, 'completed', delay)
                )
            elif mode == 'fail':
                asyncio.create_task(
                    self._send_callback_delayed(request_id, 'failed', delay)
                )
            elif mode == 'delayed':
                # Simulate longer processing
                asyncio.create_task(
                    self._send_callback_delayed(request_id, 'completed', delay)
                )

            return web.json_response(response_data)

        except Exception as e:
            logger.error(f'Error handling parse request: {e}')
            return web.json_response({'error': str(e)}, status=500)

    async def _send_callback_delayed(self, request_id: str, status: str, delay: int):
        """Send callback to bot after delay."""
        await asyncio.sleep(delay)

        callback_data = {
            'request_id': request_id,
            'status': status
        }

        if status == 'completed':
            callback_data['result_url'] = 'https://grist.example.com/mock-event-123'

        logger.info(f'Sending callback for {request_id} with status {status}')

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.bot_callback_url,
                    json=callback_data,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        logger.info(f'Callback sent successfully for {request_id}')
                    else:
                        logger.error(
                            f'Callback failed with status {response.status}: '
                            f'{await response.text()}'
                        )
        except Exception as e:
            logger.error(f'Error sending callback: {e}')


async def start_server(host: str = '0.0.0.0', port: int = 8000):
    """Start the mock agent server."""
    agent = MockAgent()
    runner = web.AppRunner(agent.app)
    await runner.setup()

    site = web.TCPSite(runner, host, port)
    await site.start()

    logger.info(f'Mock agent server started on {host}:{port}')
    logger.info('Available modes:')
    logger.info('  - POST /parse?mode=success&delay=2  (default)')
    logger.info('  - POST /parse?mode=fail&delay=2')
    logger.info('  - POST /parse?mode=delayed&delay=10')
    logger.info('')
    logger.info('Press Ctrl+C to stop')

    # Keep server running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info('Shutting down...')
        await runner.cleanup()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    asyncio.run(start_server(port=port))
