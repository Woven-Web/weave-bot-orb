"""FastAPI route definitions."""
from fastapi import APIRouter, HTTPException
from agent.core.schemas import (
    ScrapeRequest,
    ScrapeResponse,
    ParseRequest,
    ParseResponse
)
from agent.core.tasks import task_runner, ParseTask
from agent.scraper.orchestrator import ScrapingOrchestrator

router = APIRouter()


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_event(request: ScrapeRequest) -> ScrapeResponse:
    """
    Scrape event information from a URL.

    This endpoint:
    1. Fetches the webpage using browser automation
    2. Extracts and cleans the content
    3. Uses an LLM to extract structured event data
    4. Returns the event information in a standardized format

    Args:
        request: ScrapeRequest containing URL and options

    Returns:
        ScrapeResponse with extracted event data or error information
    """
    orchestrator = ScrapingOrchestrator()

    try:
        response = await orchestrator.scrape_event(
            url=str(request.url),
            wait_time=request.wait_time,
            include_screenshot=request.include_screenshot
        )
        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/parse", response_model=ParseResponse)
async def parse_event(request: ParseRequest) -> ParseResponse:
    """
    Async parse event from URL.

    Unlike /scrape, this endpoint:
    1. Returns immediately with a request_id
    2. Processes the URL in the background
    3. POSTs results to callback_url when complete

    This is designed for Discord bot integration where we need
    to respond quickly and update the user later.

    Args:
        request: ParseRequest with URL and callback_url

    Returns:
        ParseResponse with request_id for tracking
    """
    # Create response with generated request_id
    response = ParseResponse()

    # Submit background task
    task = ParseTask(
        request_id=response.request_id,
        url=str(request.url),
        callback_url=str(request.callback_url),
        discord_message_id=request.discord_message_id,
        include_screenshot=request.include_screenshot,
        wait_time=request.wait_time
    )

    task_runner.submit(task)

    return response


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Simple status message including active task count
    """
    return {
        "status": "healthy",
        "service": "event-scraper",
        "version": "0.1.0",
        "active_tasks": task_runner.get_active_count()
    }
