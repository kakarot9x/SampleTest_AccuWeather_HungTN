# AccuWeather Test Automation Framework

An automation framework built with Python, Playwright, and Pytest. 
Automates the extraction and mathematical validation of daily weather forecasts from AccuWeather. 

It solves the complex modern web challenges, including aggressive Cloudflare/Akamai Bot Protection (WAFs), 
frontend debouncing, and parallel execution race conditions in CI/CD environments.

## 🚀 Key Features

* **Advanced WAF & Bot Evasion:** Integrates `playwright-stealth` (v2) and custom Chromium launch arguments (e.g., HTTP/1.1 fallback, hiding `webdriver` flags)
* **Smart Parallel Setup (Locking):** Utilizes a custom `.lock` file mechanism alongside `pytest-xdist`. This ensures only *one* parallel worker performs the global state setup (accepting cookies, setting Fahrenheit) while others wait, preventing self-inflicted DDoS bans, and then injects that state globally via `state.json`.
* **Advanced DOM Manipulation & Trap Bypassing:** Bypasses AccuWeather's infinite-loading tracking redirects (`/web-api/three-day-redirect`) by directly evaluating the DOM to extract `data-href` targets and navigating via `wait_until="commit"`.
* **Data-Driven Testing:** Utilizes `@pytest.mark.parametrize` to dynamically run tests across multiple cities loaded from an external `data/test_data.json` file.
* **Humanized Interactions:** Uses sequential keystroke delays (`press_sequentially`) to successfully trigger modern React/Vue frontend debouncing algorithms on search inputs.
* **Rich Reporting & Artifacts:** * Automatically generates timestamped execution `.log` files per worker.
  * Captures precision screenshots specifically on test failure.
  * Integrates with **Allure** for historical analytics, attaching screenshots and CSVs natively to the visual report.
* **Data Export:** Automatically parses complex temperature strings, mathematically validates Fahrenheit to Celsius conversions, and exports cleanly formatted results to timestamped `.csv` files using `pandas`.
* **CI/CD Ready:** Includes a GitHub Actions workflow for scheduled headless execution, utilizing `uv` for lightning-fast dependency management and artifact uploading.


---

## 📂 Project Structure

```text
weather_tests/
├── .github/workflows/
│   └── weather_test.yml       # Hourly execution CI/CD pipeline
├── data/
│   └── test_data.json         # Parameterized list of target cities
├── pages/
│   ├── base_page.py           # Core Playwright wrapper methods
│   ├── home_page.py           # Locators, WAF-bypassing search, and homepage actions
│   └── daily_forecast_page.py # DOM extraction and temperature calculation logic
├── tests/
│   └── test_accuweather.py    # Parameterized test execution and assertions
├── output/                    # Auto-generated directory for all artifacts
│   ├── data/                  # Timestamped CSV exports
│   ├── logs/                  # Timestamped worker execution logs
│   └── screenshots/           # Auto-captured screenshots on failure
├── conftest.py                # Global fixtures (Stealth setup, Parallel Locks, State Injection)
├── requirements.txt           # Project dependencies (playwright, pytest, pandas, etc.)
└── README.md
```

## ⚠️ CI/CD execution notice
* **The situation**
  * Local (Pass): Tests work perfectly on residential/office IPs. 
  * GitHub Actions (Fail): AccuWeather blocks "Cloud IPs" (Azure/GitHub) to prevent bot scraping.

* **Why it happens**
  - AccuWeather’s security (Akamai/Cloudflare) identifies the GitHub runner as a data center bot. Even with our "stealth" code, the site intentionally hangs the connection (Tarpitting) or returns empty results to stop us.

* **How to fix (Production)**
  * To get a green pipeline in a professional environment, you would need:
  * Residential Proxies: Route traffic through "real" home IPs.
  * Self-Hosted Runners: Run the tests on a private machine with a whitelisted IP.
