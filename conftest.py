import pytest
import allure
import os
import datetime
from playwright.sync_api import sync_playwright
import logging

log = logging.getLogger(__name__)


# =================================================================
# 1. Dynamic Log File Configuration
# =================================================================
def pytest_configure(config):
    """Creates the output/logs directory and sets a dynamic timestamped log file per worker."""
    worker_id = os.environ.get('PYTEST_XDIST_WORKER')

    # Check if the '-n' flag was passed to pytest
    num_workers = getattr(config.option, "numprocesses", None)

    # THE FIX: If this is the Master node in a parallel run, send its logs to the void
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


# 1. Custom Command Line Options for execution flexibility
def pytest_addoption(parser):
    parser.addoption("--headless", action="store_true", default=False, help="Run browser in headless mode")
    parser.addoption("--browser-type", action="store", default="chromium", help="chromium, firefox, or webkit")


# 2. Core Browser Setup & Teardown Fixture
@pytest.fixture(scope="function")
def page(request):
    """Initializes the browser, sets viewport, yields the page, and tears it down."""
    headless_mode = request.config.getoption("--headless")
    browser_name = request.config.getoption("--browser-type")

    log.info(f"Setting up {browser_name} browser. Headless: {headless_mode}")

    with sync_playwright() as p:
        browser_type = getattr(p, browser_name)
        browser = browser_type.launch(headless=headless_mode)

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            # Automatically grant location access so the native browser prompt never appears
            permissions = ["geolocation"]
        )

        page = context.new_page()

        # =================================================================
        # THE INTERCEPTOR: Block Ads, Images, and Trackers
        # =================================================================
        block_types = ["image", "media", "font"]
        ad_domains = ["googleads", "doubleclick", "criteo", "taboola", "amazon-adsystem"]

        # page.route("**/*", lambda route: route.abort()
        # if route.request.resource_type in block_types
        #    or any(ad in route.request.url for ad in ad_domains)
        # else route.continue_()
        #            )
        # =================================================================

        yield page  # <--- Test runs here

        log.info("Tearing down browser context.")
        context.close()
        browser.close()


# 3. Hook for taking screenshots on failure and attaching to Allure
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Automatically takes a screenshot if a test fails."""
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