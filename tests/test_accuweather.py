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
    """Reads the list of cities dynamically from the JSON file."""
    # This safely gets the path to data/test_data.json no matter where you run the test from
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_file_path = os.path.join(current_dir, "..", "data", "test_data.json")

    with open(data_file_path, "r") as file:
        return json.load(file)


# ==========================================
# Test Execution
# ==========================================
# Pytest will call load_test_data() and run the test once for every city in the JSON array
@pytest.mark.parametrize("city", load_test_data())
@allure.feature("Weather Data Extraction")
@allure.story("Daily Forecast Validation")
def test_accuweather_daily_forecast(page, city):
    allure.dynamic.title(f"Extract and validate daily weather forecast for {city}")

    home_page = HomePage(page)
    daily_page = DailyForecastPage(page)

    with allure.step("Navigate to Accuweather and accept cookies"):
        home_page.navigate("https://www.accuweather.com")
        home_page.accept_cookies_if_present()

    with allure.step(f"Search for city: {city}"):
        home_page.search_city(city)

        # This acts as a hard checkpoint. If it doesn't navigate, the test stops here.
        url_formatted_city = city.lower().replace(" ", "-")
        expect(page).to_have_url(re.compile(f".*{url_formatted_city}.*"), timeout=15000)

    with allure.step("Navigate to Daily Forecast menu"):
        home_page.go_to_daily_forecast()

    with allure.step("Extract weather data"):
        # Set limit=30 if you want the full month, kept to 5 for quick testing
        weather_data = daily_page.extract_forecast_data(limit=5)

    with allure.step("Validate data extraction"):
        assert len(weather_data) > 0, "Failed to retrieve weather data"
        assert "High_Temp" in weather_data[0], "Temperature data missing"

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