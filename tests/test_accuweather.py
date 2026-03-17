import pytest
import pandas as pd
import datetime
import allure
from pages.home_page import HomePage
from pages.daily_forecast_page import DailyForecastPage


@allure.feature("Weather Data Extraction")
@allure.story("Daily Forecast Validation")
@allure.title("Extract and validate daily weather forecast for a specific city")
def test_accuweather_daily_forecast(page):  # 'page' comes from our conftest.py fixture
    home_page = HomePage(page)
    daily_page = DailyForecastPage(page)

    city = "New York"

    with allure.step("Navigate to Accuweather and accept cookies"):
        home_page.navigate("https://www.accuweather.com")
        home_page.accept_cookies_if_present()

    with allure.step(f"Search for city: {city}"):
        home_page.search_city(city)

    with allure.step("Navigate to Daily Forecast menu"):
        home_page.go_to_daily_forecast()

    with allure.step("Extract weather data"):
        # Set limit=30 if you want the full month, kept to 5 for quick testing
        weather_data = daily_page.extract_forecast_data(limit=5)

    with allure.step("Validate data extraction"):
        assert len(weather_data) > 0, "Failed to retrieve weather data"
        # Example assertion to prove framework works
        assert "High_Temp_F" in weather_data[0], "Temperature data missing"

    with allure.step("Save extracted data to CSV"):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"weather_report_{timestamp}.csv"
        df = pd.DataFrame(weather_data)
        df.to_csv(filename, index=False)
        allure.attach.file(filename, name="CSV_Report", attachment_type=allure.attachment_type.CSV)