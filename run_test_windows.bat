@echo off
echo ===================================================
echo   Starting AccuWeather Test Framework Setup...
echo ===================================================

:: 1. Check if uv is installed, install if missing
where uv >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [INFO] 'uv' not found. Installing 'uv' via PowerShell...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
) else (
    echo [INFO] 'uv' is already installed.
)

:: 2. Create Virtual Environment
echo [INFO] Creating virtual environment...
uv venv --clear

:: 3. Activate Virtual Environment
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat

:: 4. Install Requirements
echo [INFO] Installing dependencies from requirements.txt...
uv pip install -r requirements.txt

:: 5. Install Playwright Browsers
echo [INFO] Installing Playwright browsers...
playwright install chromium

:: 6. Run Tests
echo [INFO] Running pytest...
pytest tests/test_accuweather.py -v -s --alluredir=output/allure-results

:: 7. Generate and Serve Allure Report
echo ===================================================
echo   Reporting Phase
echo ===================================================
echo [INFO] Checking for Java (Required for Allure CLI)...
where java >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Java is not installed or not in PATH.
    echo [WARNING] Skipping Allure HTML generation. Please install Java to view reports.
    goto End
)

set ALLURE_CMD=allure
where allure >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [INFO] Allure CLI not found globally. Setting up local standalone copy...
    if not exist ".tools\allure-2.29.0\bin\allure.bat" (
        mkdir .tools 2>nul
        echo [INFO] Downloading Allure CLI...
        powershell -c "Invoke-WebRequest -Uri 'https://repo.maven.apache.org/maven2/io/qameta/allure/allure-commandline/2.29.0/allure-commandline-2.29.0.zip' -OutFile '.tools\allure.zip'"
        echo [INFO] Extracting Allure CLI...
        powershell -c "Expand-Archive -Path '.tools\allure.zip' -DestinationPath '.tools' -Force"
        del .tools\allure.zip
    )
    set ALLURE_CMD="%CD%\.tools\allure-2.29.0\bin\allure.bat"
)

echo [INFO] Generating and serving Allure report...
call %ALLURE_CMD% serve output/allure-results

:End
echo ===================================================
echo   Test Run Complete!
echo ===================================================
pause