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
        # Now wait for the specific result to appear in the DOM
        dropdown_result = self.page.locator(
            self.FIRST_RESULT,
            has_text=re.compile(city_name, re.IGNORECASE)
        ).first

        dropdown_result.wait_for(state="attached", timeout=15000)

        # We extract both the potential link AND the raw location key
        target_data = dropdown_result.evaluate("""(el) => {
            return {
                link: el.getAttribute('href') || el.getAttribute('data-href') || el.getAttribute('data-link'),
                key: el.getAttribute('data-location-key')
            }
        }""")

        if target_data and target_data['link']:
            target_link = target_data['link']

            # THE ULTIMATE BYPASS: If they try to route us through the trap, build the URL manually!
            if "/web-api/three-day-redirect" in target_link and target_data['key']:
                location_key = target_data['key']
                # Create a safe URL string (e.g., "New York" -> "new-york")
                safe_city = city_name.lower().replace(" ", "-")

                # Build the direct URL. (AccuWeather will auto-correct the country code if 'us' is wrong)
                target_url = f"https://www.accuweather.com/en/us/{safe_city}/{location_key}/weather-forecast/{location_key}"
                log.info(f"Detected redirect trap! Built direct URL: {target_url}")

            else:
                # If it's a normal link, use it.
                target_url = f"https://www.accuweather.com{target_link}" if target_link.startswith("/") else target_link
                log.info(f"Extracted normal URL successfully: {target_url}")

            # Go directly to the URL, ignoring heavy ad-trackers
            self.page.goto(target_url, wait_until="commit", timeout=20000)
            self.page.wait_for_load_state("domcontentloaded")
        else:
            log.warning(f"Could not extract URL for {city_name}. Executing safe click fallback.")
            # TAdd force=True so Playwright clicks it even if it thinks it is hidden
            dropdown_result.click(force=True, no_wait_after=True)
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