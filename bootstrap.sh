#!/bin/bash

echo "🛠️ Bootstrapping Voice Assistant Project..."

# Exit immediately on error
set -e

# Step 1: Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.10+ and rerun this script."
    exit 1
fi

# Step 2: Install system-level dependencies
echo "📦 Installing system dependencies (portaudio)..."
sudo apt update
sudo apt install -y portaudio19-dev

# Step 3: Create virtual environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists."
fi

# Step 4: Activate virtual environment
echo "⚙️ Activating virtual environment..."
source venv/bin/activate

# Step 5: Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Step 6: Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Step 7: Final message
echo "✅ Bootstrap complete. To start developing:"
echo "source venv/bin/activate"
