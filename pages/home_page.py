from pages.base_page import BasePage
import logging

log = logging.getLogger(__name__)

class HomePage(BasePage):
    # Locators
    SEARCH_INPUT = "input.search-input"
    FIRST_RESULT = ".search-bar-result"
    DAILY_MENU = "a[data-qa='daily']"
    COOKIE_BANNER = "div.policy-accept"

    def accept_cookies_if_present(self):
        try:
            self.click_element(self.COOKIE_BANNER, timeout=3000)
            log.info("Cookie banner accepted.")
        except Exception:
            log.warning("No cookie banner found.")

    def search_city(self, city_name: str):
        log.info(f"Typing city: '{city_name}' to trigger AccuWeather API...")
        search_field = self.page.locator(self.SEARCH_INPUT)
        search_field.clear()
        search_field.press_sequentially(city_name, delay=100)

        log.info(f"Waiting for dropdown to show: '{city_name}'...")
        target_result = self.page.locator(self.FIRST_RESULT, has_text=city_name).first
        target_result.wait_for(state="visible", timeout=15000)

        log.info("Dropdown result found! Clicking it...")
        # force=True bypasses any invisible ad overlays intercepting the click
        target_result.click(force=True)

        log.info("Waiting for the new city dashboard to load...")
        self.page.wait_for_load_state("domcontentloaded")

    def go_to_daily_forecast(self):
        log.info("Waiting for the Daily menu button to appear...")
        # Wait for the button to actually be attached to the new page
        self.page.wait_for_selector(self.DAILY_MENU, state="attached", timeout=15000)

        log.info("Clicking Daily forecast menu...")
        # Use force=True just in case a sticky header/ad is floating over it
        self.page.locator(self.DAILY_MENU).click(force=True)