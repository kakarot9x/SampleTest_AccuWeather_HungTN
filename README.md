# AccuWeather Test Automation Framework

An automation framework built with Python, Playwright, and Pytest. 
Automates the extraction and mathematical validation of daily weather forecasts from AccuWeather. 

It solves the complex modern web challenges, including aggressive Cloudflare/Akamai Bot Protection (WAFs), 
frontend debouncing, and parallel execution race conditions in CI/CD environments.

## 🚀 Key Features

* **Advanced WAF & Bot Evasion:** Integrates `playwright-stealth` (v2) and custom Chromium launch arguments (e.g., HTTP/1.1 fallback, hiding `webdriver` flags).
* **Parallel running Setup (Locking):** Utilizes a custom `.lock` file mechanism alongside `pytest-xdist`. This ensures only *one* parallel worker performs the global state setup (accepting cookies, setting Fahrenheit) while others wait, preventing self-inflicted DDoS bans, and then injects that state globally via `state.json`.
* **Advanced DOM Manipulation & Trap Bypassing:** Bypasses AccuWeather's infinite-loading tracking redirects (`/web-api/three-day-redirect`) by directly evaluating the DOM to extract `data-href` targets and navigating via `wait_until="commit"`.
* **Data-Driven Testing:** Utilizes `@pytest.mark.parametrize` to dynamically run tests across multiple cities loaded from an external `data/test_data.json` file.
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
│   └── weather_test_job.yml   # Hourly execution CI/CD pipeline
├── data/
│   └── test_data.json         # Parameterized list of target cities
├── pages/
│   ├── base_page.py           # Core Playwright wrapper methods
│   ├── home_page.py           # Locators, WAF-bypassing search, and homepage actions
│   └── daily_forecast_page.py # DOM extraction and temperature calculation logic
├── tests/
│   └── test_accuweather.py    # Parameterized test execution and assertions
├── output/                    # Auto-generated directory for all artifacts
│   ├── allure-results/        # Allure reported result 
│   ├── data/                  # Timestamped CSV exports
│   ├── logs/                  # Timestamped worker execution logs
│   └── screenshots/           # Auto-captured screenshots on failure
├── conftest.py                # Global fixtures (Stealth setup, Parallel Locks, State Injection)
├── requirements.txt           # Project dependencies (playwright, pytest, pandas, etc.)
├── run_test_windows.bat       # Windows 1-Click execution & setup script
├── run_test_linux_macos.sh    # macOS/Linux 1-Click execution & setup script
└── README.md
```

---

## 🛠️ Setup & run test (Automatically)

This repository features fully autonomous setup scripts. 
You do not need to manually configure virtual environments, install dependencies, or download reporting tools.

The execution scripts will automatically:
1. Detect and install [uv](https://docs.astral.sh/uv/) for lightning-fast dependency management.
2. Build a pristine Python Virtual Environment (`.venv`).
3. Install all required dependencies and official Playwright browser binaries.
4. Execute the Pytest suite.
5. Download a standalone, localized instance of the **Allure CLI** (if missing) to instantly generate and serve your HTML test report.

### For Windows Users
Simply double-click the `run_test_windows.bat` file in your file explorer, or execute it via terminal:
```cmd
run_test_windows.bat
```

### For macOS / Linux Users
Ensure the script has execution permissions, then run it:
```bash
chmod +x run_test_linux_macos.sh
./run_test_linux_macos.sh
```

*(Note: The scripts will automatically download the Allure CLI into a hidden `.tools/` directory. This directory is excluded via `.gitignore` to keep the repository clean).*

---

## ⚠️ CI/CD Execution Notice

### The Situation
* **Local (Pass):** Tests pass consistently in **Headed** mode.
* **GitHub Actions (Block):** AccuWeather's security (Akamai/Cloudflare) often blocks Headless browsers or Data Center IPs (GitHub/Azure) to prevent scraping.

### Why it happens
The website identifies the GitHub runner as a bot. 
It responds by "Tarpitting" (freezing) the connection or showing "No Results," which causes timeouts in headless environments.

### Current Workaround
We use **XVFB (Virtual Frame Buffer)** in GitHub Actions to simulate a headed browser environment, 
which bypasses the most basic headless detection filters.
