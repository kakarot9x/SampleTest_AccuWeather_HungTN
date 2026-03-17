#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

PROJECT_DIR="weather_tests"
echo "🚀 Starting environment setup in './$PROJECT_DIR'..."

# 1. Install uv if it is not already installed
if ! command -v uv &> /dev/null; then
    echo "📦 'uv' not found. Installing astral-sh/uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source the environment so uv is available in this session
    source "$HOME/.local/bin/env" 2>/dev/null || source "$HOME/.cargo/env" 2>/dev/null
fi

# 2. Create project directory
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# 3. Create requirements.txt
# Note: Swapped pytest-html for allure-pytest
echo "📝 Creating requirements.txt..."
cat << 'EOF' > requirements.txt
pytest>=8.0.0
playwright>=1.42.0
pytest-playwright>=0.5.0
pandas>=2.2.0
allure-pytest>=2.13.2
pytest-rerunfailures>=13.0
pytest-xdist>=3.5.0
pytest-html>=4.2.0
EOF

# 4. Create a virtual environment using uv
echo "🛠️ Creating virtual environment..."
uv venv

# 5. Activate the virtual environment
# We source it here so subsequent pip/playwright commands run inside the venv
source .venv/bin/activate

# 6. Install dependencies from requirements.txt using uv's lightning-fast pip
echo "📥 Installing dependencies..."
uv pip install -r requirements.txt

# 7. Install Playwright Chromium browser inside the venv
echo "🌐 Installing Playwright Chromium..."
playwright install chromium

echo "============================================================"
echo "✅ Environment setup complete!"
echo ""
echo "👉 Next steps before you write your test:"
echo "   1. cd $PROJECT_DIR"
echo "   2. Activate the environment: source .venv/bin/activate"
echo "============================================================"