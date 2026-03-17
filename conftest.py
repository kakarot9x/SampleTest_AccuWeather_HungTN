import time

import pytest
import allure
import os
import datetime
import logging
from playwright.sync_api import sync_playwright

from pages.home_page import HomePage

log = logging.getLogger(__name__)
STATE_FILE = "state.json"
LOCK_FILE = "state.lock"

# Log File Configuration
def pytest_configure(config):
    """
    Creates the output/logs directory and sets a dynamic timestamped log file per worker.
    """
    worker_id = os.environ.get('PYTEST_XDIST_WORKER')

    # Check if the '-n' flag was passed to pytest
    num_workers = getattr(config.option, "numprocesses", None)

    # If this is the Master node in a parallel run, send its logs to the void
    if num_workers is not None and not worker_id:
        config.option.log_file = os.devnull
        return

    # Create the nested directory structure
    log_dir = os.path.join("output", "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Generate timestamp for the file name
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")

    # If running sequentially, fallback to 'main'
    worker_name = worker_id if worker_id else 'main'
    log_file_path = os.path.join(log_dir, f"test_run_{timestamp}_{worker_name}.log")

    # Override Pytest's internal log_file option dynamically
    config.option.log_file = log_file_path


# Custom Command Line Options for execution flexibility
def pytest_addoption(parser):
    parser.addoption("--headless", action="store_true", default=False, help="Run browser in headless mode")
    parser.addoption("--browser-type", action="store", default="chromium", help="chromium, firefox, or webkit")


@pytest.fixture(scope="function")
def page(request):
    headless_mode = request.config.getoption("--headless")
    browser_name = request.config.getoption("--browser-type")

    # 1. Anti-Bot Launch Arguments
    launch_args = [
        "--disable-blink-features=AutomationControlled"  # Hides Playwright from basic bot detectors
    ]
    launch_kwargs = {"headless": headless_mode}

    if not headless_mode:
        launch_args.append("--start-maximized")
        if browser_name == "chromium":
            launch_kwargs["channel"] = "chrome"
    else:
        # THE FIX FOR GITHUB ACTIONS HTTP/2 ERROR
        launch_args.append("--disable-http2")

    launch_kwargs["args"] = launch_args

    with sync_playwright() as p:
        browser_type = getattr(p, browser_name)
        browser = browser_type.launch(**launch_kwargs)

        context_kwargs = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "permissions": ["geolocation"],
            "ignore_https_errors": True  # Prevents SSL handshake failures in CI
        }

        if headless_mode:
            context_kwargs["viewport"] = {"width": 1920, "height": 1080}
        else:
            context_kwargs["no_viewport"] = True

        # ==========================================
        # ONE-TIME SETUP WITH PARALLEL LOCKING
        # ==========================================
        if not os.path.exists(STATE_FILE):
            # Check if another worker is already creating the state file
            if os.path.exists(LOCK_FILE):
                print("\n[INFO] Another worker is setting up state. Waiting...")
                while not os.path.exists(STATE_FILE):
                    time.sleep(1)  # Wait in 1-second increments
            else:
                # Claim the lock so other workers wait
                open(LOCK_FILE, 'w').close()
                print("\n[INFO] Lock claimed. Performing global setup...")
                try:
                    setup_context = browser.new_context(**context_kwargs)
                    setup_page = setup_context.new_page()
                    setup_home = HomePage(setup_page)

                    setup_home.navigate("https://www.accuweather.com")
                    setup_home.accept_cookies_if_present()
                    setup_home.configure_fahrenheit()

                    setup_context.storage_state(path=STATE_FILE)
                    setup_context.close()
                    print("[INFO] Setup complete. State saved.")
                finally:
                    # Always clean up the lock file, even if the setup fails
                    if os.path.exists(LOCK_FILE):
                        os.remove(LOCK_FILE)

        # ==========================================
        # STANDARD TEST CONTEXT
        # ==========================================
        context = browser.new_context(
            **context_kwargs,
            storage_state=STATE_FILE
        )

        page = context.new_page()
        yield page

        context.close()
        browser.close()


# Hook for taking screenshots on failure and attaching to Allure
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Automatically takes a screenshot if a test fails.
    """
    outcome = yield
    report = outcome.get_result()

    # We only care about the actual test execution phase (call), not setup/teardown
    if report.when == "call" and report.failed:
        # Access the 'page' fixture from the failing test
        page_fixture = item.funcargs.get('page')
        if page_fixture:
            try:
                screenshot = page_fixture.screenshot(full_page=True)
                allure.attach(
                    screenshot,
                    name="screenshot_on_failure",
                    attachment_type=allure.attachment_type.PNG
                )
                log.error("Test failed. Screenshot captured and attached to Allure.")
            except Exception as e:
                log.error(f"Failed to take screenshot: {e}")
