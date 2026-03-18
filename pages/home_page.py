import re
import time
import logging

import pytest

from pages.base_page import BasePage

# Initialize logger
log = logging.getLogger(__name__)


class HomePage(BasePage):
    SEARCH_INPUT = "input.search-input"
    FIRST_RESULT = ".search-bar-result"
    DAILY_MENU = "a[data-qa='daily']"
    COOKIE_BANNER = "div.policy-accept"

    def accept_cookies_if_present(self):
        """Attempts to accept the cookie banner if it appears."""
        try:
            self.click_element(self.COOKIE_BANNER, timeout=3000)
            log.info("Cookie banner accepted.")
        except Exception:
            log.warning("No cookie banner found.")

    def configure_fahrenheit(self):
        """Navigates to settings and forces the temperature unit to Fahrenheit."""
        log.info("Navigating to dedicated settings page to force Fahrenheit...")
        self.navigate("https://www.accuweather.com/en/settings")
        self.page.wait_for_load_state("domcontentloaded")

        try:
            unit_dropdown = self.page.locator("select", has=self.page.locator("option[value='F']")).first
            if unit_dropdown.count() > 0:
                unit_dropdown.select_option("F")
                log.info("Forced browser to Fahrenheit successfully.")
                self.page.wait_for_timeout(2000)  # Allow cookie to register
            else:
                log.warning("Could not find the unit dropdown on the settings page.")
        except Exception as e:
            log.warning(f"Error while setting Fahrenheit: {e}")

        log.info("Returning to home page...")
        self.navigate("https://www.accuweather.com")

    def search_city(self, city_name: str):
        log.info(f"========== SEARCHING FOR: {city_name} ==========")

        encoded_city = city_name.replace(" ", "%20")
        search_url = f"https://www.accuweather.com/en/search-locations?query={encoded_city}"

        log.info(f"Bypassing search bar. Navigating to search route: {search_url}")
        self.page.goto(search_url, wait_until="domcontentloaded", timeout=25000)

        if "weather-forecast" in self.page.url or "current-weather" in self.page.url:
            log.info(f"Directly arrived at forecast page: {self.page.url}")
            return

        log.info("Landed on search results page. Searching for city links...")

        result_selectors = [
            ".search-results a",
            ".find-location-list a",
            ".locations-list a",
            "a.search-result"
        ]
        super_locator = self.page.locator(", ".join(result_selectors))

        try:
            # 1. Wait for the link to exist in the HTML
            super_locator.first.wait_for(state="attached", timeout=15000)

            # 2. Find the specific city link
            final_link = super_locator.filter(has_text=re.compile(city_name, re.IGNORECASE)).first

            log.info(f"Selecting result: {final_link.text_content().strip()}")

            # THE CRITICAL FIX: Use evaluate to click via JavaScript.
            # This ignores 'Breaking News' banners or ads that overlap the link.
            final_link.evaluate("el => el.click()")

            # 3. Use a soft wait for navigation
            self.page.wait_for_load_state("domcontentloaded", timeout=15000)

        except Exception as e:
            if "No results found" in self.page.content():
                pytest.fail(f"WAF Block: AccuWeather returned an empty search page for {city_name}.")
            log.error(f"Failed to interact with search results: {e}")
            raise


    def go_to_daily_forecast(self):
        """Clicks the Daily menu to view the extended forecast."""
        log.info("Waiting for the Daily menu button to appear...")
        self.page.wait_for_selector(self.DAILY_MENU, state="attached", timeout=15000)
        log.info("Clicking Daily forecast menu...")
        self.page.locator(self.DAILY_MENU).click(force=True)