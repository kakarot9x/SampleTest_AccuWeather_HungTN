#!/bin/bash

echo "==================================================="
echo "  Starting AccuWeather Test Framework Setup..."
echo "==================================================="

# 1. Check if uv is installed, install if missing
if ! command -v uv &> /dev/null; then
    echo "[INFO] 'uv' not found. Installing 'uv'..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
else
    echo "[INFO] 'uv' is already installed."
fi

# 2. Create Virtual Environment
echo "[INFO] Creating virtual environment..."
uv venv --clear

# 3. Activate Virtual Environment
echo "[INFO] Activating virtual environment..."
source .venv/bin/activate

# 4. Install Requirements
echo "[INFO] Installing dependencies from requirements.txt..."
uv pip install -r requirements.txt

# 5. Install Playwright Browsers and OS Dependencies
echo "[INFO] Installing Playwright browsers (Chromium & Branded Chrome)..."
playwright install chromium chrome

echo "[INFO] Installing Linux OS dependencies for Playwright..."
# Note: This command usually requires sudo privileges on Linux/GitHub Actions
playwright install-deps

# 6. Run Tests
echo "[INFO] Running pytest..."
pytest tests/test_accuweather.py -v -s --alluredir=output/allure-results

# 7. Generate and Serve Allure Report
echo "==================================================="
echo "  Reporting Phase"
echo "==================================================="
echo "[INFO] Checking for Java (Required for Allure CLI)..."
if ! command -v java &> /dev/null; then
    echo "[WARNING] Java is not installed or not in PATH."
    echo "[WARNING] Skipping Allure HTML generation. Please install Java to view reports."
else
    ALLURE_CMD="allure"
    if ! command -v allure &> /dev/null; then
        echo "[INFO] Allure CLI not found globally. Setting up local standalone copy..."
        if [ ! -f ".tools/allure-2.29.0/bin/allure" ]; then
            mkdir -p .tools
            echo "[INFO] Downloading Allure CLI..."
            # Using tgz/tar here because 'unzip' isn't always installed on minimal Linux environments
            curl -sL https://repo.maven.apache.org/maven2/io/qameta/allure/allure-commandline/2.29.0/allure-commandline-2.29.0.tgz | tar -zx -C .tools/
        fi
        ALLURE_CMD="./.tools/allure-2.29.0/bin/allure"
    fi

    echo "[INFO] Generating and serving Allure report..."
    $ALLURE_CMD serve output/allure-results
fi

echo "==================================================="
echo "  Test Run Complete!"
echo "==================================================="