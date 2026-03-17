from pages.base_page import BasePage
import logging
import re


class DailyForecastPage(BasePage):
    # Locators
    DAILY_WRAPPER = ".daily-wrapper"
    DAILY_CARDS = ".daily-wrapper .daily-forecast-card"  # Adjusted for better specificity

    def _convert_f_to_c(self, f_temp: int) -> int:
        return round((f_temp - 32) * 5.0 / 9.0)

    def extract_forecast_data(self, limit=5) -> list:
        logging.info("Waiting for daily forecast cards to load...")
        self.page.wait_for_selector(self.DAILY_WRAPPER)

        cards = self.page.locator(self.DAILY_CARDS).all()
        scraped_data = []

        for card in cards[:limit]:
            card.click()
            self.page.wait_for_timeout(500)  # Small wait for UI expansion animation

            # Extract
            date_text = card.locator(".date").inner_text().replace('\n', ' ')
            high_temp_str = card.locator(".high").inner_text()
            weather_desc = card.locator(".phrase").first.inner_text()

            panel = card.locator(".half-day-card.day")
            real_feel = panel.locator(".real-feel").inner_text() if panel.locator(".real-feel").count() > 0 else "N/A"

            # Clean and calculate
            high_temp_f = int(re.sub(r'[^\d-]', '', high_temp_str))
            calculated_c = self._convert_f_to_c(high_temp_f)

            scraped_data.append({
                "Date": date_text,
                "High_Temp_F": high_temp_f,
                "Calculated_Temp_C": calculated_c,
                "Main_Weather": weather_desc,
                "Real_Feel": real_feel.replace('\n', ' ')
            })
            logging.info(f"Extracted data for: {date_text}")

        return scraped_data