from pages.base_page import BasePage
import logging

class HomePage(BasePage):
    # Locators
    SEARCH_INPUT = "input.search-input"
    FIRST_RESULT = ".search-bar-result"
    DAILY_MENU = "a[data-qa='daily']"
    COOKIE_BANNER = "div.policy-accept"

    def accept_cookies_if_present(self):
        try:
            self.click_element(self.COOKIE_BANNER, timeout=3000)
            logging.info("Cookie banner accepted.")
        except Exception:
            logging.info("No cookie banner found.")

    def search_city(self, city_name: str):
        self.fill_text(self.SEARCH_INPUT, city_name)

        # 1. Wait for the auto-suggest dropdown to actually appear
        self.page.wait_for_selector(self.FIRST_RESULT, state="visible", timeout=10000)

        # 2. Click the first suggestion in the dropdown (DO NOT press Enter)
        self.page.locator(self.FIRST_RESULT).first.click()

        # 3. Wait for the city dashboard to load before moving to the next step
        self.page.wait_for_load_state("domcontentloaded")

    def go_to_daily_forecast(self):
        self.click_element(self.DAILY_MENU)