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

        # 1. THE "DEEP-LINK" BYPASS
        # Instead of typing, we go straight to the Search Results page.
        # This bypasses the search-bar trackers and the redirect-trap entirely.
        encoded_city = city_name.replace(" ", "%20")
        search_url = f"https://www.accuweather.com/en/search-locations?query={encoded_city}"

        log.info(f"Bypassing search bar. Navigating to search route: {search_url}")
        # We use 'domcontentloaded' because the WAF often hangs 'load' events
        self.page.goto(search_url, wait_until="domcontentloaded", timeout=25000)

        # 2. CHECK FOR DIRECT REDIRECT
        # If there's only one London or Tokyo, AccuWeather often jumps straight to the forecast.
        if "weather-forecast" in self.page.url or "current-weather" in self.page.url:
            log.info(f"Directly arrived at forecast page: {self.page.url}")
            return

        # 3. HANDLE SEARCH RESULTS PAGE
        log.info("Landed on search results page. Searching for city links...")

        # We use a broad, prioritized list of locators found across different regions
        result_selectors = [
            ".search-results a",
            ".find-location-list a",
            ".locations-list a",
            "a.search-result"
        ]

        # Combine them into one "Super Locator"
        super_locator = self.page.locator(", ".join(result_selectors))

        try:
            # Wait for any of these to appear in the DOM
            super_locator.first.wait_for(state="attached", timeout=10000)

            # Filter the links to find one that actually contains our city name
            # This prevents us from clicking "Current Location" or "Radar" links
            final_link = super_locator.filter(has_text=re.compile(city_name, re.IGNORECASE)).first

            log.info(f"Selecting result: {final_link.text_content().strip()}")
            final_link.click()
            self.page.wait_for_load_state("domcontentloaded")

        except Exception:
            # 4. CAPTCHA / BLOCK CHECK
            if self.page.get_by_text("No results found").is_visible() or \
                    self.page.get_by_text("Try searching for a city").is_visible():
                log.error(f"AccuWeather WAF Block: 'No results' page displayed for {city_name}.")
                pytest.fail("WAF Soft-Block: AccuWeather returned an empty search page.")

            if self.page.locator("iframe[src*='captcha']").count() > 0:
                pytest.fail("WAF Hard-Block: Captcha detected.")

            log.error("Failed to find any result links on the search page.")
            raise


    def go_to_daily_forecast(self):
        """Clicks the Daily menu to view the extended forecast."""
        log.info("Waiting for the Daily menu button to appear...")
        self.page.wait_for_selector(self.DAILY_MENU, state="attached", timeout=15000)
        log.info("Clicking Daily forecast menu...")
        self.page.locator(self.DAILY_MENU).click(force=True)