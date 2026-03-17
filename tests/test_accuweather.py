import pytest
import pandas as pd
import datetime
import allure
import os
import json
import re
from playwright.sync_api import expect
from pages.home_page import HomePage
from pages.daily_forecast_page import DailyForecastPage


# ==========================================
# Data Provider Helper
# ==========================================
def load_test_data():
    """
    Reads the list of cities dynamically from the JSON file.
    """
    # This safely gets the path to data/test_data.json no matter where you run the test from
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_file_path = os.path.join(current_dir, "..", "data", "test_data.json")

    with open(data_file_path, "r") as file:
        return json.load(file)


# ==========================================
# Test Execution
# ==========================================
# Pytest call load_test_data() and run the test once for every city in the JSON array
@pytest.mark.parametrize("city", load_test_data())
@allure.feature("Weather Data Extraction")
@allure.story("Daily Forecast Validation")
def test_accuweather_daily_forecast(page, city):
    allure.dynamic.title(f"Extract and validate daily weather forecast for {city}")

    home_page = HomePage(page)
    daily_page = DailyForecastPage(page)

    with allure.step("Navigate to AccuWeather (with injected settings)"):
        # load the site in the new context before searching.
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
        assert len(weather_data) > 0, "Failed to retrieve weather data"

        first_day = weather_data[0]
        assert "Day_Value" in first_day, "Missing Day Value string"
        assert "Condition" in first_day, "Missing Condition data"

        # Validate the Math Requirement
        f_val = first_day["Extracted_Integer_F"]
        c_val = first_day["Calculated_Celsius"]

        if f_val != "N/A":
            expected_c = round((f_val - 32) * 5.0 / 9.0)
            assert c_val == expected_c, f"Math Validation Failed! Expected {expected_c}C but calculated {c_val}C"

    with allure.step(f"Save {city} extracted data to CSV"):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_city_name = city.replace(" ", "_").lower()

        # 1. Create the output/data directory safely
        data_dir = os.path.join("output", "data")
        os.makedirs(data_dir, exist_ok=True)

        # 2. Route the filename to that new directory
        filename = os.path.join(data_dir, f"weather_report_{safe_city_name}_{timestamp}.csv")

        df = pd.DataFrame(weather_data)
        df.to_csv(filename, index=False)
        allure.attach.file(filename, name=f"CSV_Report_{safe_city_name}", attachment_type=allure.attachment_type.CSV)