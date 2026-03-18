import os
import time
import datetime
import logging
import pytest
import allure
from playwright.sync_api import sync_playwright, Page
from playwright_stealth import Stealth
from pages.home_page import HomePage

# Initialize logger
log = logging.getLogger(__name__)

STATE_FILE = "state.json"
LOCK_FILE = "state.lock"


def pytest_configure(config):
    """
    Creates the output/logs directory and sets a dynamic timestamped log file per worker.
    Ensures parallel runs route logs cleanly.
    """
    worker_id = os.environ.get('PYTEST_XDIST_WORKER')
    num_workers = getattr(config.option, "numprocesses", None)

    if num_workers is not None and not worker_id:
        config.option.log_file = os.devnull
        return

    log_dir = os.path.join("output", "logs")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    worker_name = worker_id if worker_id else 'main'
    log_file_path = os.path.join(log_dir, f"test_run_{timestamp}_{worker_name}.log")

    config.option.log_file = log_file_path


def pytest_addoption(parser):
    """Custom Command Line Options for execution flexibility"""
    parser.addoption("--headless", action="store_true", default=False, help="Run browser in headless mode")
    parser.addoption("--browser-type", action="store", default="chromium", help="Browser type: chromium, firefox, or webkit")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hooks into Pytest to track test execution status for teardown actions."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(scope="function")
def page(request):
    """
    Core browser fixture. Initializes Playwright, applies bot-stealth, handles
    parallel-safe global state setup (cookies/settings), and manages failure screenshots.
    """
    headless_mode = request.config.getoption("--headless")
    browser_name = request.config.getoption("--browser-type")

    launch_args = ["--disable-blink-features=AutomationControlled"]
    launch_kwargs = {"headless": headless_mode}

    # OS Window/Network optimizations based on execution mode
    if not headless_mode:
        launch_args.append("--start-maximized")
        if browser_name == "chromium":
            launch_kwargs["channel"] = "chrome"
    else:
        launch_args.append("--disable-http2")

    launch_kwargs["args"] = launch_args

    with Stealth().use_sync(sync_playwright()) as p:
        browser_type = getattr(p, browser_name)
        browser = browser_type.launch(**launch_kwargs)

        context_kwargs = {
            "permissions": ["geolocation"],
            "ignore_https_errors": True
        }

        if headless_mode:
            context_kwargs["viewport"] = {"width": 1920, "height": 1080}
        else:
            context_kwargs["no_viewport"] = True

        # Parallel-safe global state setup
        if not os.path.exists(STATE_FILE):
            if os.path.exists(LOCK_FILE):
                log.info("Another worker is setting up global state. Waiting...")
                while not os.path.exists(STATE_FILE):
                    if not os.path.exists(LOCK_FILE):
                        pytest.fail("Primary worker crashed during setup. Aborting to prevent infinite hang.")
                    time.sleep(1)
            else:
                open(LOCK_FILE, 'w').close()
                log.info("Lock claimed. Performing one-time global setup...")
                try:
                    setup_context = browser.new_context(**context_kwargs)
                    setup_page = setup_context.new_page()
                    setup_home = HomePage(setup_page)

                    setup_home.navigate("https://www.accuweather.com")
                    setup_home.accept_cookies_if_present()
                    setup_home.configure_fahrenheit()

                    setup_context.storage_state(path=STATE_FILE)
                    setup_context.close()
                    log.info("Global setup complete. State saved.")
                finally:
                    if os.path.exists(LOCK_FILE):
                        os.remove(LOCK_FILE)

        # Standard context injection for the actual test execution
        context = browser.new_context(**context_kwargs, storage_state=STATE_FILE)
        test_page: Page = context.new_page()

        yield test_page

        # Teardown & Screenshot capture
        if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
            screenshot_dir = os.path.join(os.getcwd(), "output", "screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)

            safe_test_name = request.node.name.replace(" ", "_").replace("/", "_")
            screenshot_path = os.path.join(screenshot_dir, f"{safe_test_name}.png")

            try:
                test_page.screenshot(path=screenshot_path, timeout=5000)
                log.error(f"Test failed! Screenshot saved: {screenshot_path}")
                allure.attach.file(
                    screenshot_path,
                    name=f"Failed_{safe_test_name}",
                    attachment_type=allure.attachment_type.PNG
                )
            except Exception as e:
                log.error(f"Failed to capture screenshot: {e}")

        context.close()
        browser.close()