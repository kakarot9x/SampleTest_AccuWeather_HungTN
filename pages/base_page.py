from playwright.sync_api import Page
import logging

class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def navigate(self, url: str):
        logging.info(f"Navigating to {url}")
        self.page.goto(url)

    def click_element(self, selector: str, timeout=15000): # Updated to 15 seconds
        logging.info(f"Clicking element: {selector}")
        self.page.locator(selector).click(timeout=timeout)

    def fill_text(self, selector: str, text: str):
        logging.info(f"Filling text '{text}' into {selector}")
        self.page.locator(selector).fill(text)