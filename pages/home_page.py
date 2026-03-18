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
        log.info(f"Searching for city: '{city_name}'...")
        search_input = self.page.locator(self.SEARCH_INPUT)

        search_input.click()
        search_input.clear()
        search_input.press_sequentially(city_name, delay=100)
        time.sleep(0.5)

        log.info(f"Waiting for dropdown item matching: '{city_name}'...")

        # We look for any result that matches the city name
        dropdown_result = self.page.locator(
            self.FIRST_RESULT,
            has_text=re.compile(city_name, re.IGNORECASE)
        ).first

        # Wait for it to be attached (more stable in CI than 'visible')
        dropdown_result.wait_for(state="attached", timeout=15000)

        # Extract the link and the specific location key
        target_data = dropdown_result.evaluate("""(el) => {
            return {
                link: el.getAttribute('href') || el.getAttribute('data-href') || el.getAttribute('data-link'),
                key: el.getAttribute('data-location-key')
            }
        }""")

        if target_data and target_data['link']:
            target_link = target_data['link']

            # THE CI BYPASS: Detect if this is the poisoned redirect trap
            if "/web-api/three-day-redirect" in target_link:
                # Extract the 'key' (GEO coordinates or Numeric ID) from the trap link
                match = re.search(r'key=([^&]+)', target_link)
                key = match.group(1) if match else target_data.get('key')

                if key:
                    # Navigate via the "Safe Search" route.
                    # This tells AccuWeather: "I already have the ID, just show me the page."
                    target_url = f"https://www.accuweather.com/en/search-locations?query={key}"
                    log.info(f"Redirect trap detected! Bypassing via Safe Search URL: {target_url}")
                else:
                    # Final fallback: Use the city name in the safe search route
                    target_url = f"https://www.accuweather.com/en/search-locations?query={city_name.replace(' ', '%20')}"
                    log.info(f"Redirect trap detected but no key found. Bypassing via city name: {target_url}")
            else:
                # It's a normal direct link
                target_url = f"https://www.accuweather.com{target_link}" if target_link.startswith("/") else target_link
                log.info(f"Extracted normal URL successfully: {target_url}")

            # Execute the navigation with 'commit' to prevent hanging on ad-trackers
            self.page.goto(target_url, wait_until="commit", timeout=20000)
            self.page.wait_for_load_state("domcontentloaded")

        else:
            log.warning(f"Could not extract URL for {city_name}. Executing safe click fallback.")
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