"""FastAPI route definitions."""
from fastapi import APIRouter, HTTPException
from agent.core.schemas import ScrapeRequest, ScrapeResponse
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


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Simple status message
    """
    return {
        "status": "healthy",
        "service": "event-scraper",
        "version": "0.1.0"
    }
