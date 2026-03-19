import re
import logging
import allure
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

log = logging.getLogger(__name__)


class DailyForecastPage:
    def __init__(self, page: Page):
        self.page = page
        self.day_cards = page.locator(".daily-forecast-card")

    def extract_forecast_data(self, max_days=30):
        with allure.step(f"Extracting up to {max_days} days of detailed forecast data via Crawler"):
            log.info("Collecting daily detail links...")
            self.day_cards.first.wait_for(state="visible", timeout=15000)

            count = self.day_cards.count()
            limit = min(count, max_days)
            daily_links = []

            # --- STEP 1: Harvest the URLs ---
            for i in range(limit):
                href = self.day_cards.nth(i).get_attribute("href")
                if href:
                    # Handle relative vs absolute URLs
                    full_url = f"https://www.accuweather.com{href}" if href.startswith("/") else href
                    daily_links.append(full_url)

            weather_data = []

            # --- STEP 2: Navigate to each day and scrape the deep HTML ---
            for i, url in enumerate(daily_links):
                # Strip the base domain for day 3 and beyond to make the logs much shorter
                display_url = url if i < 2 else url.replace("https://www.accuweather.com/", "")

                # Smart Logging: Only print Days 1, 2, 3, and the final day to prevent log spam
                if i < 3:
                    log.info(f"Extracting Day {i + 1} details: {display_url}")
                elif i == 3:
                    log.info("... [Extracting remaining days] ...")
                elif i == len(daily_links) - 1:
                    log.info(f"Extracting Day {i + 1} details: {display_url}")

                try:
                    # Navigate to the actual full URL
                    self.page.goto(url, timeout=20000, wait_until="domcontentloaded")
                except Exception as e:
                    log.warning(f"Failed to load Day {i + 1} URL: {e}")
                    continue

                # Helper to safely grab text from the new page structure
                def safe_text(selector, timeout=2000):
                    try:
                        return self.page.locator(selector).first.text_content(timeout=timeout).strip()
                    except PlaywrightTimeoutError:
                        return "N/A"

                # 1. Day Value (From the breadcrumb: e.g., "Thursday, March 19")
                day_value = safe_text(".subnav-pagination div")
                if day_value == "N/A":
                    day_value = f"Day {i + 1}"

                # 2. Extract High Temp
                high_temp_str = safe_text(".temperature:has-text('Hi'), .temperature")

                # 3. Condition (From the first phrase block)
                condition = safe_text(".half-day-card .phrase")

                # 4. RealFeel
                rf_raw = safe_text(".real-feel")
                rf_match = re.search(r'(RealFeel(?:®|™)?\s*\d+°)', rf_raw, re.IGNORECASE)
                real_feel = re.sub(r'\s+', ' ', rf_match.group(1)).strip() if rf_match else "N/A"

                # 5. Humidity (Using the panel items)
                try:
                    # Grab all the text from the data panels (Wind, UV, etc.)
                    all_panels = self.page.locator(".panel-item").all_inner_texts()
                    full_panel_text = " ".join(all_panels)
                    # Search for Humidity in the combined string
                    hum_match = re.search(r'(Humidity[:\s]*\d+%)', full_panel_text, re.IGNORECASE)
                    humidity = hum_match.group(1) if hum_match else "N/A"
                except:
                    humidity = "N/A"

                # 6. Day / Night Info (Grab both half-day cards and join them)
                try:
                    blocks = self.page.locator(".half-day-card").all_inner_texts()
                    clean_blocks = [re.sub(r'\s+', ' ', text).strip() for text in blocks]
                    day_night_info = " | ".join(clean_blocks) if clean_blocks else "N/A"
                except:
                    day_night_info = "N/A"

                # --- 7. Math Formatting ---
                temp_match = re.search(r'\d+', high_temp_str)
                f_val = int(temp_match.group()) if temp_match else "N/A"
                c_val = round((f_val - 32) * 5.0 / 9.0) if f_val != "N/A" else "N/A"

                data_row = {
                    "Day_Value": day_value,
                    "Condition": condition,
                    "Extracted_Integer_F": f_val,
                    "Calculated_Celsius": c_val,
                    "RealFeel": real_feel,
                    "Humidity": humidity,
                    "Day_Night_Info": day_night_info
                }

                weather_data.append(data_row)

            log.info(f"Successfully extracted data for {len(weather_data)} days.")
            return weather_data