"""Data schemas for events and API requests/responses."""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, HttpUrl, Field


class EventLocation(BaseModel):
    """Location information for an event."""
    type: Literal["physical", "virtual", "hybrid"] = "physical"
    venue: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    url: Optional[str] = None


class EventOrganizer(BaseModel):
    """Organizer information for an event."""
    name: Optional[str] = None
    contact: Optional[str] = None
    url: Optional[str] = None


class Event(BaseModel):
    """Structured event data extracted from a webpage."""
    title: str = "Unknown Event"  # Default fallback if LLM returns null
    description: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    timezone: Optional[str] = None
    location: Optional[EventLocation] = None
    organizer: Optional[EventOrganizer] = None
    registration_url: Optional[str] = None
    price: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    source_url: str  # The URL we scraped from
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="LLM's confidence in the extraction quality"
    )
    extraction_notes: Optional[str] = Field(
        default=None,
        description="Any issues, warnings, or notes about the extraction"
    )


class ScrapeRequest(BaseModel):
    """Request to scrape an event from a URL."""
    url: HttpUrl
    include_screenshot: bool = True
    wait_time: int = Field(
        default=3000,
        ge=0,
        le=30000,
        description="Time to wait for page load in milliseconds"
    )


class ScrapeResponse(BaseModel):
    """Response from scraping operation."""
    success: bool
    event: Optional[Event] = None
    error: Optional[str] = None
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata about the scraping process"
    )
