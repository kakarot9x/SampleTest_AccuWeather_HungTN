import pytest
import logging
import allure
from playwright.sync_api import sync_playwright


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

    logging.info(f"Setting up {browser_name} browser. Headless: {headless_mode}")

    with sync_playwright() as p:
        # Dynamically select browser based on CLI arg
        browser_type = getattr(p, browser_name)
        browser = browser_type.launch(headless=headless_mode)

        # Configure context (Screen size, user-agent, etc.)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            # Optional: Add user-agent to help bypass basic bot detection
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        page = context.new_page()

        yield page  # <--- Test runs here

        logging.info("Tearing down browser context.")
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
                logging.error("Test failed. Screenshot captured and attached to Allure.")
            except Exception as e:
                logging.error(f"Failed to take screenshot: {e}")