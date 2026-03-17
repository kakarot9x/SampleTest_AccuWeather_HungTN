from pages.base_page import BasePage
import re


class DailyForecastPage(BasePage):
    # Locators
    DAILY_WRAPPER = ".daily-wrapper"
    DAILY_CARDS = ".daily-wrapper .daily-forecast-card"
    TOP_SUMMARY = ".page-title, .title, h1"  # Generic headers for the top date range

    def _convert_f_to_c(self, f_temp: int) -> int:
        """Mathematical conversion from Fahrenheit to Celsius"""
        return round((f_temp - 32) * 5.0 / 9.0)

    def extract_forecast_data(self):
        # 1. Wait for the wrappers to load
        self.page.wait_for_selector(self.DAILY_WRAPPER, state="attached", timeout=15000)

        # 2. Extract Top Page Summary (e.g., "March 18 - April 16")
        summary_loc = self.page.locator(".module-title").first
        top_summary = summary_loc.text_content().strip() if summary_loc.count() > 0 else "Summary Not Found"

        # 3. Get ALL available day wrappers
        wrappers = self.page.locator(self.DAILY_WRAPPER).all()
        weather_data = []

        for i, wrapper in enumerate(wrappers):
            # Extract Date (e.g., "Wed 3/18")
            date_loc = wrapper.locator("h2.date").first
            day_value = re.sub(r'\s+', ' ', date_loc.text_content().strip()) if date_loc.count() > 0 else f"Day {i + 1}"

            # Extract Temps
            high_loc = wrapper.locator(".temp .high").first
            high_temp = high_loc.text_content().strip() if high_loc.count() > 0 else "N/A"

            low_loc = wrapper.locator(".temp .low").first
            low_temp = low_loc.text_content().replace("/", "").strip() if low_loc.count() > 0 else "N/A"

            # Extract Phrase
            phrase_loc = wrapper.locator(".phrase").first
            condition = phrase_loc.text_content().strip() if phrase_loc.count() > 0 else "N/A"

            # Extract RealFeel
            rf_loc = wrapper.locator(".panel-item:has-text('RealFeel®') .value").first
            real_feel = rf_loc.text_content().strip() if rf_loc.count() > 0 else "N/A"

            # 4. Temperature Validation Logic (Using High Temp)
            raw_temp = re.sub(r'[^\d\-]', '', high_temp)  # Strip out "°" or "F"
            temp_f = "N/A"
            temp_c_calc = "N/A"

            if raw_temp:
                try:
                    temp_f = int(raw_temp)
                    temp_c_calc = self._convert_f_to_c(temp_f)
                except ValueError:
                    pass

            # Append to master list
            weather_data.append({
                "Top_Page_Summary": top_summary,
                "Day_Value": day_value,
                "High_Temp": high_temp,
                "Low_Temp": low_temp,
                "Condition": condition,
                "RealFeel": real_feel,
                "Extracted_Integer_F": temp_f,
                "Calculated_Celsius": temp_c_calc
            })

        return weather_data