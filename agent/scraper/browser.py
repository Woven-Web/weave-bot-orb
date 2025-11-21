"""Browser automation using Playwright."""
import asyncio
import base64
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
from agent.core.config import settings


class BrowserManager:
    """Manages browser automation for web scraping."""

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None

    async def __aenter__(self):
        """Start browser context."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=settings.headless
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close browser context."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def scrape_page(
        self,
        url: str,
        wait_time: int = 3000,
        include_screenshot: bool = True
    ) -> Dict[str, Any]:
        """
        Scrape a webpage and extract content.

        Args:
            url: The URL to scrape
            wait_time: Time to wait for page load in milliseconds
            include_screenshot: Whether to capture a screenshot

        Returns:
            Dictionary containing HTML, text, screenshot, and metadata
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized. Use async context manager.")

        page = await self.browser.new_page()

        partial_load = False
        try:
            # Navigate to URL - use longer timeout, be fault-tolerant
            await page.goto(url, wait_until="networkidle", timeout=settings.browser_timeout)
        except PlaywrightTimeout:
            # Timeout is OK - continue with partial content (fault-tolerant approach)
            partial_load = True
        except Exception as e:
            # For other navigation errors, still try to extract what we can
            partial_load = True

        try:
            # Wait additional time for dynamic content
            await asyncio.sleep(wait_time / 1000)

            # Extract content - this works even on partial loads
            html_content = await page.content()
            text_content = await page.evaluate("() => document.body.innerText || ''")

            # Get page title
            title = await page.title()

            # Capture screenshot if requested
            screenshot_b64 = None
            if include_screenshot and settings.screenshot_enabled:
                try:
                    screenshot_bytes = await page.screenshot(full_page=True, type="png")
                    screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                except Exception:
                    pass  # Screenshot failed, continue without it

            # Consider it a success if we got any content
            has_content = bool(html_content and len(html_content) > 500)

            result = {
                "success": has_content,
                "url": url,
                "title": title,
                "html": html_content,
                "text": text_content,
                "screenshot": screenshot_b64,
                "error": "Partial page load (timeout)" if partial_load else None,
                "partial": partial_load
            }

        except PlaywrightTimeout as e:
            result = {
                "success": False,
                "url": url,
                "title": None,
                "html": None,
                "text": None,
                "screenshot": None,
                "error": f"Timeout loading page: {str(e)}"
            }

        except Exception as e:
            result = {
                "success": False,
                "url": url,
                "title": None,
                "html": None,
                "text": None,
                "screenshot": None,
                "error": f"Error scraping page: {str(e)}"
            }

        finally:
            await page.close()

        return result
