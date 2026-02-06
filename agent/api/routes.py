"""FastAPI route definitions."""
from fastapi import APIRouter, HTTPException
from agent.core.schemas import (
    ScrapeRequest,
    ScrapeResponse,
    ParseRequest,
    ParseResponse
)
from agent.core.tasks import task_runner, ParseTask
from agent.core.org_config import get_org_config, get_all_org_configs
from agent.llm.factory import create_extractor
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
        request: ScrapeRequest containing URL, org_id, and options

    Returns:
        ScrapeResponse with extracted event data or error information
    """
    try:
        org_config = get_org_config(request.org_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    llm_extractor = create_extractor(org_config)
    orchestrator = ScrapingOrchestrator(llm_extractor=llm_extractor)

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
    Async parse event from URL and/or image.

    Unlike /scrape, this endpoint:
    1. Returns immediately with a request_id
    2. Processes the URL/image in the background
    3. POSTs results to callback_url when complete

    Supports three parse modes:
    - "url": Parse from webpage (requires url)
    - "image": Parse from uploaded image (requires image_base64)
    - "hybrid": Parse from both URL and image together

    Args:
        request: ParseRequest with URL/image, org_id, and callback_url

    Returns:
        ParseResponse with request_id for tracking
    """
    # Validate org_id early
    try:
        get_org_config(request.org_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Validate required fields based on parse_mode
    if request.parse_mode == "url" and not request.url:
        raise HTTPException(
            status_code=400,
            detail="URL is required for 'url' parse mode"
        )
    if request.parse_mode == "image" and not request.image_base64:
        raise HTTPException(
            status_code=400,
            detail="image_base64 is required for 'image' parse mode"
        )
    if request.parse_mode == "hybrid" and (not request.url or not request.image_base64):
        raise HTTPException(
            status_code=400,
            detail="Both URL and image_base64 are required for 'hybrid' parse mode"
        )

    # Create response with generated request_id
    response = ParseResponse()

    # Submit background task
    task = ParseTask(
        request_id=response.request_id,
        url=str(request.url) if request.url else None,
        callback_url=str(request.callback_url),
        client_reference_id=request.client_reference_id,
        org_id=request.org_id,
        parse_mode=request.parse_mode,
        image_base64=request.image_base64,
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
        Status with active task count and configured orgs
    """
    orgs = get_all_org_configs()
    org_info = {
        org_id: {"name": cfg.name, "llm_provider": cfg.llm.provider}
        for org_id, cfg in orgs.items()
    }

    return {
        "status": "healthy",
        "service": "event-scraper",
        "version": "0.2.0",
        "active_tasks": task_runner.get_active_count(),
        "orgs": org_info,
    }
