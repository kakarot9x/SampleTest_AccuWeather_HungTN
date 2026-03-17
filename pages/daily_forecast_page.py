from pages.base_page import BasePage
import re

class DailyForecastPage(BasePage):
    # Locators
    DAILY_WRAPPER = ".daily-wrapper"
    DAILY_CARDS = ".daily-wrapper .daily-forecast-card"  # Adjusted for better specificity

    def _convert_f_to_c(self, f_temp: int) -> int:
        return round((f_temp - 32) * 5.0 / 9.0)

    def extract_forecast_data(self, limit=5):
        # Wait for the cards to exist in the DOM
        self.page.wait_for_selector(".daily-wrapper .daily-forecast-card", state="attached", timeout=15000)
        cards = self.page.locator(".daily-wrapper .daily-forecast-card").all()

        weather_data = []
        for i, card in enumerate(cards[:limit]):
            # 1. Defensive Date (Cleaned up with regex)
            date_loc = card.locator(".date").first
            if date_loc.count() > 0:
                raw_date = date_loc.text_content().strip()
                date_text = re.sub(r'\s+', ' ', raw_date)  # Turns "Tue \t\t 3/17" into "Tue 3/17"
            else:
                date_text = f"Day {i + 1}"

            # 2. Defensive High Temp
            high_loc = card.locator(".high").first
            high_temp_str = high_loc.text_content().strip() if high_loc.count() > 0 else "N/A"

            # 3. THE FIX: Defensive Phrase
            phrase_loc = card.locator(".phrase").first
            weather_desc = phrase_loc.text_content().strip() if phrase_loc.count() > 0 else "N/A"

            # 4. Defensive Real Feel
            panel = card.locator(".half-day-card.day").first
            real_feel_loc = panel.locator(".real-feel").first
            real_feel = real_feel_loc.text_content().strip() if real_feel_loc.count() > 0 else "N/A"

            # Add to your list
            weather_data.append({
                "Date": date_text,
                "High_Temp": high_temp_str,
                "Condition": weather_desc,
                "Real_Feel": real_feel
            })

        return weather_data