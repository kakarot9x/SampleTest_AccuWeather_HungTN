import csv
import os
import json
import re
import sys

import pytest
import allure
import logging
from datetime import datetime
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

def export_forecast_to_csv(weather_data, location_identifier):
    """
    Shared helper to save weather data to CSV and attach it to the Allure report.
    """
    if not weather_data:
        pytest.fail(f"No weather data extracted to save for {location_identifier}.")

    output_dir = os.path.join("output", "data")
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = location_identifier.lower().replace(" ", "_")
    filename = os.path.join(output_dir, f"weather_report_{safe_name}_{timestamp}.csv")

    keys = weather_data[0].keys()

    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(weather_data)

    log.info(f"Successfully saved {len(weather_data)} rows to {filename}")

    allure.attach.file(
        filename,
        name=f"{location_identifier}_CSV",
        attachment_type=allure.attachment_type.CSV
    )


@pytest.mark.skipif(
    os.environ.get('CI') == 'true' or sys.platform == 'linux',
    reason="Geolocation tests are unreliable in CI/CD (Data Center IPs) and Linux runners."
)
@allure.feature("Local Weather")
@allure.story("Automatic Geolocation")
def test_weather_by_current_location(page):
    """
    Independent test that uses the 'Use Current Location' feature.
    """
    home_page = HomePage(page)
    daily_page = DailyForecastPage(page)

    with allure.step("Navigate to AccuWeather"):
        home_page.navigate("https://www.accuweather.com")

    with allure.step("Click 'Use Current Location'"):
        log.info("Focusing search bar to reveal location options...")

        # 1. Explicitly click the search input to trigger the dropdown
        search_input = page.locator("input.search-input")
        search_input.click()

        # 2. Locate the 'Use Current Location' button (text or icon)
        current_loc_btn = page.locator(".current-location-result, .icon-location").first

        # 3. Wait for it to actually become visible before clicking
        current_loc_btn.wait_for(state="visible", timeout=10000)
        log.info("Location button is visible. Clicking...")
        current_loc_btn.click()

    with allure.step("Detect Location from URL"):
        # Playwright auto-waits for the navigation, but this ensures we have the final URL
        page.wait_for_url(re.compile(r".*/weather-forecast/.*"), timeout=25000)
        current_url = page.url

        # Regex breakdown:
        # accuweather\.com/ -> matches the domain
        # [^/]+/ -> skips the language code (e.g., 'en/')
        # [^/]+/ -> skips the country code (e.g., 'vn/')
        # ([^/]+) -> CAPTURES the location slug (e.g., 'district-12')
        match = re.search(r'accuweather\.com/[^/]+/[^/]+/([^/]+)/', current_url)

        if match:
            # Converts 'district-12' to 'District 12' for a nicer Allure attachment name
            detected_location = match.group(1).title().replace("-", " ")
        else:
            log.warning("Could not parse location from URL. Falling back to 'Unknown Local'.")
            detected_location = "Unknown_Local"

        log.info(f"Dynamically detected location: {detected_location}")

    with allure.step("Export 30-Day Forecast for Current Location"):
        home_page.go_to_daily_forecast()
        weather_data = daily_page.extract_forecast_data()

        assert len(weather_data) >= 30, "Forecast data did not load properly."

        # Call the shared helper using the dynamically extracted name!
        export_forecast_to_csv(weather_data, detected_location)


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

    with allure.step("Export data to CSV"):
        export_forecast_to_csv(weather_data, city)

    log.info(f"========== COMPLETED TEST FOR: {city.upper()} ==========\n")