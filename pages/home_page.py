import re
import time
import logging
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
        """
        Simulates human typing to trigger the search API, identifies the correct
        dropdown item, and extracts the target URL to bypass redirect traps.
        """
        log.info(f"Searching for city: '{city_name}'...")
        search_input = self.page.locator(self.SEARCH_INPUT)

        search_input.click()
        search_input.clear()
        search_input.press_sequentially(city_name, delay=100)
        time.sleep(0.5)

        log.info(f"Waiting for dropdown item matching: '{city_name}'...")
        dropdown_result = self.page.locator(
            self.FIRST_RESULT,
            has_text=re.compile(city_name, re.IGNORECASE)
        ).first

        dropdown_result.wait_for(state="visible", timeout=15000)

        # Extract URL directly from the DOM to bypass AccuWeather tracking redirects
        target_path = dropdown_result.evaluate(
            "(el) => el.getAttribute('href') || el.getAttribute('data-href') || (el.querySelector('a') ? el.querySelector('a').getAttribute('href') : null)"
        )

        if target_path:
            target_url = f"https://www.accuweather.com{target_path}" if target_path.startswith("/") else target_path
            log.info(f"Extracted URL successfully. Navigating directly to: {target_url}")

            self.page.goto(target_url, wait_until="commit", timeout=20000)
            self.page.wait_for_load_state("domcontentloaded")
        else:
            log.debug(f"Could not extract URL for {city_name}. Executing safe click fallback.")
            dropdown_result.click(no_wait_after=True)
            try:
                self.page.wait_for_load_state("domcontentloaded", timeout=15000)
            except Exception:
                log.info("DOM load timed out during fallback click, proceeding to validation.")

    def go_to_daily_forecast(self):
        """Clicks the Daily menu to view the extended forecast."""
        log.info("Waiting for the Daily menu button to appear...")
        self.page.wait_for_selector(self.DAILY_MENU, state="attached", timeout=15000)
        log.info("Clicking Daily forecast menu...")
        self.page.locator(self.DAILY_MENU).click(force=True)