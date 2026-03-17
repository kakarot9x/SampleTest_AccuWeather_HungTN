# AccuWeather Test Automation Framework

A robust, scalable UI test automation framework built with Python, Playwright, and Pytest. This project automates the extraction and validation of 30-day daily weather forecasts from AccuWeather, built with a focus on speed, resilience, and rich reporting.

## 🚀 Key Features
* **Modern Stack:** Python + Playwright for fast, reliable browser automation.
* **Environment Management:** Powered by `uv` for lightning-fast dependency and virtual environment management.
* **Architecture:** Strict Page Object Model (POM) design pattern for maintainability.
* **Data-Driven Testing:** Utilizes `@pytest.mark.parametrize` to dynamically run tests across multiple cities (e.g., New York, London, Tokyo).
* **Parallel Execution:** Cuts execution time using `pytest-xdist` to run UI tests concurrently across multiple workers.
* **Auto-Retries:** Gracefully handles UI flakiness with `pytest-rerunfailures`.
* **Dual Reporting:** * `pytest-html`: Generates a portable, single-file HTML report with embedded Base64 failure screenshots for quick sharing.
  * `Allure`: Generates a comprehensive, historical analytics dashboard with natively attached screenshots.
* **Data Export:** Automatically parses temperature strings, mathematically validates Fahrenheit to Celsius conversion, and exports results to timestamped `.csv` files using `pandas`.
* **CI/CD Ready:** Includes a GitHub Actions workflow for scheduled (hourly) headless execution.

---

## 📂 Project Structure

```text
weather_tests/
├── .github/workflows/
│   └── weather_test.yml       # Hourly execution CI/CD pipeline
├── pages/
│   ├── base_page.py           # Core Playwright wrapper methods
│   ├── home_page.py           # Locators and actions for the Accuweather homepage
│   └── daily_forecast_page.py # Locators and actions for the daily weather view
├── tests/
│   └── test_accuweather.py    # Parameterized test execution and assertions
├── allure-results/            # Auto-generated raw JSON test data (Ignored in git)
├── conftest.py                # Global fixtures (Browser setup/teardown, screenshot hooks)
├── pytest.ini                 # Global Pytest config (Retries, parallel workers, logging)
├── pyproject.toml             # uv project configuration
├── uv.lock                    # Dependency lockfile
└── README.md