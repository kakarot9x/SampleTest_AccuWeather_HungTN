import re
import logging
from typing import List, Dict
from pages.base_page import BasePage

# Initialize logger
log = logging.getLogger(__name__)

class DailyForecastPage(BasePage):
    DAILY_WRAPPER = ".daily-wrapper"
    TOP_SUMMARY = ".page-title, .title, h1"

    def _convert_f_to_c(self, f_temp: int) -> int:
        return round((f_temp - 32) * 5.0 / 9.0)

    def extract_forecast_data(self) -> List[Dict]:
        log.info("Waiting for daily forecast wrapper to load...")
        self.page.wait_for_selector(self.DAILY_WRAPPER, state="attached", timeout=15000)

        summary_loc = self.page.locator(".module-title").first
        top_summary = summary_loc.text_content().strip() if summary_loc.count() > 0 else "Summary Not Found"

        log.info(f"Forecast Header: '{top_summary}'")

        wrappers = self.page.locator(self.DAILY_WRAPPER).all()
        weather_data = []

        for i, wrapper in enumerate(wrappers):
            date_loc = wrapper.locator("h2.date").first
            day_value = re.sub(r'\s+', ' ', date_loc.text_content().strip()) if date_loc.count() > 0 else f"Day {i + 1}"

            high_loc = wrapper.locator(".temp .high").first
            high_temp = high_loc.text_content().strip() if high_loc.count() > 0 else "N/A"

            low_loc = wrapper.locator(".temp .low").first
            low_temp = low_loc.text_content().replace("/", "").strip() if low_loc.count() > 0 else "N/A"

            phrase_loc = wrapper.locator(".phrase").first
            condition = phrase_loc.text_content().strip() if phrase_loc.count() > 0 else "N/A"

            rf_loc = wrapper.locator(".panel-item:has-text('RealFeel®') .value").first
            real_feel = rf_loc.text_content().strip() if rf_loc.count() > 0 else "N/A"

            raw_temp = re.sub(r'[^\d\-]', '', high_temp)
            temp_f = "N/A"
            temp_c_calc = "N/A"

            if raw_temp:
                try:
                    temp_f = int(raw_temp)
                    temp_c_calc = self._convert_f_to_c(temp_f)
                except ValueError:
                    pass

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

        # Log the final count before returning the data
        log.info(f"Successfully extracted weather data for {len(weather_data)} days.")
        return weather_data