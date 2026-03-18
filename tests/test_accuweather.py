import os
import json
import re
import datetime
import pytest
import pandas as pd
import allure
import logging
from playwright.sync_api import expect
from pages.home_page import HomePage
from pages.daily_forecast_page import DailyForecastPage

# Initialize logger
log = logging.getLogger(__name__)


def load_test_data():
    """Reads the list of target cities dynamically from the JSON configuration."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_file_path = os.path.join(current_dir, "..", "data", "test_data.json")

    with open(data_file_path, "r") as file:
        return json.load(file)

@pytest.mark.parametrize("city", load_test_data())
@allure.feature("Weather Data Extraction")
@allure.story("Daily Forecast Validation")
def test_accuweather_daily_forecast(page, city):
    allure.dynamic.title(f"Extract and validate daily weather forecast for {city}")
    log.info(f"========== STARTING TEST FOR: {city.upper()} ==========")

    home_page = HomePage(page)
    daily_page = DailyForecastPage(page)

    with allure.step("Navigate to AccuWeather (with injected settings)"):
        home_page.navigate("https://www.accuweather.com")

    with allure.step(f"Search for city: {city}"):
        home_page.search_city(city)
        url_formatted_city = city.lower().replace(" ", "-")
        expect(page).to_have_url(re.compile(f".*{url_formatted_city}.*"), timeout=15000)

    with allure.step("Navigate to Daily Forecast menu"):
        home_page.go_to_daily_forecast()

    with allure.step("Extract weather data for ALL available days"):
        weather_data = daily_page.extract_forecast_data()

    with allure.step("Validate data extraction and Temperature Conversion"):
        log.info(f"Validating mathematical temperature conversions for {city}...")
        assert len(weather_data) > 0, "Failed to retrieve weather data."

        first_day = weather_data[0]
        assert "Day_Value" in first_day, "Missing Day Value string."
        assert "Condition" in first_day, "Missing Condition data."

        f_val = first_day["Extracted_Integer_F"]
        c_val = first_day["Calculated_Celsius"]

        if f_val != "N/A":
            expected_c = round((f_val - 32) * 5.0 / 9.0)
            assert c_val == expected_c, f"Math Validation Failed! Expected {expected_c}C but calculated {c_val}C"
            log.info(f"Math validation passed! ({f_val}F correctly calculated as {expected_c}C)")

    with allure.step(f"Save {city} extracted data to CSV"):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_city_name = city.replace(" ", "_").lower()

        data_dir = os.path.join("output", "data")
        os.makedirs(data_dir, exist_ok=True)

        filename = os.path.join(data_dir, f"weather_report_{safe_city_name}_{timestamp}.csv")

        df = pd.DataFrame(weather_data)
        df.to_csv(filename, index=False)

        log.info(f"Successfully saved {len(weather_data)} rows to {filename}")

        allure.attach.file(
            filename,
            name=f"CSV_Report_{safe_city_name}",
            attachment_type=allure.attachment_type.CSV
        )

    log.info(f"========== COMPLETED TEST FOR: {city.upper()} ==========\n")