import csv
import os
import json
import re
import sys

import pytest
import allure
import logging
from datetime import datetime
from playwright.sync_api import expect, TimeoutError as PlaywrightTimeoutError
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


def validate_all_days_data(weather_data, location):
    """
    Loops through EVERY extracted day to validate data presence and F-to-C math.
    """
    log.info(f"Validating fields and mathematical conversions for all days in {location}...")
    assert len(weather_data) > 0, f"Failed to retrieve weather data for {location}."

    for index, day in enumerate(weather_data):
        day_name = day.get('Day_Value', f'Row {index}')

        # 1. Field presence validation
        expected_keys = [
            "Day_Value",
            "Condition",
            "Extracted_Integer_F",
            "Calculated_Celsius",
            "RealFeel",
            "Humidity",
            "Day_Night_Info"
        ]

        for key in expected_keys:
            assert key in day, f"Data Validation Failed on {day_name}: Missing key '{key}'"

        # 2. Mathematical Validation (F to C)
        f_val = day.get("Extracted_Integer_F")
        c_val = day.get("Calculated_Celsius")

        if f_val != "N/A" and isinstance(f_val, (int, float)):
            expected_c = round((f_val - 32) * 5.0 / 9.0)
            assert c_val == expected_c, (
                f"Math Validation Failed on {day_name}! "
                f"Fahrenheit: {f_val}F -> Expected {expected_c}C, but got {c_val}C"
            )

    log.info(f"Successfully validated all {len(weather_data)} days for {location}!")


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

        search_input = page.locator("input.search-input")
        current_loc_btn = page.locator(".current-location-result, .icon-location").first

        # Active Retry Loop to defeat "Dead Clicks"
        redirected = False
        for attempt in range(3):
            search_input.click()  # Ensure dropdown is open
            current_loc_btn.wait_for(state="visible", timeout=5000)

            log.info(f"Clicking location button (Attempt {attempt + 1})...")
            current_loc_btn.click(force=True)

            try:
                # We wait 8 seconds to see if the URL changes to a city page
                page.wait_for_url(re.compile(r".*accuweather\.com/[^/]+/[^/]+/.+"), timeout=8000)
                redirected = True
                break  # Success! Exit the loop.
            except PlaywrightTimeoutError:
                log.warning("Click did not trigger redirect. React may be hydrating. Retrying...")

        if not redirected:
            pytest.fail("Failed to trigger Geolocation redirect after 3 attempts.")

    with allure.step("Detect Location from URL"):
        current_url = page.url
        match = re.search(r'accuweather\.com/[^/]+/[^/]+/([^/]+)/', current_url)

        if match:
            detected_location = match.group(1).title().replace("-", " ")
        else:
            log.warning("Could not parse location from URL. Falling back to 'Unknown Local'.")
            detected_location = "Unknown_Local"

        log.info(f"Dynamically detected location: {detected_location}")

    with allure.step("Extract and Validate 30-Day Forecast"):
        home_page.go_to_daily_forecast()
        weather_data = daily_page.extract_forecast_data()

        # Use the new shared validation loop
        validate_all_days_data(weather_data, detected_location)

    with allure.step("Export data to CSV"):
        export_forecast_to_csv(weather_data, detected_location)

    log.info(f"========== COMPLETED TEST FOR: {detected_location.upper()} ==========\n")


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

    with allure.step("Extract and Validate ALL available days"):
        weather_data = daily_page.extract_forecast_data()

        # Use the new shared validation loop
        validate_all_days_data(weather_data, city)

    with allure.step("Export data to CSV"):
        export_forecast_to_csv(weather_data, city)

    log.info(f"========== COMPLETED TEST FOR: {city.upper()} ==========\n")