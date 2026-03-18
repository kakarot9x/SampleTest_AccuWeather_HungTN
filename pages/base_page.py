import logging
from playwright.sync_api import Page

# Initialize logger
log = logging.getLogger(__name__)


class BasePage:
    """Base class containing common Playwright interactions."""

    def __init__(self, page: Page):
        self.page = page

    def navigate(self, url: str):
        log.info(f"Navigating to {url}")
        # Stop waiting for heavy ads to load. Just wait for the DOM.
        self.page.goto(url, wait_until="domcontentloaded", timeout=30000)

    def click_element(self, selector: str, timeout: int = 15000):
        log.info(f"Clicking element: {selector}")
        self.page.locator(selector).click(timeout=timeout)

    def fill_text(self, selector: str, text: str):
        log.info(f"Filling text '{text}' into {selector}")
        self.page.locator(selector).fill(text)