"""Main FastAPI application."""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent.api.routes import router
from agent.core.config import settings

# Configure logging
logging.basicConfig(
    level=settings.log_level.upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Event Scraper API",
    description="Generalized event scraping using browser automation and LLM extraction",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes (no version prefix - keep it simple for now)
app.include_router(router, tags=["scraping"])


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("Starting Event Scraper API")
    logger.info(f"Server will run on {settings.host}:{settings.port}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Shutting down Event Scraper API")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Event Scraper API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "agent.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level
    )
